"""Parcours dans un vrai navigateur (Playwright, Chromium) : chaque page s'affiche sans erreur JavaScript et sans
défilement horizontal, à 320 px comme sur desktop. Lancé contre un serveur uvicorn démarré pour l'occasion.

Sauté si Playwright ou son navigateur manquent (`uv run playwright install chromium`).
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.request

import pytest

from pipeline.db import DB_PATH

sync_api = pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.skipif(not DB_PATH.exists(), reason="lancer `make build` d'abord")

PAGES = ["/fr/", "/fr/sources", "/fr/comprendre/1", "/fr/comprendre/4", "/fr/grands-equilibres",
         "/fr/depenses-publiques", "/fr/recettes-publiques", "/fr/budget-etat", "/fr/depenses-fiscales",
         "/fr/territoires", "/fr/territoires/DEP-33", "/fr/territoires/REG-84", "/fr/verifier", "/fr/explorer",
         "/fr/atelier", "/fr/serie", "/fr/comparer", "/fr/contexte", "/fr/donnees", "/fr/methode", "/fr/lacunes",
         "/fr/lexique", "/fr/mentions", "/fr/theme/enseignement", "/fr/theme/protection-sociale", "/fr/theme", "/fr/differences", "/fr/differences?a=m1&b=m2", "/fr/machine", "/fr/montant/1", "/en/", "/en/public-spending",
         "/en/territories/DEP-33", "/en/machine", "/en/topic/enseignement"]
LARGEURS = (320, 1280)


@pytest.fixture(scope="module")
def serveur():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--port", str(port), "--log-level", "warning"])
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(base + "/sante", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    yield base
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="module")
def navigateur():
    with sync_api.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:  # navigateur non installé
            pytest.skip(f"Chromium indisponible : {e}")
        yield b
        b.close()


# Défilement horizontal de la page elle-même ; les tableaux larges défilent dans leur cadre, c'est voulu.
DEBORDE = """() => {
  const w = document.documentElement.clientWidth;
  const fautifs = [...document.querySelectorAll('body *')].filter((el) => {
    if (el.closest('.table-wrap, .mc-defil, pre, [data-defile]')) return false;
    for (let a = el.parentElement; a && a !== document.body; a = a.parentElement)  // dans un cadre qui défile ou coupe
      if (/(auto|scroll|hidden|clip)/.test(getComputedStyle(a).overflowX)) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.right > w + 1 && getComputedStyle(el).position !== 'fixed';
  }).slice(0, 4).map((el) => [el.tagName, el.className && el.className.baseVal === undefined ? el.className : '', el.parentElement.className, Math.round(el.getBoundingClientRect().right)].join('|'));
  return {largeur: document.documentElement.scrollWidth, vue: w, fautifs};
}"""


@pytest.mark.parametrize("largeur", LARGEURS)
@pytest.mark.parametrize("page", PAGES)
def test_page_sans_erreur_ni_debordement(serveur, navigateur, page, largeur):
    ctx = navigateur.new_context(viewport={"width": largeur, "height": 800})
    onglet = ctx.new_page()
    erreurs = []
    onglet.on("pageerror", lambda e: erreurs.append(str(e)))
    onglet.on("console", lambda m: m.type == "error" and erreurs.append(m.text))
    r = onglet.goto(serveur + page, wait_until="networkidle")
    assert r.status == 200
    d = onglet.evaluate(DEBORDE)
    ctx.close()
    assert erreurs == []
    assert d["largeur"] <= d["vue"], f"défilement horizontal à {largeur} px : {d}"
