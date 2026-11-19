"""Documents cités : chaque source renvoie à un document précis (titre officiel, identifiant, adresse qui n'est pas la
racine d'un site), relevé dans un fichier collecté ; chaque loi citée porte son numéro, son JO et son NOR."""

import html
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import pytest

from pipeline.catalog import ROOT
from pipeline.db import DB_PATH

pytestmark = pytest.mark.skipif(not DB_PATH.exists(), reason="lancer `make build` d'abord")


@pytest.fixture(scope="module")
def con():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api.main import app
    return TestClient(app)


def plat(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def test_chaque_source_a_son_document_precis(con):
    for s in con.execute("SELECT id FROM source"):
        d = con.execute("SELECT * FROM document WHERE source_id=? AND role='jeu'", (s["id"],)).fetchone()
        assert d, f"{s['id']} : aucun document officiel relevé"
        assert d["titre"] and d["identifiant"], s["id"]
        assert urlparse(d["url"]).path.strip("/"), f"{s['id']} : l'adresse citée est la racine d'un site ({d['url']})"


def test_chaque_source_a_sa_licence_publiee(con):
    """Licence relevée dans ce que publie l'éditeur, ou lacune déclarée : jamais une licence supposée."""
    for s in con.execute("SELECT id FROM source"):
        l = con.execute("SELECT * FROM document WHERE source_id=? AND role='licence'", (s["id"],)).fetchone()
        lacune = con.execute("SELECT 1 FROM lacune WHERE source_id=? AND titre LIKE 'Licence non publiée%'",
                             (s["id"],)).fetchone()
        assert (l and l["titre"] and urlparse(l["url"]).path.strip("/")) or lacune, f"{s['id']} : licence non relevée"


def test_document_releve_dans_son_fichier(con):
    """Le titre cité se retrouve tel quel dans le fichier collecté où il a été relevé."""
    for d in con.execute("SELECT d.*, fi.chemin FROM document d JOIN fichier fi ON fi.id=d.fichier_id"):
        p = Path(ROOT / d["chemin"])
        assert p.is_file(), d["chemin"]
        if p.stat().st_size > 40_000_000:
            continue
        contenu = plat(p.read_text(encoding="utf-8", errors="replace"))
        assert plat(d["titre"]) in contenu or d["titre"] in d["url"], (d["source_id"], d["titre"])


def test_pages_officielles_prouvees(con):
    """Les contrôles de lien (page officielle qui cite le fichier ou le code, éditeur conforme) passent tous."""
    rows = con.execute("SELECT nom, ok FROM controle WHERE nom LIKE 'Page officielle%' OR nom LIKE 'Éditeur%'"
                       " OR nom LIKE 'Fiche de métadonnées%'").fetchall()
    assert len(rows) >= 20 and all(r["ok"] for r in rows), [r["nom"] for r in rows if not r["ok"]]


def test_producteur_de_lacune_est_un_editeur_publie(con):
    editeurs = {r[0] for r in con.execute("SELECT editeur FROM source")}
    for r in con.execute("SELECT DISTINCT responsable FROM lacune"):
        assert r[0] in editeurs, r[0]


def test_rien_de_saisi_a_la_main_n_est_affiche():
    for p in (ROOT / "templates").glob("*.html"):
        t = p.read_text(encoding="utf-8")
        assert "perimetre }}" not in t and "document_reference" not in t and ".licence }}" not in t, p.name


def test_lois_citees_completement(con):
    lois = con.execute("SELECT * FROM loi WHERE code_loi IS NOT NULL").fetchall()
    assert len(lois) >= 30
    for l in lois:
        assert re.fullmatch(r"\d{4}-\d+", l["code_loi"]) and l["nor"] and l["num_jo"] and l["date_jo"], dict(l)


def test_vote_cite_sa_loi(client, con):
    r = client.get("/fr/contexte?de=2018&a=2019")
    assert "Loi n° 2018-1317 de finances pour 2019" in r.text and "CPAX1823550L" in r.text
    uid = con.execute("SELECT dossier_uid FROM loi WHERE code_loi='2018-1317'").fetchone()[0]
    p = client.get(f"/fr/preuve/loi/{uid}")
    assert p.status_code == 200 and '"codeLoi": "2018-1317"' in html.unescape(p.text)


def test_mention_cite_identifiant_et_date(client):
    r = client.get("/fr/depenses-publiques")
    assert re.search(r'class="fig-src">Sources? :.*?<code>gov_10a_exp</code>, mise à jour du \d{4}-\d{2}-\d{2}', r.text, re.S)


def test_lien_de_scrutin_seulement_si_page_collectee(client, con):
    prouves = {r[0] for r in con.execute("SELECT page_url FROM scrutin WHERE page_url IS NOT NULL")}
    r = client.get("/fr/contexte?de=2013&a=2026")
    liens = set(re.findall(r'href="(https://www\.assemblee-nationale\.fr/dyn/[^"]+)"', r.text))
    assert liens and liens <= prouves, liens - prouves
