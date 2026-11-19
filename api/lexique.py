"""Relie automatiquement chaque terme technique du lexique dans le HTML rendu.

Le passage se fait APRÈS le rendu, sur les nœuds texte : aucun terme ne peut être oublié par un
gabarit. Chaque occurrence devient un lien vers le lexique, porteur d'une infobulle (data-concept).
Exclus : liens existants, titres de page, scripts, styles, champs de formulaire, éléments marqués
`data-nolink` (ex. le contenu des infobulles et les définitions elles-mêmes).
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from html.parser import HTMLParser

SKIP_TAGS = {"a", "script", "style", "title", "head", "textarea", "option", "select", "button", "code", "svg"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
WORD = r"[0-9A-Za-zÀ-ÖØ-öø-ÿ'’]"


@dataclass(frozen=True)
class Alias:
    concept_id: str
    texte: str


def compile_aliases(aliases: list[Alias]) -> tuple[re.Pattern | None, dict[str, str]]:
    """Motif unique, alias les plus longs d'abord. Sigles (tout en majuscules) : sensibles à la casse."""
    if not aliases:
        return None, {}
    lookup: dict[str, str] = {}
    parts = []
    for a in sorted(aliases, key=lambda a: -len(a.texte)):
        acronym = a.texte.isupper()
        key = a.texte if acronym else a.texte.lower()
        if key in lookup:
            continue
        lookup[key] = a.concept_id
        body = re.escape(a.texte)
        parts.append(body if acronym else f"(?i:{body})")
    pattern = re.compile(rf"(?<!{WORD})(?:{'|'.join(parts)})(?!{WORD})")
    return pattern, lookup


class _Linker(HTMLParser):
    def __init__(self, pattern: re.Pattern, lookup: dict[str, str], href: str):
        super().__init__(convert_charrefs=False)
        self.pattern, self.lookup, self.href = pattern, lookup, href
        self.out: list[str] = []
        self.stack: list[tuple[str, bool]] = []  # (tag, bloque le lien)
        self.used: set[str] = set()

    def _blocked(self) -> bool:
        return any(blocks for _, blocks in self.stack)

    def handle_starttag(self, tag, attrs):
        self.out.append(self.get_starttag_text())
        if tag not in VOID_TAGS:
            blocks = tag in SKIP_TAGS or any(k == "data-nolink" for k, _ in attrs)
            self.stack.append((tag, blocks))

    def handle_startendtag(self, tag, attrs):
        self.out.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.out.append(f"</{tag}>")
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._blocked() or not data.strip():
            self.out.append(data)
            return
        self.out.append(self.pattern.sub(self._replace, data))

    def _replace(self, m: re.Match) -> str:
        t = m.group(0)
        cid = self.lookup.get(t) or self.lookup.get(t.lower())
        if cid is None:
            return t
        self.used.add(cid)
        return (f'<a class="terme" href="{self.href}#{cid}" data-concept="{cid}">{t}</a>')

    def handle_entityref(self, name):
        self.out.append(f"&{name};")

    def handle_charref(self, name):
        self.out.append(f"&#{name};")

    def handle_comment(self, data):
        self.out.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.out.append(f"<!{decl}>")


def link_terms(page: str, pattern: re.Pattern | None, lookup: dict[str, str], href: str) -> tuple[str, set[str]]:
    if pattern is None:
        return page, set()
    p = _Linker(pattern, lookup, href)
    p.feed(page)
    p.close()
    return "".join(p.out), p.used


def unlinked_terms(page: str, pattern: re.Pattern | None) -> list[str]:
    """Pour les tests : occurrences de termes du lexique restées en texte brut."""
    if pattern is None:
        return []
    found: list[str] = []

    class _Scan(_Linker):
        def handle_data(self, data):
            if not self._blocked():
                found.extend(m.group(0) for m in self.pattern.finditer(html.unescape(data)))

    s = _Scan(pattern, {}, "")
    s.feed(page)
    return found
