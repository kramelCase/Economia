"""Catalogue des sources : lit `sources.yaml` et localise les collectes brutes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT / "sources.yaml"
RAW_DIR = ROOT / "raw"
PROFILES_DIR = ROOT / "docs" / "profils"

REQUIRED = ("id", "titre", "editeur", "type", "licence", "perimetre")


@dataclass(frozen=True)
class Source:
    id: str
    titre: str
    editeur: str
    type: str
    licence: str
    perimetre: str
    document_reference: str = ""
    portail: str = ""
    dataset: str = ""
    url: str = ""
    where: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


def load_sources(path: Path = SOURCES_FILE) -> list[Source]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: list[Source] = []
    seen: set[str] = set()
    for entry in data["sources"]:
        missing = [k for k in REQUIRED if not entry.get(k)]
        if missing:
            raise ValueError(f"source {entry.get('id')!r} : champs manquants {missing}")
        if entry["id"] in seen:
            raise ValueError(f"source en double : {entry['id']}")
        seen.add(entry["id"])
        if entry["type"] == "ods" and not (entry.get("portail") and entry.get("dataset")):
            raise ValueError(f"source {entry['id']} : 'portail' et 'dataset' requis pour type ods")
        if entry["type"] == "http_csv" and not entry.get("url"):
            raise ValueError(f"source {entry['id']} : 'url' requis pour type http_csv")
        if entry["type"] == "http_file" and not (entry.get("url") and entry.get("fichier")):
            raise ValueError(f"source {entry['id']} : 'url' et 'fichier' requis pour type http_file")
        known = {f for f in Source.__dataclass_fields__ if f != "extra"}
        out.append(Source(**{k: v for k, v in entry.items() if k in known},
                          extra={k: v for k, v in entry.items() if k not in known}))
    return out


def get_source(source_id: str) -> Source:
    for s in load_sources():
        if s.id == source_id:
            return s
    raise KeyError(source_id)


def latest_snapshot(source_id: str) -> Path | None:
    """Dossier de la collecte la plus récente (raw/<id>/<horodatage>/), ou None."""
    base = RAW_DIR / source_id
    if not base.is_dir():
        return None
    snaps = sorted(p for p in base.iterdir() if (p / "meta.json").is_file())
    return snaps[-1] if snaps else None
