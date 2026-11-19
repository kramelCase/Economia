"""La machine : les comptes de l'ensemble des administrations publiques figurés comme un circuit d'eau (prototype).

Inspirée de la machine hydraulique de Phillips (1949) : les recettes entrent par le fond, le besoin de financement
publié arrive à part, par le côté (un financement, pas une recette), les dépenses sortent par fonction (COFOG), et la
dette publiée est un réservoir à part. La section de chaque tuyau est proportionnelle au montant publié ; le niveau du
réservoir de dette aussi. Aucun tuyau ne relie le solde à la dette : les comptes publiés ne relient pas ces deux montants.
Page non reliée au menu tant que le user ne l'a pas validée (static/machine.js).
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse

from api import fiches
from api import queries as q
from api.comprendre import payload
from api.colonnes import ICONES
from api.i18n import money, translations
from api.main import app, con, label, nom_entite, render, sources_de
from pipeline.loaders.apu import RECETTES

ENTITE = "APU-S13"
VISIBLES = 4  # catégories de recettes dessinées seules ; les autres forment un tuyau « autres » (somme calculée)
DECOUVERTE_F = 6  # niveau 1 : les six plus grandes fonctions COFOG ; les autres sont regroupées (calcul du site)
NIVEAUX = ("decouverte", "exploration", "analyse")
# Pictogramme de chaque poste (api/colonnes.py) : il nomme le poste d'un coup d'œil, le libellé publié reste dans la liste.
ICO = {"D61REC": "personnel", "D2REC": "usine", "D5REC": "revenu", "P11_P12_P131": "ventes", "D4REC": "epargne",
       "D7REC": "reseaux", "D9REC": "batiment", "D39REC": "subvention", "AUTRES": "point",
       "GF01": "general", "GF02": "defense", "GF03": "securite", "GF04": "economie", "GF05": "environnement",
       "GF06": "habitat", "GF07": "sante", "GF08": "culture", "GF09": "enseignement", "GF10": "social",
       "AUTRES_FN": "point",
       "B9": "emprunt", "GD": "dette", "TR": "entree", "TE": "sortie"}
ACTEURS = (("S1311", "etat"), ("S1313", "lieu"), ("S1314", "social"))
# Qui paie : postes publiés sous une catégorie de recettes (pipeline/loaders/apu_detail.py ; leur parent dans
# gov_10a_taxag égale la catégorie de gov_10a_main, contrôlé au chargement). Les postes ne couvrent pas tout le parent.
DETAIL = {"D2REC": ("D211", "D214", "D29"), "D5REC": ("D51A", "D51B"), "D61REC": ("D611", "D613")}
# Qui détient la dette (stock en fin d'année, publié depuis 2020), du bas de la tour vers le haut.
DETENTEURS = ("S2", "S121", "S122_S123", "S124-S129", "S11_S14_S15")
ICO.update({"D211": "ventes", "D214": "usine", "D29": "usine", "D51A": "personnel", "D51B": "economie",
            "D611": "economie", "D613": "personnel", "S2": "reseaux", "S121": "balance", "S122_S123": "tresorerie",
            "S124-S129": "couches", "S11_S14_S15": "personnel"})


def courts(lang: str) -> dict[str, str]:
    """Noms courts posés sur le schéma (texte d'interface ; le libellé publié est dans la liste et l'infobulle)."""
    _ = translations(lang).gettext
    return {"D61REC": _("Cotisations sociales"), "D2REC": _("Impôts sur la production"),
            "D5REC": _("Impôts sur le revenu"), "P11_P12_P131": _("Ventes et production"),
            "D4REC": _("Revenus de la propriété"), "D7REC": _("Transferts courants"), "D9REC": _("Transferts en capital"),
            "D39REC": _("Subventions reçues"), "AUTRES": _("Autres recettes"),
            "GF01": _("Services généraux"), "GF02": _("Défense"), "GF03": _("Ordre et sécurité"), "GF04": _("Économie"),
            "GF05": _("Environnement"), "GF06": _("Logement"), "GF07": _("Santé"), "GF08": _("Loisirs et culture"),
            "GF09": _("Enseignement"), "GF10": _("Protection sociale"), "AUTRES_FN": _("Autres fonctions"),
            "D211": _("TVA"), "D214": _("Autres impôts sur les produits"), "D29": _("Autres impôts sur la production"),
            "D51A": _("Ménages"), "D51B": _("Sociétés"), "D611": _("Employeurs"), "D613": _("Ménages"),
            "S2": _("Reste du monde"), "S121": _("Banque centrale"), "S122_S123": _("Banques"),
            "S124-S129": _("Assurances, fonds et autres"), "S11_S14_S15": _("Ménages et entreprises"),
            "S1311": _("Administrations centrales"), "S1313": _("Administrations locales"), "S1314": _("Sécurité sociale"),
            # Natures de dépense (suffixe des nœuds « GFxx.D1 ») : nom court, le libellé publié est dans la fiche.
            "D1": _("Rémunérations"), "P2": _("Consommations intermédiaires"), "D62_D632": _("Prestations sociales"),
            "D3": _("Subventions"), "D7": _("Autres transferts courants"), "D9": _("Transferts en capital"),
            "D4": _("Revenus de la propriété (dont intérêts)"), "D29_D5_D8": _("Impôts et ajustements"),
            "OP5ANP": _("Investissement")}


def point(noeud_id: int, annee: int, mesure: str, lang: str, entite: str = ENTITE) -> dict[str, Any] | None:
    m = q.single(con, noeud_id, q.Filtre(entite, annee, "compte", mesure, "MIO_EUR"))
    return None if m is None else {"v": m["valeur"], "m": m["id"], "prov": bool(m["provisoire"]),
                                   "t": money(m["valeur"], lang, "MIO_EUR")}


@app.get("/{lang}/machine", response_class=HTMLResponse)
def machine(request: Request, lang: str, annee: int | None = None, niveau: str = "decouverte"):
    agr = {c: q.noeud(con, "apu_agregats", c) for c in ("TR", "TE", "B9", "GD", *RECETTES)}
    cofog = q.noeud(con, "cofog", "TOTAL")
    fonctions = q.children(con, cofog["id"])
    annees = sorted(set(q.years(con, "cofog", ENTITE, "compte", "depense", "MIO_EUR"))
                    & {r["exercice"] for r in q.series(con, agr["GD"]["id"], ENTITE, "compte", "agregat", "MIO_EUR")}
                    & {r["exercice"] for r in q.series(con, agr["B9"]["id"], ENTITE, "compte", "agregat", "MIO_EUR")})
    annee = annee if annee in annees else annees[-1]
    niveau = niveau if niveau in NIVEAUX else "decouverte"
    # Les catégories dessinées seules : les plus grandes la dernière année (la couleur et la place suivent la catégorie).
    der = {c: point(agr[c]["id"], annees[-1], "agregat", lang) for c in RECETTES}
    seules = sorted((c for c in RECETTES if der[c]), key=lambda c: -der[c]["v"])[:VISIBLES]
    autres = [c for c in RECETTES if c not in seules]
    det = {c: q.noeud(con, "apu_prelevements", c) for v in DETAIL.values() for c in v}
    hol = {c: q.noeud(con, "dette_detenteurs", c) for c in (*DETENTEURS, "S1_S2")}
    # Sous-fonctions COFOG (GFxxyy) de chaque fonction : leur somme égale la fonction (contrôlé au chargement).
    sousf = {f["code"]: q.children(con, f["id"]) for f in fonctions}
    # Natures de dépense de chaque fonction (nœuds « GFxx.D1 »...) : leur somme égale la fonction (contrôlé au chargement).
    natures = {f["code"]: q.children(con, q.noeud(con, "depenses_nature", f["code"])["id"]) for f in fonctions}
    noms = ({c: label(agr[c]["id"], lang) for c in agr} | {f["code"]: label(f["id"], lang) for f in fonctions}
            | {c: label(n["id"], lang) for c, n in (det | hol).items()}
            | {s["code"]: label(s["id"], lang) for v in (*sousf.values(), *natures.values()) for s in v})

    ans: dict[int, Any] = {}
    ids: list[int] = []

    def comptes(a: int, ent: str) -> dict[str, Any]:
        """Les comptes publiés d'un secteur une année : entrées par catégorie (+ « autres », somme calculée), sorties par
        fonction, recettes, dépenses, solde et dette."""
        p = {c: point(agr[c]["id"], a, "agregat", lang, ent) for c in agr}
        reste = [p[c] for c in autres if p[c]]
        somme = sum(x["v"] for x in reste)
        entrees = [{"k": c, **p[c]} for c in seules if p[c]] + [{
            "k": "AUTRES", "v": somme, "m": None, "ids": [x["m"] for x in reste], "prov": any(x["prov"] for x in reste),
            "t": money(somme, lang, "MIO_EUR")}]
        sorties = [{"k": f["code"], **x} for f in fonctions if (x := point(f["id"], a, "depense", lang, ent))]
        ids.extend(x["m"] for x in [*entrees, *sorties, p["TR"], p["TE"], p["B9"], p["GD"]] if x and x.get("m"))
        ids.extend(i for x in entrees for i in x.get("ids", []))
        return {"entrees": entrees, "sorties": sorties, "TR": p["TR"], "TE": p["TE"], "B9": p["B9"], "GD": p["GD"]}

    def postes(a: int, noeuds: dict, codes, mesure: str) -> list[dict[str, Any]]:
        r = [{"k": c, **x} for c in codes if (x := point(noeuds[c]["id"], a, mesure, lang))]
        ids.extend(x["m"] for x in r)
        return r

    for a in annees:
        ans[a] = comptes(a, ENTITE) | {"secteurs": {s: comptes(a, f"APU-{s}") for s, _ in ACTEURS}}
        ans[a]["detail"] = {k: postes(a, det, v, "agregat") for k, v in DETAIL.items()}
        ans[a]["detenteurs"] = postes(a, hol, DETENTEURS, "detention")
        ans[a]["sousf"] = {k: postes(a, {s["code"]: s for s in v}, [s["code"] for s in v], "depense") for k, v in sousf.items()}
        ans[a]["natures"] = {k: postes(a, {s["code"]: s for s in v}, [s["code"] for s in v], "depense") for k, v in natures.items()}

    textes = {k: v["texte"] for k, v in noms.items()}
    acteurs = [{"code": s, "nom": nom_entite(q.entite(con, f"APU-{s}")["nom"], lang), "ico": i} for s, i in ACTEURS]
    return render(request, lang, "machine.html", annees=annees, annee=annee, niveau=niveau, a=ans[annee], noms=noms, ico=ICO,
                  autres=[noms[c] for c in autres], sources=sources_de(ids), acteurs=acteurs,
                  data=payload({"annees": annees, "annee": annee, "decF": DECOUVERTE_F, "ans": ans, "noms": textes,
                                "courts": courts(lang),
                                "fiches": {f["code"]: k for f in fonctions if (k := fiches.fiche_cofog(f["code"]))},
                                "ico": ICO, "svg": {i: ICONES[i] for i in {*ICO.values(), *(i for _, i in ACTEURS)}},
                                "acteurs": acteurs}))
