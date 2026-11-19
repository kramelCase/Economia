"""Comparateur : un tableau de travail, lignes × colonnes, trié et filtré, chaque cellule reliée à sa ligne source.

Trois jeux : les collectivités (OFGL, une ligne par région ou département, une colonne par agrégat ou fonction), les
fonctions publiques (COFOG, une ligne par fonction ou sous-fonction, une colonne par périmètre) et les comptes des
administrations publiques (Eurostat, une ligne par poste : recettes, dépenses, solde, intérêts, dette). Un seul niveau de
nomenclature à la fois : on ne trie jamais ensemble des postes emboîtés. Rien n'est additionné. Quand un même code
porte plusieurs lignes publiées pour une année (anciennes régions avant 2016, Bas-Rhin et Haut-Rhin sous DEP-67A),
la cellule le dit et renvoie aux lignes, sans total.
Les écarts entre deux années, les rangs et les statistiques (médiane, minimum, maximum) sont des calculs du site.
Le tri et les filtres sont appliqués ici (liens et formulaires sans JavaScript) et à l'identique par static/comparer.js.
"""

from __future__ import annotations

import csv
import io
from functools import lru_cache
from statistics import median
from typing import Any
from urllib.parse import urlencode

from babel.numbers import format_decimal
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from api import queries as q
from api.i18n import translations
from api.main import SECTEURS, app, con, indicateurs, label, perimetre_nom, render, sources_de

JEUX = ("collectivites", "fonctions", "comptes")
COLS_MAX = 8
UNITES = {"collectivites": ("EUR_HAB", "EUR"), "fonctions": ("PC_TOT", "MIO_EUR", "PC_GDP"), "comptes": ("PC_GDP", "MIO_EUR")}
NIVEAUX = {"collectivites": ("departement", "region"), "fonctions": ("fonction", "sous-fonction"), "comptes": ("poste",)}
NOMENCLATURE = {"fonctions": ("cofog", "depense"), "comptes": ("apu_agregats", "agregat")}
DEFAUT_COLS = {"collectivites": ["Dépenses totales", "Frais de personnel", "Dépenses d'investissement", "Encours de dette"],
               "fonctions": ["S13", "S1311", "S1313", "S1314"], "comptes": ["S13", "S1311", "S1313", "S1314"]}


def unite_courte(u: str, lang: str) -> str:
    _ = translations(lang).gettext
    return {"EUR_HAB": _("€/hab."), "EUR": _("M€"), "MIO_EUR": _("Md€"), "PC_TOT": _("part du total, %"),
            "PC_GDP": _("part du PIB, %")}[u]


def symbole(u: str, lang: str) -> str:
    """L'unité écrite à côté de chaque valeur du tableau (l'en-tête la dit en entier)."""
    _ = translations(lang).gettext
    return {"EUR_HAB": _("€/hab."), "EUR": _("M€"), "MIO_EUR": _("Md€"), "PC_TOT": "%", "PC_GDP": "%"}[u]


def nombre(v: float | None, u: str, lang: str) -> str:
    """Valeur dans l'unité de la colonne, sans suffixe (l'unité est dans l'en-tête)."""
    if v is None:
        return "—"
    if u == "EUR_HAB":
        return format_decimal(v, "#,##0", locale=lang)
    if u == "EUR":
        return format_decimal(v / 1e6, "#,##0.0", locale=lang)
    if u == "MIO_EUR":
        return format_decimal(v / 1e3, "#,##0.0", locale=lang)
    return format_decimal(v, "#,##0.0", locale=lang)


