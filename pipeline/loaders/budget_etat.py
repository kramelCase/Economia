"""Budget de l'État : budget vert du PLF 2026 (crédits, dépenses fiscales, taxes affectées)
et dépenses du PLF 2025 selon destination (mission > programme > action > sous-action)."""

from __future__ import annotations

import re

from pipeline.db import Builder, attrs, num
from pipeline.rawio import iter_records

BV = "budget_vert_plf2026"
PLF25 = "lolf_plf2025"
ETAT = "ETAT"

TYPES = {"Crédits budgétaires": "CB", "Dépenses fiscales": "DF", "Taxes affectées plafonnées": "TA"}
# Colonne -> (exercice, stade). Pour les dépenses fiscales, tous les chiffres sont des estimations
# publiées dans le PLF 2026 : stade « plf », mesure « cout_estime ».
BV_COLS = (("execution_2024_cp", 2024, "execution"),
           ("lfi_2025_cp_ou_prevision_2025_si_depense_fiscale", 2025, "lfi"),
           ("plf_2026_cp_ou_prevision_2026_si_depense_fiscale", 2026, "plf"))
DF_MARKER = "depenses_fiscales_e_montant_inferieur_a_0_5_meur_nc_montant_non_calcule_en_prevision_2026"
SHARE_COLS = {2024: "2024_si_different_de_100", 2025: "2025_si_different_de_100", 2026: "2026_si_different_de_100"}
POLICY_CODE = re.compile(r"^\d{3}-\d{2}$|^\d+$")  # action 110-02 ou code de dépense numérique


def is_technique(code: str) -> bool:
    """MP/MT (périmètre/transfert), FDC/ADP (fonds de concours), T2_CAS... : lignes techniques."""
    return not POLICY_CODE.match(code)


def load_budget_vert(b: Builder) -> None:
    f = b.fichier("etat_budget_vert_plf2026")
    b.nomenclature(BV, "Budget de l'État (PLF 2026, budget vert) : type > mission > programme > ligne",
                   "etat_budget_vert_plf2026")
    etat = b.entite(ETAT, "etat", "État")
    rows = []
    for ligne, r in iter_records(f.path):
        t = TYPES[r["type_depense"]]
        b.noeud(BV, t, r["type_depense"], f, ligne, None, 0)
        m = f"{t}|{r['mission']}"
        b.noeud(BV, m, r["mission"], f, ligne, t, 1)
        p = f"{m}|{r['numero_programme'] or '?'}"
        b.noeud(BV, p, r["programme"] or "(programme non renseigné)", f, ligne, m, 2)
        code = r["code_depense"]
        leaf = f"{p}|{code}"
        libelle = r["action_si_credit_budgetaire"] if t == "CB" and r["action_si_credit_budgetaire"] else r["libelle"]
        nid = b.noeud(BV, leaf, libelle, f, ligne, p, 3, technique=is_technique(code))
        a = dict(code_depense=code, impot=r["impot_si_depense_fiscale"], affectataire=r["affectataire_si_taxe_affectee"],
                 cotation=r["cotation_globale"], categorie=r["categorie_generale"])
        for col, exercice, stade in BV_COLS:
            v = num(r[col])
            if v is None:
                continue
            share = num(r[SHARE_COLS[exercice]])
            rows.append((etat, nid, exercice, "plf" if t == "DF" else stade,
                         "cout_estime" if t == "DF" else ("montant" if t == "TA" else "cp"),
                         "EUR", v, 0, attrs(**a, part=share), f.id, ligne))
        marker = r[DF_MARKER].strip()
        if t == "DF" and marker in ("nc", "ε"):
            b.lacune("non_chiffre" if marker == "nc" else "sous_seuil",
                     f"Dépense fiscale {code} {'non chiffrée' if marker == 'nc' else 'inférieure à 0,5 M€'}",
                     f"{r['libelle']} ({r['impot_si_depense_fiscale']}). Marqueur officiel « {marker} » en prévision 2026.",
                     f.source.editeur, "Budget vert PLF 2026, collecte automatique",
                     source_id=f.source.id, fichier_id=f.id, ligne_source=ligne, noeud_id=nid, exercice=2026)
    b.montants(rows)


def load_plf2025(b: Builder) -> None:
    f = b.fichier("etat_plf2025_destination")
    b.nomenclature(PLF25, "Budget de l'État (PLF 2025) : type de budget > mission > programme > action > sous-action",
                   "etat_plf2025_destination")
    etat = b.entite(ETAT, "etat", "État")
    rows = []
    for ligne, r in iter_records(f.path):
        tb = r["typebudget"]
        b.noeud(PLF25, tb, tb, f, ligne, None, 0)
        m = f"{tb}|{r['mission']}"
        b.noeud(PLF25, m, r["libelle_mission"], f, ligne, tb, 1)
        p = f"{m}|{r['programme']}"
        b.noeud(PLF25, p, r["libelle_programme"], f, ligne, m, 2)
        a = f"{p}|{r['action']}"
        b.noeud(PLF25, a, r["libelle_action"], f, ligne, p, 3)
        s = f"{a}|{r['sous_action']}"
        nid = b.noeud(PLF25, s, r["libelle_sous_action"] or r["libelle_action"], f, ligne, a, 4)
        facettes = attrs(ministere=r["libelle_ministere"], titre=r["titre"], categorie=r["categorie"])
        for col, mesure in (("autorisation_engagement", "ae"), ("credit_de_paiement", "cp")):
            v = num(r[col])
            if v is not None:
                rows.append((etat, nid, int(r["exercice"]), "plf", mesure, "EUR", v, 0, facettes, f.id, ligne))
    # Le jeu ne publie aucun total : pas de contrôle de bouclage possible, aucun n'est simulé.
    b.montants(rows)


def load(b: Builder) -> None:
    load_budget_vert(b)
    load_plf2025(b)
