"""Vie institutionnelle, d'après l'open data de l'Assemblée nationale.

Retenu : la présidence de la République, les ministères et leurs titulaires (qualité publiée), les groupes et les
partis politiques, et les scrutins publics sur l'ensemble d'un texte budgétaire (loi de finances, rectificative ou de
fin de gestion, loi de règlement ou d'approbation des comptes, loi de financement de la sécurité sociale), avec la
position de chaque groupe. Le type de texte et l'exercice viennent du titre publié du scrutin, par une règle unique
(TEXTES ci-dessous) ; un titre qui ne la suit pas n'est pas retenu.
"""

from __future__ import annotations

import json
import re
import zipfile
from collections.abc import Iterator
from typing import Any

from pipeline.db import Builder

ORGANES = ("PRESREP", "GOUVERNEMENT", "MINISTERE", "GP", "PARPOL", "ASSEMBLEE")
QUALITES_EXCLUES = ("en mission",)  # députés chargés d'une mission auprès d'un ministre : pas membres du gouvernement
# Titre publié -> (type de texte, exercice). L'« ensemble du projet » seulement : ni une partie, ni un article.
TEXTES = (
    (re.compile(r"^l'ensemble du projet de loi de finances rectificative pour (\d{4})", re.I), "lfr"),
    (re.compile(r"^l'ensemble du projet de loi de finances de fin de gestion pour (\d{4})", re.I), "lfr"),
    (re.compile(r"^l'ensemble du projet de loi de finances pour (\d{4})", re.I), "lf"),
    (re.compile(r"^l'ensemble du projet de loi de financement de la sécurité sociale rectificative pour (\d{4})", re.I), "lfssr"),
    (re.compile(r"^l'ensemble du projet de loi de financement de la sécurité sociale pour (\d{4})", re.I), "lfss"),
    (re.compile(r"^l'ensemble du projet de loi (?:de règlement du budget et d'approbation des comptes|relative aux résultats "
                r"de la gestion et portant approbation des comptes) de l'année (\d{4})", re.I), "reglement"),
    (re.compile(r"^l'ensemble du projet de loi d'approbation des comptes de la sécurité sociale (?:pour|de) l'année (\d{4})", re.I), "acss"),
)
LECTURE = re.compile(r"\(([^()]*(?:lecture|commission mixte paritaire|commission paritaire)[^()]*)\)", re.I)


def liste(x: Any) -> list:
    return [] if x is None else x if isinstance(x, list) else [x]


def entier(x: Any) -> int:
    return int(x) if x not in (None, "") else 0


def voix(d: dict, cle: str) -> int:
    """Décompte publié ; la XIVe législature écrit « abstention » au singulier."""
    return entier(d.get(cle, d.get(cle.rstrip("s"))))


def classer(titre: str) -> tuple[str, int] | None:
    for motif, texte in TEXTES:
        m = motif.match(titre.strip())
        if m:
            return texte, int(m.group(1))
    return None


def page_scrutin(fi, s: dict, pages: dict[str, str]) -> str | None:
    """URL de la page d'analyse collectée avec l'archive, si son titre et son contenu prouvent qu'elle est celle du scrutin."""
    nom = f"scrutin_{int(s['numero'])}.html"
    p = fi.path.parent / nom
    if nom not in pages or not p.is_file():
        return None
    t = p.read_text(encoding="utf-8", errors="replace")
    titre = re.search(r"<title>([^<]*)", t)
    attendu = f"Analyse du scrutin n°{int(s['numero'])} - {int(s['legislature'])}e législature"
    return pages[nom] if titre and titre.group(1).startswith(attendu) and s["uid"] in t else None


def iter_scrutins(z: zipfile.ZipFile) -> Iterator[tuple[str, dict]]:
    for name in z.namelist():
        if not name.endswith(".json"):
            continue
        d = json.loads(z.read(name))
        if "scrutins" in d:  # XIVe législature : un seul fichier
            for s in liste(d["scrutins"]["scrutin"]):
                yield f"{name}#{s['numero']}", s
        else:
            yield name, d["scrutin"]


def iter_dossiers(z: zipfile.ZipFile) -> Iterator[tuple[str, dict]]:
    for name in z.namelist():
        if not name.endswith(".json"):
            continue
        d = json.loads(z.read(name))
        if "export" in d:  # XIVe législature : un seul fichier
            for x in liste(d["export"]["dossiersLegislatifs"]["dossier"]):
                yield f"{name}#{x['dossierParlementaire']['uid']}", x["dossierParlementaire"]
        elif "dossierParlementaire" in d:
            yield name, d["dossierParlementaire"]


