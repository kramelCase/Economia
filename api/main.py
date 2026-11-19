"""Interface web : pages par question, en FR/EN, chaque chiffre relié à sa source.

Lancer : make serve  (http://127.0.0.1:8790)
"""

from __future__ import annotations

import json
import random
import sqlite3
import unicodedata
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from api import queries as q
from api.i18n import DEFAULT_LANG, LANG_NAMES, LANGS, integer, money, share, translations
from api.lexique import Alias, compile_aliases, link_terms
from pipeline.catalog import ROOT

app = FastAPI(title="Economia", docs_url=None, redoc_url=None)
from api.adresses import adresses, traduire_liens  # noqa: E402
app.middleware("http")(adresses)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(),
                  extensions=["jinja2.ext.i18n"])
con = q.connect()

# Agrégats OFGL présentés sur la fiche d'une collectivité (dans cet ordre).
AGREGATS_FICHE = ("Dépenses totales", "Dépenses de fonctionnement", "Frais de personnel", "Dépenses d'intervention",
                  "Dépenses d'investissement", "Dépenses d'équipement", "Recettes totales", "Epargne brute",
                  "Encours de dette")
SECTEURS = ("S13", "S1311", "S1313", "S1314")
FONCTION_AGREGAT = "Dépenses totales hors remb"


# --- Sources : la mention discrète sous chaque graphique et chaque tableau ---
@lru_cache(maxsize=None)
def source_info(sid: str) -> dict[str, Any]:
    """Citation du jeu officiel : titre, identifiant, date de mise à jour et adresse, tous relevés dans un fichier
    collecté (table `document`) ; la description citée est celle que publie l'éditeur."""
    s = con.execute("SELECT * FROM source WHERE id=?", (sid,)).fetchone()
    if s is None:
        raise KeyError(f"source inconnue : {sid}")
    f = con.execute("SELECT MAX(collecte) c FROM fichier WHERE source_id=?", (sid,)).fetchone()["c"]
    docs = [dict(r) for r in con.execute(
        """SELECT d.*, fi.chemin, fi.url fichier_url FROM document d JOIN fichier fi ON fi.id = d.fichier_id
           WHERE d.source_id=? ORDER BY CASE d.role WHEN 'jeu' THEN 0 WHEN 'page' THEN 1 WHEN 'metadonnees' THEN 2
           ELSE 3 END, d.titre""", (sid,))]
    jeu = next(d for d in docs if d["role"] == "jeu")
    lic = next((d for d in docs if d["role"] == "licence"), None)
    desc = next((d for d in docs if d["extrait"] and d["role"] != "licence"), None)
    return {"id": sid, "titre": jeu["titre"], "titre_en": jeu["titre_en"], "editeur": s["editeur"],
            "editeur_court": s["editeur"].split(",")[0], "identifiant": jeu["identifiant"], "maj": jeu["date_maj"],
            "url": jeu["url"], "collecte": f, "documents": [d for d in docs if d["role"] != "licence"], "licence": lic,
            "extrait": desc["extrait"] if desc else None, "extrait_lang": desc["extrait_lang"] if desc else None}


def src_info(ids: Any) -> list[dict[str, Any]]:
    """Sources d'une figure, dans l'ordre donné, sans doublon. Une source inconnue ou une liste vide font échouer le
    rendu : une figure sans source ne doit pas s'afficher."""
    out = [source_info(i) for i in dict.fromkeys(x for x in ids if x)]
    if not out:
        raise ValueError("figure sans source")
    return out


def sources_de(montant_ids: Any) -> list[str]:
    """Sources des montants affichés dans une figure : la mention suit les données, elle n'est pas écrite à la main."""
    ids = sorted({int(i) for i in montant_ids if i})
    out: list[str] = []
    for k in range(0, len(ids), 900):
        part = ids[k:k + 900]
        out += [r[0] for r in con.execute(
            f"""SELECT DISTINCT fi.source_id FROM montant m JOIN fichier fi ON fi.id = m.fichier_id
                WHERE m.id IN ({','.join('?' * len(part))})""", part)]
    return sorted(set(out))


env.globals["src_info"] = src_info
env.globals["source_info"] = source_info


@lru_cache(maxsize=None)
def linker(lang: str):
    return compile_aliases([Alias(c, a) for c, a in q.aliases(con, lang)])


@lru_cache(maxsize=None)
def concepts_index(lang: str) -> dict[str, dict[str, Any]]:
    return {c["id"]: c for c in q.concepts(con, lang)}


