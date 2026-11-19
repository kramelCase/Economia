"""Constructeur de vues : quoi × qui × quand × unité × forme, toujours dans cet ordre (docs/vision/USAGES.md §4).

Une période donne une courbe, une aire ou des barres ; une année donne un chiffre, un classement ou un tableau. Chaque
choix ne propose que ce que la source publie ; une combinaison impossible est grisée avec sa raison. Le résultat porte
une phrase descriptive générée à partir des seules valeurs affichées, ses sources, ses exports et un lien permanent.

Règles (docs/vision/dataviz.md) : jamais deux sources ni deux unités sur un graphique ; aucune série n'est
additionnée à une autre ; toute variation affichée est un calcul du site, signalé comme tel.
Importé à la fin de api/main.py (il en réutilise l'application, le rendu et les libellés).
"""

from __future__ import annotations

import csv
import io
import json
from collections import Counter
from typing import Any
from urllib.parse import urlencode

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from api import queries as q
from api.i18n import money, translations
from api import contexte
from api.main import AGREGATS_FICHE, SECTEURS, app, con, label, line_data, perimetre_nom, render

SERIES_MAX = 5  # au-delà, la palette catégorielle ne distingue plus les séries
FORMES = ("courbe", "aires", "barres")           # sur une période
FORMES_ANNEE = ("chiffre", "classement", "tableau")  # pour une année
TOUS = {"@region": "REG-", "@departement": "DEP-"}  # « toutes les régions » : jeton du lien permanent, développé à la lecture
UNITES = ("PC_GDP", "PC_TOT", "MIO_EUR", "EUR_HAB", "EUR")
BARRES_MAX = 2  # barres groupées : au-delà de deux séries, illisible sur 30 ans


def domaines(lang: str) -> dict[str, dict[str, Any]]:
    _ = translations(lang).gettext
    return {
        "cofog": {"nom": _("Dépenses par fonction"), "jeu": "Eurostat gov_10a_exp", "nomenclature": "cofog", "mesure": "depense",
                  "unites": ("PC_GDP", "PC_TOT", "MIO_EUR"), "source": "eurostat_cofog_fr",
                  "defaut": {"ind": ["TOTAL"], "qui": ["S13"], "unite": "PC_GDP"}},
        "apu": {"nom": _("Recettes, dépenses, solde, dette"), "jeu": "Eurostat gov_10a_main, gov_10dd_edpt1",
                "nomenclature": "apu_agregats", "mesure": "agregat",
                "unites": ("PC_GDP", "MIO_EUR"), "source": "eurostat_apu_principaux",
                "defaut": {"ind": ["TR", "TE", "B9"], "qui": ["S13"], "unite": "PC_GDP"}},
        "ofgl": {"nom": _("Régions et départements"), "jeu": "OFGL", "nomenclature": "ofgl_agregats", "mesure": "agregat",
                 "unites": ("EUR_HAB", "EUR"), "source": None,
                 "defaut": {"ind": [str(q.noeud(con, "ofgl_agregats", "Dépenses totales")["id"])],
                            "qui": [q.entites(con, "region")[0]["code"]], "unite": "EUR_HAB"}},
    }


def unite_nom(u: str, lang: str) -> str:
    _ = translations(lang).gettext
    return {"PC_GDP": _("part du PIB (%)"), "PC_TOT": _("part des dépenses du périmètre (%)"), "MIO_EUR": _("euros courants"),
            "EUR": _("euros courants"), "EUR_HAB": _("euros par habitant")}[u]