def parcourir(x: Any) -> Iterator[dict]:
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from parcourir(v)
    elif isinstance(x, list):
        for v in x:
            yield from parcourir(v)


def promulgation(dossier: dict) -> dict:
    """Loi promulguée telle que publiée dans le dossier (n°, titre, JO, NOR, lien Légifrance), ou vide."""
    for x in parcourir(dossier):
        if x.get("codeLoi"):
            jo = x.get("infoJO") or {}
            return {"code": x["codeLoi"], "titre": x.get("titreLoi"), "date_jo": (jo.get("dateJO") or "")[:10] or None,
                    "num_jo": jo.get("numJO"), "nor": jo.get("referenceNOR") or x.get("referenceNOR"),
                    "url": jo.get("urlLegifrance") or x.get("urlLegifrance")}
    return {}


def votes_cites(dossier: dict) -> set[str]:
    out: set[str] = set()
    for x in parcourir(dossier):
        for r in liste(x.get("voteRef")):
            if isinstance(r, str):
                out.add(r)
    return out


def load_dossiers(b: Builder) -> None:
    """Relie chaque scrutin retenu au dossier législatif qui le cite, et ce dossier à la loi promulguée."""
    retenus = {r[0] for r in b.con.execute("SELECT uid FROM scrutin")}
    lies: dict[str, str] = {}
    for leg in (14, 15, 16, 17):
        fi = b.fichier(f"an_dossiers_{leg}", "dossiers.zip")
        for entree, d in iter_dossiers(zipfile.ZipFile(fi.path)):
            cites = votes_cites(d) & retenus
            if not cites:
                continue
            p = promulgation(d)
            b.con.execute("INSERT INTO loi VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          (d["uid"], leg, d["titreDossier"]["titre"], p.get("code"), p.get("titre"), p.get("date_jo"),
                           p.get("num_jo"), p.get("nor"), p.get("url"), fi.id, entree))
            for v in cites:
                lies.setdefault(v, d["uid"])
    b.con.executemany("UPDATE scrutin SET dossier_uid = ? WHERE uid = ?", [(d, v) for v, d in lies.items()])
    # Un scrutin qu'aucun dossier ne cite (et dont la référence législative publiée est vide) reste sans loi : c'est
    # une lacune de la source, pas un rapprochement à faire par le titre.
    for (uid, fid, entree, ex) in b.con.execute(
            "SELECT uid, fichier_id, entree, exercice FROM scrutin WHERE dossier_uid IS NULL").fetchall():
        b.con.execute(
            """INSERT INTO lacune (type, titre, description, responsable, constat, source_id, fichier_id, exercice)
               VALUES ('non_publie', ?, ?, 'Assemblée nationale', ?,
                       (SELECT source_id FROM fichier WHERE id = ?), ?, ?)""",
            (f"Scrutin {uid} : dossier législatif non publié",
             "Aucun dossier législatif de l'open data ne cite ce scrutin (voteRef), et sa référence législative publiée "
             "est vide : ce site ne peut pas le relier à une loi.",
             f"Entrée {entree} du fichier des scrutins ; dossiers législatifs des XIVe à XVIIe législatures", fid, fid, ex))


