"""Langues de l'interface. Le français est la langue source (celle des données officielles) :
les chaînes sont écrites en français dans le code et les gabarits, traduites via gettext (locales/)."""

from __future__ import annotations

import gettext
from functools import lru_cache
from pathlib import Path

from babel.numbers import format_decimal, format_percent

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
LANGS = ("fr", "en")
DEFAULT_LANG = "fr"
LANG_NAMES = {"fr": "Français", "en": "English"}


@lru_cache(maxsize=None)
def translations(lang: str) -> gettext.NullTranslations:
    if lang == DEFAULT_LANG:
        return gettext.NullTranslations()
    return gettext.translation("messages", localedir=str(LOCALES_DIR), languages=[lang])


def money(value: float | None, lang: str, unit: str = "EUR") -> str:
    """Montant lisible : « 148,6 Md€ », « 1 234 €/hab. », « 8,9 % »."""
    if value is None:
        return "—"
    if unit == "PC_TOT" or unit == "PC_GDP":
        return format_decimal(value, "#,##0.0", locale=lang) + " %"
    if unit == "EUR_HAB":
        return format_decimal(value, "#,##0", locale=lang) + (" €/hab." if lang == "fr" else " € per capita")
    euros = value * 1e6 if unit == "MIO_EUR" else value
    a = abs(euros)
    if a >= 1e9:
        s, suffix = euros / 1e9, ("Md€" if lang == "fr" else "bn €")
    elif a >= 1e6:
        s, suffix = euros / 1e6, ("M€" if lang == "fr" else "m €")
    elif a >= 1e3:
        s, suffix = euros / 1e3, ("k€" if lang == "fr" else "k €")
    else:
        return format_decimal(euros, "#,##0", locale=lang) + " €"
    return format_decimal(s, "#,##0.0", locale=lang) + " " + suffix


def share(part: float, total: float, lang: str) -> str:
    return format_percent(part / total if total else 0, "#,##0.0 %", locale=lang)


def integer(n: int, lang: str) -> str:
    return format_decimal(n, "#,##0", locale=lang)
