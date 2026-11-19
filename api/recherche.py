"""Recherche typée : la page de résultats et les suggestions, chaque suggestion avec son chiffre.

Détaché de api/main.py. Importé à la fin de api/main.py, avant api/portes.py.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from api import fiches, queries as q
from api.i18n import LANGS, money, translations
from api.main import app, bv_cols, cofog_divisions, cofog_reponse, con, concepts_index, fold, label, render


@app.get("/{lang}/recherche", response_class=HTMLResponse)
def recherche(request: Request, lang: str, q_: str = Query("", alias="q")):
    """Résultats de la recherche quand on valide sans choisir de suggestion (ou sans JavaScript)."""
    return render(request, lang, "recherche.html", q=q_, resultats=suggest(lang, q_, SUGGEST_PAGE))


# Recherche typée : chaque suggestion porte déjà son chiffre, ou dit qu'il n'existe pas.
@lru_cache(maxsize=None)
def suggest_index(lang: str) -> list[dict[str, Any]]:
    _ = translations(lang).gettext
    out: list[dict[str, Any]] = []
    for n in cofog_divisions():
        r = cofog_reponse(n["code"], "S13", lang)
        out.append({"g": _("Fonction, toutes administrations"), "t": r["label"]["texte"], "an": r["annee"],
                    "fig": money(r["m"]["valeur"], lang, "MIO_EUR") if r["m"] else None,
                    "href": f"/{lang}/theme/{k}" if (k := fiches.fiche_cofog(n["code"])) else f"/{lang}/?f={n['code']}#carte",
                    "actions": [{"t": _("Carte"), "href": f"/{lang}/?f={n['code']}#carte"},
                                {"t": _("Série"), "href": f"/{lang}/serie?dom=cofog&ind={n['code']}"},
                                {"t": _("Comparer"), "href": f"/{lang}/comparer?jeu=fonctions&sel={n['code']}"}]})
    for n in con.execute("SELECT * FROM noeud WHERE nomenclature_id = 'apu_agregats' ORDER BY id"):
        rows = q.series_provenance(con, n["id"], "APU-S13", "compte", "agregat", "PC_GDP")
        out.append({"g": _("Comptes des administrations publiques"), "t": label(n["id"], lang)["texte"],
                    "an": rows[-1]["exercice"] if rows else None,
                    "fig": f"{money(rows[-1]['valeur'], lang, 'PC_GDP')} {_('du PIB')}" if rows else None,
                    "href": f"/{lang}/serie?dom=apu&ind={n['code']}",
                    "actions": [{"t": _("Comparer"), "href": f"/{lang}/comparer?jeu=comptes&sel={n['code']}"},
                                {"t": _("Contexte"), "href": f"/{lang}/contexte"}]})
    for p in con.execute("""SELECT DISTINCT p.uid, p.nom FROM personne p JOIN fonction f ON f.personne_uid = p.uid
                            JOIN organe o ON o.uid = f.organe_uid WHERE o.type = 'MINISTERE'"""):
        fs = con.execute("""SELECT MIN(substr(f.debut, 1, 4)) de, MAX(COALESCE(substr(f.fin, 1, 4), '9999')) a FROM fonction f
                            JOIN organe o ON o.uid = f.organe_uid WHERE o.type = 'MINISTERE' AND f.personne_uid = ?""",
                         (p["uid"],)).fetchone()
        a = min(int(fs["a"]), 9999)
        out.append({"g": _("Membre du gouvernement"), "t": p["nom"], "fig": None,
                    "an": f"{fs['de']}–{fs['a'] if a != 9999 else ''}",
                    "href": f"/{lang}/contexte?de={fs['de']}" + (f"&a={a}" if a != 9999 else "")})
    cb = q.noeud(con, "budget_vert_plf2026", "CB")
    for m in q.children(con, cb["id"]):
        v = bv_cols(m["id"], "cp")[2]["v"]
        out.append({"g": _("Mission du budget de l'État"), "t": label(m["id"], lang)["texte"], "an": 2026,
                    "fig": money(v, lang) if v else None, "href": f"/{lang}/budget-etat?mission={m['id']}#zoom"})
    for d in q.depenses_fiscales(con, 2026):
        out.append({"g": _("Dépense fiscale"), "t": d["libelle"], "fig": money(d["valeur"], lang), "an": 2026,
                    "href": f"/{lang}/montant/{d['montants'][0]}"})
    for l in q.lacunes(con, ("non_chiffre",)):
        out.append({"g": _("Dépense fiscale"), "t": l["description"].split(". Marqueur")[0], "fig": None, "an": 2026,
                    "gap": _("sans montant publié"), "href": f"/{lang}/lacunes"})
    racine = q.noeud(con, "ofgl_agregats", "Dépenses totales")
    for niveau, g in (("region", _("Région")), ("departement", _("Département"))):
        for e in q.entites(con, niveau):
            annees = q.years(con, "ofgl_agregats", e["code"], "compte", "agregat", "EUR_HAB")
            ms = q.lignes(con, racine["id"], q.Filtre(e["code"], annees[-1], "compte", "agregat", "EUR_HAB")) \
                if annees else []
            m = ms[0] if len(ms) == 1 else None
            out.append({"g": g, "t": e["nom"], "code": e["code_insee"] or "", "an": annees[-1] if annees else None,
                        "fig": money(m["valeur"], lang, "EUR_HAB") if m else None,
                        "href": f"/{lang}/territoires/{e['code']}",
                        "actions": [{"t": _("Comparer"), "href": f"/{lang}/comparer?niveau={niveau}&sel={e['code']}"},
                                    {"t": _("Série"), "href": f"/{lang}/serie?dom=ofgl&qui={e['code']}"}]})
    sigles: dict[str, list[str]] = {}
    for cid, alias in q.aliases(con, lang):
        sigles.setdefault(cid, []).append(alias)
    for c in concepts_index(lang).values():
        out.append({"g": _("Lexique"), "t": c["terme"], "fig": None, "href": f"/{lang}/lexique#{c['id']}",
                    "alias": sigles.get(c["id"], [])})
    for o in out:
        o["k"] = fold(" ".join([o["t"], o.get("code", ""), *o.get("alias", [])]))
        o["x"] = {fold(t) for t in [o["t"], o.get("code", ""), *o.pop("alias", [])] if t}
    return out


SUGGEST_PAR_GROUPE = 4
SUGGEST_MAX = 10


SUGGEST_PAGE = 60


@app.get("/{lang}/suggest")
def suggest_route(lang: str, q_: str = Query("", alias="q")):
    return suggest(lang, q_)


def suggest(lang: str, q_: str, limite: int = 0) -> list[dict[str, Any]]:
    if lang not in LANGS:
        raise HTTPException(404)
    words = fold(q_).split()
    if not words:
        return []
    hits = [o for o in suggest_index(lang) if all(w in o["k"] for w in words)]
    # Le nom exact, puis ce qui commence par le mot tapé, puis un mot qui commence par lui ; à égalité, le plus court.
    typed = " ".join(words)
    hits.sort(key=lambda o: (typed not in o["x"], not o["k"].startswith(words[0]),
                             f" {words[0]}" not in f" {o['k']}", len(o["k"])))
    per: dict[str, int] = {}
    out = []
    for o in hits:
        if limite and len(out) < limite or per.get(o["g"], 0) < SUGGEST_PAR_GROUPE and len(out) < SUGGEST_MAX:
            per[o["g"]] = per.get(o["g"], 0) + 1
            out.append({k: v for k, v in o.items() if k not in ("k", "x")})
    return out
