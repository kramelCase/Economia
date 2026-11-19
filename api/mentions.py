"""Mentions légales et licences : qui publie le site, sous quelles licences sont les données, le code et les éléments
réutilisés (polices, modèles 3D, bibliothèques), et ce que le site garde dans le navigateur.

L'identité de l'éditeur et de l'hébergeur vient de `content/editeur.yaml`, rempli par le user ; un champ vide est
affiché « à compléter », jamais deviné. Les licences des données sont lues dans la table `source`.
Importé à la fin de api/main.py, avant api/portes.py.
"""

from __future__ import annotations

import yaml
from fastapi import Request
from fastapi.responses import HTMLResponse

from api.main import app, con, render
from pipeline.catalog import ROOT

# Éléments réutilisés, avec la licence publiée par leur auteur (fichiers de licence dans static/vendor/).
TIERS = (
    ("IBM Plex Sans, IBM Plex Mono", "SIL Open Font License 1.1", "https://github.com/IBM/plex"),
    ("Source Serif 4", "SIL Open Font License 1.1", "https://github.com/adobe-fonts/source-serif"),
    ("Kenney : City Kit (Commercial, Industrial, Suburban), Car Kit, Castle Kit", "CC0 1.0", "https://kenney.nl/assets"),
    ("three.js 0.160.0", "MIT", "https://github.com/mrdoob/three.js"),
    ("D3 7.9.0", "ISC", "https://github.com/d3/d3"),
    ("Observable Plot 0.6.16", "ISC", "https://github.com/observablehq/plot"),
)


def editeur() -> dict:
    p = ROOT / "content/editeur.yaml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None) or {}


@app.get("/{lang}/mentions", response_class=HTMLResponse)
def mentions(request: Request, lang: str):
    licences: dict[str, list] = {}
    for r in con.execute("SELECT id, editeur, licence FROM source ORDER BY editeur, id"):
        licences.setdefault(r["licence"], []).append(r)
    return render(request, lang, "mentions.html", ed=editeur(), licences=licences, tiers=TIERS)
