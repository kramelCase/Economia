"""Adresses par langue : le français est la langue des routes, l'anglais a ses propres mots dans l'adresse.

Une requête /en/<mot anglais>… est servie par la route française ; une adresse /en/<mot français>… (anciens liens,
liens construits en JavaScript) est redirigée vers son équivalent anglais. Les pages sont rendues avec des liens
français, que `traduire_liens` réécrit : une seule table, ici, pour l'entrée comme pour la sortie.
"""

from __future__ import annotations

import re

from starlette.responses import RedirectResponse

EN = {
    "comprendre": "understand", "grands-equilibres": "key-balances", "recettes-publiques": "public-revenue",
    "depenses-publiques": "public-spending", "budget-etat": "state-budget", "depenses-fiscales": "tax-expenditures",
    "verifier": "check", "recherche": "search", "montant": "figure", "preuve": "evidence", "methode": "method",
    "lacunes": "missing-data", "territoires": "territories", "explorer": "explore", "atelier": "chart-studio",
    "serie": "series", "comparer": "compare", "contexte": "context", "donnees": "data", "lexique": "glossary", "mentions": "legal", "theme": "topic",
}
FR = {v: k for k, v in EN.items()}
assert len(FR) == len(EN) and not set(FR) & set(EN)

# Anciennes adresses françaises, renommées pour qu'un nom de menu ait une adresse (redirigées dans les deux langues).
ANCIENNES = {"bases": "comprendre"}

_CHEMIN = re.compile(r"^/(fr|en)/([a-z-]+)(.*)$", re.S)
_LIEN = re.compile(r"(?<=[\"'(=\s])/en/(" + "|".join(sorted(EN, key=len, reverse=True)) + r")(?![\w-])")


def traduire_liens(page: str) -> str:
    """Réécrit les liens /en/<mot français> d'une page rendue en /en/<mot anglais>."""
    return _LIEN.sub(lambda m: "/en/" + EN[m.group(1)], page)


async def adresses(request, call_next):
    m = _CHEMIN.match(request.scope["path"])
    if m:
        lang, mot, reste = m.groups()
        q = request.scope.get("query_string", b"").decode("latin-1")
        cible = None
        if mot in ANCIENNES:
            mot2 = ANCIENNES[mot]
            cible = f"/{lang}/{EN[mot2] if lang == 'en' else mot2}{reste}"
        elif lang == "en" and mot in EN:
            cible = f"/en/{EN[mot]}{reste}"
        if cible and request.method in ("GET", "HEAD"):
            return RedirectResponse(cible + (f"?{q}" if q else ""), status_code=301)
        if lang == "en" and mot in FR:
            interne = f"/en/{FR[mot]}{reste}"
            request.scope["path"] = interne
            request.scope["raw_path"] = interne.encode()
    return await call_next(request)
