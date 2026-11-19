"""Données (docs/vision/INTERFACE.md §3.7) : la méthode, ce qui manque, les exports.

La base SQLite reste interne : ni téléchargement ni description publique (décision du user). Importé à la fin de
api/main.py, avant api/portes.py.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response

from api.i18n import translations
from api.main import app, con, render
from pipeline.export_donnees import OUT


@lru_cache(maxsize=1)
def couverture_brute() -> tuple[dict, ...]:
    """Ce que la base contient, source par source : lu dans les montants chargés, jamais écrit à la main."""
    rows = con.execute("""
        SELECT f.source_id AS id, s.titre, s.editeur, s.perimetre, MIN(m.exercice) AS de, MAX(m.exercice) AS a,
               COUNT(*) AS n, GROUP_CONCAT(DISTINCT e.niveau) AS niveaux, GROUP_CONCAT(DISTINCT m.stade) AS stades,
               GROUP_CONCAT(DISTINCT m.unite) AS unites, COUNT(DISTINCT m.noeud_id) AS postes,
               GROUP_CONCAT(DISTINCT n.nomenclature_id) AS nomenclatures, MAX(f.collecte) AS collecte
        FROM montant m JOIN fichier f ON f.id = m.fichier_id JOIN source s ON s.id = f.source_id
             JOIN entite e ON e.id = m.entite_id JOIN noeud n ON n.id = m.noeud_id
        GROUP BY f.source_id ORDER BY s.editeur, s.titre""").fetchall()
    lac = dict(con.execute("SELECT source_id, COUNT(*) FROM lacune WHERE source_id IS NOT NULL GROUP BY 1").fetchall())
    noms = dict(con.execute("SELECT id, titre FROM nomenclature").fetchall())
    return tuple({**dict(r), "lacunes": lac.get(r["id"], 0),
                  "nomenclatures": [noms[x] for x in (r["nomenclatures"] or "").split(",") if x in noms]} for r in rows)


def couverture(lang: str) -> list[dict]:
    _ = translations(lang).gettext
    niveau = {"etat": _("État"), "secteur_apu": _("Administrations publiques et leurs sous-secteurs"),
              "region": _("Régions"), "departement": _("Départements")}
    stade = {"plf": _("projet de loi"), "lfi": _("loi votée"), "execution": _("exécution"), "compte": _("comptes")}
    return [{**r, "niveaux": [niveau.get(x, x) for x in r["niveaux"].split(",")],
             "stades": [stade.get(x, x) for x in r["stades"].split(",")],
             "collecte": r["collecte"][:10]} for r in couverture_brute()]  # horodatage UTC « 2026-10-27T122424Z »


@app.get("/{lang}/donnees", response_class=HTMLResponse)
def donnees(request: Request, lang: str):
    return render(request, lang, "donnees.html", couv=couverture(lang))


# --- Fichiers des widgets (docs/vision/WIDGETS.md §4 bis) ---
# Seuls les fichiers listés dans le manifeste sont servis : le chemin demandé n'est jamais assemblé tel quel. Les noms
# contiennent leur empreinte, donc le cache est permanent ; la version compressée est écrite d'avance.
@lru_cache(maxsize=2)
def fichiers(mtime: float) -> frozenset[str]:
    import json
    m = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    return frozenset(x["fichier"] for d in m["documents"].values()
                     for x in [d["dictionnaire"], *d["parties"].values()])


@app.get("/data/manifest.json")
def manifeste():
    p = OUT / "manifest.json"
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="application/json", headers={"Cache-Control": "no-cache"})


@app.get("/data/{doc}/{nom}")
def fichier_donnees(request: Request, doc: str, nom: str):
    m = OUT / "manifest.json"
    if not m.exists() or f"{doc}/{nom}" not in fichiers(m.stat().st_mtime):
        raise HTTPException(404)
    entetes = {"Cache-Control": "public, max-age=31536000, immutable", "Vary": "Accept-Encoding"}
    if "gzip" in request.headers.get("accept-encoding", ""):
        corps = (OUT / doc / (nom + ".gz")).read_bytes()
        return Response(corps, media_type="application/json", headers={**entetes, "Content-Encoding": "gzip"})
    return FileResponse(OUT / doc / nom, media_type="application/json", headers=entetes)
