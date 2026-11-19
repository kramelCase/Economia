"""Collectivités (OFGL, d'après les balances DGFiP) : agrégats consolidés des régions et départements,
présentation fonctionnelle des départements, et arbre officiel des agrégats."""

from __future__ import annotations

from pipeline.db import Builder, attrs, num
from pipeline.rawio import iter_records

AGREGATS = "ofgl_agregats"
# Agrégats de dépense retenus pour la présentation fonctionnelle (les autres restent dans le brut).
AGREGATS_FONCTIONNELS = ("Dépenses totales hors remb", "Dépenses de fonctionnement", "Dépenses d'investissement hors remb")


def load_agregats_tree(b: Builder) -> None:
    """Arbre des agrégats d'après la colonne `chemin` des définitions officielles OFGL."""
    f = b.fichier("ofgl_definitions_agregats")
    b.nomenclature(AGREGATS, "Agrégats financiers OFGL", "ofgl_definitions_agregats")
    recs = list(iter_records(f.path))
    pending = {r["agregat"]: (ligne, [p.strip() for p in r["chemin"].split(">") if p.strip()]) for ligne, r in recs}
    # Les racines et étapes intermédiaires citées dans un chemin sans ligne propre deviennent des nœuds
    # rattachés à la première ligne qui les cite.
    while pending:
        progressed = False
        for name, (ligne, path) in list(pending.items()):
            parent = path[-1] if path else None
            if parent is not None and b.noeud_id(AGREGATS, parent) is None:
                if parent not in pending:
                    pending[parent] = (ligne, path[:-1])
                continue
            b.noeud(AGREGATS, name, name, f, ligne, parent, len(path))
            del pending[name]
            progressed = True
        if not progressed:
            raise RuntimeError(f"arbre OFGL incohérent : {sorted(pending)[:5]}")


def _agregat_node(b: Builder, f, ligne: int, agregat: str) -> int:
    nid = b.noeud_id(AGREGATS, agregat)
    if nid is None:
        nid = b.noeud(AGREGATS, agregat, agregat, f, ligne, None, 0)
        b.lacune("sans_definition", f"Agrégat OFGL sans définition publiée : {agregat}",
                 f"L'agrégat « {agregat} » figure dans les comptes mais pas dans le jeu officiel des définitions.",
                 b.sources["ofgl_definitions_agregats"].editeur, "Comparaison automatique des jeux OFGL",
                 source_id="ofgl_definitions_agregats",
                 fichier_id=f.id, ligne_source=ligne, noeud_id=nid)
    return nid


def load_consolides(b: Builder, source_id: str, niveau: str) -> None:
    f = b.fichier(source_id)
    rows = []
    for ligne, r in iter_records(f.path):
        if niveau == "region":
            code = f"REG-{r['reg_code']}"
            ent = b.entite(code, "region", r["reg_name"], r["reg_code"], r["siren"])
        else:
            code = f"DEP-{r['dep_code']}"
            ent = b.entite(code, "departement", r["dep_name"], r["dep_code"], r["siren"])
        nid = _agregat_node(b, f, ligne, r["agregat"])
        exercice = int(r["exer"][:4])
        a = attrs(categorie=r["categ"], population=r["ptot"], siren=r["siren"], ctu=r.get("reg_is_ctu"))
        for col, unite in (("montant", "EUR"), ("euros_par_habitant", "EUR_HAB")):
            v = num(r[col])
            if v is not None:
                rows.append((ent, nid, exercice, "compte", "agregat", unite, v, 0, a, f.id, ligne))
    b.montants(rows)


def load_fonctionnelle_departements(b: Builder) -> None:
    """Fonctions M52 (jusqu'en 2023 environ) et M57 : deux nomenclatures distinctes, codes non comparables."""
    f = b.fichier("ofgl_departements_fonctionnelle")
    for nomen in ("M52", "M57"):
        b.nomenclature(f"fonctions_dep_{nomen.lower()}", f"Fonctions des départements (nomenclature {nomen})",
                       "ofgl_departements_fonctionnelle")
    def keep(r: dict) -> bool:
        return r["agregat"] in AGREGATS_FONCTIONNELS and r["type_de_budget"] == "Budget principal"

    # Passe 1 : les fonctions (le fichier ne garantit pas l'ordre parent avant enfant).
    found: dict[tuple[str, str], tuple[int, str, int]] = {}
    for ligne, r in iter_records(f.path):
        if keep(r):
            found.setdefault((f"fonctions_dep_{r['nomen'].lower()}", r["fonction"]),
                             (int(r["niveau_hierarchique"]), r["nom_fonction"], ligne))
    for (nom, code), (niv, libelle, ligne) in sorted(found.items(), key=lambda kv: kv[1][0]):
        parent = code[:-1] if niv > 1 else None
        if parent is not None and (nom, parent) not in found:
            parent = None  # parent absent de la source : rattaché à la racine, sans libellé inventé
        b.noeud(nom, code, libelle, f, ligne, parent, niv)

    # Passe 2 : les montants.
    rows = []
    for ligne, r in iter_records(f.path):
        if not keep(r):
            continue
        nid = b.noeud_id(f"fonctions_dep_{r['nomen'].lower()}", r["fonction"])
        ent = b.entite(f"DEP-{r['dep_code']}", "departement", r["dep_name"], r["dep_code"], r["siren"])
        a = attrs(budget="Budget principal", nomenclature=r["nomen"])
        # La mesure porte le nom de l'agrégat : deux agrégats ne s'additionnent jamais par erreur.
        for col, unite in (("montant", "EUR"), ("euros_par_habitant", "EUR_HAB")):
            v = num(r[col])
            if v is not None:
                rows.append((ent, nid, int(r["exer"][:4]), "compte", r["agregat"], unite, v, 0, a, f.id, ligne))
    b.montants(rows)


def load(b: Builder) -> None:
    load_agregats_tree(b)
    load_consolides(b, "ofgl_regions", "region")
    load_consolides(b, "ofgl_departements", "departement")
    load_fonctionnelle_departements(b)
