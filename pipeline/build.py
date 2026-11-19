"""Construit comptes.sqlite depuis les collectes brutes (raw/). Échoue si un contrôle de bouclage échoue.

Usage : python -m pipeline.build
"""

from __future__ import annotations

import sqlite3
import sys
import time

import yaml

from pipeline.catalog import ROOT
from pipeline.db import DB_PATH, Builder
from pipeline.loaders import apu, apu_detail, assemblee, budget_etat, concepts, documents, eurostat, ofgl

LOADERS = (("COFOG (Eurostat)", eurostat.load), ("Comptes des APU", apu.load), ("Payeurs et détenteurs", apu_detail.load),
           ("Budget de l'État", budget_etat.load),
           ("Collectivités (OFGL)", ofgl.load), ("Vie institutionnelle", assemblee.load), ("Lexique", concepts.load),
           ("Documents officiels", documents.load))


def load_lacunes(b: Builder) -> None:
    data = yaml.safe_load((ROOT / "content" / "lacunes.yaml").read_text(encoding="utf-8"))
    for l in data["lacunes"]:
        resp = b.sources[l.get("responsable_source") or l["source_id"]].editeur
        b.lacune(l["type"], l["titre"], l["description"], resp, l["constat"], source_id=l.get("source_id"))


def main() -> int:
    tmp = DB_PATH.with_suffix(".sqlite.tmp")
    b = Builder.create(tmp)
    for name, fn in LOADERS:
        t0 = time.time()
        fn(b)
        print(f"OK  {name:24} {time.time() - t0:6.1f} s")
    load_lacunes(b)
    b.con.commit()

    failed = b.con.execute("SELECT nom, attendu, obtenu, tolerance FROM controle WHERE ok = 0").fetchall()
    counts = {t: b.con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("fichier", "entite", "noeud", "montant", "lacune", "concept", "controle",
                        "organe", "fonction", "scrutin", "loi", "document")}
    print("    " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    b.con.close()
    if failed:
        for r in failed:
            print(f"ÉCHEC contrôle : {r['nom']} (attendu {r['attendu']}, obtenu {r['obtenu']}, tolérance {r['tolerance']})",
                  file=sys.stderr)
        print("Base NON publiée : comptes.sqlite inchangé.", file=sys.stderr)
        return 1
    tmp.replace(DB_PATH)
    print(f"Base écrite : {DB_PATH.name}")
    from pipeline.export_donnees import exporter  # données des widgets, recalculées depuis la base publiée
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as con:
        exporter(con)
    print("Données des widgets écrites : data/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