def render(request: Request, lang: str, template: str, **ctx) -> HTMLResponse:
    if lang not in LANGS:
        raise HTTPException(404)
    tr = translations(lang)
    env.install_gettext_translations(tr, newstyle=True)
    path = request.url.path
    other = {l: "/" + l + path[len(lang) + 1:] for l in LANGS}
    from api.portes import ariane, entree_courante, entrees  # importé ici : api.portes importe ce module
    from api.colonnes import icone
    ctx.setdefault("icone", icone)
    page = env.get_template(template).render(
        lang=lang, langs=LANG_NAMES, other=other, path=path, query=str(request.url.query), cmd_pages=cmd_pages(lang),
        menu=entrees(lang), menu_courant=entree_courante(lang, path), ariane=ariane(lang, path),
        money=lambda v, u="EUR": money(v, lang, u), share=lambda a, b: share(a, b, lang),
        integer=lambda n: integer(n, lang), nom_entite=lambda n: nom_entite(n, lang), **ctx)
    pattern, lookup = linker(lang)
    page, used = link_terms(page, pattern, lookup, f"/{lang}/lexique")
    # Infobulles : définitions courtes des seuls termes présents sur la page.
    idx = concepts_index(lang)
    tips = {cid: {"terme": idx[cid]["terme"],
                  "def": (idx[cid]["definition"] or "").split("\n\n")[0][:420],
                  "src": idx[cid]["source_titre"] or "", "statut": idx[cid]["statut"],
                  "officielle": idx[cid]["officielle"], "langue": idx[cid]["langue_def"]}
            for cid in used if cid in idx}
    payload = json.dumps(tips, ensure_ascii=False).replace("</", "<\\/")
    page = page.replace("<!--TIPS-->", f'<script id="tips" type="application/json">{payload}</script>')
    return HTMLResponse(traduire_liens(page))


@lru_cache(maxsize=None)
def cmd_pages(lang: str) -> list[dict[str, str]]:
    """Pages proposées par la palette de commandes avant toute saisie : les cinq entrées et leurs pages."""
    from api.portes import entrees
    out = []
    for e in entrees(lang):
        out.append({"g": e["t"], "t": e.get("titre", e["t"]), "href": e["href"]})
        out += [{"g": e["t"], "t": x["t"], "href": x["href"]} for x in e.get("pages", [])]
    return out


def label(noeud_id: int, lang: str) -> dict[str, Any]:
    text, official = q.libelle(con, noeud_id, lang)
    return {"texte": text, "fr_only": lang != "fr" and not official}


# --- Données des graphiques (la mise en forme reste dans les gabarits) ---
PARTS_MAX = 5  # au-delà, les segments d'un anneau se lisent mal : le reste est regroupé dans « Autres »


def parts(items: list[dict[str, Any]], ref: list[str] | None = None) -> dict[str, Any]:
    """Anneau : 5 parts au plus + « Autres ». La couleur suit l'entité : les parts mises en avant sont
    celles d'une année de référence (`ref`), quel que soit le filtre, pour qu'un poste garde sa couleur."""
    pos = [i for i in items if i["v"] is not None and i["v"] > 0]
    by = {i["key"]: i for i in pos}
    keys = [k for k in ref if k in by][:PARTS_MAX] if ref else \
        [i["key"] for i in sorted(pos, key=lambda i: -i["v"])[:PARTS_MAX]]
    featured = [dict(by[k], slot=s + 1) for s, k in enumerate(keys)]
    rest = sorted((i for i in pos if i["key"] not in keys), key=lambda i: -i["v"])
    if len(rest) == 1:  # un « Autres » d'un seul poste : on le montre sous son nom
        featured.append(dict(rest[0], slot=0))
        rest = []
    return {"featured": featured, "other": {"v": sum(i["v"] for i in rest), "liste": rest} if rest else None,
            "total": sum(i["v"] for i in pos), "exclus": [i for i in items if i["v"] is not None and i["v"] <= 0],
            "sources": parts_sources(items)}


def parts_sources(items: list[dict[str, Any]]) -> list[str]:
    """Sources des montants d'un anneau : ceux cités par chaque part (montant, lignes sommées, ou total d'un nœud)."""
    mids = [(i["m"]["id"] if not isinstance(i["m"], int) else i["m"]) for i in items if i.get("m")]
    mids += [x for i in items for x in i.get("ids", [])]
    out = set(sources_de(mids))
    for i in items:
        if not i.get("m") and not i.get("ids") and (i.get("href") or "").startswith("provenance/noeud/"):
            nid = int(i["href"].split("/")[2].split("?")[0])
            out.update(r[0] for r in con.execute(
                "SELECT DISTINCT fi.source_id FROM montant m JOIN fichier fi ON fi.id=m.fichier_id WHERE m.noeud_id IN "
                "(WITH RECURSIVE t(id) AS (SELECT ? UNION ALL SELECT n.id FROM noeud n JOIN t ON n.parent_id=t.id) SELECT id FROM t)",
                (nid,)))
    return sorted(out)


