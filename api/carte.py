"""Page d'accueil : la carte de la dépense publique (COFOG, Eurostat), à zoomer comme une carte.

Chaque case est une fonction publiée ; sa surface est proportionnelle au montant publié en euros, et le chiffre affiché
est celui de l'unité choisie, relié à sa ligne d'origine. Rien n'est additionné : les parts sont celles d'Eurostat.
Importé à la fin de api/main.py (il en réutilise l'application, le rendu et les libellés).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any
from urllib.parse import urlencode

from babel.numbers import format_decimal
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from api import queries as q
from api.i18n import LANGS, money, translations
from api.main import SECTEURS, SOURCE_COFOG, app, cofog_ordre, con, label, line_data, render, sources_de

UNITES = ("PC_TOT", "MIO_EUR", "PC_GDP")
# Deux cadrages de la même carte : paysage (écrans larges) et portrait (téléphones). Rapport largeur / hauteur.
CADRES = {"l": 16 / 9, "p": 3 / 4}


def squarify(valeurs: list[float], ratio: float) -> list[tuple[float, float, float, float]]:
    """Découpage « squarified » (Bruls, Huizing, van Wijk, 2000) d'un cadre de largeur `ratio` et de hauteur 1.

    L'ordre des valeurs est conservé (les cases ne changent pas de place d'une année à l'autre) ; renvoie, pour chaque
    valeur, (x, y, largeur, hauteur) en fractions du cadre.
    """
    total = sum(valeurs)
    if total <= 0:
        return [(0, 0, 0, 0)] * len(valeurs)
    aires = [v / total * ratio for v in valeurs]
    out: list[tuple[float, float, float, float]] = []
    x, y, w, h = 0.0, 0.0, ratio, 1.0
    i = 0

    def pire(rangee: list[float], cote: float) -> float:
        s = sum(rangee)
        return max(max(cote * cote * r / (s * s), s * s / (cote * cote * r)) for r in rangee)

    while i < len(aires):
        cote = min(w, h)
        rangee = [aires[i]]
        i += 1
        while i < len(aires) and pire(rangee + [aires[i]], cote) <= pire(rangee, cote):
            rangee.append(aires[i])
            i += 1
        s = sum(rangee)
        if w >= h:  # colonne à gauche
            cw = s / h
            yy = y
            for r in rangee:
                out.append((x, yy, cw, r / cw))
                yy += r / cw
            x, w = x + cw, w - cw
        else:  # rangée en haut
            rh = s / w
            xx = x
            for r in rangee:
                out.append((xx, y, r / rh, rh))
                xx += r / rh
            y, h = y + rh, h - rh
    return [(a / ratio, b, c / ratio, d) for a, b, c, d in out]


def pour_cent_euros(v: float, lang: str) -> str:
    """Une part publiée en %, lue « sur 100 € » : 41,5 % → « 41,5 € ». Simple changement d'écriture, aucun calcul."""
    n = format_decimal(v, "#,##0.0", locale=lang)
    return n + " €" if lang == "fr" else "€" + n


def valeur(v: float | None, unite: str, lang: str) -> str:
    if v is None:
        return "—"
    return pour_cent_euros(v, lang) if unite == "PC_TOT" else money(v, lang, unite)


def ordre(secteur: str, parent: str) -> tuple[str, ...]:
    """Ordre fixe des cases : décroissant selon la dernière année publiée, pour que la carte reste stable dans le temps."""
    return cofog_ordre(secteur, parent)


def lien(lang: str, **p: Any) -> str:
    p = {k: v for k, v in p.items() if v not in (None, "")}
    return f"/{lang}/?{urlencode(p)}#carte" if p else f"/{lang}/#carte"