def indicateurs(dom: str, lang: str) -> list[dict[str, Any]]:
    """Indicateurs d'une source, avec leur groupe d'affichage. Le libellé officiel « Total » de la COFOG est précisé
    (« Dépenses, toutes fonctions ») : seul, il ne dit pas de quoi il est le total."""
    _ = translations(lang).gettext
    if dom == "apu":
        tr = q.noeud(con, "apu_agregats", "TR")["id"]
        return [{"key": n["code"], "id": n["id"], "texte": label(n["id"], lang)["texte"],
                 "groupe": _("Catégories de recettes") if n["parent_id"] == tr else _("Grands postes")}
                for n in con.execute("SELECT * FROM noeud WHERE nomenclature_id = 'apu_agregats' ORDER BY id")]
    if dom == "cofog":
        total = q.noeud(con, "cofog", "TOTAL")
        return [{"key": n["code"], "id": n["id"], "groupe": _("Fonctions") if n["parent_id"] else _("Total"),
                 "texte": _("Dépenses, toutes fonctions") if n["code"] == "TOTAL" else label(n["id"], lang)["texte"]}
                for n in [total, *q.children(con, total["id"])]]
    out = []
    for nom in AGREGATS_FICHE:
        n = q.noeud(con, "ofgl_agregats", nom)
        if n is not None:
            out.append({"key": str(n["id"]), "id": n["id"], "texte": label(n["id"], lang)["texte"], "groupe": None})
    return out


def territoires(dom: str, lang: str) -> list[dict[str, Any]]:
    if dom in ("cofog", "apu"):
        return [{"key": s, "entite": f"APU-{s}", "texte": perimetre_nom(s, lang), "groupe": None} for s in SECTEURS]
    _ = translations(lang).gettext
    return [{"key": e["code"], "entite": e["code"], "texte": e["nom"], "groupe": g}
            for niveau, g in (("region", _("Régions")), ("departement", _("Départements")))
            for e in q.entites(con, niveau)]


def lire(params: dict[str, str], lang: str) -> dict[str, Any]:
    """Valide les paramètres d'URL ; tout ce qui n'existe pas donne une 404, jamais un graphique vide."""
    doms = domaines(lang)
    dom = params.get("dom", "cofog")
    if dom not in doms:
        raise HTTPException(404)
    d = doms[dom]
    inds = {i["key"]: i for i in indicateurs(dom, lang)}
    geos = {t["key"]: t for t in territoires(dom, lang)}
    ind = [k for k in params.get("ind", ",".join(d["defaut"]["ind"])).split(",") if k] or d["defaut"]["ind"]
    qui_lien = [k for k in params.get("qui", ",".join(d["defaut"]["qui"])).split(",") if k] or d["defaut"]["qui"]
    qui = [g for k in qui_lien for g in
           ([t["key"] for t in geos.values() if t["entite"].startswith(TOUS[k])] if k in TOUS and dom == "ofgl" else [k])]
    unite = params.get("unite", d["defaut"]["unite"])
    quand = params.get("quand", "periode")
    formes = FORMES_ANNEE if quand == "annee" else FORMES
    forme = params.get("forme", "")
    if any(k not in inds for k in ind) or any(k not in geos for k in qui) or unite not in d["unites"] \
            or quand not in ("periode", "annee") or (forme and forme not in formes):
        raise HTTPException(404)
    ind, qui = list(dict.fromkeys(ind)), list(dict.fromkeys(qui))
    if not forme:  # forme par défaut : la plus simple qui convient aux choix précédents
        forme = "courbe" if quand == "periode" else "chiffre" if len(ind) * len(qui) == 1 \
            else "classement" if len(ind) == 1 else "tableau"
    annees = sorted({a for i in ind for g in qui for a in
                     (r["exercice"] for r in q.series(con, inds[i]["id"], geos[g]["entite"], "compte", d["mesure"], unite))})
    if not annees:
        raise HTTPException(404)
    de = int(params["de"]) if params.get("de", "").isdigit() else annees[0]
    a = int(params["a"]) if params.get("a", "").isdigit() else annees[-1]
    de, a = max(min(de, a), annees[0]), min(max(de, a), annees[-1])
    annee = None
    if quand == "annee":
        annee = int(params["annee"]) if params.get("annee", "").isdigit() and int(params["annee"]) in annees else annees[-1]
        de = a = annee
    return {"dom": dom, "d": d, "inds": inds, "geos": geos, "ind": ind, "qui": qui,
            "qui_lien": list(dict.fromkeys(qui_lien)), "unite": unite, "forme": forme, "quand": quand, "annee": annee,
            "de": de, "a": a, "annees": annees, "reperes": quand == "periode" and params.get("reperes") == "1"}