def ecart(v: float | None, r: float | None, u: str, lang: str, montant: bool = False) -> tuple[float | None, str]:
    """Écart entre l'année comparée et l'année de référence : en points pour une part, en % sinon. `montant` : écart
    en milliards d'euros (comptes des APU, où un solde change de signe et un pourcentage n'aurait pas de sens)."""
    if v is None or r is None or (not u.startswith("PC_") and not montant and not r):
        return None, "—"
    if montant and not u.startswith("PC_"):
        d = (v - r) / 1e3
        return d, ("+" if d > 0 else "−" if d < 0 else "") + format_decimal(abs(d), "#,##0.0", locale=lang) + " Md€"
    d = v - r if u.startswith("PC_") else (v / r - 1) * 100
    s = format_decimal(abs(d), "#,##0.0", locale=lang)
    return d, ("+" if d > 0 else "−" if d < 0 else "") + s + (" pt" if u.startswith("PC_") else " %")


@lru_cache(maxsize=None)
def agregats_ofgl(niveau: str) -> tuple[tuple[int, str, int, str], ...]:
    """Tous les agrégats publiés par l'OFGL pour ce niveau, dans l'ordre de leur arbre publié : (id, code, profondeur,
    famille). La famille est la racine de l'arbre : dépenses totales, recettes totales, ou le reste (dette, épargne,
    équilibre). Un agrégat sans valeur à ce niveau n'est pas proposé."""
    avec = {r[0] for r in con.execute(
        """SELECT DISTINCT m.noeud_id FROM montant m JOIN noeud n ON n.id=m.noeud_id JOIN entite e ON e.id=m.entite_id
           WHERE n.nomenclature_id='ofgl_agregats' AND e.niveau=?""", (niveau,))}
    noeuds = [dict(r) for r in con.execute("SELECT id, code, parent_id FROM noeud WHERE nomenclature_id='ofgl_agregats' ORDER BY id")]
    enfants: dict[int | None, list[dict[str, Any]]] = {}
    for n in noeuds:
        enfants.setdefault(n["parent_id"], []).append(n)
    out: list[tuple[int, str, int, str]] = []

    def visite(n: dict[str, Any], d: int, fam: str) -> None:
        if n["id"] in avec:
            out.append((n["id"], n["code"], d, fam))
        for c in enfants.get(n["id"], []):
            visite(c, d + 1, fam)

    for r in enfants.get(None, []):
        visite(r, 0, {"Dépenses totales": "depenses", "Recettes totales": "recettes"}.get(r["code"], "dette"))
    ordre = {"depenses": 0, "recettes": 1, "dette": 2}
    return tuple(sorted(out, key=lambda x: ordre[x[3]]))  # tri stable : l'ordre de l'arbre est gardé


def colonnes_possibles(jeu: str, niveau: str, lang: str) -> list[dict[str, Any]]:
    _ = translations(lang).gettext
    if jeu == "collectivites":
        familles = {"depenses": _("Dépenses"), "recettes": _("Recettes : impôts, dotations, subventions…"),
                    "dette": _("Dette, épargne et équilibre")}
        groupes = {"f57": _("Fonctions (nomenclature M57)"), "f52": _("Fonctions (nomenclature M52)")}
        return [{"key": code, "texte": label(i, lang)["texte"], "groupe": familles[fam], "gk": fam, "niv": d, "noeud": i,
                 "mesure": "agregat", "nomen": "agregat"} for i, code, d, fam in agregats_ofgl(niveau)] + \
               [{"key": i["key"], "texte": i["label"]["texte"], "groupe": groupes[i["groupe"]], "gk": "fonctions", "niv": 0,
                 "noeud": i["noeud"]["id"], "mesure": i["mesure"], "nomen": i["groupe"], "fr": i["noeud"]["libelle"]}
                for i in indicateurs(niveau, lang) if i["groupe"] != "agregat"]
    ico = {"S13": "fonctions", "S1311": "etat", "S1313": "habitat", "S1314": "social"}
    return [{"key": s, "texte": perimetre_nom(s, lang)[0].upper() + perimetre_nom(s, lang)[1:], "groupe": None,
             "entite": f"APU-{s}", "ico": ico.get(s)} for s in SECTEURS]


