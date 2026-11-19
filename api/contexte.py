"""Contexte institutionnel d'une période : qui exerçait la présidence, la direction du gouvernement et les ministères
chargés des finances, quels textes budgétaires ont été soumis au vote de l'Assemblée et comment chaque groupe a voté,
et, pour chaque exercice, le solde et la dette publiés.

Tout vient de l'open data de l'Assemblée nationale et d'Eurostat. Ce module rapproche des faits datés ; il n'établit
aucun lien de cause entre une fonction, un vote et un montant. Importé à la fin de api/main.py.
"""

from __future__ import annotations

import json
import re
import zipfile
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from api import queries as q
from api.i18n import money, translations
from api.main import LANGS, app, con, label, render, source_info
from pipeline.catalog import ROOT

# Ministères retenus : ceux dont l'objet, d'après l'intitulé publié, porte sur les finances, le budget ou les comptes
# publics. L'objet est ce qui suit « chargé(e) de » ; sans cette mention, ce qui précède « auprès de ». Un secrétariat
# « auprès du ministre de l'économie et des finances, chargé du numérique » n'est donc pas retenu.
OBJET_FINANCES = re.compile(r"\b(finances|budget|comptes publics)\b", re.I)


def objet(libelle: str) -> str:
    m = re.search(r"\bchargée? (?:de la |de l'|du |des |de )?(.*)$", libelle, re.I)
    if m:
        return m.group(1)
    return re.split(r"\bauprès d", libelle, maxsplit=1, flags=re.I)[0]


def chevauche(debut: str | None, fin: str | None, de: int, a: int) -> bool:
    return (debut or "0000") <= f"{a}-12-31" and (fin or "9999") >= f"{de}-01-01"


def parti(personne: str, date: str) -> dict[str, str] | None:
    """Parti de rattachement publié à cette date, s'il existe (les députés seulement : voir les lacunes)."""
    r = con.execute(
        """SELECT o.libelle, f.id FROM fonction f JOIN organe o ON o.uid = f.organe_uid WHERE o.type = 'PARPOL'
           AND f.personne_uid = ? AND f.debut <= ? AND (f.fin IS NULL OR f.fin >= ?) ORDER BY f.debut DESC LIMIT 1""",
        (personne, date, date)).fetchone()
    return {"nom": r["libelle"], "preuve": f"fonction/{r['id']}"} if r else None


def presidences(de: int, a: int) -> list[dict[str, Any]]:
    rows = con.execute("SELECT * FROM organe WHERE type = 'PRESREP' ORDER BY debut").fetchall()
    return [{"nom": re.sub(r"^.*?:\s*(M\.|Mme)\s*", "", r["libelle"]), "libelle": r["libelle"], "debut": r["debut"],
             "fin": r["fin"], "uid": r["uid"], "preuve": f"organe/{r['uid']}"}
            for r in rows if chevauche(r["debut"], r["fin"], de, a)]


def fonctions(de: int, a: int, premier: bool) -> list[dict[str, Any]]:
    rows = con.execute(
        """SELECT f.*, p.nom, o.libelle FROM fonction f JOIN personne p ON p.uid = f.personne_uid
           JOIN organe o ON o.uid = f.organe_uid WHERE o.type = 'MINISTERE' ORDER BY f.debut, p.nom""").fetchall()
    out = []
    for r in rows:
        if not chevauche(r["debut"], r["fin"], de, a):
            continue
        if premier != (r["qualite"] == "Premier ministre"):
            continue
        if not premier and not OBJET_FINANCES.search(objet(r["libelle"])):
            continue
        out.append({"nom": r["nom"], "qualite": r["qualite"], "libelle": r["libelle"], "debut": r["debut"],
                    "fin": r["fin"], "parti": parti(r["personne_uid"], r["debut"]), "preuve": f"fonction/{r['id']}"})
    return out


