"""Fiches thématiques (docs/ROADMAP.md, chantier C) : une page par politique publique, qui rassemble ce que le site sait
du sujet, publication par publication, avec ses limites.

Le thème est décrit dans content/themes.yaml (fonction COFOG, missions de l'État, fonction des départements). Ces
rattachements sont un regroupement du site : chaque bloc garde sa source et son périmètre, et aucun bloc n'est
additionné à un autre. Importé à la fin de api/main.py, avant api/portes.py.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from api import differences as dif
from api import queries as q
from api.main import (BV_STADES, SOURCE_COFOG, app, bv_cols, con, env, label, line_data, nom_entite, perimetre_nom,
                      render, sources_de)
from pipeline.catalog import ROOT

SECTEURS = ("S1311", "S1313", "S1314")


@lru_cache(maxsize=1)
def themes() -> dict[str, dict[str, Any]]:
    return yaml.safe_load((ROOT / "content/themes.yaml").read_text(encoding="utf-8")) or {}


def fiche_cofog(code: str) -> str | None:
    """Clé de la fiche d'une fonction COFOG (division ou sous-fonction), pour les liens des autres pages."""
    return next((k for k, t in themes().items() if code.startswith(t["cofog"])), None)


env.globals["fiche_cofog"] = fiche_cofog


def montant(noeud_id: int, ent: str, annee: int, unite: str) -> dict[str, Any] | None:
    m = q.single(con, noeud_id, q.Filtre(ent, annee, "compte", "depense", unite))
    return dict(m) if m else None


def cofog(code: str, lang: str) -> dict[str, Any]:
    """Comptes nationaux : le total publié, sa part, son évolution, qui dépense et à quoi, la dernière année publiée."""
    n = q.noeud(con, "cofog", code)
    annees = q.years(con, "cofog", "APU-S13", "compte", "depense", "MIO_EUR")
    a = annees[-1]
    serie = q.series(con, n["id"], "APU-S13", "compte", "depense", "PC_GDP")
    evolution = line_data(lang, [r["exercice"] for r in serie], [
        {"name": perimetre_nom("S13", lang), "slot": 1,
         "points": {r["exercice"]: (r["valeur"], r["id"], r["provisoire"]) for r in serie}}], "PC_GDP", zero=True)
    secteurs = [{"nom": nom_entite(q.entite(con, f"APU-{s}")["nom"], lang), "m": montant(n["id"], f"APU-{s}", a, "MIO_EUR")}
                for s in SECTEURS]
    detail = [{"label": label(c["id"], lang), "m": montant(c["id"], "APU-S13", a, "MIO_EUR")}
              for c in q.children(con, n["id"])]
    detail = sorted([d for d in detail if d["m"]], key=lambda d: -d["m"]["valeur"])
    return {"noeud": n, "label": label(n["id"], lang), "annee": a, "debut": annees[0],
            "m": montant(n["id"], "APU-S13", a, "MIO_EUR"), "pib": montant(n["id"], "APU-S13", a, "PC_GDP"),
            "part": montant(n["id"], "APU-S13", a, "PC_TOT"), "evolution": evolution,
            "secteurs": [s for s in secteurs if s["m"]], "detail": detail,
            "sources": [SOURCE_COFOG], "lacunes": [l for l in q.lacunes(con) if l["source_id"] == SOURCE_COFOG][:5]}


def etat(missions: list[str], lang: str) -> list[dict[str, Any]]:
    """Budget de l'État : crédits de paiement de chaque mission rattachée, aux trois stades publiés, et le coût estimé
    des dépenses fiscales que la même publication rattache à la mission."""
    out = []
    for nom in missions:
        cb = q.noeud(con, "budget_vert_plf2026", f"CB|{nom}")
        if cb is None:
            continue
        df = q.noeud(con, "budget_vert_plf2026", f"DF|{nom}")
        niches = None
        if df is not None:
            f = q.Filtre("ETAT", 2026, "plf", "cout_estime", "EUR")
            v, nb, _p = q.total(con, df["id"], f)
            niches = {"v": v, "n": nb, "href": f"provenance/noeud/{df['id']}?{f.query()}"} if nb else None
        out.append({"id": cb["id"], "label": label(cb["id"], lang), "cols": bv_cols(cb["id"], "cp"), "niches": niches})
    return out


def paire_etat(cle: str, lang: str) -> dict[str, Any] | None:
    """Exemple de l'outil « pourquoi ces chiffres diffèrent » : les administrations centrales en comptes nationaux face à
    la première mission rattachée, la même année si le budget vert la publie (sinon la plus ancienne publiée)."""
    t = themes()[cle]
    cb = next((n for m in t.get("missions", []) if (n := q.noeud(con, "budget_vert_plf2026", f"CB|{m}"))), None)
    n = q.noeud(con, "cofog", t["cofog"])
    a = q.years(con, "cofog", "APU-S1311", "compte", "depense", "MIO_EUR")[-1]
    m = q.single(con, n["id"], q.Filtre("APU-S1311", a, "compte", "depense", "MIO_EUR"))
    if cb is None or m is None:
        return None
    annee, stade = next((s for s in BV_STADES if s[0] == a), BV_STADES[0])
    f = q.Filtre("ETAT", annee, stade, "cp", "EUR")
    if q.total(con, cb["id"], f)[0] is None:
        return None
    ra, rb = f"m{m['id']}", dif.ref_total(cb["id"], f)
    ca, cb_ = dif.cote(ra, lang), dif.cote(rb, lang)
    return {"a": ca, "b": cb_, "crit": dif.comparer(ca, cb_, lang), "href": f"/{lang}/differences?a={ra}&b={rb}"}


@app.get("/{lang}/theme", response_class=HTMLResponse)
def fiches(request: Request, lang: str):
    from api.colonnes import icone
    from api.machine import ICO  # importé ici : api.machine importe ce module
    liste = [{"cle": k, "ico": ICO.get(t["cofog"], "point"), "label": label(q.noeud(con, "cofog", t["cofog"])["id"], lang)}
             for k, t in themes().items()]
    return render(request, lang, "fiches.html", liste=liste, icone=icone)


@app.get("/{lang}/theme/{cle}", response_class=HTMLResponse)
def fiche(request: Request, lang: str, cle: str):
    t = themes().get(cle)
    if t is None:
        raise HTTPException(404)
    c = cofog(t["cofog"], lang)
    m57 = q.noeud(con, "fonctions_dep_m57", t["m57"]) if t.get("m57") else None
    return render(request, lang, "fiche.html", cle=cle, c=c, etat=etat(t.get("missions", []), lang), stades=BV_STADES,
                  paire=paire_etat(cle, lang),
                  m57=m57 and {"code": t["m57"], "label": label(m57["id"], lang)},
                  sources_etat=["etat_budget_vert_plf2026"],
                  sources_secteurs=sources_de([s["m"]["id"] for s in c["secteurs"]]),
                  sources_detail=sources_de([d["m"]["id"] for d in c["detail"]]))