def lignes_possibles(jeu: str, niveau: str, lang: str) -> list[dict[str, Any]]:
    if jeu == "collectivites":
        return [{"key": e["code"], "nom": e["nom"], "code": e["code_insee"] or "", "groupe": None,
                 "href": f"/{lang}/territoires/{e['code']}"} for e in q.entites(con, niveau)]
    if jeu == "comptes":
        return [{"key": n["code"], "nom": label(n["id"], lang)["texte"], "code": n["code"], "groupe": None, "noeud": n["id"],
                 "href": f"/{lang}/serie?dom=apu&ind={n['code']}"}
                for n in con.execute("SELECT * FROM noeud WHERE nomenclature_id = 'apu_agregats' ORDER BY id")]
    total = q.noeud(con, "cofog", "TOTAL")
    out = []
    for d in q.children(con, total["id"]):
        if niveau == "fonction":
            out.append({"key": d["code"], "nom": label(d["id"], lang)["texte"], "code": d["code"], "groupe": None,
                        "noeud": d["id"], "href": f"/{lang}/?f={d['code']}#carte"})
        else:
            g = label(d["id"], lang)["texte"]
            out += [{"key": s["code"], "nom": label(s["id"], lang)["texte"], "code": s["code"], "groupe": g,
                     "noeud": s["id"], "href": f"/{lang}/depenses-publiques?fonction={d['code']}#zoom"}
                    for s in q.children(con, d["id"])]
    return out


def valeurs(jeu: str, niveau: str, col: dict[str, Any], lignes: list[dict[str, Any]], unite: str,
            annees: tuple[int, ...]) -> dict[tuple[str, int], list[Any]]:
    """{(clé de ligne, année): [montants publiés]} pour une colonne. Plusieurs montants = plusieurs lignes publiées."""
    out: dict[tuple[str, int], list[Any]] = {}
    ans = ",".join("?" * len(annees))
    if jeu == "collectivites":
        rows = con.execute(
            f"""SELECT e.code k, m.id, m.exercice, m.valeur, m.provisoire FROM montant m JOIN entite e ON e.id=m.entite_id
                WHERE m.noeud_id=? AND m.mesure=? AND m.unite=? AND e.niveau=? AND m.stade='compte' AND m.exercice IN ({ans})""",
            (col["noeud"], col["mesure"], unite, niveau, *annees))
    else:
        ids = [l["noeud"] for l in lignes]
        rows = con.execute(
            f"""SELECT n.code k, m.id, m.exercice, m.valeur, m.provisoire FROM montant m JOIN entite e ON e.id=m.entite_id
                JOIN noeud n ON n.id=m.noeud_id WHERE e.code=? AND m.mesure=? AND m.unite=? AND m.stade='compte'
                AND m.exercice IN ({ans}) AND m.noeud_id IN ({','.join('?' * len(ids))})""",
            (col["entite"], NOMENCLATURE[jeu][1], unite, *annees, *ids))
    for r in rows:
        out.setdefault((r["k"], r["exercice"]), []).append(r)
    return out


def annees_disponibles(jeu: str, niveau: str, cols: list[dict[str, Any]], unite: str) -> list[int]:
    if jeu == "collectivites":
        ids = [c["noeud"] for c in cols]
        rows = con.execute(
            f"""SELECT DISTINCT m.exercice FROM montant m JOIN entite e ON e.id=m.entite_id WHERE e.niveau=? AND m.unite=?
                AND m.stade='compte' AND m.noeud_id IN ({','.join('?' * len(ids))})""", (niveau, unite, *ids))
    else:
        rows = con.execute(
            """SELECT DISTINCT exercice FROM montant m JOIN noeud n ON n.id=m.noeud_id WHERE n.nomenclature_id=?
               AND m.unite=? AND m.stade='compte' AND m.mesure=?""", (NOMENCLATURE[jeu][0], unite, NOMENCLATURE[jeu][1]))
    return sorted(r[0] for r in rows)


