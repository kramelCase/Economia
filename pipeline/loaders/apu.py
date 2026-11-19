"""Comptes des administrations publiques : recettes et leurs catégories, dépenses, solde, intérêts (gov_10a_main) et
dette (gov_10dd_edpt1).

Les postes sont ceux de la nomenclature NA_ITEM d'Eurostat, avec ses libellés officiels en français et en anglais.
Rien n'est calculé : le solde (B9) est le chiffre publié, pas une différence faite ici. Les contrôles vérifient que
le solde publié égale recettes moins dépenses, que les catégories de recettes s'additionnent au total publié, et que les dépenses totales égalent celles de la série par fonction.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict

import pypdf

from pipeline.db import Builder, num
from pipeline.loaders.eurostat import SECTEURS
from pipeline.rawio import iter_records

NOMENCLATURE = "apu_agregats"
POSTES = ("TR", "TE", "B9", "D41PAY", "GD")  # ordre d'affichage : recettes, dépenses, solde, intérêts, dette
# Catégories de recettes : leur somme est le total des recettes (TR) dans la définition d'Eurostat ; le contrôle le vérifie.
RECETTES = ("D2REC", "D5REC", "D61REC", "P11_P12_P131", "D4REC", "D7REC", "D9REC", "D39REC")


# Phrase de la note INSEE qui fixe le calendrier, et titre qui nomme les années de la campagne.
PHRASE_CALENDRIER = re.compile(r"fin mai de l.ann[ée]e n\+1, sont publi[ée]s des comptes annuels complets.*?\(compte d[ée]finitif\)\.",
                               re.S)
ANNEES_CAMPAGNE = re.compile(r"pour les\s+ann[ée]es\s+(\d{4}),\s*(\d{4})\s+et\s+(\d{4})")


def statuts_insee(b: Builder) -> tuple[dict[int, str], str]:
    """{année: statut du compte} pour la dernière campagne, lus dans la note INSEE collectée, et la phrase citée.
    Échoue si la phrase ou les années ne s'y trouvent plus : rien n'est supposé."""
    f = b.fichier("insee_note_revisions", "note.pdf")
    texte = "\n".join(p.extract_text() or "" for p in pypdf.PdfReader(str(f.path)).pages[:2])
    plat = re.sub(r"\s+", " ", texte.replace("’", "'").replace("- ", "-"))
    m, a = PHRASE_CALENDRIER.search(plat), ANNEES_CAMPAGNE.search(plat)
    if not m or not a:
        raise ValueError("note INSEE : phrase du calendrier ou années de la campagne introuvables")
    d, s, p = sorted(int(x) for x in a.groups())
    return {p: "compte provisoire", s: "compte semi-définitif", d: "compte définitif"}, m.group(0)


def load(b: Builder) -> None:
    lib_fr = b.fichier("eurostat_na_item_fr")
    lib_en = b.fichier("eurostat_na_item_en")
    b.nomenclature(NOMENCLATURE, "Postes des comptes nationaux des administrations publiques (NA_ITEM, SEC 2010)",
                   "eurostat_na_item_fr")
    trouves = {}
    for ligne, r in iter_records(lib_fr.path, has_header=False):
        if r["col_1"] in POSTES + RECETTES:
            trouves[r["col_1"]] = (r["col_2"], ligne)
    manquants = set(POSTES + RECETTES) - set(trouves)
    if manquants:
        raise ValueError(f"NA_ITEM : postes absents de la nomenclature publiée {sorted(manquants)}")
    for code in POSTES:
        b.noeud(NOMENCLATURE, code, trouves[code][0], lib_fr, trouves[code][1])
    for code in RECETTES:
        b.noeud(NOMENCLATURE, code, trouves[code][0], lib_fr, trouves[code][1], parent_code="TR", niveau=2)
    for ligne, r in iter_records(lib_en.path, has_header=False):
        if r["col_1"] in POSTES + RECETTES:
            b.con.execute("INSERT INTO noeud_traduction VALUES (?,?,?,?,?,?)",
                          (b.noeud_id(NOMENCLATURE, r["col_1"]), "en", r["col_2"], "officielle", lib_en.id, ligne))

    entites = {"S13": b.entite("APU-S13", "secteur_apu", SECTEURS["S13"])}
    for code in ("S1311", "S1313", "S1314"):
        entites[code] = b.entite(f"APU-{code}", "secteur_apu", SECTEURS[code], parent="APU-S13")

    # Eurostat ne marque pas les années récentes : leur statut vient de la note INSEE de la dernière campagne.
    statuts, phrase = statuts_insee(b)
    vals: dict[tuple, dict[str, float]] = defaultdict(dict)
    for sid in ("eurostat_apu_principaux", "eurostat_dette_maastricht"):
        data = b.fichier(sid)
        rows = []
        for ligne, r in iter_records(data.path):
            v = num(r["OBS_VALUE"])
            if v is None or r["na_item"] not in POSTES + RECETTES:
                continue
            an = int(r["TIME_PERIOD"])
            st = statuts.get(an)
            attributs = json.dumps({"statut du compte (Insee)": st}, ensure_ascii=False) if st else None
            prov = "p" in (r["OBS_FLAG"] or "") or st in ("compte provisoire", "compte semi-définitif")
            rows.append((entites[r["sector"]], b.noeud_id(NOMENCLATURE, r["na_item"]), an, "compte",
                         "agregat", r["unit"], v, int(prov), attributs, data.id, ligne))
            if r["unit"] == "MIO_EUR":
                vals[(r["sector"], int(r["TIME_PERIOD"]))][r["na_item"]] = v
        b.montants(rows)

    # Bouclage : solde publié = recettes − dépenses publiées (même fichier), pour chaque secteur et chaque année.
    ecarts = [(abs(d["TR"] - d["TE"] - d["B9"]), k) for k, d in vals.items() if {"TR", "TE", "B9"} <= d.keys()]
    pire = max(ecarts, default=(0.0, None))
    b.controle("Comptes des APU : solde publié = recettes − dépenses (pire écart, tous secteurs et années)",
               "eurostat_apu_principaux", 0.0, round(pire[0], 3), 0.5,
               f"{len(ecarts)} couples secteur-année ; pire écart sur {pire[1]} (arrondis Eurostat au 0,1 M€)")
    # Bouclage : somme des catégories de recettes publiées = recettes totales publiées.
    ecarts = [(abs(sum(d[c] for c in RECETTES) - d["TR"]), k) for k, d in vals.items() if {"TR", *RECETTES} <= d.keys()]
    incomplets = sum(1 for d in vals.values() if "TR" in d and not set(RECETTES) <= d.keys())
    pire = max(ecarts, default=(0.0, None))
    b.controle("Recettes des APU : somme des catégories publiées = recettes totales publiées (pire écart)",
               "eurostat_apu_principaux", 0.0, round(pire[0], 3), 0.5,
               f"{len(ecarts)} couples secteur-année ; pire écart sur {pire[1]} (arrondis Eurostat au 0,1 M€)"
               + (f" ; {incomplets} couples sans toutes les catégories, non contrôlés" if incomplets else ""))
    # Bouclage entre deux jeux : dépenses totales (gov_10a_main) = total de la série par fonction (gov_10a_exp).
    # Les années encore provisoires dans la série par fonction y sont publiées dans une version antérieure : l'écart
    # est réel, il est dit dans le détail du contrôle au lieu d'être masqué. Le contrôle porte sur les années définitives.
    cofog = {(r["code"], r["exercice"]): (r["valeur"], r["provisoire"]) for r in b.con.execute(
        """SELECT substr(e.code, 5) code, m.exercice, m.valeur, m.provisoire FROM montant m JOIN entite e ON e.id = m.entite_id
           JOIN noeud n ON n.id = m.noeud_id WHERE n.nomenclature_id = 'cofog' AND n.code = 'TOTAL'
           AND m.unite = 'MIO_EUR'""")}
    croises = [(abs(d["TE"] - cofog[k][0]), k, cofog[k][1]) for k, d in vals.items() if "TE" in d and k in cofog]
    pire = max((c for c in croises if not c[2]), default=(0.0, None, 0))
    prov = max((c for c in croises if c[2]), default=None)
    b.controle("Dépenses totales des APU : comptes principaux = total par fonction, années définitives (pire écart)",
               "eurostat_apu_principaux", 0.0, round(pire[0], 3), 5.0,
               f"{sum(1 for c in croises if not c[2])} couples secteur-année définitifs comparés entre gov_10a_main et "
               f"gov_10a_exp ; pire écart sur {pire[1]} (arrondis)"
               + (f". Années provisoires de la série par fonction : jusqu'à {prov[0]:.1f} M€ d'écart ({prov[1][0]} "
                  f"{prov[1][1]}), les deux jeux n'en publiant pas la même version" if prov else ""))
