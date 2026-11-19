"""Requêtes de l'interface. Règle : on ne somme que des montants d'une même source, le long de sa
propre nomenclature, avec le même stade, la même mesure et la même unité."""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from typing import Any

from pipeline.db import DB_PATH


class PerThread:
    """Une connexion en lecture seule par thread : le serveur répond à plusieurs requêtes à la fois
    (page + suggestions de recherche), et une connexion sqlite3 partagée entre threads se corrompt."""

    def __init__(self) -> None:
        self._local = threading.local()

    def execute(self, sql: str, params: tuple | list = ()) -> sqlite3.Cursor:
        con = getattr(self._local, "con", None)
        if con is None:
            con = self._local.con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
        return con.execute(sql, params)


def connect() -> PerThread:
    return PerThread()


@dataclass(frozen=True)
class Filtre:
    """Ce qui identifie une série de montants additionnables (sert aussi au lien de provenance)."""

    entite: str
    exercice: int
    stade: str
    mesure: str
    unite: str

    def query(self) -> str:
        return (f"entite={self.entite}&exercice={self.exercice}&stade={self.stade}"
                f"&mesure={self.mesure}&unite={self.unite}")


def libelle(con, noeud_id: int, lang: str) -> tuple[str, bool]:
    """(libellé, traduit officiellement ?). Sans traduction officielle : libellé français d'origine."""
    if lang != "fr":
        r = con.execute("SELECT libelle FROM noeud_traduction WHERE noeud_id=? AND langue=?", (noeud_id, lang)).fetchone()
        if r:
            return r["libelle"], True
    return con.execute("SELECT libelle FROM noeud WHERE id=?", (noeud_id,)).fetchone()["libelle"], lang == "fr"


def noeud(con, nomenclature: str, code: str) -> sqlite3.Row:
    return con.execute("SELECT * FROM noeud WHERE nomenclature_id=? AND code=?", (nomenclature, code)).fetchone()


def children(con, parent_id: int) -> list[sqlite3.Row]:
    return con.execute("SELECT * FROM noeud WHERE parent_id=? ORDER BY code", (parent_id,)).fetchall()


SUBTREE = """
WITH RECURSIVE sub(id) AS (SELECT ? UNION ALL SELECT n.id FROM noeud n JOIN sub ON n.parent_id = sub.id)
"""


def total(con, noeud_id: int, f: Filtre, recursive: bool = True) -> tuple[float | None, int, bool]:
    """(somme, nombre de montants, contient du provisoire). None si aucun montant : pas de zéro inventé."""
    nodes = f"{SUBTREE} SELECT id FROM sub" if recursive else "SELECT ?"
    r = con.execute(
        f"""SELECT SUM(valeur) s, COUNT(*) n, MAX(provisoire) p FROM montant m JOIN entite e ON e.id = m.entite_id
            WHERE m.noeud_id IN ({nodes}) AND e.code=? AND exercice=? AND stade=? AND mesure=? AND unite=?""",
        (noeud_id, f.entite, f.exercice, f.stade, f.mesure, f.unite)).fetchone()
    return (r["s"] if r["n"] else None), r["n"], bool(r["p"])


def contributions(con, noeud_id: int, f: Filtre, limit: int = 500) -> list[sqlite3.Row]:
    return con.execute(
        f"""{SUBTREE}
        SELECT m.*, n.libelle, n.code, fi.chemin, fi.url, fi.sha256, fi.collecte, s.titre source_titre, s.editeur,
               s.perimetre, s.id source_id
        FROM montant m JOIN entite e ON e.id = m.entite_id JOIN noeud n ON n.id = m.noeud_id
        JOIN fichier fi ON fi.id = m.fichier_id JOIN source s ON s.id = fi.source_id
        WHERE m.noeud_id IN (SELECT id FROM sub) AND e.code=? AND exercice=? AND stade=? AND mesure=? AND unite=?
        ORDER BY ABS(m.valeur) DESC LIMIT ?""",
        (noeud_id, f.entite, f.exercice, f.stade, f.mesure, f.unite, limit)).fetchall()


def years(con, nomenclature: str, entite: str, stade: str, mesure: str, unite: str) -> list[int]:
    return [r[0] for r in con.execute(
        """SELECT DISTINCT exercice FROM montant m JOIN entite e ON e.id=m.entite_id JOIN noeud n ON n.id=m.noeud_id
           WHERE n.nomenclature_id=? AND e.code=? AND stade=? AND mesure=? AND unite=? ORDER BY exercice""",
        (nomenclature, entite, stade, mesure, unite))]


def entites(con, niveau: str) -> list[sqlite3.Row]:
    return con.execute("SELECT * FROM entite WHERE niveau=? ORDER BY nom", (niveau,)).fetchall()