def cellule(ms: list[Any] | None, u: str, lang: str) -> dict[str, Any]:
    if not ms:
        return {"v": None, "f": "—", "etat": "absent"}
    if len(ms) > 1:
        return {"v": None, "f": translations(lang).gettext("%(n)s lignes") % {"n": len(ms)}, "etat": "multi",
                "ids": [m["id"] for m in ms]}
    m = ms[0]
    return {"v": m["valeur"], "f": nombre(m["valeur"], u, lang), "etat": "ok", "id": m["id"], "prov": bool(m["provisoire"])}


def lire(p: dict[str, str], lang: str) -> dict[str, Any]:
    jeu = p.get("jeu", "collectivites")
    if jeu not in JEUX:
        raise HTTPException(404)
    niveau = p.get("niveau", NIVEAUX[jeu][0])
    unite = p.get("unite", UNITES[jeu][0])
    if niveau not in NIVEAUX[jeu] or unite not in UNITES[jeu]:
        raise HTTPException(404)
    possibles = {c["key"]: c for c in colonnes_possibles(jeu, niveau, lang)}
    # Colonnes inconnues ignorées (elles viennent d'un autre niveau ou d'un autre jeu) ; aucune : colonnes par défaut.
    keys = [k for k in dict.fromkeys(p.get("cols", "").split(",")) if k in possibles][:COLS_MAX] \
        or [k for k in DEFAUT_COLS[jeu] if k in possibles]
    cols = [possibles[k] for k in keys]
    annees = annees_disponibles(jeu, niveau, cols, unite)
    if not annees:
        raise HTTPException(404)
    annee = int(p["annee"]) if p.get("annee", "").isdigit() and int(p["annee"]) in annees else annees[-1]
    ref = int(p["ref"]) if p.get("ref", "").isdigit() and int(p["ref"]) in annees and int(p["ref"]) != annee else None
    sens = p.get("sens", "desc") if p.get("sens") in ("asc", "desc") else "desc"
    tri = p.get("tri", "")
    if tri != "nom" and not (tri[:2] in ("v:", "d:") and tri[2:] in keys and (tri[0] == "v" or ref)):
        tri = f"v:{keys[0]}"
    return {"jeu": jeu, "niveau": niveau, "unite": unite, "keys": keys, "cols": cols, "possibles": possibles,
            "annees": annees, "annee": annee, "ref": ref, "tri": tri, "sens": sens, "q": p.get("q", "").strip(),
            "groupe": p.get("groupe", ""), "sel": [s for s in p.get("sel", "").split(",") if s],
            "vue": "sel" if p.get("vue") == "sel" else "tout", "teinte": p.get("teinte") == "1",
            "bornes": {k: (p.get(f"min_{k}", ""), p.get(f"max_{k}", "")) for k in [f"v:{c}" for c in keys] + [f"d:{c}" for c in keys]
                       if p.get(f"min_{k}") or p.get(f"max_{k}")}}