def top_keys(items: list[dict[str, Any]]) -> list[str]:
    return [i["key"] for i in sorted((i for i in items if i["v"]), key=lambda i: -i["v"])[:PARTS_MAX]]


def line_data(lang: str, x: list[int], series: list[dict[str, Any]], unit: str, zero: bool = True) -> dict[str, Any]:
    """Courbe : series = [{name, slot, points: {annee: (valeur, montant_id | None, provisoire)}}]."""
    tr = translations(lang)
    out = []
    ids = [p[1] for s in series for p in s["points"].values() if p and p[1]]
    for s in series:
        pts = []
        for a in x:
            p = s["points"].get(a)
            pts.append(None if p is None else {"v": p[0], "f": money(p[0], lang, unit), "prov": bool(p[2]),
                                               "href": f"/{lang}/montant/{p[1]}" if p[1] else None})
        out.append({"name": s["name"], "slot": s["slot"], "points": pts})
    tick = {"PC_TOT": "{v} %", "PC_GDP": "{v} %", "EUR_HAB": "{v} €"}.get(unit, "{v}")
    mult = {"MIO_EUR": 1e6, "EUR": 1}.get(unit)
    return {"x": x, "series": out, "zero": zero, "tick": tick, "prov": tr.gettext("provisoire"), "sources": sources_de(ids),
            "mult": mult, "suf": ["Md€", "M€"] if lang == "fr" else ["bn €", "m €"]}


@app.get("/")
def root(request: Request):
    best = request.headers.get("accept-language", "")[:2]
    return RedirectResponse(f"/{best if best in LANGS else DEFAULT_LANG}/")


# Accueil : api/carte.py (la carte de la dépense publique).


# --- Budget de l'État (budget vert PLF 2026 : exécution 2024, LFI 2025, PLF 2026) ---
BV_STADES = ((2024, "execution"), (2025, "lfi"), (2026, "plf"))


def bv_cols(noeud_id: int, mesure: str) -> list[dict[str, Any]]:
    out = []
    for annee, stade in BV_STADES:
        f = q.Filtre("ETAT", annee, stade, mesure, "EUR")
        v, n, _ = q.total(con, noeud_id, f)
        out.append({"v": v, "n": n, "href": f"provenance/noeud/{noeud_id}?{f.query()}"})
    return out


# --- Territoires (OFGL) ---
NIVEAUX = ("departement", "region")
NOMENS_FONCTIONS = {"f57": "fonctions_dep_m57", "f52": "fonctions_dep_m52"}


def indicateurs(niveau: str, lang: str) -> list[dict[str, Any]]:
    """Ce qu'on peut comparer : les agrégats OFGL, et pour les départements chaque fonction (par nomenclature,
    car M52 et M57 ne se comparent pas)."""
    out = []
    for nom in AGREGATS_FICHE:
        n = q.noeud(con, "ofgl_agregats", nom)
        if n is not None:
            out.append({"key": nom, "groupe": "agregat", "noeud": n, "label": label(n["id"], lang),
                        "mesure": "agregat"})
    if niveau == "departement":
        for k, nomen in NOMENS_FONCTIONS.items():
            for n in con.execute("SELECT * FROM noeud WHERE nomenclature_id=? AND niveau=1 ORDER BY code", (nomen,)):
                out.append({"key": f"{k}:{n['code']}", "groupe": k, "noeud": n, "label": label(n["id"], lang),
                            "mesure": FONCTION_AGREGAT})
    return out


# --- Prototype « explorer » : la phrase-requête (docs/vision/SYNTHESE.md §8) ---
# Une question = un thème × un périmètre. La réponse ne combine jamais deux sources : une combinaison que
# les sources ne publient pas est affichée comme telle, avec la raison et la question voisine qui existe.
PERIMETRES = ("S13", "S1311", "S1313", "S1314", "ETAT")
THEME_NICHES = "depenses-fiscales"
SOURCE_NICHES = "etat_budget_vert_plf2026"
SOURCE_COFOG = "eurostat_cofog_fr"


def statuts_noms(lang: str) -> dict[str, str]:
    """Les marqueurs publiés par l'OFGL (colonnes categ et reg_is_ctu), nommés pour l'affichage."""
    _ = translations(lang).gettext
    return {"CTU": _("collectivité territoriale unique (reg_is_ctu, OFGL)"),
            "ML": _("Métropole de Lyon (catégorie ML, OFGL)"), "PARIS": _("Ville de Paris (catégorie PARIS, OFGL)")}


