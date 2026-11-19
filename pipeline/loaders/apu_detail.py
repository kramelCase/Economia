"""Qui paie et qui prête : le détail des prélèvements reçus par les administrations publiques (gov_10a_taxag) et la
dette publique par secteur détenteur (gov_10dd_ggd).

Les postes de prélèvements nommés par payeur sont ceux de NA_ITEM (impôts sur le revenu des ménages / des sociétés,
cotisations à la charge des employeurs / des ménages) ; les détenteurs sont les secteurs de la nomenclature SECTOR.
Rien n'est calculé : les contrôles vérifient que les détenteurs publiés s'additionnent aux totaux publiés, et
comparent la dette ventilée à la dette publiée dans gov_10dd_edpt1.
"""

from __future__ import annotations

import json
from collections import defaultdict

from pipeline.db import Builder, num
from pipeline.loaders.apu import statuts_insee
from pipeline.rawio import iter_records

PRELEVEMENTS = "apu_prelevements"
# Poste publié -> postes détaillés publiés dessous (l'ordre est celui de l'affichage).
DETAIL = {"D2": ("D211", "D214", "D29"), "D5": ("D51A", "D51B"), "D61": ("D611", "D613")}
DETENTEURS = "dette_detenteurs"
# Secteur détenteur -> secteurs publiés dessous : S1_S2 = S1 + S2 ; S1 = ses quatre composantes.
SOUS = {"S1_S2": ("S1", "S2"), "S1": ("S121", "S122_S123", "S124-S129", "S11_S14_S15")}
NATURE = "depenses_nature"
# Natures de dépense publiées par fonction (gov_10a_exp) ; leur somme est le total TE : rémunérations, consommations
# intermédiaires, prestations sociales, subventions, autres transferts courants, transferts en capital, revenus de la
# propriété (intérêts), autres impôts et transferts, investissement (formation de capital et actifs non produits).
NATURES = ("D1", "P2", "D62_D632", "D3", "D7", "D9", "D4", "D29_D5_D8", "OP5ANP")


def libelles(b: Builder, source: str, codes: set[str]) -> dict[str, tuple[str, int]]:
    f = b.fichier(source)
    trouves = {r["col_1"]: (r["col_2"], ligne) for ligne, r in iter_records(f.path, has_header=False) if r["col_1"] in codes}
    if codes - trouves.keys():
        raise ValueError(f"{source} : codes absents de la nomenclature publiée {sorted(codes - trouves.keys())}")
    return trouves


def nomenclature(b: Builder, nid: str, titre: str, src_fr: str, src_en: str, arbre: dict[str, tuple[str, ...]]) -> None:
    codes = set(arbre) | {c for v in arbre.values() for c in v}
    fr, en = libelles(b, src_fr, codes), libelles(b, src_en, codes)
    b.nomenclature(nid, titre, src_fr)
    parents = {c: p for p, v in arbre.items() for c in v}
    ordre = sorted(codes, key=lambda c: (c in parents and parents[c] in parents, c in parents))
    for code in ordre:
        p = parents.get(code)
        b.noeud(nid, code, fr[code][0], b.fichier(src_fr), fr[code][1], parent_code=p,
                niveau=1 + (p is not None) + (p in parents))
        b.con.execute("INSERT INTO noeud_traduction VALUES (?,?,?,?,?,?)",
                      (b.noeud_id(nid, code), "en", en[code][0], "officielle", b.fichier(src_en).id, en[code][1]))


