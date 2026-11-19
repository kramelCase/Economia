"""Profilage automatique des collectes brutes -> docs/profils/<source>.md.

But : décrire ce que les données contiennent VRAIMENT (colonnes, types, valeurs, marqueurs de
données manquantes) avant de concevoir le moindre schéma.

Usage : python -m pipeline.profile [id_source ...]
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from pipeline.catalog import PROFILES_DIR, load_sources, latest_snapshot
from pipeline.rawio import iter_records, read_header

# Marqueurs officiels ou usuels de « donnée absente » : on les compte, on ne les remplace jamais.
MISSING_MARKERS = {"", "nc", "n.c.", "nd", "n.d.", "ε", "-", "na", "n/a", "#n/a"}
NUM_RE = re.compile(r"^-?\d+([.,]\d+)?([eE][-+]?\d+)?$")
TOP_N = 12
MAX_DISTINCT_TRACKED = 5000


def _new_col(name: str) -> dict:
    return {"name": name, "n": 0, "missing": Counter(), "num": 0, "values": Counter(),
            "overflow": False, "min": None, "max": None}


def _observe(c: dict, v: str) -> None:
    c["n"] += 1
    s = v.strip()
    if s.lower() in MISSING_MARKERS:
        c["missing"][s or "(vide)"] += 1
        return
    if NUM_RE.match(s):
        c["num"] += 1
        x = float(s.replace(",", "."))
        c["min"] = x if c["min"] is None else min(c["min"], x)
        c["max"] = x if c["max"] is None else max(c["max"], x)
    if not c["overflow"]:
        c["values"][s] += 1
        c["overflow"] = len(c["values"]) > MAX_DISTINCT_TRACKED


def profile_file(path: Path, has_header: bool = True) -> dict:
    delim, header = read_header(path, has_header)
    cols = {h: _new_col(h) for h in header}
    rows = bad_width = 0
    for _, rec in iter_records(path, has_header):
        rows += 1
        if len(rec) != len(header):
            bad_width += 1
        for name, v in rec.items():
            if name in cols:
                _observe(cols[name], v)
    return {"delimiter": delim, "rows": rows, "bad_width": bad_width, "columns": list(cols.values())}


def col_kind(c: dict) -> str:
    filled = c["n"] - sum(c["missing"].values())
    if filled == 0:
        return "vide"
    if c["num"] == filled:
        return "numérique"
    if c["num"] > 0.8 * filled:
        return "numérique (mixte)"
    return "texte"


def render(src, snap: Path, prof: dict) -> str:
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    fic = next(f for f in meta["fichiers"] if f["nom"] == "data.csv")
    out = [f"# Profil : {src.titre}", "",
           f"- **id** : `{src.id}`",
           f"- **éditeur** : {src.editeur}",
           f"- **périmètre** : {src.perimetre}",
           f"- **collecte** : `{snap.name}`, sha256 `{fic['sha256'][:16]}…`, {fic['octets'] / 1e6:.1f} Mo",
           f"- **URL** : {fic['url']}",
           f"- **lignes** : {prof['rows']} (largeur incohérente : {prof['bad_width']})",
           f"- **séparateur** : `{prof['delimiter']}`", "",
           "| colonne | type | remplies | manquantes (marqueurs) | distinctes | min / max | valeurs fréquentes |",
           "|---|---|---|---|---|---|---|"]
    for c in prof["columns"]:
        miss = sum(c["missing"].values())
        markers = ", ".join(f"`{k}`×{v}" for k, v in c["missing"].most_common(4))
        distinct = f">{MAX_DISTINCT_TRACKED}" if c["overflow"] else str(len(c["values"]))
        rng = f"{c['min']:g} / {c['max']:g}" if c["min"] is not None else ""
        kind = col_kind(c)
        top = "" if kind == "numérique" else ", ".join(
            f"`{k[:40]}`×{v}" for k, v in c["values"].most_common(TOP_N if len(c["values"]) <= 60 else 5))
        out.append(f"| `{c['name']}` | {kind} | {c['n'] - miss} | {miss} {markers} | {distinct} | {rng} | {top} |")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    for src in load_sources():
        if argv and src.id not in argv:
            continue
        snap = latest_snapshot(src.id)
        if snap is None:
            print(f"--  {src.id:34} pas de collecte (lancer make fetch)")
            continue
        if not (snap / "data.csv").is_file():
            continue  # source non tabulaire (pages de définitions)
        prof = profile_file(snap / "data.csv", has_header=src.extra.get("entete", True))
        (PROFILES_DIR / f"{src.id}.md").write_text(render(src, snap, prof), encoding="utf-8")
        print(f"OK  {src.id:34} {prof['rows']:>8} lignes, {len(prof['columns'])} colonnes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
