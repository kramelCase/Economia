"""Comprendre : les grands équilibres des comptes publics en volumes (scènes 3D, static/volumes.js).

Chaque scène ne dessine que des montants publiés, une source et une unité par scène ; la hauteur est la seule
grandeur encodée (caméra orthographique : pas de perspective qui grossit le premier plan). Le tableau jumeau et les
valeurs écrites dans la légende donnent les mêmes chiffres sans WebGL.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse

from api import queries as q
from api.main import SECTEURS, app, con, label, nom_entite, render, sources_de
from api.i18n import money

EQUILIBRE = ("TR", "TE", "B9")


def serie(code: str, entite: str, unite: str, lang: str) -> dict[str, Any]:
    n = q.noeud(con, "apu_agregats", code)
    return {"code": code, "label": label(n["id"], lang),
            "points": {r["exercice"]: {"v": r["valeur"], "m": r["id"], "prov": bool(r["provisoire"]),
                                       "t": money(r["valeur"], lang, unite)}
                       for r in q.series(con, n["id"], entite, "compte", "agregat", unite)}}


def montants(*series: dict[str, Any]) -> list[int]:
    return [p["m"] for s in series for p in s["points"].values()]


def payload(d: dict[str, Any]) -> str:
    return json.dumps(d, ensure_ascii=False).replace("</", "<\\/")


@app.get("/{lang}/grands-equilibres", response_class=HTMLResponse)
def comprendre(request: Request, lang: str, annee: int | None = None):
    eq = {c: serie(c, "APU-S13", "PC_GDP", lang) for c in EQUILIBRE}
    sect = {s: serie("TE", f"APU-{s}", "MIO_EUR", lang) for s in SECTEURS}
    for s in SECTEURS:
        sect[s]["nom"] = nom_entite(q.entite(con, f"APU-{s}")["nom"], lang)
    dette = serie("GD", "APU-S13", "PC_GDP", lang)
    annees = sorted(set(eq["TR"]["points"]) & set(eq["TE"]["points"]) & set(eq["B9"]["points"])
                    & set(sect["S13"]["points"]) & set(dette["points"]))
    annee = annee if annee in annees else annees[-1]
    return render(request, lang, "comprendre.html", annees=annees, annee=annee, eq=eq, sect=sect, dette=dette,
                  secteurs=SECTEURS,
                  src_eq=sources_de(montants(*eq.values())), src_sect=sources_de(montants(*sect.values())),
                  src_dette=sources_de(montants(dette)),
                  data=payload({"annees": annees, "annee": annee, "eq": eq, "sect": sect, "dette": dette,
                                "secteurs": list(SECTEURS)}))