def lire(b: Builder, source: str, cle: str, nid: str, mesure: str, apu: int, statuts: dict[int, str]) -> dict:
    data = b.fichier(source)
    rows, vals = [], defaultdict(dict)
    for ligne, r in iter_records(data.path):
        v = num(r["OBS_VALUE"])
        if v is None or r["sector"] != "S13" or r["unit"] != "MIO_EUR":
            continue
        an = int(r["TIME_PERIOD"])
        st = statuts.get(an)
        attributs = json.dumps({"statut du compte (Insee)": st}, ensure_ascii=False) if st else None
        prov = "p" in (r["OBS_FLAG"] or "") or st in ("compte provisoire", "compte semi-définitif")
        rows.append((apu, b.noeud_id(nid, r[cle]), an, "compte", mesure, "MIO_EUR", v, int(prov), attributs, data.id, ligne))
        vals[an][r[cle]] = v
    b.montants(rows)
    return vals


def bouclage(b: Builder, nom: str, source: str, vals: dict, arbre: dict[str, tuple[str, ...]], tolerance: float) -> None:
    """Somme des postes publiés dessous = poste publié au-dessus (pire écart sur toutes les années)."""
    ecarts = [(abs(sum(d[c] for c in v) - d[p]), a, p) for a, d in vals.items() for p, v in arbre.items()
              if {p, *v} <= d.keys()]
    pire = max(ecarts, default=(0.0, None, None))
    b.controle(nom, source, 0.0, round(pire[0], 3), tolerance,
               f"{len(ecarts)} couples poste-année ; pire écart sur {pire[2]} {pire[1]} (arrondis Eurostat)")


def natures(b: Builder, apu: int, statuts: dict[int, str]) -> None:
    """Comment c'est dépensé : chaque fonction COFOG (nœud GFxx) et ses dépenses par nature (nœuds « GFxx.D1 »...).
    Les libellés sont ceux, publiés, de COFOG99 et de NA_ITEM ; le contrôle vérifie que les natures s'additionnent au
    total publié de chaque fonction."""
    fonctions = [f"GF{i:02d}" for i in range(1, 11)]
    cof = {lg: libelles(b, f"eurostat_cofog_libelles_{lg}", set(fonctions)) for lg in ("fr", "en")}
    nat = {lg: libelles(b, f"eurostat_na_item_{lg}", set(NATURES)) for lg in ("fr", "en")}
    b.nomenclature(NATURE, "Dépenses des administrations publiques par fonction et par nature (COFOG × NA_ITEM)",
                   "eurostat_na_item_fr")
    for f in fonctions:
        for code, parent, lib, src in [(f, None, cof, "eurostat_cofog_libelles"),
                                       *((f"{f}.{n}", f, {lg: {f"{f}.{n}": nat[lg][n]} for lg in nat}, "eurostat_na_item")
                                         for n in NATURES)]:
            fr, en = lib["fr"][code], lib["en"][code]
            b.noeud(NATURE, code, fr[0], b.fichier(f"{src}_fr"), fr[1], parent_code=parent, niveau=1 + (parent is not None))
            b.con.execute("INSERT INTO noeud_traduction VALUES (?,?,?,?,?,?)",
                          (b.noeud_id(NATURE, code), "en", en[0], "officielle", b.fichier(f"{src}_en").id, en[1]))
    data = b.fichier("eurostat_depenses_nature")
    rows, vals = [], defaultdict(dict)
    for ligne, r in iter_records(data.path):
        v = num(r["OBS_VALUE"])
        if v is None or r["sector"] != "S13" or r["unit"] != "MIO_EUR":
            continue
        an, code = int(r["TIME_PERIOD"]), r["cofog99"] if r["na_item"] == "TE" else f'{r["cofog99"]}.{r["na_item"]}'
        st = statuts.get(an)
        attributs = json.dumps({"statut du compte (Insee)": st}, ensure_ascii=False) if st else None
        prov = "p" in (r["OBS_FLAG"] or "") or st in ("compte provisoire", "compte semi-définitif")
        rows.append((apu, b.noeud_id(NATURE, code), an, "compte", "depense", "MIO_EUR", v, int(prov), attributs, data.id, ligne))
        vals[(r["cofog99"], an)][r["na_item"]] = v
    b.montants(rows)
    ecarts = [(abs(sum(d[n] for n in NATURES) - d["TE"]), f, a) for (f, a), d in vals.items() if {"TE", *NATURES} <= d.keys()]
    pire = max(ecarts, default=(0.0, None, None))
    b.controle("Dépenses par nature : somme des neuf natures = total publié de chaque fonction (pire écart)",
               "eurostat_depenses_nature", 0.0, round(pire[0], 3), 0.5,
               f"{len(ecarts)} couples fonction-année ; pire écart sur {pire[1]} {pire[2]} (arrondis Eurostat)")


