"""Les quatre entrées du site : Accueil, Thèmes, Ma collectivité, Sources.

Une arborescence courte : l'accueil répond à « où va l'argent public ? », chaque thème a sa fiche, chaque collectivité
sa page, et Sources rassemble tout ce qui sert à vérifier. Les autres pages (outils, séries, budget de l'État...) restent
ouvertes depuis ces pages, rattachées à une entrée par `chemins`. Le menu et la page Sources lisent la même liste.
Importé à la fin de api/main.py (il en réutilise l'application et le rendu).
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from api.i18n import translations
from api.main import app, render


def entrees(lang: str) -> list[dict[str, Any]]:
    """Les quatre entrées : lien, chemins rattachés (pour marquer l'entrée courante) et, pour Sources, ses pages."""
    _ = translations(lang).gettext
    return [
        {"cle": "accueil", "ico": "batiment", "t": _("Accueil"), "href": f"/{lang}/",
         "chemins": ("/", "/machine", "/grands-equilibres", "/recettes-publiques", "/comprendre", "/bases", "/contexte")},
        {"cle": "themes", "ico": "fonctions", "t": _("Thèmes"), "href": f"/{lang}/theme",
         "chemins": ("/theme", "/depenses-publiques", "/budget-etat", "/depenses-fiscales", "/explorer", "/serie",
                     "/atelier")},
        {"cle": "collectivite", "ico": "lieu", "t": _("Ma collectivité"), "href": f"/{lang}/territoires",
         "chemins": ("/territoires", "/comparer")},
        {"cle": "sources", "ico": "fichiers", "t": _("Sources"), "href": f"/{lang}/sources",
         "chemins": ("/sources", "/verifier", "/recherche", "/montant", "/provenance", "/preuve", "/differences",
                     "/donnees", "/methode", "/lacunes", "/lexique", "/source", "/mentions"),
         "titre": _("D'où viennent les chiffres"), "recherche": True,
         "lede": _("Chaque chiffre vient d'un fichier officiel. Ici, on peut le vérifier."),
         "pages": [
             {"t": _("Vérifier un chiffre entendu"), "ico": "loupe", "href": f"/{lang}/verifier"},
             {"t": _("Pourquoi deux chiffres diffèrent"), "ico": "balance", "href": f"/{lang}/differences"},
             {"t": _("Lexique"), "ico": "livre", "href": f"/{lang}/lexique"},
             {"t": _("Données non disponibles"), "ico": "manque", "href": f"/{lang}/lacunes"},
             {"t": _("Méthode et fichiers collectés"), "ico": "fichiers", "href": f"/{lang}/methode"},
             {"t": _("Données couvertes et téléchargements"), "ico": "tableau", "href": f"/{lang}/donnees"},
         ]},
    ]


def entree_courante(lang: str, path: str) -> str | None:
    p = path[len(lang) + 1:] if path.startswith(f"/{lang}") else path
    for e in entrees(lang):
        if any(p == c or p.startswith(c + "/") or p.startswith(c + "?") for c in e["chemins"]):
            return e["cle"]
    return None


def ariane(lang: str, path: str) -> list[dict[str, str]] | None:
    """Fil d'Ariane : l'entrée du menu, puis la page d'entrée qui contient la page courante (fiches thématiques pour
    une fiche...). Le dernier maillon, le titre de la page, est ajouté par base.html. None sur l'accueil."""
    p = path[len(lang) + 1:] if path.startswith(f"/{lang}") else path
    if p in ("", "/"):
        return None
    out = []
    e = next((e for e in entrees(lang) if e["cle"] == entree_courante(lang, path)), None)
    if e is not None and e["cle"] != "accueil" and e["href"] != f"/{lang}{p}":
        out.append({"t": e["t"], "href": e["href"]})
        out += [{"t": x["t"], "href": x["href"]} for x in e.get("pages", [])
                if p.startswith(x["href"][len(lang) + 1:] + "/") and x["href"] != e["href"]]
    return out


@app.get("/{lang}/{cle}", response_class=HTMLResponse)
def porte(request: Request, lang: str, cle: str):
    if cle == "comprendre":  # anciennes entrées du menu : l'accueil (ou les grands équilibres d'une année)
        if request.query_params.get("annee"):
            return RedirectResponse(f"/{lang}/grands-equilibres?{request.url.query}", status_code=301)
        return RedirectResponse(f"/{lang}/", status_code=301)
    page = next((e for e in entrees(lang) if e["href"] == f"/{lang}/{cle}" and e.get("pages")), None)
    if page is None:
        raise HTTPException(404)
    from api.colonnes import icone
    return render(request, lang, "porte.html", e=page, etapes=None, icone=icone)
