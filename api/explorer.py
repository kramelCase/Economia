"""La phrase-requête « thème × périmètre » (docs/vision/SYNTHESE.md §8).

Détaché de api/main.py. Importé à la fin de api/main.py, avant api/portes.py.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from api import queries as q
from api.i18n import LANGS, translations
from api.main import (PERIMETRES, THEME_NICHES, amorces, app, cofog_divisions, cofog_ordre, con, label, perimetre_nom,
                      possible, render, reponse, voisins)


@app.get("/{lang}/explorer", response_class=HTMLResponse)
def explorer(request: Request, lang: str, theme: str = "", qui: str = ""):
    if lang not in LANGS:
        raise HTTPException(404)
    if not theme and not qui:  # ancienne entrée « Explorer » du menu : les thèmes
        return RedirectResponse(f"/{lang}/theme", status_code=301)
    if not theme:  # par défaut : la fonction au plus grand montant publié, toutes administrations
        theme, qui = cofog_ordre("S13")[0], qui or "S13"
    divisions = cofog_divisions()
    if (theme != THEME_NICHES and theme not in {n["code"] for n in divisions}) or qui not in PERIMETRES:
        raise HTTPException(404)
    _ = translations(lang).gettext
    themes = [{"code": THEME_NICHES, "texte": _("les dépenses fiscales")}] + \
             [{"code": n["code"], "texte": label(n["id"], lang)["texte"]} for n in divisions]
    perimetres = [{"code": p, "texte": perimetre_nom(p, lang), "ok": possible(theme, p)} for p in PERIMETRES]
    return render(request, lang, "explorer.html", theme=theme, qui=qui, themes=themes, perimetres=perimetres,
                  r=reponse(theme, qui, lang), voisins=voisins(theme, qui, lang), amorces=amorces(lang),
                  theme_nom=next(t["texte"] for t in themes if t["code"] == theme), qui_nom=perimetre_nom(qui, lang),
                  sujets=sujets(lang), entrees=entrees(lang))


def sujets(lang: str) -> list[list[dict[str, Any]]]:
    """Les deux rubans de sujets : chaque étiquette mène à une réponse qui existe (ou à la liste des lacunes)."""
    _ = translations(lang).gettext
    fonctions = [{"t": label(n["id"], lang)["texte"], "href": f"/{lang}/explorer?theme={n['code']}&qui=S13#question"}
                 for n in cofog_divisions()]
    autres = [{"t": _("Dépenses fiscales"), "href": f"/{lang}/explorer?theme={THEME_NICHES}&qui=ETAT#question"},
              {"t": _("Budget de l'État"), "href": f"/{lang}/budget-etat"},
              {"t": _("Données non disponibles"), "href": f"/{lang}/lacunes", "gap": True}]
    regions = [{"t": e["nom"], "href": f"/{lang}/territoires/{e['code']}"} for e in q.entites(con, "region")]
    return [fonctions + autres[:2], regions + autres[2:]]


def entrees(lang: str) -> list[dict[str, Any]]:
    _ = translations(lang).gettext
    return [
        {"t": _("Construire une vue"), "href": f"/{lang}/serie",
         "d": _("Indicateurs, périmètres et territoires sur toute la période publiée ; export CSV, JSON, image.")},
        {"t": _("Où va l'argent ?"), "href": f"/{lang}/depenses-publiques",
         "d": _("Toutes les administrations publiques, par fonction COFOG, depuis 1995.")},
        {"t": _("D'où vient l'argent ?"), "href": f"/{lang}/recettes-publiques",
         "d": _("Toutes les administrations publiques, par catégorie de recettes des comptes nationaux, depuis 1995.")},
        {"t": _("Budget de l'État"), "href": f"/{lang}/budget-etat",
         "d": _("Missions et programmes : exécuté en 2024, voté pour 2025, proposé pour 2026.")},
        {"t": _("Dépenses fiscales"), "href": f"/{lang}/depenses-fiscales",
         "d": _("Montant publié de chaque dépense fiscale, et nombre de dépenses publiées sans montant.")},
        {"t": _("Ma région, mon département"), "href": f"/{lang}/territoires",
         "d": _("Par habitant, comparé à la médiane des collectivités du même niveau.")},
        {"t": _("Données non disponibles"), "href": f"/{lang}/lacunes", "gap": True,
         "d": _("Données absentes des sources collectées, avec l'organisme producteur.")},
    ]