def entite(con, code: str) -> sqlite3.Row | None:
    return con.execute("SELECT * FROM entite WHERE code=?", (code,)).fetchone()


def montant_detail(con, montant_id: int) -> sqlite3.Row | None:
    return con.execute(
        """SELECT m.*, e.code entite_code, e.nom entite_nom, n.libelle, n.code noeud_code, n.nomenclature_id,
                  fi.chemin, fi.url, fi.sha256, fi.collecte, fi.octets, s.id source_id, s.titre source_titre,
                  s.editeur, s.licence, s.perimetre, s.document_reference
           FROM montant m JOIN entite e ON e.id=m.entite_id JOIN noeud n ON n.id=m.noeud_id
           JOIN fichier fi ON fi.id=m.fichier_id JOIN source s ON s.id=fi.source_id WHERE m.id=?""",
        (montant_id,)).fetchone()


class Plusieurs(LookupError):
    """Le fichier publie plusieurs lignes sous ce code pour cette année (anciennes régions avant 2016, Bas-Rhin et
    Haut-Rhin sous DEP-67A…). Ce site ne choisit pas entre elles et ne les additionne pas : l'appelant doit le dire."""

    def __init__(self, rows: list[sqlite3.Row]):
        super().__init__(f"{len(rows)} lignes publiées")
        self.rows = rows


def lignes(con, noeud_id: int, f: Filtre) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT m.* FROM montant m JOIN entite e ON e.id=m.entite_id
           WHERE m.noeud_id=? AND e.code=? AND exercice=? AND stade=? AND mesure=? AND unite=? ORDER BY m.ligne_source""",
        (noeud_id, f.entite, f.exercice, f.stade, f.mesure, f.unite)).fetchall()


def single(con, noeud_id: int, f: Filtre) -> sqlite3.Row | None:
    """Le montant unique d'un nœud (ex. une fonction COFOG pour un secteur et une année). Lève `Plusieurs` si le
    fichier en publie plusieurs : jamais de choix silencieux."""
    rows = lignes(con, noeud_id, f)
    if len(rows) > 1:
        raise Plusieurs(rows)
    return rows[0] if rows else None


# Catégories publiées par l'OFGL pour des collectivités à statut particulier (colonne categ) ; les régions portent en
# plus le drapeau reg_is_ctu (collectivité territoriale unique). Seuls ces marqueurs publiés sont utilisés.
CATEGORIES_PARTICULIERES = ("ML", "PARIS")


def statuts_ofgl(con, exercice: int) -> dict[str, str]:
    """{code entité: marqueur publié} des collectivités à statut particulier pour un exercice (agrégats OFGL)."""
    out = {}
    for r in con.execute(
            """SELECT DISTINCT e.code, json_extract(m.attributs, '$.categorie') c, json_extract(m.attributs, '$.ctu') ctu
               FROM montant m JOIN entite e ON e.id=m.entite_id JOIN noeud n ON n.id=m.noeud_id
               WHERE n.nomenclature_id='ofgl_agregats' AND m.exercice=? AND m.unite='EUR'""", (exercice,)):
        if r["ctu"] == "Oui":
            out[r["code"]] = "CTU"
        elif r["c"] in CATEGORIES_PARTICULIERES:
            out[r["code"]] = r["c"]
    return out


# Une population publiée qui varie de plus de moitié en un an signale un changement de périmètre (seuil du site :
# la plus forte variation suivante, Mayotte 2018, est de 21 %).
RUPTURE_POPULATION = 0.5


def ruptures_detail(rows: list[Any]) -> list[dict[str, Any]]:
    """Changements de collectivité ou de périmètre sous un même code, lus dans les attributs publiés de chaque ligne :
    le SIREN change (Ville de Paris 2019, collectivité de Corse 2018) ou la population publiée varie de plus de
    moitié (Rhône 2015). Lignes d'une seule série, une par année."""
    out, siren0, pop0 = [], None, None
    for r in rows:
        a = json.loads(r["attributs"]) if r["attributs"] else {}
        siren, pop = a.get("siren"), int(a["population"]) if a.get("population") else None
        if siren and siren0 and siren != siren0:
            out.append({"a": r["exercice"], "motif": "siren"})
        elif pop and pop0 and abs(pop / pop0 - 1) > RUPTURE_POPULATION:
            out.append({"a": r["exercice"], "motif": "population", "avant": pop0, "apres": pop})
        siren0, pop0 = siren or siren0, pop or pop0
    return out


def ruptures(rows: list[Any]) -> list[int]:
    return [x["a"] for x in ruptures_detail(rows)]


