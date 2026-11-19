"""Dépenses des administrations publiques par fonction (COFOG), Eurostat d'après l'INSEE."""

from __future__ import annotations

from collections import defaultdict

from pipeline.db import Builder, num
from pipeline.rawio import iter_records

NOMENCLATURE = "cofog"
SECTEURS = {
    "S13": "Ensemble des administrations publiques",
    "S1311": "Administrations publiques centrales",
    "S1313": "Administrations publiques locales",
    "S1314": "Administrations de sécurité sociale",
}


def parent_code(code: str) -> str | None:
    if code == "TOTAL":
        return None
    if len(code) == 4:      # GF09
        return "TOTAL"
    return code[:4]         # GF0901 -> GF09


def load(b: Builder) -> None:
    lib_fr = b.fichier("eurostat_cofog_libelles_fr")
    lib_en = b.fichier("eurostat_cofog_libelles_en")
    b.nomenclature(NOMENCLATURE, "Classification des fonctions des administrations publiques (COFOG 1999)",
                   "eurostat_cofog_libelles_fr")

    # Nœuds : l'ordre du fichier place toujours le parent avant ses enfants (TOTAL, GF01, GF0101...).
    for ligne, r in iter_records(lib_fr.path, has_header=False):
        code, libelle = r["col_1"], r["col_2"]
        b.noeud(NOMENCLATURE, code, libelle, lib_fr, ligne, parent_code(code), 0 if code == "TOTAL" else len(code) // 2 - 1)
    for ligne, r in iter_records(lib_en.path, has_header=False):
        nid = b.noeud_id(NOMENCLATURE, r["col_1"])
        if nid is not None:
            b.con.execute("INSERT INTO noeud_traduction VALUES (?,?,?,?,?,?)",
                          (nid, "en", r["col_2"], "officielle", lib_en.id, ligne))

    apu = b.entite("APU-S13", "secteur_apu", SECTEURS["S13"])
    entites = {"S13": apu}
    for code in ("S1311", "S1313", "S1314"):
        entites[code] = b.entite(f"APU-{code}", "secteur_apu", SECTEURS[code], parent="APU-S13")

    data = b.fichier("eurostat_cofog_fr")
    rows = []
    totals: dict[tuple, dict[str, float]] = defaultdict(dict)
    for ligne, r in iter_records(data.path):
        v = num(r["OBS_VALUE"])
        nid = b.noeud_id(NOMENCLATURE, r["cofog99"])
        if v is None or nid is None:
            continue
        rows.append((entites[r["sector"]], nid, int(r["TIME_PERIOD"]), "compte", "depense", r["unit"], v,
                     int(r["OBS_FLAG"] == "p"), None, data.id, ligne))
        if r["unit"] == "MIO_EUR":
            totals[(r["sector"], r["TIME_PERIOD"])][r["cofog99"]] = v
    b.montants(rows)

    # Bouclage : somme des 10 divisions = TOTAL publié, pour chaque secteur et chaque année.
    worst = max(((abs(sum(v for k, v in d.items() if len(k) == 4) - d["TOTAL"]), key)
                 for key, d in totals.items() if "TOTAL" in d), default=(0.0, None))
    b.controle("COFOG : somme des 10 fonctions = total publié (pire écart, tous secteurs et années)",
               "eurostat_cofog_fr", 0.0, round(worst[0], 3), 0.5,
               f"{len(totals)} couples secteur-année ; pire écart sur {worst[1]} (arrondis Eurostat au 0,1 M€)")
    # Bouclage : somme des sous-fonctions (GFxxyy) = fonction publiée (GFxx) ; l'interface s'appuie dessus.
    ecarts = [(abs(sum(v for k, v in d.items() if len(k) == 6 and k[:4] == div) - d[div]), key, div)
              for key, d in totals.items() for div in d if len(div) == 4 and any(len(k) == 6 and k[:4] == div for k in d)]
    pire = max(ecarts, default=(0.0, None, None))
    b.controle("COFOG : somme des sous-fonctions = fonction publiée (pire écart, tous secteurs et années)",
               "eurostat_cofog_fr", 0.0, round(pire[0], 3), 0.5,
               f"{len(ecarts)} fonctions vérifiées ; pire écart sur {pire[1]} {pire[2]} (arrondis Eurostat au 0,1 M€)")
