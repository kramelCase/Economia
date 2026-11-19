"""Ma collectivité : régions et départements (OFGL), la liste comparée et la page de chaque collectivité.

Détaché de api/main.py. Importé à la fin de api/main.py, avant api/portes.py.
"""

from __future__ import annotations

from statistics import median
from urllib.parse import quote

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from api import queries as q
from api.i18n import translations
from api.main import (AGREGATS_FICHE, FONCTION_AGREGAT, NIVEAUX, app, con, fold, indicateurs, label, line_data, parts,
                      render, source_info, sources_de, statuts_noms)


@app.get("/{lang}/territoires", response_class=HTMLResponse)
def territoires(request: Request, lang: str, niveau: str = "departement", indicateur: str = "Dépenses totales",
                annee: int | None = None, unite: str = "EUR_HAB", nom: str = ""):
    if niveau not in NIVEAUX or unite not in ("EUR", "EUR_HAB"):
        raise HTTPException(404)
    toutes = [e for n in ("region", "departement") for e in q.entites(con, n)]
    trouves = None
    if nom.strip():
        t = fold(nom.strip())
        exact = [e for e in toutes if t in (fold(e["nom"]), (e["code_insee"] or "").lower())]
        trouves = exact or [e for e in toutes if t in fold(e["nom"])]
        if len(trouves) == 1:
            return RedirectResponse(f"/{lang}/territoires/{trouves[0]['code']}", status_code=303)
    inds = indicateurs(niveau, lang)
    ind = next((i for i in inds if i["key"] == indicateur), inds[0])
    ents = q.entites(con, niveau)
    codes = [e["code"] for e in ents]
    marks = ",".join("?" * len(codes))
    annees = [r[0] for r in con.execute(
        f"""SELECT DISTINCT exercice FROM montant m JOIN entite e ON e.id=m.entite_id WHERE m.noeud_id=? AND m.mesure=?
            AND m.unite=? AND e.code IN ({marks}) ORDER BY exercice""", (ind["noeud"]["id"], ind["mesure"], unite, *codes))]
    if not annees:
        raise HTTPException(404)
    annee = annee if annee in annees else annees[-1]
    vals, plusieurs = {}, {}
    for r in con.execute(
            f"""SELECT e.code, m.id, m.valeur FROM montant m JOIN entite e ON e.id=m.entite_id WHERE m.noeud_id=?
                AND m.mesure=? AND m.unite=? AND m.exercice=? AND e.code IN ({marks}) ORDER BY m.ligne_source""",
            (ind["noeud"]["id"], ind["mesure"], unite, annee, *codes)):
        plusieurs.setdefault(r["code"], []).append(r)
    for c in list(plusieurs):
        if len(plusieurs[c]) == 1:
            vals[c] = plusieurs.pop(c)[0]
    speciaux = q.statuts_ofgl(con, annee)
    lignes = sorted(({"code": e["code"], "nom": e["nom"], "code_insee": e["code_insee"], "v": vals[e["code"]]["valeur"],
                      "m": vals[e["code"]]["id"], "statut": speciaux.get(e["code"])} for e in ents if e["code"] in vals),
                    key=lambda l: -l["v"])
    absents = [e for e in ents if e["code"] not in vals and e["code"] not in plusieurs]
    multiples = [{"e": e, "rows": plusieurs[e["code"]]} for e in ents if e["code"] in plusieurs]
    vmax = max((abs(l["v"]) for l in lignes), default=0)
    communes = [l["v"] for l in lignes if not l["statut"]]
    med = median(communes) if communes else None
    return render(request, lang, "territoires.html", niveau=niveau, inds=inds, ind=ind, annee=annee, annees=annees,
                  unite=unite, lignes=lignes, absents=absents, multiples=multiples, vmax=vmax, mediane=med, nom=nom,
                  n_mediane=len(communes), statuts=statuts_noms(lang),
                  trouves=trouves,
                  toutes=toutes,
                  sources=sources_de([l["m"] for l in lignes]))