def reperes(de: int, a: int) -> list[dict[str, Any]]:
    """Débuts de présidence dans la période, pour les traits verticaux des graphiques."""
    out = []
    for p in presidences(de, a):
        an = int(p["debut"][:4])
        if de <= an <= a:
            jour = (int(p["debut"][5:7]) - 1) * 30.5 + int(p["debut"][8:10])
            out.append({"an": an, "frac": round(jour / 366, 3), "t": p["nom"], "date": p["debut"]})
    return out


def scrutins(de: int, a: int) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = {}
    for s in con.execute("""SELECT s.*, fi.source_id, l.titre_dossier, l.code_loi, l.titre_loi, l.date_jo, l.num_jo,
                                   l.nor, l.url_legifrance, lf.source_id loi_source
                            FROM scrutin s JOIN fichier fi ON fi.id = s.fichier_id
                            LEFT JOIN loi l ON l.dossier_uid = s.dossier_uid LEFT JOIN fichier lf ON lf.id = l.fichier_id
                            WHERE s.exercice BETWEEN ? AND ? ORDER BY s.exercice, s.date, s.numero""", (de, a)):
        groupes = [dict(g) for g in con.execute(
            """SELECT g.*, o.libelle, o.abrege FROM scrutin_groupe g JOIN organe o ON o.uid = g.groupe_uid
               WHERE g.scrutin_uid = ? ORDER BY g.membres DESC""", (s["uid"],))]
        out.setdefault(s["exercice"], []).append({**dict(s), "groupes": groupes, "href": s["page_url"]})
    return out


def comptes(lang: str, de: int, a: int) -> dict[int, dict[str, Any]]:
    """Solde et dette publiés de l'ensemble des administrations publiques, en part du PIB, par exercice."""
    out: dict[int, dict[str, Any]] = {}
    for code in ("B9", "GD"):
        n = q.noeud(con, "apu_agregats", code)
        for r in q.series_provenance(con, n["id"], "APU-S13", "compte", "agregat", "PC_GDP"):
            if de <= r["exercice"] <= a:
                out.setdefault(r["exercice"], {})[code] = {"f": money(r["valeur"], lang, "PC_GDP"), "id": r["id"],
                                                          "prov": bool(r["provisoire"]), "nom": label(n["id"], lang)["texte"]}
    return out


def bornes() -> tuple[int, int]:
    r = con.execute("SELECT MIN(exercice), MAX(exercice) FROM montant m JOIN noeud n ON n.id = m.noeud_id "
                    "WHERE n.nomenclature_id = 'apu_agregats'").fetchone()
    return r[0], r[1]


def enregistrement(chemin: str, entree: str) -> Any:
    """L'enregistrement tel que publié, relu dans l'archive collectée (chemin du JSON, ou chemin#numéro)."""
    nom, _, numero = entree.partition("#")
    with zipfile.ZipFile(ROOT / chemin) as z:
        d = json.loads(z.read(nom))
    if numero and "scrutins" in d:  # XIVe législature : tous les scrutins dans un seul fichier
        return next(s for s in d["scrutins"]["scrutin"] if s["numero"] == numero)
    if numero and "export" in d:  # idem pour les dossiers législatifs
        return next(x for x in d["export"]["dossiersLegislatifs"]["dossier"] if x["dossierParlementaire"]["uid"] == numero)
    return d


def extrait_dossier(d: dict) -> dict:
    """Du dossier : son titre, l'acte de promulgation (n°, JO, NOR, Légifrance) et les scrutins qu'il cite, tels quels."""
    from pipeline.loaders.assemblee import parcourir, votes_cites
    d = d.get("dossierParlementaire", d)
    acte = next((x for x in parcourir(d) if x.get("codeLoi")), None)
    return {"uid": d["uid"], "titreDossier": d["titreDossier"], "acte de promulgation": acte,
            "voteRef cités": sorted(votes_cites(d))}


