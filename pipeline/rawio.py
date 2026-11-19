"""Lecture des fichiers bruts, avec le numéro d'enregistrement de chaque ligne (provenance).

Convention de `ligne_source` : numéro d'enregistrement CSV en partant de 1, l'en-tête compris
(la première ligne de données d'un fichier avec en-tête porte donc le n° 2). C'est le numéro
qu'affiche un tableur à l'ouverture du fichier, sauf si une cellule contient un retour à la ligne.
"""

from __future__ import annotations

import csv
import sys
from collections.abc import Iterator
from pathlib import Path

csv.field_size_limit(sys.maxsize)


def sniff_delimiter(sample: str) -> str:
    first = sample.splitlines()[0] if sample else ""
    return max((";", ",", "\t"), key=first.count)


def iter_records(path: Path, has_header: bool = True) -> Iterator[tuple[int, dict[str, str]]]:
    """Itère (ligne_source, {colonne: valeur}). Sans en-tête : colonnes col_1..col_n."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        delim = sniff_delimiter(f.read(20000))
        f.seek(0)
        reader = csv.reader(f, delimiter=delim)
        if has_header:
            header = next(reader)
            n = 1
        else:
            header = None
            n = 0
        for row in reader:
            n += 1
            if header is None:
                header = [f"col_{i + 1}" for i in range(len(row))]
            yield n, dict(zip(header, row))


def read_header(path: Path, has_header: bool = True) -> tuple[str, list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        sample = f.read(20000)
    delim = sniff_delimiter(sample)
    first = next(csv.reader([sample.splitlines()[0]], delimiter=delim))
    return delim, first if has_header else [f"col_{i + 1}" for i in range(len(first))]