def nombre_saisi(s: str) -> float | None:
    try:
        return float(s.replace(" ", "").replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def construire(e: dict[str, Any], lang: str) -> dict[str, Any]:
    u = e["unite"]
    lignes = lignes_possibles(e["jeu"], e["niveau"], lang)
    annees = (e["annee"],) + ((e["ref"],) if e["ref"] else ())
    for c in e["cols"]:
        vals = valeurs(e["jeu"], e["niveau"], c, lignes, u, annees)
        for l in lignes:
            cell = cellule(vals.get((l["key"], e["annee"])), u, lang)
            if e["ref"]:
                r = cellule(vals.get((l["key"], e["ref"])), u, lang)
                cell["ref"] = r
                cell["d"], cell["df"] = ecart(cell["v"], r["v"], u, lang, montant=e["jeu"] == "comptes")
            l.setdefault("cells", {})[c["key"]] = cell
    # Une ligne sans aucune valeur sur les colonnes choisies est listée à part, pas en tête ni en queue de tri.
    vides = [l for l in lignes if all(x["etat"] == "absent" for x in l["cells"].values())]
    lignes = [l for l in lignes if l not in vides]
    groupes = sorted({l["groupe"] for l in lignes if l["groupe"]})

    def garde(l: dict[str, Any]) -> bool:
        if e["vue"] == "sel" and l["key"] not in e["sel"]:
            return False
        if e["q"] and e["q"].casefold() not in f"{l['nom']} {l['code']}".casefold():
            return False
        if e["groupe"] and l["groupe"] != e["groupe"]:
            return False
        for k, (lo, hi) in e["bornes"].items():
            kind, col = k.split(":", 1)
            v = l["cells"][col]["v" if kind == "v" else "d"] if col in l["cells"] else None
            lo_, hi_ = nombre_saisi(lo) if lo else None, nombre_saisi(hi) if hi else None
            if v is None or (lo_ is not None and v < lo_) or (hi_ is not None and v > hi_):
                return False
        return True

    visibles = [l for l in lignes if garde(l)]

    def cle(l: dict[str, Any]):
        if e["tri"] == "nom":
            return (0, l["nom"].casefold())
        kind, col = e["tri"].split(":", 1)
        v = l["cells"].get(col, {}).get("v" if kind == "v" else "d")
        return (0, v) if v is not None else (1, 0)

    if e["tri"] == "nom":
        visibles.sort(key=cle, reverse=e["sens"] == "desc")
    else:
        avec = [l for l in visibles if cle(l)[0] == 0]
        sans = [l for l in visibles if cle(l)[0] == 1]
        avec.sort(key=lambda l: cle(l)[1], reverse=e["sens"] == "desc")
        visibles = avec + sans  # sans valeur : toujours en bas
    # Rang dans l'ordre du tri, puis les lignes épinglées remontent en tête (elles gardent leur rang).
    for i, l in enumerate(visibles, start=1):
        l["rang"] = i
    visibles = [l for l in visibles if l["key"] in e["sel"]] + [l for l in visibles if l["key"] not in e["sel"]]
    stats = {}
    for c in e["cols"]:
        for kind in ("v", "d") if e["ref"] else ("v",):
            xs = [l["cells"][c["key"]][kind] for l in visibles if l["cells"][c["key"]].get(kind) is not None]
            stats[f"{kind}:{c['key']}"] = {"med": median(xs), "min": min(xs), "max": max(xs), "n": len(xs)} if xs else None
    return {"lignes": visibles, "total": len(lignes), "vides": vides, "groupes": groupes, "stats": stats}


def lien(lang: str, e: dict[str, Any], **change: Any) -> str:
    p = {"jeu": e["jeu"], "niveau": e["niveau"], "unite": e["unite"], "cols": ",".join(e["keys"]), "annee": e["annee"],
         "ref": e["ref"], "tri": e["tri"], "sens": e["sens"], "q": e["q"], "groupe": e["groupe"],
         "sel": ",".join(e["sel"]), "vue": e["vue"] if e["vue"] == "sel" else None, "teinte": "1" if e["teinte"] else None}
    if not change.pop("sans_filtres", False):
        for k, (lo, hi) in e["bornes"].items():
            p[f"min_{k}"], p[f"max_{k}"] = lo, hi
    else:
        p.update({"q": None, "groupe": None, "vue": None})
    p.update(change)
    p = {k: v for k, v in p.items() if v not in (None, "", [])}
    return f"/{lang}/comparer?{urlencode(p)}"


@app.get("/{lang}/comparer", response_class=HTMLResponse)
def comparer(request: Request, lang: str):
    e = lire(dict(request.query_params), lang)
    t = construire(e, lang)
    _ = translations(lang).gettext
    u = e["unite"]
    vmax = {c["key"]: max((abs(l["cells"][c["key"]]["v"]) for l in t["lignes"] if l["cells"][c["key"]]["v"] is not None),
                          default=0) for c in e["cols"]}
    notes = []
    if u in ("EUR", "EUR_HAB", "MIO_EUR"):
        notes.append(_("Montants en euros courants : l'inflation n'est pas déduite."))
    if u == "PC_TOT":
        notes.append(_("Part publiée par Eurostat, en pourcentage des dépenses totales du périmètre de la colonne."))
    if e["ref"] and e["jeu"] != "collectivites":
        notes.append(_("Le contexte institutionnel liste qui exerçait les fonctions gouvernementales et les textes budgétaires votés entre ces deux années ; il ne dit pas ce qui explique l'écart."))
    if any(c.get("nomen") in ("f57", "f52") for c in e["cols"]):
        notes.append(_("Les fonctions M52 et M57 relèvent de deux nomenclatures différentes : chaque département publie dans l'une ou l'autre, elles ne se comparent pas entre elles."))
    if any(x["etat"] == "multi" for l in t["lignes"] for x in l["cells"].values()) or \
            any(x.get("ref", {}).get("etat") == "multi" for l in t["lignes"] for x in l["cells"].values()):
        notes.append(_("« n lignes » : le fichier publie plusieurs budgets sous ce code pour cette année. Ce site ne les additionne pas ; le lien ouvre les lignes publiées."))
    from api import colonnes as k  # importé ici : api.colonnes importe api.main, comme ce module
    onglets = k.panneaux(list(e["possibles"].values()), set(e["keys"]), e["annee"], _) if e["jeu"] == "collectivites" else None
    groupes_cols: dict[str, list[dict[str, Any]]] = {}
    for c in e["possibles"].values():
        groupes_cols.setdefault(c["groupe"] or "", []).append(c)
    contexte_href = f"/{lang}/contexte?de={min(e['annee'], e['ref'])}&a={max(e['annee'], e['ref'])}" if e["ref"] else None
    return render(request, lang, "comparer.html", e=e, t=t, vmax=vmax, notes=notes, groupes_cols=groupes_cols,
                  onglets=onglets, icone=k.icone,
                  contexte_href=contexte_href,
                  sources=sources_de([i for l in t["lignes"] for x in l["cells"].values()
                                      for c in (x, x.get("ref") or {}) for i in ([c["id"]] if c.get("id") else c.get("ids", []))]),
                  unite_courte=unite_courte(u, lang), lien=lambda **c: lien(lang, e, **c),
                  sans_filtres=lien(lang, e, sans_filtres=True),
                  reinit=lien(lang, e, sans_filtres=True, sel=None, tri=None, sens=None),
                  csv_href=lien(lang, e).replace("/comparer?", "/comparer.csv?"),
                  nombre=lambda v: nombre(v, u, lang), symbole=symbole(u, lang), unites=[(x, unite_courte(x, lang)) for x in UNITES[e["jeu"]]],
                  base_url=str(request.base_url).rstrip("/"))


@app.get("/{lang}/comparer.csv")
def comparer_csv(request: Request, lang: str):
    """Les lignes affichées (mêmes filtres, même tri), une ligne par cellule, avec la référence de chaque montant."""
    e = lire(dict(request.query_params), lang)
    t = construire(e, lang)
    base = str(request.base_url).rstrip("/")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["rang", "cle", "nom", "colonne", "unite", "annee", "valeur", "provisoire", "montant_id", "source",
                "annee_ref", "valeur_ref", "montant_id_ref", "ecart_calcul_du_site"])
    for i, l in enumerate(t["lignes"], start=1):
        for c in e["cols"]:
            x = l["cells"][c["key"]]
            r = x.get("ref", {})
            w.writerow([i, l["key"], l["nom"], c["texte"], e["unite"], e["annee"], x["v"] if x["v"] is not None else "",
                        int(bool(x.get("prov"))), x.get("id", ";".join(map(str, x.get("ids", [])))),
                        f"{base}/{lang}/montant/{x['id']}" if x.get("id") else "",
                        e["ref"] or "", r.get("v") if r.get("v") is not None else "", r.get("id", ""),
                        "" if x.get("d") is None else round(x["d"], 4)])
    return Response(buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="comptes-publics-comparaison.csv"'})