@app.get("/{lang}/territoires/{code}", response_class=HTMLResponse)
def territoire(request: Request, lang: str, code: str, annee: int | None = None):
    ent = q.entite(con, code)
    if ent is None or ent["niveau"] not in ("region", "departement"):
        raise HTTPException(404)
    racine = q.noeud(con, "ofgl_agregats", "Dépenses totales")
    annees = q.years(con, "ofgl_agregats", code, "compte", "agregat", "EUR")
    annee = annee if annee in annees else annees[-1]
    pairs = [e["code"] for e in q.entites(con, ent["niveau"])]
    speciaux = q.statuts_ofgl(con, annee)
    lignes = []
    for nom in AGREGATS_FICHE:
        n = q.noeud(con, "ofgl_agregats", nom)
        if n is None:
            continue
        eur = q.lignes(con, n["id"], q.Filtre(code, annee, "compte", "agregat", "EUR"))
        hab = q.lignes(con, n["id"], q.Filtre(code, annee, "compte", "agregat", "EUR_HAB"))
        # Médiane sur les collectivités qui publient une seule ligne cette année-là (plusieurs budgets : non retenues),
        # hors statuts particuliers publiés par l'OFGL (Paris, Métropole de Lyon, collectivités territoriales uniques).
        par_code = {r["code"]: r["valeur"] for r in con.execute(
            f"""SELECT e.code, MIN(valeur) valeur FROM montant m JOIN entite e ON e.id=m.entite_id WHERE noeud_id=? AND exercice=?
                AND unite='EUR_HAB' AND mesure='agregat' AND e.code IN ({','.join('?' * len(pairs))})
                GROUP BY e.code HAVING COUNT(*)=1""",
            (n["id"], annee, *pairs)) if r["code"] not in speciaux}
        autres = list(par_code.values())
        # Rang calculé par ce site, parmi les mêmes collectivités que la médiane (1 = montant par habitant le plus élevé).
        rang = 1 + sum(v > par_code[code] for v in autres) if code in par_code else None
        lignes.append({"nom": nom, "label": label(n["id"], lang), "eur": eur[0] if len(eur) == 1 else None,
                       "hab": hab[0] if len(hab) == 1 else None, "plusieurs": eur if len(eur) > 1 else [],
                       "mediane": median(autres) if autres else None, "nb": len(autres), "rang": rang,
                       "href": f"/{lang}/territoires?niveau={ent['niveau']}&indicateur={quote(nom)}&annee={annee}"})
    fonctions, nomen_fonctions = [], None
    if ent["niveau"] == "departement":
        for nomen in ("fonctions_dep_m57", "fonctions_dep_m52"):
            rows = con.execute(
                """SELECT n.id, n.code, m.id mid, m.valeur, (SELECT valeur FROM montant h WHERE h.noeud_id=n.id
                     AND h.entite_id=m.entite_id AND h.exercice=m.exercice AND h.mesure=m.mesure AND h.unite='EUR_HAB'
                     AND h.ligne_source=m.ligne_source) hab
                   FROM montant m JOIN noeud n ON n.id=m.noeud_id JOIN entite e ON e.id=m.entite_id
                   WHERE n.nomenclature_id=? AND n.niveau=1 AND e.code=? AND m.exercice=? AND m.mesure=? AND m.unite='EUR'
                   ORDER BY m.valeur DESC""", (nomen, code, annee, FONCTION_AGREGAT)).fetchall()
            if rows:
                fonctions = [{"label": label(r["id"], lang), "mid": r["mid"], "v": r["valeur"], "hab": r["hab"],
                              "code": r["code"]} for r in rows]
                nomen_fonctions = nomen[-3:].upper()
                break
    camembert = parts([{"key": f["code"], "label": f["label"], "v": f["v"], "m": f["mid"]} for f in fonctions])
    # Évolution des dépenses totales par habitant, et médiane du même niveau chaque année (calculée par ce site).
    par_an: dict[int, list[float]] = {}
    mien: dict[int, tuple[float, int, bool]] = {}
    for r in con.execute(
            f"""SELECT e.code, MIN(m.id) id, m.exercice, MIN(m.valeur) valeur FROM montant m JOIN entite e ON e.id=m.entite_id
                WHERE m.noeud_id=? AND m.mesure='agregat' AND m.unite='EUR_HAB' AND e.code IN ({','.join('?' * len(pairs))})
                GROUP BY e.code, m.exercice HAVING COUNT(*)=1""",
            (racine["id"], *pairs)):
        par_an.setdefault(r["exercice"], []).append(r["valeur"])
        if r["code"] == code:
            mien[r["exercice"]] = (r["valeur"], r["id"], False)
    xs = sorted(par_an)
    sans_point = sorted(set(annees) - set(mien))
    rupture = q.ruptures_detail(q.series_provenance(con, racine["id"], code, "compte", "agregat", "EUR"))
    evolution = line_data(lang, xs, [
        {"name": ent["nom"], "slot": 1, "points": mien},
        {"name": translations(lang).gettext("Médiane du même niveau"), "slot": 2,
         "points": {a: (median(v), None, False) for a, v in par_an.items()}}], "EUR_HAB", zero=False)
    sources_table = sources_de([x["id"] for l in lignes for x in (l["eur"], l["hab"], *l["plusieurs"]) if x])
    return render(request, lang, "territoire.html", ent=ent, annee=annee, annees=annees, lignes=lignes,
                  sources_table=sources_table, description=source_info(sources_table[0]) if sources_table else None,
                  fonctions=fonctions, nomen=nomen_fonctions, racine=racine, camembert=camembert, evolution=evolution,
                  sans_point=sans_point, rupture=rupture, statut=speciaux.get(code), statuts_noms=statuts_noms(lang),
                  total_fonctions=sum(f["v"] for f in fonctions) if fonctions else None)
