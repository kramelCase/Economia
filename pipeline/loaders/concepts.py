"""Lexique : concepts de content/concepts.yaml (INSEE collecté, Légifrance relevé) + agrégats OFGL."""

from __future__ import annotations

import html
import json
import re
import unicodedata

import yaml

from pipeline.catalog import ROOT
from pipeline.db import Builder
from pipeline.rawio import iter_records

CONCEPTS_FILE = ROOT / "content" / "concepts.yaml"
INSEE_MARKERS = {"fr": "Définition", "en": "Definition"}
SECTION_END = ("<h2", "<h3", "</section>", "</main>", "<script")
SHARE_BLOCK = {"fr": "Partager", "en": "Share"}
BLOCK_TAGS = re.compile(r"</?(p|li|ul|ol|div|br|h\d)[^>]*>", re.I)


def extract_insee(page: str, lang: str) -> str:
    """Texte de la définition : entre le titre « Définition » et « Voir aussi », balises retirées."""
    start = INSEE_MARKERS[lang]
    i = page.find(f">{start}<")
    if i < 0:
        raise ValueError(f"titre « {start} » introuvable")
    after_heading = page.find(">", i + len(start) + 2) + 1   # saute la balise fermante du titre
    # La définition s'arrête au titre suivant (« Voir aussi », « Concept plus générique »...) ou à la fin de section.
    ends = [k for k in (page.find(t, after_heading) for t in SECTION_END) if k > 0]
    if not ends:
        raise ValueError("fin de définition introuvable")
    seg = page[after_heading: min(ends)]
    seg = BLOCK_TAGS.sub("\n", seg)
    seg = html.unescape(re.sub(r"<[^>]+>", "", seg))
    seg = seg.replace("­", "")              # césures conditionnelles invisibles
    paras = [re.sub(r"\s+", " ", p).strip() for p in seg.split("\n")]
    paras = [p for p in paras if p]
    if SHARE_BLOCK[lang] in paras:               # boutons de partage de la page, pas du texte
        paras = paras[: paras.index(SHARE_BLOCK[lang])]
    text = "\n\n".join(paras)
    if len(text) < 40:
        raise ValueError("définition vide ou trop courte")
    return text


def texte_html(s: str) -> str:
    """Texte d'une description HTML publiée : balises retirées, espaces normalisés."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _alias(b: Builder, cid: str, lang: str, aliases: list[str]) -> None:
    for a in aliases:
        b.con.execute("INSERT OR IGNORE INTO concept_alias VALUES (?,?,?)", (cid, lang, a))


def load(b: Builder) -> None:
    data = yaml.safe_load(CONCEPTS_FILE.read_text(encoding="utf-8"))
    for c in data["concepts"]:
        cid, terme = c["id"], c["terme"]
        if c.get("insee"):
            b.con.execute("INSERT INTO concept VALUES (?, 'cite')", (cid,))
            for lang in ("fr", "en"):
                fic = b.fichier("insee_definitions", f"{c['insee']}.{lang}.html")
                text = extract_insee(fic.path.read_text(encoding="utf-8"), lang)
                b.con.execute(
                    "INSERT INTO concept_traduction (concept_id, langue, terme, definition, statut, source_url,"
                    " source_titre, fichier_id) VALUES (?,?,?,?,?,?,?,?)",
                    (cid, lang, terme[lang], text, "officielle",
                     f"https://www.insee.fr/{lang}/metadonnees/definition/{c['insee']}", "INSEE, définition", fic.id))
        elif c.get("metadonnees"):
            m = c["metadonnees"]
            fic = b.fichier(m["source"], "dataset.json")
            meta = json.loads(fic.path.read_text(encoding="utf-8"))
            if m.get("champ"):  # description publiée d'un champ du jeu
                desc = next(x["description"] for x in meta["fields"] if x["name"] == m["champ"])
            else:
                desc = texte_html(meta["metas"]["default"]["description"])
            i = desc.find(m["debut"])
            if i < 0:
                raise ValueError(f"{cid} : « {m['debut']} » absent des métadonnées de {m['source']}")
            phrase = desc[i:desc.index(".", i) + 1] if "." in desc[i:] else desc[i:]
            src = b.sources[m["source"]]
            b.con.execute("INSERT INTO concept VALUES (?, 'cite')", (cid,))
            b.con.execute(
                "INSERT INTO concept_traduction (concept_id, langue, terme, definition, statut, source_url,"
                " source_titre, fichier_id) VALUES (?,?,?,?,?,?,?,?)",
                (cid, "fr", terme["fr"], phrase, "officielle", f"{src.portail}/explore/dataset/{src.dataset}/",
                 f"{src.editeur} : description du champ « {m['champ']} » du jeu « {src.dataset} »" if m.get("champ")
                 else f"{src.editeur} : description du jeu « {src.dataset} »", fic.id))
            b.con.execute("INSERT INTO concept_traduction (concept_id, langue, terme, statut)"
                          " VALUES (?,?,?, 'non_officielle')", (cid, "en", terme["en"]))
        elif c.get("releve"):
            r = c["releve"]
            b.con.execute("INSERT INTO concept VALUES (?, 'cite')", (cid,))
            releve = f"{r['date']} : {r['methode']}"
            b.con.execute(
                "INSERT INTO concept_traduction (concept_id, langue, terme, definition, statut, source_url,"
                " source_titre, releve) VALUES (?,?,?,?,?,?,?,?)",
                (cid, "fr", terme["fr"], r["fr"], "officielle", r["url"], r["titre"], releve))
            if r.get("en"):
                b.con.execute(
                    "INSERT INTO concept_traduction (concept_id, langue, terme, definition, statut, source_url,"
                    " source_titre, releve) VALUES (?,?,?,?,?,?,?,?)",
                    (cid, "en", terme["en"], r["en"], "non_officielle", r["url"], r["titre"],
                     releve + " Traduction non officielle du texte français."))
        else:
            b.con.execute("INSERT INTO concept VALUES (?, 'a_sourcer')", (cid,))
            for lang in ("fr", "en"):
                b.con.execute("INSERT INTO concept_traduction (concept_id, langue, terme, statut)"
                              " VALUES (?,?,?, 'non_officielle')", (cid, lang, terme[lang]))
        for lang, aliases in (c.get("alias") or {}).items():
            _alias(b, cid, lang, aliases)

    # Agrégats OFGL : définition officielle française (pas de version anglaise publiée).
    f = b.fichier("ofgl_definitions_agregats")
    for ligne, r in iter_records(f.path):
        if not r["commentaire"].strip():
            continue
        cid = f"ofgl_{slug(r['agregat'])}"
        b.con.execute("INSERT INTO concept VALUES (?, 'cite')", (cid,))
        b.con.execute(
            "INSERT INTO concept_traduction (concept_id, langue, terme, definition, statut, source_url,"
            " source_titre, fichier_id, ligne_source) VALUES (?,?,?,?,?,?,?,?,?)",
            (cid, "fr", r["agregat"], r["commentaire"].strip(), "officielle",
             "https://data.ofgl.fr/explore/dataset/methodologie-ofgl-definitions-agregats-financiers/",
             "OFGL, Méthodologie - définitions des agrégats financiers", f.id, ligne))
        _alias(b, cid, "fr", [r["agregat"]])