def carte(lang: str, secteur: str, annee: int | None, zoom: str | None, unite: str) -> dict[str, Any]:
    if secteur not in SECTEURS or unite not in UNITES:
        raise HTTPException(404)
    ent = f"APU-{secteur}"
    annees = q.years(con, "cofog", ent, "compte", "depense", "MIO_EUR")
    annee = annee if annee in annees else annees[-1]
    total = q.noeud(con, "cofog", "TOTAL")
    parent = q.noeud(con, "cofog", zoom) if zoom else None
    if zoom and (parent is None or parent["parent_id"] != total["id"]):
        raise HTTPException(404)
    parent = parent or total
    fm = q.Filtre(ent, annee, "compte", "depense", "MIO_EUR")
    fu = q.Filtre(ent, annee, "compte", "depense", unite)
    codes = {n["code"]: n for n in q.children(con, parent["id"])}
    base = {"secteur": secteur if secteur != "S13" else None, "annee": annee if annee != annees[-1] else None,
            "unite": unite if unite != "PC_TOT" else None}

    cases, absentes = [], []
    for code in ordre(secteur, parent["code"]):
        n = codes[code]
        m, u = q.single(con, n["id"], fm), q.single(con, n["id"], fu)
        lab = label(n["id"], lang)
        if m is None or not m["valeur"] or m["valeur"] <= 0:
            absentes.append({"code": code, "label": lab})
            continue
        c = {"code": code, "id": n["id"], "label": lab, "m": m["valeur"], "u": u, "f": valeur(u["valeur"] if u else None, unite, lang),
             "prov": bool(u and u["provisoire"])}
        if parent is total:
            c["href"] = lien(lang, **base, f=code)
            # « dont » : les deux premières sous-fonctions publiées, libellés officiels.
            subs = sorted(((s, q.single(con, s["id"], fm)) for s in q.children(con, n["id"])),
                          key=lambda t: -(t[1]["valeur"] if t[1] else 0))
            c["dont"] = [label(s["id"], lang)["texte"] for s, sm in subs[:2] if sm and sm["valeur"] > 0]
        cases.append(c)
    vmax = max((c["m"] for c in cases), default=1)
    for k, ratio in CADRES.items():
        for c, r in zip(cases, squarify([c["m"] for c in cases], ratio)):
            c[k] = r
    for c in cases:
        # Teinte d'encre proportionnelle à la racine de la part (redouble la surface ; ne désigne aucune catégorie).
        c["t"] = round(8 + 34 * (c["m"] / vmax) ** .5)
        c["aire"] = c["m"] / sum(x["m"] for x in cases)

    tot_m = q.single(con, total["id"], fm)
    ids = [x["id"] for c in cases for x in (c["u"],) if x] + [tot_m["id"] if tot_m else None]
    out = {"secteur": secteur, "annee": annee, "annees": annees, "unite": unite, "zoom": zoom, "cases": cases,
           "absentes": absentes, "total": tot_m, "base": base, "source": q.source(con, SOURCE_COFOG),
           "entite": q.entite(con, ent), "sources": sources_de(ids)}
    if zoom:
        out["parent"] = {"code": zoom, "label": label(parent["id"], lang),
                         **{x: q.single(con, parent["id"], q.Filtre(ent, annee, "compte", "depense", x)) for x in UNITES}}
        serie = q.series(con, parent["id"], ent, "compte", "depense", "PC_TOT")
        out["evolution"] = line_data(lang, [p["exercice"] for p in serie], [{
            "name": label(parent["id"], lang)["texte"], "slot": 1,
            "points": {p["exercice"]: (p["valeur"], p["id"], p["provisoire"]) for p in serie}}], "PC_TOT")
    return out


# Chiffres repères de l'accueil : quatre postes publiés des administrations publiques, en part du PIB, la dernière année
# publiée pour les quatre. Le lien « Qu'est-ce que c'est ? » mène à l'étape du parcours Comprendre qui l'explique.
REPERES = (("TR", "/comprendre/2"), ("TE", "/comprendre/2"), ("B9", "/comprendre/2"), ("GD", "/comprendre/5"))


def reperes(lang: str) -> dict[str, Any]:
    _ = translations(lang).gettext
    noms = {"TR": _("Recettes"), "TE": _("Dépenses"), "B9": _("Solde"), "GD": _("Dette")}
    series = {}
    for code, _lien in REPERES:
        n = q.noeud(con, "apu_agregats", code)
        series[code] = (n, {r["exercice"]: r for r in q.series(con, n["id"], "APU-S13", "compte", "agregat", "PC_GDP")})
    annee = max(set.intersection(*(set(s) for _n, s in series.values())))
    icos = {"TR": "entree", "TE": "sortie", "B9": "balance", "GD": "couches"}
    return {"annee": annee, "postes": [{"code": c, "nom": noms[c], "officiel": label(series[c][0]["id"], lang), "ico": icos[c],
                                         "m": series[c][1][annee], "href": f"/{lang}{lien}"} for c, lien in REPERES]}


@app.get("/{lang}/", response_class=HTMLResponse)
def accueil(request: Request, lang: str, secteur: str = "S13", annee: int | None = None, f: str | None = None,
            unite: str = "PC_TOT"):
    if lang not in LANGS:
        raise HTTPException(404)
    _ = translations(lang).gettext
    c = carte(lang, secteur, annee, f or None, unite)
    noms = {"S13": _("Toutes les administrations"), "S1311": _("État et administrations centrales"),
            "S1313": _("Collectivités locales"), "S1314": _("Sécurité sociale")}
    unites = {"PC_TOT": _("Pour 100 € dépensés"), "MIO_EUR": _("En euros"), "PC_GDP": _("Part du PIB (%)")}
    lk = lambda **ch: lien(lang, **{**c["base"], "f": f or None, **ch})  # noqa: E731
    from api.colonnes import icone
    return render(request, lang, "index.html", c=c, noms=noms, unites=unites, reperes=reperes(lang), icone=icone,
                  lk=lk, valeur=lambda v, u: valeur(v, u, lang))
