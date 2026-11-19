"""D'où vient l'argent public ? Les recettes des administrations publiques par catégorie (gov_10a_main, Eurostat).

Pendant de la page des dépenses par fonction : même périmètre (APU et sous-secteurs), mêmes formes. Les catégories
sont les postes NA_ITEM qu'Eurostat additionne pour former les recettes totales ; le chargeur vérifie cette somme.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from api import queries as q
from api.main import SECTEURS, app, con, label, line_data, parts, render, top_keys
from pipeline.loaders.apu import RECETTES


def categories(ent: str, annee: int, lang: str, secteur: str) -> list[dict[str, Any]]:
    f = q.Filtre(ent, annee, "compte", "agregat", "MIO_EUR")
    out = []
    for code in RECETTES:
        n = q.noeud(con, "apu_agregats", code)
        m = q.single(con, n["id"], f)
        if m is not None:
            out.append({"key": code, "id": n["id"], "label": label(n["id"], lang), "v": m["valeur"], "m": m["id"],
                        "prov": m["provisoire"], "p": None,
                        "drill": f"?secteur={secteur}&annee={annee}&categorie={code}#zoom"})
    return out


@app.get("/{lang}/recettes-publiques", response_class=HTMLResponse)
def recettes_publiques(request: Request, lang: str, secteur: str = "S13", annee: int | None = None,
                       categorie: str = ""):
    if secteur not in SECTEURS:
        raise HTTPException(404)
    ent = f"APU-{secteur}"
    tr = q.noeud(con, "apu_agregats", "TR")
    annees = [r["exercice"] for r in q.series(con, q.noeud(con, "apu_agregats", RECETTES[0])["id"], ent, "compte",
                                               "agregat", "MIO_EUR")]
    annee = annee if annee in annees else annees[-1]
    tot = q.single(con, tr["id"], q.Filtre(ent, annee, "compte", "agregat", "MIO_EUR"))
    # Couleurs : les cinq catégories au montant le plus élevé pour ce secteur la dernière année publiée.
    ref = top_keys(categories(ent, annees[-1], lang, secteur))
    anneau = parts(categories(ent, annee, lang, secteur), ref)
    code = categorie if categorie in RECETTES else ref[0]
    n = q.noeud(con, "apu_agregats", code)
    cat_m = q.single(con, n["id"], q.Filtre(ent, annee, "compte", "agregat", "MIO_EUR"))
    serie = q.series(con, n["id"], ent, "compte", "agregat", "PC_GDP")
    courbe = line_data(lang, [p["exercice"] for p in serie], [{
        "name": label(n["id"], lang)["texte"], "slot": 1,
        "points": {p["exercice"]: (p["valeur"], p["id"], p["provisoire"]) for p in serie}}], "PC_GDP")
    secteurs = [{"code": s, "nom": q.entite(con, f"APU-{s}")["nom"]} for s in SECTEURS]
    f = lambda s: q.single(con, tr["id"], q.Filtre(f"APU-{s}", annee, "compte", "agregat", "MIO_EUR"))
    somme_sous_secteurs = sum((f(s) or {"valeur": 0})["valeur"] for s in SECTEURS[1:])
    return render(request, lang, "recettes_publiques.html", secteur=secteur, secteurs=secteurs, annee=annee,
                  annees=annees, tot=tot, tr_label=label(tr["id"], lang), anneau=anneau, categorie=code,
                  categorie_label=label(n["id"], lang), categorie_m=cat_m, evolution=courbe,
                  somme_sous_secteurs=somme_sous_secteurs, tot_s13=f("S13"))