def load(b: Builder) -> None:
    apu = b.entite("APU-S13", "secteur_apu", "Ensemble des administrations publiques")
    statuts, _ = statuts_insee(b)

    nomenclature(b, PRELEVEMENTS, "Impôts et cotisations reçus par les administrations publiques (NA_ITEM, SEC 2010)",
                 "eurostat_na_item_fr", "eurostat_na_item_en", DETAIL)
    lire(b, "eurostat_prelevements_detail", "na_item", PRELEVEMENTS, "agregat", apu, statuts)
    # Les postes détaillés ne couvrent pas tout leur parent (droits d'importation, gains de détention, cotisations
    # imputées...) : aucun bouclage de somme ici, seulement le rapprochement avec les catégories de gov_10a_main.
    croise = b.con.execute(
        """SELECT p.code, m.exercice, m.valeur, (SELECT m2.valeur FROM montant m2 JOIN noeud n2 ON n2.id = m2.noeud_id
             WHERE n2.nomenclature_id = 'apu_agregats' AND n2.code = p.code || 'REC' AND m2.entite_id = m.entite_id
             AND m2.exercice = m.exercice AND m2.unite = 'MIO_EUR') FROM montant m JOIN noeud p ON p.id = m.noeud_id
           WHERE p.nomenclature_id = ? AND p.code IN ('D2', 'D5', 'D61') AND m.entite_id = ?""", (PRELEVEMENTS, apu)).fetchall()
    ecarts = [(abs(v - w) / w * 100, c, a) for c, a, v, w in croise if w]
    pire = max(ecarts, default=(0.0, None, None))
    b.controle("Prélèvements des APU : postes de gov_10a_taxag = catégories de gov_10a_main (pire écart, en %)",
               "eurostat_prelevements_detail", 0.0, round(pire[0], 2), 5.0,
               f"{len(ecarts)} couples poste-année ; pire écart sur {pire[1]} {pire[2]}")

    natures(b, apu, statuts)

    nomenclature(b, DETENTEURS, "Secteurs détenteurs de la dette publique (SECTOR, SEC 2010)",
                 "eurostat_secteurs_fr", "eurostat_secteurs_en", SOUS)
    vals = lire(b, "eurostat_dette_detenteurs", "sector2", DETENTEURS, "detention", apu, statuts)
    bouclage(b, "Dette par détenteur : somme des secteurs publiés = total publié (pire écart)",
             "eurostat_dette_detenteurs", vals, SOUS, 5.0)
    gd = dict(b.con.execute(
        """SELECT m.exercice, m.valeur FROM montant m JOIN noeud n ON n.id = m.noeud_id WHERE n.nomenclature_id =
           'apu_agregats' AND n.code = 'GD' AND m.entite_id = ? AND m.unite = 'MIO_EUR'""", (apu,)).fetchall())
    ecarts = [(abs(d["S1_S2"] - gd[a]) / gd[a] * 100, a) for a, d in vals.items() if "S1_S2" in d and a in gd]
    pire = max(ecarts, default=(0.0, None))
    b.controle("Dette par détenteur (gov_10dd_ggd) = dette publiée (gov_10dd_edpt1), pire écart en %",
               "eurostat_dette_detenteurs", 0.0, round(pire[0], 2), 2.0, f"{len(ecarts)} années ; pire écart en {pire[1]}")
