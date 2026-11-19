"""« Pourquoi ces deux chiffres diffèrent-ils ? » (docs/ROADMAP.md, chantier A) : deux chiffres côte à côte, critère par
critère (cadre comptable, administrations couvertes, année, stade, grandeur, unité, poste, statut, source).

Un côté est soit un montant publié (`m<id>`), soit une somme le long d'un arbre budgétaire, écrite comme un lien de
provenance (`n<noeud>~<entité>~<exercice>~<stade>~<mesure>~<unité>`). L'outil ne dit jamais lequel des deux est « le
bon » : il nomme ce qui les sépare. L'écart n'est calculé que dans la même unité, et marqué « calcul du site ».
Importé à la fin de api/main.py, avant api/portes.py.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from api import queries as q
from api.i18n import translations
from api.main import app, con, env, label, nom_entite, render
from pipeline.catalog import load_sources


@lru_cache(maxsize=1)
def referentiels() -> dict[str, str]:
    """Cadre comptable de chaque source, déclaré dans sources.yaml (clé `referentiel`)."""
    return {s.id: s.extra["referentiel"] for s in load_sources() if s.extra.get("referentiel")}


def noms(lang: str) -> dict[str, dict[str, str]]:
    _ = translations(lang).gettext
    return {
        "referentiel": {"comptes_nationaux": _("Comptabilité nationale (SEC 2010)"),
                        "budget_etat": _("Comptabilité budgétaire de l'État (LOLF)"),
                        "comptes_locaux": _("Comptes de gestion des collectivités locales")},
        "stade": {"plf": _("Projet de loi de finances"), "lfi": _("Loi de finances initiale"),
                  "execution": _("Exécution budgétaire"), "compte": _("Comptes publiés")},
        "mesure": {"ae": _("Autorisations d'engagement"), "cp": _("Crédits de paiement"), "depense": _("Dépense"),
                   "agregat": _("Agrégat publié"), "cout_estime": _("Coût estimé"), "cout_prevu": _("Coût prévu"),
                   "recette": _("Recette")},
        "unite": {"MIO_EUR": _("millions d'euros"), "EUR": _("euros"), "EUR_HAB": _("euros par habitant"),
                  "PC_GDP": _("pour cent du PIB"), "PC_TOT": _("pour cent du total")},
    }


def cadre_comptable(sid: str, lang: str) -> str | None:
    return noms(lang)["referentiel"].get(referentiels().get(sid, ""))


env.globals["cadre_comptable"] = cadre_comptable


def cote(ref: str, lang: str) -> dict[str, Any]:
    """Un côté de la comparaison, lu dans la base ; HTTPException 404 si la référence ne désigne rien."""
    if ref.startswith("m") and ref[1:].isdigit():
        m = q.montant_detail(con, int(ref[1:]))
        if m is None:
            raise HTTPException(404)
        # Millions d'euros ramenés en euros : un changement d'échelle, pas de grandeur (l'écart devient calculable).
        mio = m["unite"] == "MIO_EUR"
        return {"v": m["valeur"] * 1e6 if mio else m["valeur"], "unite": "EUR" if mio else m["unite"], "prov": bool(m["provisoire"]), "exercice": m["exercice"],
                "stade": m["stade"], "mesure": m["mesure"], "entite": m["entite_code"],
                "entite_nom": nom_entite(m["entite_nom"], lang), "label": label(m["noeud_id"], lang),
                "nomenclature": m["nomenclature_id"], "sources": [m["source_id"]], "collecte": m["collecte"][:10],
                "nb": 1, "href": f"/{lang}/montant/{m['id']}"}
    parts = ref[1:].split("~")
    if not ref.startswith("n") or len(parts) != 6 or not parts[0].isdigit() or not parts[2].isdigit():
        raise HTTPException(404)
    f = q.Filtre(parts[1], int(parts[2]), *parts[3:])
    v, nb, prov = q.total(con, int(parts[0]), f)
    n = con.execute("SELECT * FROM noeud WHERE id=?", (int(parts[0]),)).fetchone()
    e = q.entite(con, f.entite)
    if v is None or n is None or e is None:
        raise HTTPException(404)
    rows = q.contributions(con, n["id"], f)
    return {"v": v, "unite": f.unite, "prov": prov, "exercice": f.exercice, "stade": f.stade, "mesure": f.mesure,
            "entite": f.entite, "entite_nom": nom_entite(e["nom"], lang), "label": label(n["id"], lang),
            "nomenclature": n["nomenclature_id"], "sources": sorted({r["source_id"] for r in rows}),
            "collecte": max(r["collecte"] for r in rows)[:10], "nb": nb,
            "href": f"/{lang}/provenance/noeud/{n['id']}?{f.query()}"}


BLOQUANTS = ("referentiel", "entite", "mesure", "unite")


def ref_total(noeud_id: int, f: q.Filtre) -> str:
    return f"n{noeud_id}~{f.entite}~{f.exercice}~{f.stade}~{f.mesure}~{f.unite}"


def comparer(a: dict[str, Any], b: dict[str, Any], lang: str) -> list[dict[str, Any]]:
    """Les critères, chacun avec la valeur de chaque côté, s'il diffère et ce que cela veut dire."""
    _ = translations(lang).gettext
    N = noms(lang)
    ra = " / ".join(N["referentiel"].get(referentiels().get(s, ""), "—") for s in a["sources"])
    rb = " / ".join(N["referentiel"].get(referentiels().get(s, ""), "—") for s in b["sources"])
    crit = [
        ("referentiel", _("Cadre comptable"), ra, rb,
         _("Deux cadres comptables différents, chacun avec ses propres règles d'enregistrement : les deux chiffres ne mesurent pas la même chose.")),
        ("entite", _("Administrations couvertes"), a["entite_nom"], b["entite_nom"],
         _("Ils ne couvrent pas les mêmes administrations.")),
        ("exercice", _("Année"), str(a["exercice"]), str(b["exercice"]), _("Ils ne portent pas sur la même année.")),
        ("stade", _("Stade"), N["stade"][a["stade"]], N["stade"][b["stade"]],
         _("Ils ne sont pas au même stade : un projet, une loi votée, une exécution et des comptes publiés sont des étapes différentes.")),
        ("mesure", _("Grandeur mesurée"), N["mesure"].get(a["mesure"], a["mesure"]), N["mesure"].get(b["mesure"], b["mesure"]),
         _("Ils ne mesurent pas la même grandeur.")),
        ("unite", _("Unité"), N["unite"][a["unite"]], N["unite"][b["unite"]],
         _("Les unités diffèrent : les deux chiffres ne se comparent pas sans conversion.")),
        ("poste", _("Poste"), a["label"]["texte"], b["label"]["texte"],
         _("Ils ne classent pas la dépense dans le même poste, ni forcément dans la même nomenclature.")),
        ("prov", _("Statut"), _("provisoire") if a["prov"] else _("définitif ou non précisé"),
         _("provisoire") if b["prov"] else _("définitif ou non précisé"),
         _("Au moins l'un des deux est provisoire : il peut encore être révisé.")),
    ]
    out = []
    for cle, nom, va, vb, sens in crit:
        differe = (a["nomenclature"], a["label"]["texte"]) != (b["nomenclature"], b["label"]["texte"]) \
            if cle == "poste" else va != vb
        out.append({"cle": cle, "nom": nom, "a": va, "b": vb, "differe": differe, "sens": sens if differe else ""})
    return out


@app.get("/{lang}/differences", response_class=HTMLResponse)
def differences(request: Request, lang: str, a: str = "", b: str = ""):
    if not a or not b:
        return render(request, lang, "differences.html", exemples=exemples(lang), ca=None, cb=None)
    ca, cb = cote(a, lang), cote(b, lang)
    crit = comparer(ca, cb, lang)
    # Aucune soustraction entre cadres comptables, périmètres, grandeurs ou unités différents.
    ecart = None if any(c["differe"] for c in crit if c["cle"] in BLOQUANTS) else ca["v"] - cb["v"]
    return render(request, lang, "differences.html", ca=ca, cb=cb, crit=crit, ecart=ecart, exemples=[],
                  nb_diff=sum(c["differe"] for c in crit))


def exemples(lang: str) -> list[dict[str, Any]]:
    """Paires toutes faites, tirées des fiches thématiques (une par thème qui a une mission de l'État)."""
    from api.fiches import paire_etat, themes
    out = []
    for cle in themes():
        p = paire_etat(cle, lang)
        if p:
            out.append(p)
    return out