def allege(s: dict) -> dict:
    """Scrutin sans les listes nominatives (le décompte par groupe et la synthèse restent intacts)."""
    s = json.loads(json.dumps(s))
    for g in s.get("ventilationVotes", {}).get("organe", {}).get("groupes", {}).get("groupe", []):
        g.get("vote", {}).pop("decompteNominatif", None)
    return s


@app.get("/{lang}/preuve/{genre}/{cle}", response_class=HTMLResponse)
def preuve(request: Request, lang: str, genre: str, cle: str):
    if genre == "organe":
        r = con.execute("SELECT * FROM organe WHERE uid=?", (cle,)).fetchone()
    elif genre == "fonction" and cle.isdigit():
        r = con.execute("""SELECT f.*, p.nom, o.libelle FROM fonction f JOIN personne p ON p.uid=f.personne_uid
                           JOIN organe o ON o.uid=f.organe_uid WHERE f.id=?""", (int(cle),)).fetchone()
    elif genre == "scrutin":
        r = con.execute("SELECT * FROM scrutin WHERE uid=?", (cle,)).fetchone()
    elif genre == "loi":
        r = con.execute("SELECT * FROM loi WHERE dossier_uid=?", (cle,)).fetchone()
    else:
        r = None
    if r is None:
        raise HTTPException(404)
    fi = con.execute("SELECT * FROM fichier WHERE id=?", (r["fichier_id"],)).fetchone()
    d = enregistrement(fi["chemin"], r["entree"])
    if genre == "fonction":  # dans la fiche de la personne, le seul mandat cité
        d = next(m for m in (lambda x: x if isinstance(x, list) else [x])(d["acteur"]["mandats"]["mandat"])
                 if r["organe_uid"] in json.dumps(m["organes"]) and m.get("dateDebut") == r["debut"])
    elif genre == "scrutin":
        d = allege(d.get("scrutin", d))
    elif genre == "loi":
        d = extrait_dossier(d)
    else:
        d = d.get("organe", d)
    return render(request, lang, "preuve.html", genre=genre, r=dict(r), fi=fi, info=source_info(fi["source_id"]),
                  brut=json.dumps(d, ensure_ascii=False, indent=1)[:20000],
                  officiel=r["page_url"] if genre == "scrutin" else r["url_legifrance"] if genre == "loi" else None)


@app.get("/{lang}/contexte", response_class=HTMLResponse)
def contexte(request: Request, lang: str, de: str = "", a: str = ""):
    if lang not in LANGS:
        raise HTTPException(404)
    lo, hi = bornes()
    d = int(de) if de.isdigit() else hi - 9
    f = int(a) if a.isdigit() else hi
    d, f = max(lo, min(d, f)), min(hi, max(d, f))
    premier_vote = con.execute("SELECT MIN(exercice) FROM scrutin").fetchone()[0]
    votes = scrutins(d, f)
    annees = list(range(d, f + 1))
    _ = translations(lang).gettext
    sources_votes = sorted({r[0] for r in con.execute(
        """SELECT fi.source_id FROM scrutin s JOIN fichier fi ON fi.id=s.fichier_id WHERE s.exercice BETWEEN ? AND ?
           UNION SELECT lf.source_id FROM scrutin s JOIN loi l ON l.dossier_uid = s.dossier_uid
           JOIN fichier lf ON lf.id = l.fichier_id WHERE s.exercice BETWEEN ? AND ?""", (d, f, d, f))})
    return render(request, lang, "contexte.html", de=d, a=f, lo=lo, hi=hi, annees=annees, sources_votes=sources_votes,
                  presidences=presidences(d, f), premiers=fonctions(d, f, True), ministres=fonctions(d, f, False),
                  votes=votes, comptes=comptes(lang, d, f), premier_vote=premier_vote,
                  lf_sans_vote=[x for x in annees if x >= premier_vote and not any(v["texte"] == "lf" for v in votes.get(x, []))],
                  periodes=[(_("10 dernières années"), hi - 9, hi), (_("Toute la période"), lo, hi)])
