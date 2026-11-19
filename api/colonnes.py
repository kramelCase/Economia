"""Menu « Colonnes » du tableau de travail (collectivités) : les agrégats OFGL rangés en familles, chacune un onglet,
en arbre dépliable (premier niveau d'abord), et les fonctions des départements par nomenclature, la plus publiée
l'année choisie en premier. Chaque rubrique porte une icône, choisie d'après son libellé publié.
"""

from __future__ import annotations

import re
from typing import Any

from markupsafe import Markup

from api.main import con

# Pictogrammes 24 × 24 en trait (currentColor) : ils suivent le thème clair ou sombre.
ICONES = {
    "depenses": '<path d="M4 12h12m-4-4 4 4-4 4"/><path d="M20 5v14"/>',
    "recettes": '<path d="M20 12H8m4-4-4 4 4 4"/><path d="M4 5v14"/>',
    "dette": '<rect x="4" y="5" width="16" height="4" rx="1"/><rect x="4" y="10" width="16" height="4" rx="1"/><rect x="4" y="15" width="16" height="4" rx="1"/>',
    # Emprunt net de l'année : la pile de la dette, avec une couche qui arrive (même famille, pas le même objet).
    "emprunt": '<rect x="4" y="11" width="16" height="4" rx="1"/><rect x="4" y="16" width="16" height="4" rx="1"/><path d="M12 2.5v6M9 5.5l3 3 3-3"/>',
    "fonctions": '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/>',
    "personnel": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c1-4 4-6 7-6s6 2 7 6"/>',
    "fonctionnement": '<circle cx="12" cy="12" r="3"/><path d="M12 3v3m0 12v3M3 12h3m12 0h3M5.6 5.6l2.1 2.1m8.6 8.6 2.1 2.1M5.6 18.4l2.1-2.1m8.6-8.6 2.1-2.1"/>',
    "batiment": '<path d="M4 20h16M6 20V9l6-4 6 4v11"/><path d="M10 20v-5h4v5"/>',
    "social": '<path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/>',
    "subvention": '<circle cx="12" cy="12" r="7"/><path d="M14.5 9.5a3 3 0 1 0 0 5M8.5 11h5m-5 2h5"/>',
    "impots": '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
    "etat": '<path d="M3 9 12 4l9 5"/><path d="M5 10v8m4-8v8m6-8v8m4-8v8M3 20h18"/>',
    "epargne": '<rect x="4" y="8" width="16" height="12" rx="3"/><path d="M10 8V5h4v3M9 14h6"/>',
    "tresorerie": '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M16 12h5M3 10h18"/>',
    "transport": '<rect x="4" y="5" width="16" height="11" rx="2"/><path d="M4 11h16"/><circle cx="8" cy="18.5" r="1.5"/><circle cx="16" cy="18.5" r="1.5"/>',
    "securite": '<path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6z"/>',
    "enseignement": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c2 2 10 2 12 0v-5"/>',
    "culture": '<path d="m12 3 2.6 5.6 6 .7-4.5 4.1 1.2 6-5.3-3-5.3 3 1.2-6L3.4 9.3l6-.7z"/>',
    "habitat": '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/>',
    "environnement": '<path d="M5 19c0-8 5-13 14-14-1 9-6 14-14 14z"/><path d="M5 19 13 11"/>',
    "economie": '<path d="M4 18l5-5 4 3 7-8"/><path d="M15 8h5v5"/>',
    "general": '<rect x="4" y="7" width="16" height="12" rx="2"/><path d="M9 7V5h6v2M4 12h16"/>',
    "reseaux": '<circle cx="5" cy="12" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><path d="M7 11l10-4M7 13l10 4"/>',
    "ventes": '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.5"/>',
    "point": '<circle cx="12" cy="12" r="3"/>',
    "graphique": '<path d="M4 20V4M4 20h16"/><path d="M8 16v-4m4 4V8m4 8v-6"/>',
    "liste": '<path d="M9 6h11M9 12h11M9 18h11"/><path d="M4.5 6h.01M4.5 12h.01M4.5 18h.01"/>',
    "tableau": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/>',
    "entree": '<path d="M17 7 7 17M7 9v8h8"/>',
    "sortie": '<path d="M7 17 17 7M9 7h8v8"/>',
    "balance": '<path d="M12 4v16M8 20h8M5 7h14"/><path d="m5 7-3 6a3 3 0 0 0 6 0zm14 0-3 6a3 3 0 0 0 6 0z"/>',
    "couches": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>',
    "lieu": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "livre": '<path d="M12 6c-2-1.5-5-2-8-2v14c3 0 6 .5 8 2 2-1.5 5-2 8-2V4c-3 0-6 .5-8 2zm0 0v14"/>',
    "loupe": '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
    "fichiers": '<path d="M8 3h7l4 4v11a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M15 3v4h4M4 7v13a1 1 0 0 0 1 1h10"/>',
    "manque": '<circle cx="12" cy="12" r="8" stroke-dasharray="3.2 3"/><path d="M12 8v5M12 16v.5"/>',
    "calendrier": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4m8-4v4"/>',
    "usine": '<path d="M3 20V10l5 3V10l5 3V6h3l1 6h4v8z"/><path d="M7 17h2m4 0h2"/>',
    "revenu": '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18"/><circle cx="16" cy="14.5" r="1.5"/>',
    "defense": '<path d="M5 21V4"/><path d="M5 4h11l-2 4 2 4H5"/>',
    "sante": '<rect x="4" y="4" width="16" height="16" rx="4"/><path d="M12 8v8M8 12h8"/>',
}
# Le premier motif qui correspond au libellé publié choisit l'icône (ordre du plus précis au plus général).
REGLES = (
    (r"personnel", "personnel"), (r"vacataire|titulaire", "personnel"),
    (r"impôt|taxe|tic?pe|tsca|fiscal|dmto", "impots"),
    (r"concours de l.etat|dotation|dges|dres|ddec|fctva|fmdi", "etat"),
    (r"culture|sport|loisir", "culture"), (r"^recettes", "recettes"),
    (r"subvention|participation|cnsa", "subvention"),
    (r"(rsa|apa|pch)|social|hébergement|médico", "social"), (r"santé", "social"),
    (r"sdis|sécurité", "securite"),
    (r"transport|véhicule|réseaux et infra", "transport"),
    (r"enseignement", "enseignement"),
    (r"habitat|aménagement des territoires", "habitat"), (r"environnement", "environnement"),
    (r"économique", "economie"), (r"services généraux", "general"), (r"réseaux", "reseaux"),
    (r"ventes", "ventes"), (r"épargne|epargne", "epargne"),
    (r"dette|emprunt|annuité|remboursement|charges financières|flux net", "dette"),
    (r"trésor|roulement|trésorerie|dépôts", "tresorerie"),
    (r"équipement|investissement|construction|travaux|immobilisation", "batiment"),
    (r"fonctionnement|achats|charges", "fonctionnement"),
    (r"intervention|allocation", "social"),
    (r"^recettes", "recettes"), (r"^dépenses", "depenses"),
)


