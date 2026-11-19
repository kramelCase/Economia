"""Vérifier un chiffre (docs/vision/INTERFACE.md §3.4).

Un nombre entendu (« 3 000 milliards », « 5,8 % »), un mot et une année facultatifs : la page montre les valeurs
publiées les plus proches, chacune avec ce qu'elle mesure (indicateur, périmètre, unité, stade, année) et sa source.
Le site ne dit jamais « vrai » ou « faux » : il écrit comment il a lu le nombre saisi et l'écart avec chaque valeur.
Importé à la fin de api/main.py, avant api/portes.py (dont la route /{lang}/{cle} masquerait celle-ci).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from babel.numbers import format_decimal, format_percent
from fastapi import Query, Request
from fastapi.responses import HTMLResponse

from api.i18n import money, translations
from api.main import app, con, fold, label, render
from api.serie import unite_nom

RESULTATS = 8
# Au-delà de cet écart relatif (valeurs absolues), une valeur publiée n'est pas « proche » : la page le dit plutôt que
# de proposer 3 Md€ pour 60 Md€. Choix du site, affiché sur la page.
ECART_MAX = 0.5
# Unités comparables entre elles : les euros (€ et M€ ramenés en euros), les parts (en points), les euros par habitant.
FAMILLES = {"eur": ("EUR", "MIO_EUR"), "pct": ("PC_GDP", "PC_TOT"), "hab": ("EUR_HAB",)}
MULTIPLES = ((("mille milliard", "trillion"), 1e12), (("milliard", "md", "mrd", "bn", "billion"), 1e9),
             (("million", "m€", "m "), 1e6), (("mille", "k€", "k "), 1e3))
NOMBRE = re.compile(r"-?\d[\d\s  .,]*")
# Les thèmes proposés d'entrée (on n'a pas à connaître un chiffre ni un libellé) : un poste des comptes de l'ensemble
# des administrations publiques, publié par Eurostat en euros et en part du PIB. (clé, code du poste, icône)
THEMES = (("dette", "GD", "dette"), ("deficit", "B9", "economie"), ("depenses", "TE", "depenses"),
          ("recettes", "TR", "recettes"), ("impots", "D5REC", "impots"), ("cotisations", "D61REC", "social"),
          ("interets", "D41PAY", "tresorerie"))


def lire(texte: str, lang: str) -> dict[str, Any] | None:
    """Le nombre saisi, lu en une valeur et une famille d'unités. None si aucun nombre."""
    m = NOMBRE.search(texte)
    if not m:
        return None
    brut = re.sub(r"[\s  ]", "", m.group()).rstrip(".,")
    if "," in brut and "." in brut:  # le dernier séparateur est la virgule décimale
        dec = max(brut.rfind(","), brut.rfind("."))
        brut = re.sub(r"[.,]", "", brut[:dec]) + "." + brut[dec + 1:]
    elif "," in brut:  # virgule décimale en français ; en anglais, séparateur de milliers devant trois chiffres
        milliers = lang != "fr" and re.fullmatch(r"-?\d{1,3}(,\d{3})+", brut)
        brut = brut.replace(",", "") if milliers else brut.replace(",", ".")
    elif brut.count(".") > 1 or (lang == "fr" and re.search(r"\.\d{3}$", brut)):
        brut = brut.replace(".", "")
    try:
        x = float(brut)
    except ValueError:
        return None
    reste = fold(texte[m.end():]).strip() + " "
    if "%" in reste or reste.startswith(("pour cent", "percent", "pt", "point")):
        return {"x": x, "famille": "pct"}
    famille = "hab" if re.search(r"/ ?hab|par habitant|per capita|per head", reste) else "eur"
    for mots, f in MULTIPLES:
        if reste.startswith(mots):
            x *= f
            break
    return {"x": x, "famille": famille}


