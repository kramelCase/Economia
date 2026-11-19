"""Rien d'affiché sans source : chaque graphique, chaque tableau et chaque liste chiffrée porte une mention de source
(`.fig-src`) qui renvoie à la fiche de la source, et cette mention couvre les sources de tous les montants qu'il montre."""

import re
import sqlite3
from html.parser import HTMLParser

import pytest

from pipeline.db import DB_PATH
from tests.test_interface import PAGES

pytestmark = pytest.mark.skipif(not DB_PATH.exists(), reason="lancer `make build` d'abord")

# Éléments qui affichent des données ; une liste ou une carte porte sa mention juste après elle.
CIBLES = {"figure": None, "table": None, "ol": {"rank", "c-lignes"}, "ul": {"ctx-list"}, "div": {"c-cadre"}}
VIDES = {"br", "img", "input", "meta", "link", "hr", "source", "wbr", "col", "area", "base", "embed", "param", "track"}


class Figures(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pile = []        # [tag, classes, cible?, sources de la mention, montants]
        self.fermees = []     # cibles fermées qui attendent encore leur mention
        self.resultats = []   # (description, sources de la mention, montants affichés)

    def handle_starttag(self, tag, attrs):
        if tag in VIDES:
            return
        a = dict(attrs)
        cls = set((a.get("class") or "").split())
        href = a.get("href") or ""
        if "fig-src" in cls:
            for f in self.pile:
                if f[2] and f[3] is None:
                    f[3] = set()
            if self.fermees:  # mention placée juste après une liste ou une carte
                for f in self.fermees:
                    f[3] = set()
                    self.pile.append(["_mention", set(), False, f[3], set()])
                self.fermees = []
                self.pile[-1][0] = tag
                self.pile[-1][1] = cls
                return
        elif self.fermees and tag not in ("p",):
            self._clore_attente()
        m = re.search(r"/montant/(\d+)", href)
        for f in self.pile:
            if m and f[2]:
                f[4].add(int(m.group(1)))
        if a.get("data-source"):
            for f in self.pile:
                if f[3] is not None and ("fig-src" in f[1] or f[0] == "_mention"):
                    f[3].add(a["data-source"])
            for f in self.pile:
                if f[2] and f[3] is not None:
                    f[3].add(a["data-source"])
        want = CIBLES.get(tag, False)
        cible = want is None or (bool(want) and bool(want & cls))
        self.pile.append([tag, cls, cible, None, set()])

    def handle_endtag(self, tag):
        if tag in VIDES:
            return
        while self.pile:
            f = self.pile.pop()
            if f[2]:
                dedans = any(g[2] for g in self.pile)
                desc = f"<{f[0]} class='{' '.join(sorted(f[1]))}'>"
                if f[3] is not None or dedans:
                    self.resultats.append((desc, f[3] or set(), f[4], dedans))
                elif f[0] in ("figure", "table"):
                    self.resultats.append((desc, None, f[4], False))
                else:
                    self.fermees.append(f + [desc])
            if f[0] == tag:
                break

    def _clore_attente(self):
        for f in self.fermees:
            self.resultats.append((f[-1], f[3], f[4], False))
        self.fermees = []

    def close(self):
        super().close()
        self._clore_attente()


def figures(html: str):
    p = Figures()
    p.feed(html)
    p.close()
    return p.resultats


def sources_des(ids):
    if not ids:
        return set()
    con = sqlite3.connect(DB_PATH)
    q = ",".join("?" * len(ids))
    return {r[0] for r in con.execute(
        f"SELECT DISTINCT fi.source_id FROM montant m JOIN fichier fi ON fi.id=m.fichier_id WHERE m.id IN ({q})",
        sorted(ids))}


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api.main import app
    return TestClient(app)


def pages_preuves():
    con = sqlite3.connect(DB_PATH)
    out = [f"source/{r[0]}" for r in con.execute("SELECT id FROM source")]
    for genre, sql in (("organe", "SELECT uid FROM organe WHERE type='GOUVERNEMENT' LIMIT 1"),
                       ("fonction", "SELECT id FROM fonction LIMIT 1"),
                       ("scrutin", "SELECT uid FROM scrutin LIMIT 1"),
                       ("loi", "SELECT dossier_uid FROM loi LIMIT 1")):
        r = con.execute(sql).fetchone()
        if r:
            out.append(f"preuve/{genre}/{r[0]}")
    return out


@pytest.mark.parametrize("lang", ["fr", "en"])
@pytest.mark.parametrize("page", PAGES + (pages_preuves() if DB_PATH.exists() else []))
def test_chaque_figure_porte_sa_source(client, lang, page):
    r = client.get(f"/{lang}/{page}")
    assert r.status_code == 200
    for desc, mention, montants, dedans in figures(r.text):
        if dedans:
            continue  # tableau de données d'un graphique : la mention du graphique le couvre
        assert mention, f"{page} : {desc} sans mention de source"
        manquantes = sources_des(montants) - mention
        assert not manquantes, f"{page} : {desc} montre des montants de {manquantes} sans les citer"


def test_mention_renvoie_a_la_fiche_source(client):
    r = client.get("/fr/depenses-publiques")
    assert re.search(r'class="fig-src">Sources? :\s*<a href="/fr/source/[a-z0-9_]+"', r.text)
    r = client.get("/fr/source/eurostat_cofog_fr")
    assert r.status_code == 200 and "ec.europa.eu" in r.text
