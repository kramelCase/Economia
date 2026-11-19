"""Données des widgets : un fichier statique par document, écrit après la construction de la base.

docs/vision/WIDGETS.md §4 bis : aucune requête libre n'atteint le serveur. Les widgets chargent ces fichiers, que le
navigateur garde en cache (le nom contient l'empreinte), et font tous leurs calculs eux-mêmes.

Format d'une partie (colonnes plutôt que lignes) : {"cols": {"e": [codes entité], "n": [id nœud], "a": [années],
"s": [stades], "m": [mesures], "u": [unités], "v": [valeurs], "id": [id montant], "p": [0/1 provisoire], "f": [indice
de source], "x:<attribut>": [...]}, "sources": [ids]}. Le dictionnaire du document (nœuds, entités) est un fichier à
part, chargé une fois. `data/manifest.json` liste tout.

    uv run python -m pipeline.export_donnees
"""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any

from pipeline.catalog import ROOT
from pipeline.db import DB_PATH

OUT = ROOT / "data"

# (clé, nomenclature, niveau d'entité, empilable, découpe). « Empilable » : les enfants d'un même nœud bouclent sur leur
# parent (contrôle de bouclage en base) ; ailleurs (OFGL, fonctions départementales), les niveaux sont emboîtés sans
# garantie d'additivité, et les widgets n'empilent pas. « Découpe » : un fichier par unité (on compare toutes les
# fonctions d'une même unité) ou par nœud (on compare tous les territoires pour un indicateur) ; None : un seul fichier.
DOCUMENTS = (
    ("cofog", "cofog", "secteur_apu", True, "unite"),
    ("apu", "apu_agregats", "secteur_apu", True, None),
    ("ofgl-region", "ofgl_agregats", "region", False, "noeud_id"),
    ("ofgl-departement", "ofgl_agregats", "departement", False, "noeud_id"),
    ("dep-m52", "fonctions_dep_m52", "departement", False, "noeud_id"),
    ("dep-m57", "fonctions_dep_m57", "departement", False, "noeud_id"),
    ("etat-budget-vert", "budget_vert_plf2026", "etat", False, None),
    ("etat-plf-2025", "lolf_plf2025", "etat", False, None),
)


def ecrire(dossier: Path, nom: str, obj: Any) -> dict[str, Any]:
    """Écrit `nom.<empreinte>.json` et sa version compressée ; renvoie l'entrée du manifeste."""
    brut = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    h = hashlib.sha256(brut).hexdigest()
    fichier = f"{nom}.{h[:12]}.json"
    (dossier / fichier).write_bytes(brut)
    gz = gzip.compress(brut, 9, mtime=0)
    (dossier / (fichier + ".gz")).write_bytes(gz)
    return {"fichier": f"{dossier.name}/{fichier}", "octets": len(brut), "octets_gz": len(gz), "sha256": h}


def colonnes(rows: list[sqlite3.Row], attrs: list[str]) -> dict[str, list[Any]]:
    cols: dict[str, list[Any]] = {k: [] for k in ("e", "n", "a", "s", "m", "u", "v", "id", "p", "f")}
    for a in attrs:
        cols["x:" + a] = []
    for r in rows:
        for k, c in (("e", "e"), ("n", "noeud_id"), ("a", "exercice"), ("s", "stade"), ("m", "mesure"),
                     ("u", "unite"), ("v", "valeur"), ("id", "id"), ("p", "provisoire"), ("f", "source_id")):
            cols[k].append(r[c])
        if attrs:
            x = json.loads(r["attributs"] or "{}")
            for a in attrs:
                cols["x:" + a].append(x.get(a))
    return cols


def sources_index(cols: dict[str, list[Any]]) -> list[str]:
    """Remplace l'identifiant de source de chaque ligne par son indice dans la liste renvoyée."""
    ids = sorted(set(cols["f"]))
    pos = {s: i for i, s in enumerate(ids)}
    cols["f"] = [pos[s] for s in cols["f"]]
    return ids


def exporter(con: sqlite3.Connection, out: Path = OUT) -> dict[str, Any]:
    con.row_factory = sqlite3.Row
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    trad = {(r["noeud_id"]): r for r in con.execute("SELECT * FROM noeud_traduction WHERE langue='en'")}
    manifeste: dict[str, Any] = {"documents": {}}
    for cle, nomenclature, niveau, empilable, decoupe in DOCUMENTS:
        dossier = out / cle
        dossier.mkdir()
        rows = con.execute(
            """SELECT m.*, e.code e, fi.source_id FROM montant m JOIN noeud n ON n.id = m.noeud_id
               JOIN entite e ON e.id = m.entite_id JOIN fichier fi ON fi.id = m.fichier_id
               WHERE n.nomenclature_id = ? AND e.niveau = ? ORDER BY m.noeud_id, e.code, m.exercice, m.unite""",
            (nomenclature, niveau)).fetchall()
        attrs = sorted({k for r in rows if r["attributs"] for k in json.loads(r["attributs"])})
        presents = {r["noeud_id"] for r in rows}
        noeuds = [{"id": n["id"], "code": n["code"], "parent": n["parent_id"], "niveau": n["niveau"],
                   "fr": n["libelle"], "en": trad[n["id"]]["libelle"] if n["id"] in trad else None,
                   "donnees": n["id"] in presents}
                  for n in con.execute("SELECT * FROM noeud WHERE nomenclature_id = ? ORDER BY id", (nomenclature,))]
        entites = [{"code": e["code"], "nom": e["nom"], "insee": e["code_insee"]}
                   for e in con.execute("SELECT * FROM entite WHERE niveau = ? ORDER BY code", (niveau,))]
        titre = con.execute("SELECT titre FROM nomenclature WHERE id = ?", (nomenclature,)).fetchone()["titre"]
        doc: dict[str, Any] = {
            "titre": titre, "nomenclature": nomenclature, "niveau": niveau, "empilable": empilable,
            "unites": sorted({r["unite"] for r in rows}), "stades": sorted({r["stade"] for r in rows}),
            "mesures": sorted({r["mesure"] for r in rows}), "attributs": attrs,
            "annees": [min(r["exercice"] for r in rows), max(r["exercice"] for r in rows)], "lignes": len(rows),
            "dictionnaire": ecrire(dossier, "dictionnaire", {"noeuds": noeuds, "entites": entites}),
        }
        parts: dict[str, list[sqlite3.Row]] = {}
        for r in rows:
            parts.setdefault(str(r[decoupe]) if decoupe else "tout", []).append(r)
        doc["decoupe"] = decoupe
        doc["parties"] = {}
        for nom, rs in parts.items():
            cols = colonnes(rs, attrs)
            srcs = sources_index(cols)
            doc["parties"][nom] = {**ecrire(dossier, nom, {"cols": cols, "sources": srcs}), "lignes": len(rs),
                                   "sources": srcs}
        manifeste["documents"][cle] = doc
    (out / "manifest.json").write_text(json.dumps(manifeste, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return manifeste


def main() -> int:
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    m = exporter(con)
    for cle, d in m["documents"].items():
        octets = sum(p["octets_gz"] for p in d["parties"].values())
        print(f"OK  {cle:18} {d['lignes']:7} lignes  {len(d['parties']):4} fichier(s)  {octets / 1e3:8.0f} ko compressés")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