@lru_cache(maxsize=None)
def index_libelles(lang: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """(nœuds, entités) avec leur libellé replié, en français et dans la langue de la page."""
    noeuds = {}
    for r in con.execute("SELECT id, libelle FROM noeud"):
        noeuds[r["id"]] = fold(r["libelle"])
    if lang != "fr":
        for r in con.execute("SELECT noeud_id, libelle FROM noeud_traduction WHERE langue=?", (lang,)):
            noeuds[r["noeud_id"]] += " " + fold(r["libelle"])
    entites = [(r["id"], fold(r["nom"] + " " + (r["code_insee"] or ""))) for r in con.execute("SELECT * FROM entite")]
    return list(noeuds.items()), entites


@lru_cache(maxsize=None)
def mesures_citees() -> list[tuple[str, int, int]]:
    """(forme repliée, nœud, entité) : les termes du lexique dont la définition citée nomme un poste publié
    (champ `mesure` de content/concepts.yaml), pour que « déficit » trouve le besoin de financement."""
    out = []
    for c in yaml.safe_load((Path(__file__).parent.parent / "content" / "concepts.yaml").read_text("utf-8"))["concepts"]:
        m = c.get("mesure")
        if not m:
            continue
        n = con.execute("SELECT id FROM noeud WHERE nomenclature_id=? AND code=?", (m["nomenclature"], m["code"])).fetchone()
        e = con.execute("SELECT id FROM entite WHERE code=?", (m["entite"],)).fetchone()
        if n is None or e is None:
            continue
        formes = [*c["terme"].values(), *[a for v in (c.get("alias") or {}).values() for a in v]]
        out += [(fold(f), n["id"], e["id"]) for f in formes]
    return out


def noms_themes(lang: str) -> dict[str, str]:
    _ = translations(lang).gettext
    return {"dette": _("Dette publique"), "deficit": _("Déficit public"), "depenses": _("Dépenses publiques"),
            "recettes": _("Recettes publiques"), "impots": _("Impôts sur le revenu et le patrimoine"),
            "cotisations": _("Cotisations sociales"), "interets": _("Intérêts de la dette")}


@lru_cache(maxsize=None)
def poste(code: str) -> tuple[int, int]:
    """(nœud, entité) d'un thème : le poste dans les comptes de l'ensemble des administrations publiques."""
    n = con.execute("SELECT id FROM noeud WHERE nomenclature_id='apu_agregats' AND code=?", (code,)).fetchone()
    e = con.execute("SELECT id FROM entite WHERE code='APU-S13'").fetchone()
    return n["id"], e["id"]


def annees_theme(code: str) -> list[dict[str, Any]]:
    """Chaque année publiée du poste, la plus récente d'abord : montant en millions d'euros et part du PIB."""
    n, e = poste(code)
    par_an: dict[int, dict[str, Any]] = {}
    for r in con.execute("""SELECT m.id, m.valeur, m.unite, m.exercice, m.provisoire, fi.source_id FROM montant m
                            JOIN fichier fi ON fi.id = m.fichier_id
                            WHERE m.noeud_id=? AND m.entite_id=? AND m.unite IN ('MIO_EUR', 'PC_GDP')""", (n, e)):
        par_an.setdefault(r["exercice"], {"a": r["exercice"]})[r["unite"]] = dict(r)
    return [par_an[a] for a in sorted(par_an, reverse=True)]


def themes(lang: str) -> list[dict[str, Any]]:
    """Les vignettes de thème, chacune avec sa dernière année publiée."""
    noms = noms_themes(lang)
    out = []
    for cle, code, ico in THEMES:
        ans = annees_theme(code)
        d = ans[0] if ans else {}
        out.append({"cle": cle, "code": code, "ico": ico, "t": noms[cle], "label": label(poste(code)[0], lang),
                    "a": d.get("a"), "eur": d.get("MIO_EUR"), "pct": d.get("PC_GDP")})
    return out


def chercher(lu: dict[str, Any], mot: str, annee: int | None, lang: str,
             theme: str | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    """Les valeurs publiées les plus proches, et les mots saisis qu'aucun libellé publié ne contient."""
    unites = FAMILLES[lu["famille"]]
    where, args = [f"m.unite IN ({','.join('?' * len(unites))})"], list(unites)
    if theme:
        where.append("m.noeud_id = ? AND m.entite_id = ?")
        args += list(poste(theme))
    if annee:
        where.append("m.exercice = ?")
        args.append(annee)
    noeuds, entites = index_libelles(lang)
    ignores = []
    for t in fold(mot).split():
        ns = [i for i, s in noeuds if t in s]
        es = [i for i, s in entites if t in s]
        cs = sorted({(n, e) for f, n, e in mesures_citees() if t in f})
        if not ns and not es and not cs:
            ignores.append(t)
            continue
        # Des identifiants tirés de la base, passés en paramètres comme toute valeur : rien de saisi n'entre dans la requête.
        ou = [f"m.noeud_id IN ({','.join('?' * len(ns)) or 'NULL'})", f"m.entite_id IN ({','.join('?' * len(es)) or 'NULL'})"]
        ou += ["(m.noeud_id = ? AND m.entite_id = ?)"] * len(cs)
        where.append("(" + " OR ".join(ou) + ")")
        args += [*ns, *es, *[x for c in cs for x in c]]
    if ignores:  # un mot introuvable : montrer des valeurs sans rapport avec lui induirait en erreur
        return [], ignores
    rows = con.execute(
        f"""SELECT m.id, m.valeur, m.unite, m.exercice, m.stade, m.mesure, m.provisoire, m.noeud_id,
                   e.nom entite_nom, fi.source_id,
                   CASE m.unite WHEN 'MIO_EUR' THEN m.valeur * 1e6 ELSE m.valeur END v
            FROM montant m JOIN entite e ON e.id = m.entite_id JOIN fichier fi ON fi.id = m.fichier_id
            WHERE {' AND '.join(where)} ORDER BY ABS(ABS(v) - ?), m.exercice DESC LIMIT ?""",
        (*args, abs(lu["x"]), RESULTATS)).fetchall()
    return [dict(r) for r in rows], ignores


def proche(v: float, lu: dict[str, Any]) -> bool:
    x = abs(lu["x"])
    return x == 0 and v == 0 or x > 0 and abs(abs(v) - x) / x <= ECART_MAX


def ecart(v: float, lu: dict[str, Any], lang: str) -> str:
    """Écart entre la valeur publiée et le nombre saisi, calculé par le site : en points pour une part."""
    _ = translations(lang).gettext
    signe = ""
    if v * lu["x"] < 0:  # publié avec le signe opposé (un solde négatif entendu « 5,8 % ») : écart sur les valeurs absolues
        signe = " · " + (_("valeur publiée négative") if v < 0 else _("valeur publiée positive"))
    d = abs(v) - abs(lu["x"])
    if abs(d) < 1e-9 * max(1, abs(lu["x"])):
        return _("identique au nombre saisi") + signe
    if lu["famille"] == "pct":
        s = format_decimal(abs(d), "#,##0.0", locale=lang)
        return (_("%(e)s pt au-dessus du nombre saisi") if d > 0 else _("%(e)s pt au-dessous du nombre saisi")) % {"e": s} + signe
    if not lu["x"]:
        return ""
    p = money(abs(d) / abs(lu["x"]) * 100, lang, "PC_GDP")
    return (_("%(e)s au-dessus du nombre saisi") if d > 0 else _("%(e)s au-dessous du nombre saisi")) % {"e": p} + signe


@app.get("/{lang}/verifier", response_class=HTMLResponse)
def verifier(request: Request, lang: str, n: str = "", mot: str = "", annee: str = Query(""), theme: str = ""):
    _ = translations(lang).gettext
    stades = {"plf": _("Projet de loi de finances"), "lfi": _("Loi de finances initiale"),
              "execution": _("Exécution budgétaire"), "compte": _("Comptes publiés")}
    mesures = {"cp": _("crédits de paiement"), "ae": _("autorisations d'engagement")}
    a = int(annee) if annee.isdigit() and len(annee) == 4 else None
    lu = lire(n, lang) if n.strip() else None
    ths = themes(lang)
    th = next((t for t in ths if t["cle"] == theme), None)
    if th:
        mot = ""
    tous, ignores = chercher(lu, mot, a, lang, th and th["code"]) if lu else ([], [])
    resultats = [r for r in tous if proche(r["v"], lu)]
    loin = None
    if tous and not resultats:  # la plus proche, nommée sans être proposée comme « proche »
        r = tous[0]
        loin = _("La valeur publiée la plus proche pour ces critères est %(v)s (%(q)s, %(a)s) : plus de %(p)s d'écart, elle n'est pas montrée comme proche.") % {
            "v": money(r["valeur"], lang, r["unite"]), "q": label(r["noeud_id"], lang)["texte"], "a": r["exercice"],
            "p": format_percent(ECART_MAX, locale=lang)}
    for r in resultats:
        r["label"] = label(r["noeud_id"], lang)
        r["fig"] = money(r["valeur"], lang, r["unite"])
        r["unite_nom"] = unite_nom(r["unite"], lang)
        r["stade_nom"] = stades[r["stade"]]
        r["mesure_nom"] = mesures.get(r["mesure"])
        r["ecart"] = ecart(r["v"], lu, lang)
    lu_txt = None
    if lu:
        lu_txt = money(lu["x"], lang, {"eur": "EUR", "pct": "PC_GDP", "hab": "EUR_HAB"}[lu["famille"]])
    serie_th = None
    if th:  # le thème choisi : toutes ses années publiées, pour retrouver un chiffre sans le connaître
        serie_th = annees_theme(th["code"])
        for x in serie_th:
            for u in ("MIO_EUR", "PC_GDP"):
                if u in x:
                    x[u]["fig"] = money(x[u]["valeur"], lang, u)
    sources_th = sorted({t["eur"]["source_id"] for t in ths if t["eur"]} | {t["pct"]["source_id"] for t in ths if t["pct"]})
    for t in ths:
        t["eur_fig"] = t["eur"] and money(t["eur"]["valeur"], lang, "MIO_EUR")
        t["pct_fig"] = t["pct"] and money(t["pct"]["valeur"], lang, "PC_GDP")
    from api.colonnes import icone
    return render(request, lang, "verifier.html", n=n, mot=mot, annee=annee, lu=lu, lu_txt=lu_txt, a=a,
                  themes=ths, th=th, serie_th=serie_th, ent_nom=con.execute("SELECT nom FROM entite WHERE code='APU-S13'").fetchone()["nom"], sources_th=sources_th, icone=icone,
                  resultats=resultats, ignores=ignores, loin=loin,
                  regle=_("Valeurs publiées à moins de %(p)s d'écart du nombre saisi, comparées sans leur signe.") % {
                      "p": format_percent(ECART_MAX, locale=lang)},
                  exemple=_("3 000 milliards, 5,8 %, 1 200 € par habitant"), sources=sorted({r["source_id"] for r in resultats}))
