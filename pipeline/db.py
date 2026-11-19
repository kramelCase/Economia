"""Accès SQLite pour la construction : schéma, provenance (source/fichier), entités, nœuds."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.catalog import RAW_DIR, ROOT, Source, latest_snapshot, load_sources

DB_PATH = ROOT / "comptes.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


@dataclass
class Fichier:
    id: int
    path: Path
    source: Source


@dataclass
class Builder:
    """Contexte de construction partagé par les loaders."""

    con: sqlite3.Connection
    sources: dict[str, Source] = field(default_factory=dict)
    _fichiers: dict[tuple[str, str], Fichier] = field(default_factory=dict)
    _entites: dict[str, int] = field(default_factory=dict)
    _noeuds: dict[tuple[str, str], int] = field(default_factory=dict)

    @classmethod
    def create(cls, path: Path) -> "Builder":
        if path.exists():
            path.unlink()
        con = connect(path)
        con.executescript(SCHEMA.read_text(encoding="utf-8"))
        b = cls(con=con)
        for s in load_sources():
            b.sources[s.id] = s
            con.execute(
                "INSERT INTO source (id, titre, editeur, licence, perimetre, document_reference, url_portail, page,"
                " dataset) VALUES (?,?,?,?,?,?,?,?,?)",
                (s.id, s.titre, s.editeur, s.licence, s.perimetre, s.document_reference or None,
                 s.portail or s.url or None, s.extra.get("page"), s.dataset or None))
        return b

    # --- provenance ---
    def fichier(self, source_id: str, nom: str = "data.csv") -> Fichier:
        key = (source_id, nom)
        if key in self._fichiers:
            return self._fichiers[key]
        snap = latest_snapshot(source_id)
        if snap is None:
            raise FileNotFoundError(f"aucune collecte pour {source_id} : lancer `make fetch`")
        meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
        info = next((f for f in meta["fichiers"] if f["nom"] == nom), None)
        if info is None and nom == "dataset.json" and (snap / nom).is_file():  # collectes antérieures à son ajout dans meta
            from pipeline.fetch import ods_meta_url
            data = (snap / nom).read_bytes()
            info = {"url": ods_meta_url(self.sources[source_id]), "sha256": hashlib.sha256(data).hexdigest(),
                    "octets": len(data)}
        if info is None:
            raise FileNotFoundError(f"{source_id}/{snap.name} : pas de fichier {nom}")
        cur = self.con.execute(
            "INSERT INTO fichier (source_id, collecte, url, sha256, chemin, octets) VALUES (?,?,?,?,?,?)",
            (source_id, meta["fetched_at"], info["url"], info["sha256"],
             str((snap / nom).relative_to(RAW_DIR.parent)), info["octets"]))
        f = Fichier(cur.lastrowid, snap / nom, self.sources[source_id])
        self._fichiers[key] = f
        return f

    # --- entités ---
    def entite(self, code: str, niveau: str, nom: str, code_insee: str | None = None,
               siren: str | None = None, parent: str | None = None) -> int:
        if code in self._entites:
            return self._entites[code]
        cur = self.con.execute(
            "INSERT INTO entite (code, niveau, nom, code_insee, siren, parent_id) VALUES (?,?,?,?,?,?)",
            (code, niveau, nom, code_insee, siren, self._entites.get(parent) if parent else None))
        self._entites[code] = cur.lastrowid
        return cur.lastrowid

    # --- nomenclatures ---
    def nomenclature(self, nid: str, titre: str, source_id: str) -> None:
        self.con.execute("INSERT INTO nomenclature (id, titre, source_id) VALUES (?,?,?)", (nid, titre, source_id))

    def noeud(self, nomenclature_id: str, code: str, libelle: str, fichier: Fichier, ligne: int,
              parent_code: str | None = None, niveau: int = 1, technique: bool = False) -> int:
        key = (nomenclature_id, code)
        if key in self._noeuds:
            return self._noeuds[key]
        parent_id = self._noeuds[(nomenclature_id, parent_code)] if parent_code is not None else None
        cur = self.con.execute(
            "INSERT INTO noeud (nomenclature_id, code, parent_id, niveau, libelle, technique, fichier_id, ligne_source)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (nomenclature_id, code, parent_id, niveau, libelle, int(technique), fichier.id, ligne))
        self._noeuds[key] = cur.lastrowid
        return cur.lastrowid

    def noeud_id(self, nomenclature_id: str, code: str) -> int | None:
        return self._noeuds.get((nomenclature_id, code))

    # --- faits ---
    def montants(self, rows: list[tuple]) -> None:
        """rows : (entite_id, noeud_id, exercice, stade, mesure, unite, valeur, provisoire, attributs, fichier_id, ligne)."""
        self.con.executemany(
            "INSERT INTO montant (entite_id, noeud_id, exercice, stade, mesure, unite, valeur, provisoire,"
            " attributs, fichier_id, ligne_source) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)

    def lacune(self, type_: str, titre: str, description: str, responsable: str, constat: str, **refs) -> None:
        cols = ["type", "titre", "description", "responsable", "constat", *refs.keys()]
        self.con.execute(f"INSERT INTO lacune ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                         (type_, titre, description, responsable, constat, *refs.values()))

    def controle(self, nom: str, source_id: str, attendu: float, obtenu: float, tolerance: float,
                 detail: str = "") -> bool:
        ok = abs(attendu - obtenu) <= tolerance
        self.con.execute(
            "INSERT INTO controle (nom, source_id, attendu, obtenu, tolerance, ok, detail) VALUES (?,?,?,?,?,?,?)",
            (nom, source_id, attendu, obtenu, tolerance, int(ok), detail))
        return ok


def num(v: str) -> float | None:
    """Valeur numérique ou None (vide, nc, ε...). Ne transforme JAMAIS une absence en 0."""
    s = (v or "").strip()
    if not s:
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def attrs(**kv) -> str | None:
    kv = {k: v for k, v in kv.items() if v not in (None, "")}
    return json.dumps(kv, ensure_ascii=False) if kv else None