def load(b: Builder) -> None:
    amo = b.fichier("an_acteurs_organes", "amo.zip")
    z = zipfile.ZipFile(amo.path)
    organes: dict[str, dict] = {}
    for name in z.namelist():
        if "/organe/" in name:
            o = json.loads(z.read(name))["organe"]
            if o["codeType"] in ORGANES:
                organes[o["uid"]] = o
                v = o.get("viMoDe") or {}
                b.con.execute("INSERT INTO organe VALUES (?,?,?,?,?,?,?,?)",
                              (o["uid"], o["codeType"], o["libelle"], o.get("libelleAbrev") or o.get("libelleAbrege"),
                               v.get("dateDebut"), v.get("dateFin"), amo.id, name))

    gouvernants = set()
    fonctions = []
    personnes = {}
    for name in z.namelist():
        if "/acteur/" not in name:
            continue
        a = json.loads(z.read(name))["acteur"]
        ident = a["etatCivil"]["ident"]
        uid = a["uid"]["#text"] if isinstance(a["uid"], dict) else a["uid"]
        for m in liste(a.get("mandats", {}).get("mandat")):
            if m["typeOrgane"] not in ("PRESREP", "MINISTERE", "PARPOL"):
                continue
            org = liste(m["organes"]["organeRef"])[0]
            qualite = (m.get("infosQualite") or {}).get("codeQualite")
            if org not in organes or qualite in QUALITES_EXCLUES or not m.get("dateDebut"):
                continue
            personnes[uid] = (f"{ident['prenom']} {ident['nom']}", name)
            if m["typeOrgane"] != "PARPOL":
                gouvernants.add(uid)
            fonctions.append((uid, org, qualite, m["dateDebut"], m.get("dateFin"), m["typeOrgane"], name))
    for uid, (nom, name) in personnes.items():
        b.con.execute("INSERT INTO personne VALUES (?,?,?,?)", (uid, nom, amo.id, name))
    # Rattachements à un parti : seulement pour les personnes qui ont exercé une fonction gouvernementale.
    b.con.executemany("INSERT INTO fonction (personne_uid, organe_uid, qualite, debut, fin, fichier_id, entree)"
                      " VALUES (?,?,?,?,?,?,?)",
                      [(u, o, q, d, f, amo.id, n) for u, o, q, d, f, t, n in fonctions if t != "PARPOL" or u in gouvernants])

    retenus = 0
    groupes_inconnus = set()
    sans_page: list[str] = []
    for sid in ("an_scrutins_14", "an_scrutins_15", "an_scrutins_16", "an_scrutins_17"):
        fi = b.fichier(sid, "scrutins.zip")
        pages = {x["nom"]: x["url"] for x in json.loads((fi.path.parent / "meta.json").read_text(encoding="utf-8"))["fichiers"]}
        for entree, s in iter_scrutins(zipfile.ZipFile(fi.path)):
            c = classer(s["titre"])
            if c is None:
                continue
            lec = LECTURE.search(s["titre"])
            dec = s["syntheseVote"]["decompte"]
            page = page_scrutin(fi, s, pages)
            if page is None:
                sans_page.append(s["uid"])
            b.con.execute("INSERT INTO scrutin VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,?)",
                          (s["uid"], int(s["legislature"]), int(s["numero"]), s["dateScrutin"], s["titre"].strip(),
                           s["sort"]["code"], c[0], c[1], lec.group(1) if lec else None,
                           entier(s["syntheseVote"].get("nombreVotants")), voix(dec, "pour"), voix(dec, "contre"),
                           voix(dec, "abstentions"), fi.id, entree, page))
            retenus += 1
            for g in liste(s["ventilationVotes"]["organe"]["groupes"]["groupe"]):
                if g["organeRef"] not in organes:
                    groupes_inconnus.add(g["organeRef"])
                    continue
                v = g["vote"]
                d = v["decompteVoix"]
                b.con.execute("INSERT INTO scrutin_groupe VALUES (?,?,?,?,?,?,?,?)",
                              (s["uid"], g["organeRef"], entier(g.get("nombreMembresGroupe")), v.get("positionMajoritaire"),
                               voix(d, "pour"), voix(d, "contre"), voix(d, "abstentions"), voix(d, "nonVotants")))
    # Bouclage : pour chaque scrutin, la somme des voix des groupes = le décompte publié du scrutin.
    rows = b.con.execute("""SELECT s.uid, s.pour, s.contre, SUM(g.pour) gp, SUM(g.contre) gc FROM scrutin s
                            JOIN scrutin_groupe g ON g.scrutin_uid = s.uid GROUP BY s.uid""").fetchall()
    pire = max((abs(r["pour"] - r["gp"]) + abs(r["contre"] - r["gc"]) for r in rows), default=0)
    b.controle("Scrutins budgétaires : voix des groupes = décompte publié (pire écart, en voix)", "an_scrutins_15",
               0.0, float(pire), 0.0,
               f"{retenus} scrutins retenus ; groupes absents du référentiel : {len(groupes_inconnus)}")
    b.controle("Scrutins retenus dont la page d'analyse collectée ne porte pas le numéro et l'identifiant (lien non affiché)",
               "an_scrutins_17", 0.0, float(len(sans_page)), 0.0, ", ".join(sans_page))
    load_dossiers(b)
