"""Où va l'argent public (COFOG), budget de l'État et dépenses fiscales : les pages d'ensemble.

Détaché de api/main.py. Importé à la fin de api/main.py, avant api/portes.py.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from api import queries as q, serie
from api.main import (BV_STADES, PARTS_MAX, SECTEURS, app, bv_cols, cofog_ordre, con, label, line_data, nom_entite,
                      parts, render, sources_de, top_keys)


# --- Où va l'argent public ? (COFOG, toutes administrations) ---
@app.get("/{lang}/depenses-publiques", response_class=HTMLResponse)
def depenses_publiques(request: Request, lang: str, secteur: str = "S13", annee: int | None = None,
                       fonction: str = ""):
    if secteur not in SECTEURS:
        raise HTTPException(404)
    ent = f"APU-{secteur}"
    annees = q.years(con, "cofog", ent, "compte", "depense", "MIO_EUR")
    annee = annee if annee in annees else annees[-1]
    total = q.noeud(con, "cofog", "TOTAL")
    fm = q.Filtre(ent, annee, "compte", "depense", "MIO_EUR")
    fp = q.Filtre(ent, annee, "compte", "depense", "PC_TOT")
    tot = q.single(con, total["id"], fm)

    def divisions(f: q.Filtre, fpc: q.Filtre | None = None) -> list[dict[str, Any]]:
        out = []
        for n in q.children(con, total["id"]):
            m = q.single(con, n["id"], f)
            if m is not None:
                out.append({"key": n["code"], "id": n["id"], "label": label(n["id"], lang), "v": m["valeur"],
                            "m": m["id"], "prov": m["provisoire"], "p": q.single(con, n["id"], fpc) if fpc else None,
                            "drill": f"?secteur={secteur}&annee={annee}&fonction={n['code']}#zoom"})
        return out

    # Référence des couleurs : les 5 premières fonctions du secteur la dernière année publiée.
    ref = top_keys(divisions(q.Filtre(ent, annees[-1], "compte", "depense", "MIO_EUR")))
    camembert = parts(divisions(fm, fp), ref)
    fnode = q.noeud(con, "cofog", fonction) if fonction.startswith("GF") and len(fonction) == 4 else None
    fnode = fnode or q.noeud(con, "cofog", cofog_ordre(secteur)[0])  # par défaut : le plus grand montant
    fm_f = q.single(con, fnode["id"], fm)
    subs = [{"key": s["code"], "label": label(s["id"], lang), "v": m["valeur"], "m": m["id"], "prov": m["provisoire"]}
            for s in q.children(con, fnode["id"]) if (m := q.single(con, s["id"], fm)) is not None]
    zoom = parts(subs)
    serie = q.series(con, fnode["id"], ent, "compte", "depense", "PC_TOT")
    courbe = line_data(lang, [p["exercice"] for p in serie], [{
        "name": label(fnode["id"], lang)["texte"], "slot": 1,
        "points": {p["exercice"]: (p["valeur"], p["id"], p["provisoire"]) for p in serie}}], "PC_TOT")
    secteurs = [{"code": s, "nom": nom_entite(q.entite(con, f"APU-{s}")["nom"], lang)} for s in SECTEURS]
    somme_sous_secteurs = sum((q.single(con, total["id"], q.Filtre(f"APU-{s}", annee, "compte", "depense", "MIO_EUR"))
                               or {"valeur": 0})["valeur"] for s in SECTEURS[1:])
    return render(request, lang, "depenses_publiques.html", secteur=secteur, secteurs=secteurs, annee=annee,
                  annees=annees, tot=tot, camembert=camembert, fonction=fnode["code"],
                  fonction_label=label(fnode["id"], lang), fonction_m=fm_f, zoom=zoom, serie=serie, evolution=courbe,
                  somme_sous_secteurs=somme_sous_secteurs,
                  tot_s13=q.single(con, total["id"], q.Filtre("APU-S13", annee, "compte", "depense", "MIO_EUR")))


@app.get("/{lang}/budget-etat", response_class=HTMLResponse)
def budget_etat(request: Request, lang: str, vue: int = 2, mission: int | None = None):
    vue = vue if vue in range(len(BV_STADES)) else 2
    cb = q.noeud(con, "budget_vert_plf2026", "CB")
    ta = q.noeud(con, "budget_vert_plf2026", "TA")

    def item(n, cols, drill=None) -> dict[str, Any]:
        lb = label(n["id"], lang)
        if re.fullmatch(r"[A-Z0-9_]+", lb["texte"] or ""):
            # Sigle publié tel quel (PSRCT, T3_CAS…) : la même source donne un libellé long plus bas dans l'arbre.
            pile = [c["id"] for c in q.children(con, n["id"])]
            while pile:
                nid = pile.pop(0)
                long = label(nid, lang)
                if not re.fullmatch(r"[A-Z0-9_]+", long["texte"] or ""):
                    lb = dict(long, texte=f"{long['texte']} ({lb['texte']})")
                    break
                pile += [c["id"] for c in q.children(con, nid)]
        return {"key": str(n["id"]), "id": n["id"], "label": lb, "cols": cols,
                "v": cols[vue]["v"], "href": cols[vue]["href"] if cols[vue]["n"] else None, "drill": drill}

    missions = [item(m, bv_cols(m["id"], "cp"), f"?vue={vue}&mission={m['id']}#zoom") for m in q.children(con, cb["id"])]
    missions.sort(key=lambda m: -(m["v"] or 0))
    # Référence des couleurs : les 5 premières missions du PLF 2026, quelle que soit la vue.
    ref = [m["key"] for m in sorted(missions, key=lambda m: -(m["cols"][2]["v"] or 0))[:PARTS_MAX]]
    zoom = None
    if mission is not None:
        mnode = next((m for m in missions if m["id"] == mission), None)
        if mnode is None:
            raise HTTPException(404)
        progs = [item(p, bv_cols(p["id"], "cp")) for p in q.children(con, mission)]
        progs.sort(key=lambda p: -(p["v"] or 0))
        zoom = {"mission": mnode, "parts": parts(progs), "progs": progs}
    techniques = con.execute("SELECT COUNT(*) FROM noeud WHERE nomenclature_id='budget_vert_plf2026' AND technique=1"
                             ).fetchone()[0]
    total = bv_cols(cb["id"], "cp")
    vues = [{"i": i, "annee": a, "stade": s} for i, (a, s) in enumerate(BV_STADES)]
    return render(request, lang, "budget_etat.html", missions=missions, camembert=parts(missions, ref), zoom=zoom,
                  total=total, taxes=bv_cols(ta["id"], "montant"), techniques=techniques, vue=vue, vues=vues)


# --- Dépenses fiscales (« niches ») ---
@app.get("/{lang}/depenses-fiscales", response_class=HTMLResponse)
def depenses_fiscales(request: Request, lang: str, annee: int = 2026, impot: str = ""):
    if annee not in (2024, 2025, 2026):
        raise HTTPException(404)
    df = q.depenses_fiscales(con, annee)
    total = sum(d["valeur"] for d in df)

    def par_impot(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by: dict[str, dict[str, Any]] = {}
        for d in rows:
            i = by.setdefault(d["impot"] or "", {"key": d["impot"] or "", "label": {"texte": d["impot"] or "—",
                              "fr_only": lang != "fr"}, "v": 0.0, "ids": [], "n": 0})
            i["v"] += d["valeur"]
            i["ids"] += d["montants"]
            i["n"] += 1
        for i in by.values():
            i["drill"] = f"?annee={annee}&impot={quote(i['key'])}#liste"
        return sorted(by.values(), key=lambda i: -i["v"])

    impots = par_impot(df)
    # Référence des couleurs : les 5 impôts les plus concernés dans le chiffrage 2026.
    ref = top_keys(par_impot(q.depenses_fiscales(con, 2026)))
    if impot and impot not in {i["key"] for i in impots}:
        raise HTTPException(404)
    liste = [d for d in df if not impot or (d["impot"] or "") == impot]
    vmax = max((d["valeur"] for d in liste), default=0)
    lac = q.lacunes(con, ("non_chiffre", "sous_seuil"))
    nb_codes = con.execute("""SELECT COUNT(DISTINCT json_extract(attributs, '$.code_depense')) FROM montant m
        JOIN noeud n ON n.id=m.noeud_id WHERE n.code LIKE 'DF|%'""").fetchone()[0]
    racine = q.noeud(con, "budget_vert_plf2026", "DF")
    total_href = f"provenance/noeud/{racine['id']}?{q.Filtre('ETAT', annee, 'plf', 'cout_estime', 'EUR').query()}"
    return render(request, lang, "depenses_fiscales.html", liste=liste, vmax=vmax, nb=len(df), total=total,
                  sources=sources_de([i for d in liste for i in d["montants"]]) or ["etat_budget_vert_plf2026"],
                  total_href=total_href, camembert=parts(impots, ref), impots=impots, impot=impot,
                  total_impot=sum(d["valeur"] for d in liste), ids_impot=[i for d in liste for i in d["montants"]],
                  annee=annee, nc=[l for l in lac if l["type"] == "non_chiffre"],
                  eps=[l for l in lac if l["type"] == "sous_seuil"], nb_codes=nb_codes)
