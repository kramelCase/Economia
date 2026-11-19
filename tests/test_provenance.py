"""La base tient sa promesse : chaque montant remonte à une ligne de fichier brut, et la valeur y est."""

import json
import random

import pytest

from pipeline.catalog import ROOT
from pipeline.db import DB_PATH, connect
from pipeline.rawio import iter_records

pytestmark = pytest.mark.skipif(not DB_PATH.exists(), reason="lancer `make build` d'abord")


@pytest.fixture(scope="module")
def con():
    c = connect()
    yield c
    c.close()


def test_aucun_montant_sans_provenance(con):
    n = con.execute("SELECT COUNT(*) FROM montant WHERE fichier_id IS NULL OR ligne_source IS NULL").fetchone()[0]
    assert n == 0


def test_cles_etrangeres_integres(con):
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []


def test_controles_de_bouclage_conformes(con):
    rows = con.execute("SELECT nom, attendu, obtenu FROM controle WHERE ok = 0").fetchall()
    assert [tuple(r) for r in rows] == []


def test_fichiers_existent_et_sha_correspond(con):
    import hashlib
    for f in con.execute("SELECT chemin, sha256 FROM fichier"):
        p = ROOT / f["chemin"]
        assert p.is_file(), f["chemin"]
        h = hashlib.sha256()
        with p.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        assert h.hexdigest() == f["sha256"], f"{f['chemin']} modifié depuis la collecte"


def _cells_as_numbers(rec: dict) -> set[float]:
    out = set()
    for v in rec.values():
        try:
            out.add(round(float(v.replace(",", ".")), 6))
        except ValueError:
            pass
    return out


def test_tirage_de_montants_relus_dans_le_brut(con):
    """20 montants tirés au hasard (graine fixe), par source : la valeur est bien dans la ligne citée."""
    rng = random.Random(42)
    sources = [r[0] for r in con.execute("SELECT DISTINCT fi.source_id FROM montant m JOIN fichier fi ON fi.id=m.fichier_id")]
    for sid in sources:
        ids = [r[0] for r in con.execute(
            "SELECT m.id FROM montant m JOIN fichier fi ON fi.id=m.fichier_id WHERE fi.source_id=?", (sid,))]
        sample = rng.sample(ids, min(20, len(ids)))
        rows = con.execute(f"""SELECT m.valeur, m.ligne_source, fi.chemin FROM montant m JOIN fichier fi ON fi.id=m.fichier_id
                               WHERE m.id IN ({','.join('?' * len(sample))})""", sample).fetchall()
        wanted = {r["ligne_source"]: r for r in rows}
        path = ROOT / rows[0]["chemin"]
        found = {}
        for n, rec in iter_records(path):
            if n in wanted:
                found[n] = rec
            if len(found) == len(wanted):
                break
        for n, r in wanted.items():
            assert n in found, f"{sid} : ligne {n} absente"
            assert round(r["valeur"], 6) in _cells_as_numbers(found[n]), f"{sid} ligne {n} : {r['valeur']} introuvable"


def test_non_chiffre_n_est_jamais_un_zero(con):
    """Chaque dépense fiscale « nc » est une lacune, et aucun montant 2026 n'est inventé pour sa ligne."""
    lac = con.execute("SELECT fichier_id, ligne_source FROM lacune WHERE type='non_chiffre'").fetchall()
    assert len(lac) > 0
    for l in lac:
        n = con.execute("SELECT COUNT(*) FROM montant WHERE fichier_id=? AND ligne_source=? AND exercice=2026",
                        (l["fichier_id"], l["ligne_source"])).fetchone()[0]
        assert n == 0


def test_lacunes_ont_un_responsable(con):
    assert con.execute("SELECT COUNT(*) FROM lacune WHERE trim(responsable) = ''").fetchone()[0] == 0


def test_definitions_ont_une_provenance(con):
    rows = con.execute("""SELECT concept_id, langue FROM concept_traduction WHERE definition IS NOT NULL
                          AND (source_url IS NULL OR (fichier_id IS NULL AND releve IS NULL))""").fetchall()
    assert rows == []


def test_traduction_officielle_a_un_fichier(con):
    n = con.execute("""SELECT COUNT(*) FROM noeud_traduction WHERE statut='officielle'
                       AND (fichier_id IS NULL OR ligne_source IS NULL)""").fetchone()[0]
    assert n == 0


def test_depense_fiscale_ventilee_compte_une_fois_par_part(con):
    """Les lignes ventilées (parts < 1) d'une même dépense fiscale portent des parts qui somment à 1."""
    rows = con.execute("""SELECT m.attributs FROM montant m JOIN noeud n ON n.id=m.noeud_id
                          WHERE n.code LIKE 'DF|%' AND m.exercice=2026""").fetchall()
    parts: dict[str, float] = {}
    for r in rows:
        a = json.loads(r["attributs"])
        if a.get("part") is not None:
            parts[a["code_depense"]] = parts.get(a["code_depense"], 0) + a["part"]
    assert parts, "aucune dépense ventilée trouvée"
    for code, s in parts.items():
        assert abs(s - 1) < 0.011, f"{code} : parts = {s}"


def test_scrutins_et_fonctions_ont_une_provenance(con):
    # Chaque scrutin, organe et fonction remonte à un fichier collecté et à son entrée dans l'archive.
    for t in ("scrutin", "organe", "fonction", "personne"):
        assert con.execute(f"SELECT COUNT(*) FROM {t} WHERE fichier_id IS NULL OR entree = ''").fetchone()[0] == 0
    # Un scrutin retenu porte sur l'ensemble d'un texte budgétaire, et son exercice est celui du titre publié.
    for s in con.execute("SELECT titre, exercice FROM scrutin"):
        assert s["titre"].lower().startswith("l'ensemble du projet de loi") and str(s["exercice"]) in s["titre"]