def series(con, noeud_id: int, entite_code: str, stade: str, mesure: str, unite: str) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT m.id, exercice, valeur, provisoire FROM montant m JOIN entite e ON e.id=m.entite_id
           WHERE noeud_id=? AND e.code=? AND stade=? AND mesure=? AND unite=? ORDER BY exercice""",
        (noeud_id, entite_code, stade, mesure, unite)).fetchall()


def series_provenance(con, noeud_id: int, entite_code: str, stade: str, mesure: str, unite: str) -> list[sqlite3.Row]:
    """Série annuelle avec, pour chaque valeur, le fichier et la ligne d'où elle vient (exports)."""
    return con.execute(
        """SELECT m.id, m.exercice, m.valeur, m.provisoire, m.ligne_source, m.attributs, fi.chemin, fi.sha256, s.titre source_titre,
                  s.editeur FROM montant m JOIN entite e ON e.id=m.entite_id JOIN fichier fi ON fi.id=m.fichier_id
           JOIN source s ON s.id=fi.source_id
           WHERE m.noeud_id=? AND e.code=? AND m.stade=? AND m.mesure=? AND m.unite=? ORDER BY m.exercice""",
        (noeud_id, entite_code, stade, mesure, unite)).fetchall()


def depenses_fiscales(con, exercice: int) -> list[dict[str, Any]]:
    """Dépenses fiscales regroupées par code (une dépense ventilée sur plusieurs lignes reste une dépense)."""
    rows = con.execute(
        """SELECT m.id, m.valeur, m.attributs, n.libelle, n.id noeud_id FROM montant m JOIN noeud n ON n.id=m.noeud_id
           WHERE n.nomenclature_id='budget_vert_plf2026' AND n.code LIKE 'DF|%' AND m.exercice=? AND m.mesure='cout_estime'""",
        (exercice,)).fetchall()
    by: dict[str, dict[str, Any]] = {}
    for r in rows:
        a = json.loads(r["attributs"] or "{}")
        d = by.setdefault(a["code_depense"], {"code": a["code_depense"], "libelle": r["libelle"], "impot": a.get("impot"),
                                               "valeur": 0.0, "montants": []})
        d["valeur"] += r["valeur"]
        d["montants"].append(r["id"])
    return sorted(by.values(), key=lambda d: -d["valeur"])


def lacunes(con, types: tuple[str, ...] | None = None) -> list[sqlite3.Row]:
    q = """SELECT l.*, s.titre source_titre, n.libelle noeud_libelle FROM lacune l
           LEFT JOIN source s ON s.id=l.source_id LEFT JOIN noeud n ON n.id=l.noeud_id"""
    if types:
        q += f" WHERE l.type IN ({','.join('?' * len(types))})"
    return con.execute(q + " ORDER BY l.fichier_id IS NOT NULL, l.type, l.titre", types or ()).fetchall()


def concepts(con, lang: str) -> list[dict[str, Any]]:
    """Concepts dans la langue demandée, avec repli sur le français (signalé)."""
    out = []
    for c in con.execute("SELECT * FROM concept ORDER BY id"):
        t = con.execute("SELECT * FROM concept_traduction WHERE concept_id=? AND langue=?", (c["id"], lang)).fetchone()
        fr = con.execute("SELECT * FROM concept_traduction WHERE concept_id=? AND langue='fr'", (c["id"],)).fetchone()
        shown = t if t is not None and (t["definition"] or c["statut"] == "a_sourcer") else fr
        out.append({"id": c["id"], "statut": c["statut"], "terme": (t or fr)["terme"], "definition": shown["definition"],
                    "langue_def": shown["langue"], "officielle": shown["statut"] == "officielle",
                    "source_url": shown["source_url"], "source_titre": shown["source_titre"],
                    "releve": shown["releve"], "original_fr": fr["definition"] if shown["langue"] != "fr" else None})
    return sorted(out, key=lambda d: d["terme"].lower())


def aliases(con, lang: str) -> list[tuple[str, str]]:
    return [(r["concept_id"], r["alias"]) for r in con.execute("SELECT * FROM concept_alias WHERE langue=?", (lang,))]


def source(con, source_id: str) -> sqlite3.Row | None:
    return con.execute("SELECT * FROM source WHERE id=?", (source_id,)).fetchone()


def sources(con) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT s.*, COUNT(f.id) nb_fichiers, MAX(f.collecte) collecte FROM source s
           LEFT JOIN fichier f ON f.source_id=s.id GROUP BY s.id ORDER BY s.editeur, s.titre""").fetchall()


def fichiers(con, source_id: str) -> list[sqlite3.Row]:
    return con.execute("SELECT * FROM fichier WHERE source_id=? ORDER BY chemin", (source_id,)).fetchall()


def controles(con) -> list[sqlite3.Row]:
    return con.execute("SELECT * FROM controle ORDER BY id").fetchall()