def nom_entite(nom: str, lang: str) -> str:
    """Les quatre secteurs des administrations publiques portent un nom choisi par ce site (pipeline/loaders/eurostat.py) :
    c'est du texte d'interface, traduit comme tel. Les noms de collectivités restent ceux publiés."""
    _ = translations(lang).gettext
    return {"Ensemble des administrations publiques": _("Ensemble des administrations publiques"),
            "Administrations publiques centrales": _("Administrations publiques centrales"),
            "Administrations publiques locales": _("Administrations publiques locales"),
            "Administrations de sécurité sociale": _("Administrations de sécurité sociale")}.get(nom, nom)


def perimetre_nom(code: str, lang: str) -> str:
    _ = translations(lang).gettext
    return {"S13": _("toutes les administrations publiques"), "S1311": _("les administrations centrales"),
            "S1313": _("les administrations locales"), "S1314": _("les administrations de sécurité sociale"),
            "ETAT": _("le budget de l'État")}[code]


@lru_cache(maxsize=None)
def cofog_ordre(secteur: str = "S13", parent: str = "TOTAL") -> tuple[str, ...]:
    """Codes des enfants d'un nœud COFOG, du plus grand au plus petit montant publié la dernière année.
    C'est la seule règle utilisée quand une page doit choisir une fonction par défaut : aucun sujet n'est mis en
    avant à la main."""
    ent = f"APU-{secteur}"
    annees = q.years(con, "cofog", ent, "compte", "depense", "MIO_EUR")
    f = q.Filtre(ent, annees[-1], "compte", "depense", "MIO_EUR")
    enfants = [(n["code"], (q.single(con, n["id"], f) or {"valeur": 0})["valeur"])
               for n in q.children(con, q.noeud(con, "cofog", parent)["id"])]
    return tuple(c for c, _v in sorted(enfants, key=lambda t: -t[1]))


def cofog_divisions() -> list[sqlite3.Row]:
    return q.children(con, q.noeud(con, "cofog", "TOTAL")["id"])


def possible(theme: str, qui: str) -> bool:
    """Niches : chiffrées par l'État seulement. Fonctions COFOG : comptes nationaux, pas le budget de l'État."""
    return (qui == "ETAT") == (theme == THEME_NICHES)


@lru_cache(maxsize=1)
def niches_2026() -> dict[str, Any]:
    df = q.depenses_fiscales(con, 2026)
    lac = q.lacunes(con, ("non_chiffre", "sous_seuil"))
    racine = q.noeud(con, "budget_vert_plf2026", "DF")
    f = q.Filtre("ETAT", 2026, "plf", "cout_estime", "EUR")
    return {"total": sum(d["valeur"] for d in df), "n": len(df), "href": f"provenance/noeud/{racine['id']}?{f.query()}",
            "nc": sum(1 for l in lac if l["type"] == "non_chiffre"), "eps": sum(1 for l in lac if l["type"] == "sous_seuil"),
            "responsable": next((l["responsable"] for l in lac), None), "source": q.source(con, SOURCE_NICHES)}


def cofog_reponse(code: str, qui: str, lang: str) -> dict[str, Any] | None:
    n = q.noeud(con, "cofog", code)
    ent = f"APU-{qui}"
    annees = q.years(con, "cofog", ent, "compte", "depense", "MIO_EUR")
    if n is None or not annees:
        return None
    a = annees[-1]
    m = q.single(con, n["id"], q.Filtre(ent, a, "compte", "depense", "MIO_EUR"))
    p = q.single(con, n["id"], q.Filtre(ent, a, "compte", "depense", "PC_TOT"))
    return {"noeud": n, "label": label(n["id"], lang), "annee": a, "m": m, "p": p, "entite": q.entite(con, ent),
            "source": q.source(con, SOURCE_COFOG)}


def reponse(theme: str, qui: str, lang: str) -> dict[str, Any]:
    if not possible(theme, qui):
        voisin = "ETAT" if theme == THEME_NICHES else "S13"
        return {"kind": "impossible", "voisin": voisin, "voisin_nom": perimetre_nom(voisin, lang)}
    if theme == THEME_NICHES:
        autres = [l for l in q.lacunes(con) if l["source_id"] == "etat_depenses_fiscales_plf2024"]
        return {"kind": "niches", "d": niches_2026(), "lacunes": autres}
    r = cofog_reponse(theme, qui, lang)
    if r is None:
        raise HTTPException(404)
    # Lacunes du même sujet : la source elle-même, et pour le local l'absence de fonctions régionales.
    sujets = {SOURCE_COFOG} | ({"ofgl_regions"} if qui == "S1313" else set())
    return {"kind": "cofog", "d": r, "lacunes": [l for l in q.lacunes(con) if l["source_id"] in sujets]}