def icone(nom: str, taille: int = 18) -> Markup:
    return Markup(f'<svg class="k-ico" viewBox="0 0 24 24" width="{taille}" height="{taille}" aria-hidden="true" fill="none" '
                  f'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONES[nom]}</svg>')


def icone_de(libelle: str) -> str:
    t = libelle.casefold()
    return next((i for motif, i in REGLES if re.search(motif, t)), "point")


def arbre(cols: list[dict[str, Any]], coches: set[str]) -> list[dict[str, Any]]:
    """Colonnes à plat (ordre de l'arbre, avec leur profondeur) → nœuds imbriqués. Au départ, seul le premier
    niveau sous la racine de chaque famille est visible, plus ce qui mène à une colonne cochée ; le reste se déplie."""
    racines: list[dict[str, Any]] = []
    pile: list[dict[str, Any]] = []
    for c in cols:
        n = {"c": c, "enfants": [], "ico": icone_de(c.get("fr") or c["key"])}
        while pile and pile[-1]["c"]["niv"] >= c["niv"]:
            pile.pop()
        (pile[-1]["enfants"] if pile else racines).append(n)
        pile.append(n)

    def marquer(n: dict[str, Any], d: int) -> bool:
        sous = [marquer(x, d + 1) for x in n["enfants"]]
        n["ouvert"] = bool(n["enfants"]) and (d == 0 or any(sous))
        n["n_sous"] = sum(1 + x["n_sous"] for x in n["enfants"])
        return n["c"]["key"] in coches or any(sous)

    for r in racines:
        marquer(r, 0)
    return racines


def publient(nomen: str, annee: int) -> int:
    """Nombre de départements qui publient leurs comptes par fonction dans cette nomenclature cette année-là."""
    return con.execute("""SELECT COUNT(DISTINCT m.entite_id) FROM montant m JOIN noeud n ON n.id=m.noeud_id
                          WHERE n.nomenclature_id=? AND m.exercice=?""", (nomen, annee)).fetchone()[0]


def panneaux(possibles: list[dict[str, Any]], coches: set[str], annee: int, _: Any) -> list[dict[str, Any]]:
    """Un onglet par famille : dépenses, recettes, dette et épargne, puis les fonctions (départements)."""
    titres = {"depenses": _("Dépenses"), "recettes": _("Recettes"), "dette": _("Dette et épargne"), "fonctions": _("Par fonction")}
    out = []
    for fam in ("depenses", "recettes", "dette"):
        cols = [c for c in possibles if c["gk"] == fam]
        if cols:
            out.append({"cle": fam, "titre": titres[fam], "ico": fam, "racines": arbre(cols, coches),
                        "n": sum(c["key"] in coches for c in cols)})
    fonctions = [c for c in possibles if c["gk"] == "fonctions"]
    if fonctions:
        nomens = []
        for nomen, table in (("f57", "fonctions_dep_m57"), ("f52", "fonctions_dep_m52")):
            cols = [c for c in fonctions if c["nomen"] == nomen]
            if cols:
                nomens.append({"nomen": nomen.upper().replace("F", "M"), "n_dep": publient(table, annee),
                               "racines": arbre(cols, coches), "coche": any(c["key"] in coches for c in cols)})
        nomens.sort(key=lambda x: -x["n_dep"])  # la nomenclature la plus publiée l'année choisie en premier
        out.append({"cle": "fonctions", "titre": titres["fonctions"], "ico": "fonctions", "nomens": nomens,
                    "n": sum(c["key"] in coches for c in fonctions)})
    return out