def series(e: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    """Les séries demandées (indicateur × territoire) : 5 au plus sur le graphique d'une période (au-delà, les couleurs
    ne se distinguent plus), sans limite pour une année. Renvoie aussi le nombre de séries écartées."""
    paires = [(i, g) for i in e["ind"] for g in e["qui"]]
    limite = SERIES_MAX if e["quand"] == "periode" else len(paires)
    out = []
    for slot, (i, g) in enumerate(paires[:limite], start=1):
        ind, geo = e["inds"][i], e["geos"][g]
        if len(e["ind"]) > 1 and len(e["qui"]) > 1:
            nom = f"{ind['texte']} · {geo['texte']}"
        else:
            nom = geo["texte"] if len(e["qui"]) > 1 else ind["texte"]
        rows = [r for r in q.series_provenance(con, ind["id"], geo["entite"], "compte", e["d"]["mesure"], e["unite"])
                if e["de"] <= r["exercice"] <= e["a"]]
        # Plusieurs lignes publiées la même année sous ce code (anciennes régions avant 2016, DEP-67A) : pas de
        # point pour cette année, jamais une somme.
        n = Counter(r["exercice"] for r in rows)
        multi = sorted(a for a, k in n.items() if k > 1)
        rows = [r for r in rows if n[r["exercice"]] == 1]
        out.append({"slot": slot, "nom": nom, "ind": ind, "geo": geo, "rows": rows, "multi": multi,
                    "rupture": q.ruptures(rows), "rupture_detail": q.ruptures_detail(rows)})
    return out, max(0, len(paires) - limite)


def signe(v: float, lang: str) -> str:
    """Écart signé, une décimale, signe moins typographique."""
    t = f"{abs(v):.1f}".replace(".", "," if lang == "fr" else ".")
    return ("+" if v > 0 else "−" if v < 0 else "") + t


def resume(s: dict[str, Any], unite: str, lang: str) -> dict[str, Any] | None:
    """Dernière valeur publiée, et l'écart avec la première de la période (calcul du site)."""
    rows = s["rows"]
    if not rows:
        return None
    first, last = rows[0], rows[-1]
    out = {"dernier": last, "premier": first, "f": money(last["valeur"], lang, unite)}
    if first["exercice"] != last["exercice"] and not s.get("rupture"):  # pas d'écart à travers un changement de collectivité
        if unite.startswith("PC_"):
            out["ecart"] = translations(lang).gettext("%(v)s pt") % {"v": signe(last["valeur"] - first["valeur"], lang)}
        elif first["valeur"] <= 0 or last["valeur"] <= 0:
            # Un solde peut changer de signe : un pourcentage d'évolution n'aurait pas de sens, on donne l'écart en montant.
            d = last["valeur"] - first["valeur"]
            out["ecart"] = ("+" if d > 0 else "−" if d < 0 else "") + money(abs(d), lang, unite)
        elif first["valeur"]:
            pct = (last["valeur"] / first["valeur"] - 1) * 100
            out["ecart"] = signe(pct, lang) + " %"
    return out


def notes(e: dict[str, Any], ss: list[dict[str, Any]], lang: str) -> list[str]:
    """Notes déclenchées par ce qui est affiché. Celles sur la qualité des données (plusieurs budgets, valeurs
    provisoires) passent toujours ; les autres complètent jusqu'à trois."""
    _ = translations(lang).gettext
    out, qualite = [], []
    if e["unite"] in ("MIO_EUR", "EUR"):
        out.append(_("Montants en euros courants : l'inflation n'est pas déduite."))
    if e["unite"] == "PC_TOT":
        out.append(_("Part publiée par Eurostat, en pourcentage des dépenses totales du périmètre choisi."))
    if e["reperes"]:
        out.append(_("Traits verticaux : début de chaque présidence de la République, d'après l'Assemblée nationale (publié depuis 2007). Une date de début ne dit pas ce qui explique une évolution ; les montants sont annuels et les mandats ne suivent pas l'année civile."))
    if e["dom"] in ("cofog", "apu") and len(e["qui"]) > 1:
        out.append(_("Les périmètres sont affichés côte à côte ; ce site ne les additionne pas."))
    multi = sorted({a for s in ss for a in s["multi"]})
    if multi:
        qualite.append(_("Pas de point pour %(a)s : le fichier publie plusieurs budgets sous ce code ces années-là ; ce site ne les additionne pas.")
                   % {"a": f"{multi[0]}–{multi[-1]}" if len(multi) > 1 else str(multi[0])})
    rupt = sorted({(s["geo"]["texte"], x["a"]) for s in ss for x in s.get("rupture_detail", []) if x["motif"] == "siren"})
    pops = sorted({(s["geo"]["texte"], x["a"]) for s in ss for x in s.get("rupture_detail", []) if x["motif"] == "population"})
    if pops:
        qualite.append(_("La population publiée pour ce code varie de plus de moitié en %(a)s : le périmètre n'est plus le même. Ce site ne calcule pas d'évolution à travers ce changement.")
                       % {"a": ", ".join(f"{a} ({n})" for n, a in pops)})
    if rupt:
        qualite.append(_("Le fichier publie un autre numéro SIREN sous ce code à partir de %(a)s : ce n'est plus la même collectivité. Ce site ne calcule pas d'évolution à travers ce changement.")
                       % {"a": ", ".join(f"{a} ({n})" for n, a in rupt)})
    if any(r["provisoire"] for s in ss for r in s["rows"]):
        qualite.append(_("Les points creux sont des valeurs marquées provisoires dans la source."))
    return qualite + out[:max(0, 3 - len(qualite))]


def formes_possibles(e: dict[str, Any], n_series: int, lang: str) -> list[dict[str, Any]]:
    """Les formes de la période ou de l'année, chacune avec la raison pour laquelle elle ne convient pas, le cas échéant."""
    _ = translations(lang).gettext
    noms = {"courbe": _("Courbe"), "aires": _("Aire"), "barres": _("Barres"), "chiffre": _("Chiffre seul"),
            "classement": _("Classement"), "tableau": _("Tableau")}
    raisons = {"aires": None if n_series == 1 else _("Une aire ne montre qu'une seule série."),
               "barres": None if n_series <= BARRES_MAX else _("Deux séries au plus pour des barres groupées."),
               "chiffre": None if n_series == 1 else _("Il faut un seul indicateur et un seul périmètre."),
               "classement": None if len(e["ind"]) == 1 and n_series > 1 else
               _("Un classement range plusieurs périmètres ou territoires selon un seul indicateur.")}
    return [{"key": f, "nom": noms[f], "raison": raisons.get(f)} for f in (FORMES_ANNEE if e["quand"] == "annee" else FORMES)]


def unites_possibles(e: dict[str, Any], lang: str) -> list[dict[str, Any]]:
    _ = translations(lang).gettext
    out: dict[str, dict[str, Any]] = {}
    for u in UNITES:  # M€ et € portent le même nom (« euros courants ») : une seule pastille, celle de la source
        nom, ok = unite_nom(u, lang), u in e["d"]["unites"]
        if nom not in out or (ok and out[nom]["raison"]):
            out[nom] = {"key": u, "nom": nom, "raison": None if ok else _("Unité non publiée par cette source.")}
    return list(out.values())


def phrase(e: dict[str, Any], ss: list[dict[str, Any]], lang: str) -> list[str]:
    """Ce que montre la figure, en mots, tiré des seules valeurs affichées : ni adjectif, ni causalité."""
    _ = translations(lang).gettext
    u = unite_nom(e["unite"], lang)
    vus = [s for s in ss if s["rows"]]
    if not vus:
        return [_("Aucune valeur publiée pour cette sélection.")]
    m = lambda r: money(r["valeur"], lang, e["unite"])  # noqa: E731
    if e["quand"] == "annee":
        if len(vus) == 1:
            return [_("En %(a)s, %(nom)s : %(v)s (%(u)s).") % {"a": e["annee"], "nom": vus[0]["nom"], "v": m(vus[0]["rows"][0]),
                                                                "u": u}]
        tri = sorted(vus, key=lambda s: -s["rows"][0]["valeur"])
        return [_("En %(a)s, sur %(n)s valeurs publiées (%(u)s), la plus élevée est celle de %(h)s (%(vh)s), la plus basse celle de %(b)s (%(vb)s).")
                % {"a": e["annee"], "n": len(vus), "u": u, "h": tri[0]["nom"], "vh": m(tri[0]["rows"][0]),
                   "b": tri[-1]["nom"], "vb": m(tri[-1]["rows"][0])}]
    out = []
    for s in vus[:3]:
        r = resume(s, e["unite"], lang)
        if r["premier"]["exercice"] == r["dernier"]["exercice"]:
            out.append(_("%(nom)s : %(v)s en %(a)s (%(u)s).") % {"nom": s["nom"], "v": r["f"], "a": r["dernier"]["exercice"], "u": u})
        else:
            out.append(_("%(nom)s : %(v1)s en %(a1)s, %(v2)s en %(a2)s (%(u)s ; écart calculé par ce site : %(e)s).")
                       % {"nom": s["nom"], "v1": m(r["premier"]), "a1": r["premier"]["exercice"], "v2": r["f"],
                          "a2": r["dernier"]["exercice"], "u": u, "e": r.get("ecart", "—")})
    return out


def classement(ss: list[dict[str, Any]]) -> dict[str, Any]:
    """Barres horizontales d'une année, triées ; l'échelle part de zéro, des deux côtés si une valeur est négative."""
    lignes = sorted(((s, s["rows"][0]) for s in ss if s["rows"]), key=lambda t: -t[1]["valeur"])
    vals = [r["valeur"] for _s, r in lignes] or [0.0]
    bas, haut = min(0.0, *vals), max(0.0, *vals)
    etendue = (haut - bas) or 1.0
    zero = -bas / etendue * 100
    return {"zero": zero, "lignes": [{"s": s, "r": r, "rang": k + 1, "g": zero + min(0.0, r["valeur"]) / etendue * 100,
                                      "w": abs(r["valeur"]) / etendue * 100} for k, (s, r) in enumerate(lignes)]}


def lien(lang: str, e: dict[str, Any], **change: Any) -> str:
    annee = change.get("quand", e["quand"]) == "annee"
    p = {"dom": e["dom"], "ind": ",".join(e["ind"]), "qui": ",".join(e["qui_lien"]), "unite": e["unite"],
         "quand": "annee" if annee else None, "annee": (e["annee"] or e["annees"][-1]) if annee else None,
         "de": None if e["quand"] == "annee" else e["de"], "a": None if e["quand"] == "annee" else e["a"],
         "forme": None if {"quand", "ind", "qui"} & change.keys() else e["forme"],  # la forme par défaut suit ces choix
         "reperes": "1" if e["reperes"] else None}
    if change.get("quand") == "periode":
        change["quand"] = None
    p.update({k: (",".join(v) if isinstance(v, list) else v) for k, v in change.items()})
    p = {k: v for k, v in p.items() if v not in (None, "")}
    return f"/{lang}/serie?{urlencode(p)}"


def bascule(liste: list[str], k: str) -> list[str]:
    """Ajoute ou retire une pastille ; la dernière restante ne se retire pas."""
    if k in liste:
        return [x for x in liste if x != k] or liste
    return [*liste, k]


@app.get("/{lang}/serie", response_class=HTMLResponse)
def serie_page(request: Request, lang: str):
    e = lire(dict(request.query_params), lang)
    ss, ecartees = series(e)
    _ = translations(lang).gettext
    formes = formes_possibles(e, len(ss), lang)
    forme = e["forme"] if e["forme"] in [f["key"] for f in formes if not f["raison"]] else \
        next(f["key"] for f in formes if not f["raison"])
    xs = [a for a in e["annees"] if e["de"] <= a <= e["a"]]
    data = line_data(lang, xs, [{"name": s["nom"], "slot": s["slot"],
                                 "points": {r["exercice"]: (r["valeur"], r["id"], r["provisoire"]) for r in s["rows"]}}
                                for s in ss], e["unite"])
    data["forme"] = forme
    extra = ["an_acteurs_organes"] if e["reperes"] else []
    if e["reperes"]:
        data["reperes"] = [r for r in contexte.reperes(e["de"], e["a"]) if r["an"] in xs]
    doms = domaines(lang)
    pastilles_ind = [{**i, "on": i["key"] in e["ind"], "href": lien(lang, e, ind=bascule(e["ind"], i["key"]))}
                     for i in e["inds"].values()]
    qui_simple = [k for k in e["qui_lien"] if k not in TOUS] or e["qui"][:1]
    pastilles_qui = [{**t, "on": t["key"] in e["qui"], "href": lien(lang, e, qui=bascule(qui_simple, t["key"]))}
                     for t in e["geos"].values()]
    tous = [{"key": k, "texte": {"@region": _("Toutes les régions"), "@departement": _("Tous les départements")}[k],
             "on": k in e["qui_lien"], "href": lien(lang, e, qui=[k], quand="annee")} for k in TOUS] if e["dom"] == "ofgl" else []
    titre = ", ".join(s["nom"] for s in ss) if len(ss) <= 2 else \
        (_("%(ind)s : %(n)s valeurs") % {"ind": e["inds"][e["ind"][0]]["texte"], "n": sum(1 for x in ss if x["rows"])} if len(e["ind"]) == 1
         else _("%(n)s séries") % {"n": len(ss)})
    jeu = {"cofog": "fonctions", "apu": "comptes", "ofgl": "collectivites"}[e["dom"]]
    # Points de départ : décrits par ce qu'ils montrent (une forme), pas par un sujet choisi par le site.
    depart = [(_("Recettes et dépenses depuis 1995"), "?dom=apu&ind=TR,TE&unite=PC_GDP"),
              (_("Les catégories de recettes dans le temps"), "?dom=apu&ind=D2REC,D5REC,D61REC&unite=PC_GDP"),
              (_("Comparer les administrations, une année"), "?dom=apu&ind=TE&qui=S13,S1311,S1313,S1314&quand=annee&unite=MIO_EUR"),
              (_("Classer les départements"), "?dom=ofgl&qui=@departement&quand=annee"),
              (_("Classer les régions"), "?dom=ofgl&qui=@region&quand=annee")]
    depart = [{"t": t, "href": f"/{lang}/serie{h}"} for t, h in depart]
    return render(request, lang, "serie.html", e=e, ss=ss, ecartees=ecartees, data=data, forme=forme,
                  formes=formes, unites_p=unites_possibles(e, lang), depart=depart, phrases=phrase(e, ss, lang), tous=tous,
                  classement=classement(ss) if e["quand"] == "annee" else None,
                  comparer=f"/{lang}/comparer?jeu={jeu}" + (f"&annee={e['annee']}" if e["annee"] else ""), resumes=[resume(s, e["unite"], lang) for s in ss], notes=notes(e, ss, lang), extra=extra,
                  pastilles_ind=pastilles_ind, pastilles_qui=pastilles_qui, titre=titre,
                  unite_nom=unite_nom(e["unite"], lang), unites=[(u, unite_nom(u, lang)) for u in e["d"]["unites"]],
                  doms=doms, lien=lambda **c: lien(lang, e, **c), base_url=str(request.base_url).rstrip("/"),
                  sources=data["sources"])


def lignes_export(e: dict[str, Any], ss: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Format long, une ligne par valeur, avec sa provenance complète."""
    return [{"serie": s["nom"], "indicateur": s["ind"]["texte"], "perimetre": s["geo"]["texte"], "annee": r["exercice"],
             "valeur": r["valeur"], "unite": e["unite"], "provisoire": bool(r["provisoire"]), "source": r["source_titre"],
             "editeur": r["editeur"], "fichier": r["chemin"], "sha256": r["sha256"], "ligne_source": r["ligne_source"],
             "montant_id": r["id"]} for s in ss for r in s["rows"]]


@app.get("/{lang}/serie.csv")
def serie_csv(request: Request, lang: str):
    e = lire(dict(request.query_params), lang)
    rows = lignes_export(e, series(e)[0])
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()) if rows else ["serie"])
    w.writeheader()
    w.writerows(rows)
    return Response(buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="comptes-publics-serie.csv"'})


@app.get("/{lang}/serie.json")
def serie_json(request: Request, lang: str):
    e = lire(dict(request.query_params), lang)
    body = {"page": lien(lang, e), "unite": e["unite"], "valeurs": lignes_export(e, series(e)[0])}
    return Response(json.dumps(body, ensure_ascii=False, indent=1), media_type="application/json")
