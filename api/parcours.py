"""Comprendre : un parcours de six étapes (docs/vision/INTERFACE.md §3.3).

Une étape = une question en mots simples, une figure, des phrases tirées des seules valeurs affichées, les définitions
officielles citées des termes employés, l'étape suivante. Chaque figure ne montre qu'une source et une unité ; l'étape 6,
qui confronte deux périmètres, montre deux chiffres séparés, chacun avec sa source, jamais soustraits l'un de l'autre.
Importé à la fin de api/main.py, avant api/portes.py.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from api import queries as q
from api.i18n import money, translations
from api.main import (SECTEURS, nom_entite, app, bv_cols, concepts_index, con, label, line_data, parts, render, source_info,
                      top_keys)
from api.carte import valeur
from api.recettes import categories

ETAPES = ("perimetre", "equilibre", "recettes", "depenses", "dette", "etat")
CONCEPTS = {"perimetre": ("apu", "apul", "odac"), "equilibre": ("depenses_publiques", "deficit_public", "pib"),
            "recettes": ("prelevements_obligatoires",), "depenses": ("cofog", "depenses_publiques"),
            "dette": ("dette_maastricht", "deficit_public"), "etat": ("loi_de_finances", "lfi", "execution", "cp")}


def apu(code: str, entite: str, unite: str) -> dict[int, Any]:
    n = q.noeud(con, "apu_agregats", code)
    return {r["exercice"]: r for r in q.series(con, n["id"], entite, "compte", "agregat", unite)}


def titres(lang: str) -> dict[str, dict[str, str]]:
    _ = translations(lang).gettext
    return {
        "perimetre": {"q": _("Qui sont les administrations publiques ?"),
                      "intro": _("Les comptes nationaux publient les comptes de l'ensemble des administrations publiques, et séparément ceux de trois sous-secteurs.")},
        "equilibre": {"q": _("Combien entre, combien sort ?"),
                      "intro": _("Chaque année, les comptes nationaux publient les recettes, les dépenses et leur écart, le solde, en part du PIB.")},
        "recettes": {"q": _("D'où vient l'argent ?"),
                     "intro": _("Les recettes publiées, réparties selon les catégories des comptes nationaux.")},
        "depenses": {"q": _("Où va l'argent ?"),
                     "intro": _("Les dépenses publiées, réparties selon leur fonction : la classification internationale des fonctions des administrations publiques.")},
        "dette": {"q": _("Qu'est-ce que la dette ?"),
                  "intro": _("Le solde et la dette sont deux séries publiées séparément, chacune avec sa définition officielle, citée plus bas.")},
        "etat": {"q": _("Le budget de l'État, c'est la même chose ?"),
                 "intro": _("Ce sont deux publications différentes : le budget de l'État, publié par la Direction du budget, et les comptes des administrations publiques, publiés par Eurostat. Voici un chiffre de chacune, côte à côte, chacun avec sa source.")},
    }


def etape(cle: str, lang: str) -> dict[str, Any]:
    _ = translations(lang).gettext
    m = lambda v, u: money(v, lang, u)  # noqa: E731
    if cle == "perimetre":
        te = {s: apu("TE", f"APU-{s}", "MIO_EUR") for s in SECTEURS}
        a = max(set.intersection(*(set(x) for x in te.values())))
        lignes = [{"nom": nom_entite(q.entite(con, f"APU-{s}")["nom"], lang), "r": te[s][a], "total": s == "S13"} for s in SECTEURS]
        haut = max(l["r"]["valeur"] for l in lignes)
        for l in lignes:
            l["w"] = l["r"]["valeur"] / haut * 100
        somme = sum(l["r"]["valeur"] for l in lignes if not l["total"])
        phrases = [_("En %(a)s, les dépenses publiées pour l'ensemble des administrations publiques sont de %(t)s.")
                   % {"a": a, "t": m(te["S13"][a]["valeur"], "MIO_EUR")},
                   _("Les trois sous-secteurs sont publiés séparément ; la somme de leurs dépenses (%(s)s, calcul du site) dépasse le total publié. Ce site n'additionne donc jamais les sous-secteurs.")
                   % {"s": m(somme, "MIO_EUR")}]
        return {"forme": "barres", "lignes": lignes, "unite": "MIO_EUR", "annee": a, "phrases": phrases,
                "sources": ["eurostat_apu_principaux"],
                "suite": f"/{lang}/serie?dom=apu&ind=TE&qui=S13,S1311,S1313,S1314&quand=annee"}
    if cle in ("equilibre", "dette"):
        # Une source par graphique : la dette (gov_10dd_edpt1) est tracée seule ; le solde est cité dans la phrase.
        codes = ("TR", "TE") if cle == "equilibre" else ("GD",)
        ss = {c: apu(c, "APU-S13", "PC_GDP") for c in codes}
        b9 = apu("B9", "APU-S13", "PC_GDP")
        xs = sorted(set.union(*(set(s) for s in ss.values())))
        data = line_data(lang, xs, [{"name": label(q.noeud(con, "apu_agregats", c)["id"], lang)["texte"], "slot": k + 1,
                                     "points": {a: (r["valeur"], r["id"], r["provisoire"]) for a, r in ss[c].items()}}
                                    for k, c in enumerate(codes)], "PC_GDP")
        a = max(set.intersection(*(set(s) for s in ss.values())))
        if cle == "dette":
            a = max(set(ss["GD"]) & set(b9))
        if cle == "equilibre":
            phrases = [_("En %(a)s, les recettes de l'ensemble des administrations publiques représentent %(r)s du PIB et leurs dépenses %(d)s.")
                       % {"a": a, "r": m(ss["TR"][a]["valeur"], "PC_GDP"), "d": m(ss["TE"][a]["valeur"], "PC_GDP")}]
            if a in b9:
                phrases.append(_("Le solde publié pour la même année est de %(b)s du PIB : c'est l'écart entre recettes et dépenses, vérifié par ce site pour chaque année.")
                               % {"b": m(b9[a]["valeur"], "PC_GDP")})
        else:
            d0 = min(ss["GD"])
            phrases = [_("La dette publiée de l'ensemble des administrations publiques est de %(v0)s du PIB en %(a0)s et de %(v1)s en %(a1)s.")
                       % {"v0": m(ss["GD"][d0]["valeur"], "PC_GDP"), "a0": d0, "v1": m(ss["GD"][a]["valeur"], "PC_GDP"), "a1": a},
                       _("Le solde de %(a)s est de %(b)s du PIB.") % {"a": a, "b": m(b9[a]["valeur"], "PC_GDP")}]
        return {"forme": "courbe", "data": data, "phrases": phrases, "annee": a,
                "suite": f"/{lang}/serie?dom=apu&ind={','.join(codes)}&unite=PC_GDP",
                "solde": b9.get(a) if cle == "dette" else None}
    if cle == "recettes":
        annees = sorted(apu("D2REC", "APU-S13", "MIO_EUR"))
        a = annees[-1]
        anneau = parts(categories("APU-S13", a, lang, "S13"), top_keys(categories("APU-S13", a, lang, "S13")))
        for it in anneau["featured"] + (anneau["other"]["liste"] if anneau["other"] else []):
            it["drill"] = f"/{lang}/recettes-publiques?annee={a}&categorie={it['key']}#zoom"
        prem = anneau["featured"][0]
        phrases = [_("En %(a)s, les recettes publiées de l'ensemble des administrations publiques sont de %(t)s.")
                   % {"a": a, "t": m(anneau["total"], "MIO_EUR")},
                   _("La catégorie au montant le plus élevé est « %(c)s » : %(v)s, soit %(p)s du total (calcul du site).")
                   % {"c": prem["label"]["texte"], "v": m(prem["v"], "MIO_EUR"), "p": f"{prem['v'] / anneau['total'] * 100:.1f}".replace(".", "," if lang == "fr" else ".") + " %"}]
        return {"forme": "anneau", "anneau": anneau, "unite": "MIO_EUR", "annee": a, "phrases": phrases,
                "suite": f"/{lang}/recettes-publiques"}
    if cle == "depenses":
        total = q.noeud(con, "cofog", "TOTAL")
        a = q.years(con, "cofog", "APU-S13", "compte", "depense", "MIO_EUR")[-1]
        fm = q.Filtre("APU-S13", a, "compte", "depense", "MIO_EUR")
        fp = q.Filtre("APU-S13", a, "compte", "depense", "PC_TOT")
        items = [{"key": n["code"], "id": n["id"], "label": label(n["id"], lang), "v": v["valeur"], "m": v["id"],
                  "prov": v["provisoire"], "p": q.single(con, n["id"], fp), "drill": f"/{lang}/?f={n['code']}#carte"}
                 for n in q.children(con, total["id"]) if (v := q.single(con, n["id"], fm)) is not None]
        anneau = parts(items, top_keys(items))
        prem = anneau["featured"][0]
        phrases = [_("En %(a)s, la fonction au montant le plus élevé est « %(f)s » : %(v)s pour 100 € de dépense publique.")
                   % {"a": a, "f": prem["label"]["texte"], "v": valeur(prem["p"]["valeur"], "PC_TOT", lang)}]
        return {"forme": "anneau", "anneau": anneau, "unite": "MIO_EUR", "annee": a, "phrases": phrases,
                "suite": f"/{lang}/serie?dom=cofog&quand=annee&qui=S13"}
    # etat
    cb = q.noeud(con, "budget_vert_plf2026", "CB")
    etat = bv_cols(cb["id"], "cp")[0]  # exécution 2024
    te = apu("TE", "APU-S13", "MIO_EUR")
    a = 2024
    chiffres = [{"t": _("Budget de l'État : crédits de paiement exécutés en %(a)s") % {"a": a},
                 "f": m(etat["v"], "EUR"), "href": f"/{lang}/{etat['href']}", "src": "etat_budget_vert_plf2026"},
                {"t": _("Ensemble des administrations publiques : dépenses en %(a)s (comptes nationaux)") % {"a": a},
                 "f": m(te[a]["valeur"], "MIO_EUR"), "href": f"/{lang}/montant/{te[a]['id']}", "src": "eurostat_apu_principaux"}]
    phrases = [_("Les deux chiffres viennent de deux publications différentes, pour deux périmètres différents ; ce site ne les soustrait pas l'un de l'autre.")]
    return {"forme": "chiffres", "chiffres": chiffres, "annee": a, "phrases": phrases,
            "sources": ["etat_budget_vert_plf2026", "eurostat_apu_principaux"], "suite": f"/{lang}/budget-etat?vue=0"}


@app.get("/{lang}/comprendre/{n}", response_class=HTMLResponse)
def parcours(request: Request, lang: str, n: int):
    if not 1 <= n <= len(ETAPES):
        raise HTTPException(404)
    cle = ETAPES[n - 1]
    t = titres(lang)
    idx = concepts_index(lang)
    return render(request, lang, "parcours.html", n=n, total=len(ETAPES), cle=cle, t=t[cle], e=etape(cle, lang),
                  etapes=[{"n": k + 1, "q": t[c]["q"]} for k, c in enumerate(ETAPES)],
                  concepts=[idx[c] for c in CONCEPTS[cle] if c in idx], source_info=source_info)
