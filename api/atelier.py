"""Atelier de graphique (docs/vision/WIDGETS.md, W1).

Le serveur ne rend que la page et ses libellés ; le widget charge les fichiers statiques des documents
(`/data/manifest.json`, api/donnees.py) et fait tout le reste dans le navigateur. Aucun paramètre de l'URL n'atteint
une requête : ils sont relus côté navigateur, contre des listes fermées.
Importé à la fin de api/main.py, avant api/portes.py.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse

from api.i18n import translations
from api import queries as q
from api.main import SECTEURS, app, con, nom_entite, render, source_info
from api.serie import unite_nom

# Documents ouverts dans l'atelier : des séries annuelles. Les budgets de l'État (2 ou 3 années, stades différents)
# auront leur propre widget (W7).
DOCS = ("cofog", "apu", "ofgl-region", "ofgl-departement", "dep-m57", "dep-m52")


def libelles(lang: str) -> dict[str, Any]:
    _ = translations(lang).gettext
    return {
        "docs": {"cofog": _("Dépenses par fonction"), "apu": _("Recettes, dépenses, solde, dette"),
                 "ofgl-region": _("Régions"), "ofgl-departement": _("Départements"),
                 "dep-m57": _("Départements, par fonction (M57)"), "dep-m52": _("Départements, par fonction (M52)")},
        "unites": {u: unite_nom(u, lang) for u in ("PC_GDP", "PC_TOT", "MIO_EUR", "EUR", "EUR_HAB")},
        "types": {"courbe": _("Courbes"), "aires": _("Aires empilées"), "aires100": _("Aires à 100 %"),
                  "barres": _("Barres groupées"), "empilees": _("Barres empilées"), "classement": _("Classement"),
                  "pente": _("Pente (deux années)"), "points": _("Points (une année)"),
                  "multiples": _("Petits multiples"), "chaleur": _("Carte de chaleur")},
        "entites": {f"APU-{s}": nom_entite(q.entite(con, f"APU-{s}")["nom"], lang) for s in SECTEURS},
        "court_types": {"courbe": _("Courbes"), "aires": _("Aires"), "aires100": _("Parts"), "barres": _("Barres"),
                        "empilees": _("Empilées"), "classement": _("Classement"), "pente": _("Pente"),
                        "points": _("Points"), "multiples": _("Multiples"), "chaleur": _("Chaleur")},
        # Le symbole d'unité est posé à côté du mot, hors de la chaîne traduite (un « % » y passerait pour un format).
        "court": {"PC_GDP": ["%", _("du PIB")], "PC_TOT": ["%", _("du total")], "MIO_EUR": ["€", _("courants")],
                  "EUR": ["€", _("courants")], "EUR_HAB": ["€", _("par habitant")]},
        "formats": {"carre": _("Carré"), "large": _("Large"), "vertical": _("Vertical")},
        "raisons": {
            "empiler": _("Empiler n'a de sens que pour les parties d'un même total publié, dans un document dont les parties bouclent sur le total."),
            "une_entite": _("Pour empiler, un seul périmètre."),
            "deux_series": _("Il faut au moins deux séries."),
            "deux_annees": _("Il faut au moins deux années."),
            "trop": _("Cinq séries au plus sur un même graphique."),
        },
        "t": {
            "charge": _("Chargement des données…"), "erreur": _("Les données n'ont pas pu être chargées."),
            "tous": _("tous"), "base100": _("indice base 100 en %(a)s (calcul du site)"),
            "zero": _("L'axe ne part pas de zéro."), "copie": _("Lien copié."),
            "source": _("Source"), "sources": _("Sources"), "calcul": _("calcul du site"),
            "provisoire": _("provisoire"), "voir": _("source"), "aucune": _("Aucune valeur publiée pour ce choix."),
            "annee": _("Année"), "valeur": _("Valeur"), "serie": _("Série"), "retirer": _("Retirer"),
            "base100_non": _("Pas d'indice base 100 pour une forme empilée ou d'une seule année."),
            "base_neg": _("Pas d'indice quand la valeur de l'année de base est nulle ou négative"),
            "plusieurs": _("Plusieurs budgets publiés sous un même code, non tracés"),
            "rupture": _("Autre SIREN ou population publiée variant de plus de moitié sous un même code : ligne coupée, pas d'évolution à lire à travers"),
            "annot": _("Annotations ajoutées par l'auteur du graphique, pas par la source."),
        },
    }


def citations(lang: str) -> dict[str, dict[str, str]]:
    sources = {r["id"]: source_info(r["id"]) for r in con.execute("SELECT id FROM source")}
    return {sid: {"editeur": s["editeur_court"], "titre": (s["titre_en"] if lang == "en" and s["titre_en"] else s["titre"]),
                  "identifiant": s["identifiant"], "maj": s["maj"] or (s["collecte"] or "")[:10]}
            for sid, s in sources.items()}


@app.get("/{lang}/atelier", response_class=HTMLResponse)
def atelier(request: Request, lang: str):
    return render(request, lang, "atelier.html", L=libelles(lang), citations=citations(lang), docs=DOCS)