def voisins(theme: str, qui: str, lang: str) -> list[dict[str, Any]]:
    """« Et maintenant ? » : des questions qui ne changent qu'un mot de la phrase, chacune avec son chiffre."""
    _ = translations(lang).gettext
    out = []
    if theme == THEME_NICHES or qui == "ETAT":
        for code in cofog_ordre("S13")[:3]:
            r = cofog_reponse(code, "S13", lang)
            if r and r["m"]:
                out.append({"theme": code, "qui": "S13", "texte": r["label"]["texte"],
                            "qui_nom": perimetre_nom("S13", lang), "fig": money(r["m"]["valeur"], lang, "MIO_EUR"),
                            "an": r["annee"]})
        return out
    for s in PERIMETRES[:4]:
        if s != qui and (r := cofog_reponse(theme, s, lang)) and r["m"]:
            out.append({"theme": theme, "qui": s, "texte": r["label"]["texte"], "qui_nom": perimetre_nom(s, lang),
                        "fig": money(r["m"]["valeur"], lang, "MIO_EUR"), "an": r["annee"]})
    out.append({"theme": THEME_NICHES, "qui": "ETAT", "texte": _("les dépenses fiscales"),
                "qui_nom": perimetre_nom("ETAT", lang), "fig": money(niches_2026()["total"], lang),
                "an": 2026})
    return out[:5]


def amorces(lang: str, seed: int | None = None) -> list[dict[str, Any]]:
    """Questions-amorces tirées à chaque visite, chacune avec son vrai chiffre (ou le compte de ce qui manque)."""
    _ = translations(lang).gettext
    rnd = random.Random(seed)
    pool: list[dict[str, Any]] = []
    for n in rnd.sample(cofog_divisions(), 2):
        r = cofog_reponse(n["code"], "S13", lang)
        if r and r["p"]:
            pool.append({"q": _("Quelle part de la dépense publique va à « %(f)s » ?") % {"f": r["label"]["texte"]},
                         "fig": money(r["p"]["valeur"], lang, "PC_TOT"), "an": r["annee"],
                         "href": f"/{lang}/explorer?theme={n['code']}&qui=S13"})
    cb = q.noeud(con, "budget_vert_plf2026", "CB")
    mission = rnd.choice(q.children(con, cb["id"]))
    v = bv_cols(mission["id"], "cp")[2]["v"]
    if v:
        pool.append({"q": _("Combien le projet de loi de finances 2026 prévoit-il pour la mission « %(m)s » ?")
                     % {"m": label(mission["id"], lang)["texte"]}, "fig": money(v, lang), "an": 2026,
                     "href": f"/{lang}/budget-etat?mission={mission['id']}#zoom"})
    pool.append({"q": _("Combien de dépenses fiscales sont publiées sans montant dans le projet de loi de finances 2026 ?"),
                 "fig": integer(niches_2026()["nc"], lang), "an": 2026, "gap": True,
                 "href": f"/{lang}/explorer?theme={THEME_NICHES}&qui=ETAT#question"})
    dep = rnd.choice(q.entites(con, "departement"))
    racine = q.noeud(con, "ofgl_agregats", "Dépenses totales")
    annees = q.years(con, "ofgl_agregats", dep["code"], "compte", "agregat", "EUR_HAB")
    ms = q.lignes(con, racine["id"], q.Filtre(dep["code"], annees[-1], "compte", "agregat", "EUR_HAB")) if annees else []
    if len(ms) == 1 and (m := ms[0]):
        pool.append({"q": _("Combien dépense le département « %(d)s » par habitant ?") % {"d": dep["nom"]},
                     "fig": money(m["valeur"], lang, "EUR_HAB"), "an": annees[-1],
                     "href": f"/{lang}/territoires/{dep['code']}"})
    return pool


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


# Panneau d'exploration (séries) : module à part, qui réutilise ce qui précède.
from api import carte, comparer, comprendre, contexte, recettes, serie  # noqa: E402,F401
from api import depenses, explorer, provenance, recherche, territoires  # noqa: E402,F401
from api import atelier, differences, donnees, exploitation, fiches, machine, mentions, parcours, verifier  # noqa: E402,F401
from api import portes  # noqa: E402,F401  (en dernier : sa route /{lang}/{cle} ne doit masquer aucune autre)
