"""Documents officiels cités par le site : chaque champ est relevé dans un fichier collecté, jamais saisi à la main.

Pour chaque source, un document « jeu » (titre officiel, éditeur, identifiant, dates) et, quand l'éditeur en publie,
la page officielle et la fiche de métadonnées. Les liens sont prouvés par la collecte : la page officielle collectée
doit citer le fichier ou le code du jeu, sinon la construction échoue.

- Opendatasoft (data.economie.gouv.fr, data.ofgl.fr) : `dataset.json` (métadonnées du portail) + page du jeu.
- Eurostat : catalogue officiel `toc.xml` (titre FR/EN, date de mise à jour des données, lien des métadonnées) + fiche
  de métadonnées ESMS ; nomenclatures : structure SDMX de la liste de codes.
- Assemblée nationale : page de téléchargement (elle donne le lien du fichier) + date du fichier (en-tête Last-Modified).
- INSEE : page des définitions et chaque définition citée par le lexique.
"""

from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

from pipeline.db import Builder, Fichier

NT = "{urn:eu.europa.ec.eurostat.navtree}"
SDMX_S = "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure}"
SDMX_C = "{http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common}"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def texte(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def titre_html(path: Path) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", path.read_text(encoding="utf-8", errors="replace"), re.S)
    if not m:
        raise ValueError(f"{path} : pas de <title>")
    return texte(m.group(1))


def premier_paragraphe(h: str) -> str | None:
    m = re.search(r"<p[^>]*>(.*?)</p>", h or "", re.S)
    t = texte(m.group(1)) if m else texte(h or "")
    return t or None


def jour_fr(d: str) -> str:
    """21.10.2026 -> 2026-10-21 (format du catalogue Eurostat)."""
    j, m, a = d.strip().split(".")
    return f"{a}-{m}-{j}"


class Docs:
    def __init__(self, b: Builder):
        self.b = b

    def ajouter(self, source_id: str, role: str, f: Fichier, releve: str, *, titre: str, identifiant: str, url: str,
                titre_en: str | None = None, editeur: str | None = None, date_publication: str | None = None,
                date_maj: str | None = None, extrait: str | None = None, extrait_lang: str | None = None) -> None:
        if not (titre and identifiant and url):
            raise ValueError(f"{source_id}/{role} : titre, identifiant et adresse obligatoires")
        self.b.con.execute(
            """INSERT INTO document (source_id, role, titre, titre_en, editeur, identifiant, date_publication, date_maj,
               url, extrait, extrait_lang, fichier_id, releve) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (source_id, role, titre, titre_en, editeur, identifiant, date_publication, date_maj, url, extrait,
             extrait_lang, f.id, releve))

    def page(self, sid: str, cite: str, quoi: str) -> tuple[Fichier, str]:
        """Page officielle collectée ; elle doit citer `cite` (chemin du fichier ou code du jeu)."""
        f = self.b.fichier(sid, "page.html")
        contenu = f.path.read_text(encoding="utf-8", errors="replace")
        self.b.controle(f"Page officielle de « {sid} » : elle cite {quoi}", sid, 1.0, float(cite in contenu), 0.0,
                        f"recherché dans la page collectée : {cite}")
        url = json.loads((f.path.parent / "meta.json").read_text(encoding="utf-8"))
        url = next(x["url"] for x in url["fichiers"] if x["nom"] == "page.html")
        return f, url

    def editeur(self, sid: str, publie: str) -> None:
        """L'éditeur affiché (sources.yaml) est, au caractère près, celui que publient les métadonnées."""
        affiche = self.b.sources[sid].editeur
        self.b.controle(f"Éditeur de « {sid} » identique aux métadonnées publiées", sid, 1.0,
                        float(publie == affiche), 0.0, f"publié : {publie} ; affiché : {affiche}")


def url_de(f: Fichier) -> str:
    meta = json.loads((f.path.parent / "meta.json").read_text(encoding="utf-8"))
    return next(x["url"] for x in meta["fichiers"] if x["nom"] == f.path.name)


def paragraphe(path: Path, motif: str) -> str | None:
    """Premier paragraphe (ou ligne de texte) de la page qui contient `motif`, cité tel quel."""
    t = path.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"<(p|li)[^>]*>(.*?)</\1>", t, re.S):
        x = texte(m.group(2))
        if motif in x:
            return x
    return None


def licence_eurostat(d: Docs, sid: str) -> None:
    """Conditions de réutilisation publiées par Eurostat (page « Copyright notice and free re-use of data »)."""
    f = d.b.fichier(sid, "copyright.html")
    clause = paragraphe(f.path, "Reuse of statistical data")
    d.b.controle(f"Licence de « {sid} » relevée dans la page de réutilisation d'Eurostat", sid, 1.0, float(bool(clause)), 0.0)
    d.ajouter(sid, "licence", f, "copyright.html : <title> ; paragraphe « Reuse of statistical data… »",
              titre=titre_html(f.path), identifiant="help/copyright-notice", url=url_de(f), editeur="Eurostat",
              extrait=clause, extrait_lang="en")


def toc(b: Builder) -> tuple[Fichier, dict[str, dict]]:
    f = b.fichier("eurostat_catalogue", "toc.xml")
    out: dict[str, dict] = {}
    for leaf in ET.parse(f.path).getroot().iter(f"{NT}leaf"):
        code = leaf.findtext(f"{NT}code")
        if not code or code in out:
            continue
        titres = {t.get("language"): (t.text or "").strip() for t in leaf.findall(f"{NT}title")}
        sources = {t.get("language"): (t.text or "").strip() for t in leaf.findall(f"{NT}source")}
        meta = next((m.text for m in leaf.findall(f"{NT}metadata") if m.get("format") == "html"), None)
        out[code] = {"fr": titres.get("fr"), "en": titres.get("en"), "maj": leaf.findtext(f"{NT}lastUpdate"),
                     "structure": leaf.findtext(f"{NT}lastModified"), "source": sources.get("fr") or sources.get("en"),
                     "meta": meta}
    return f, out


def esms(path: Path, ancre: str) -> str | None:
    """Premier(s) paragraphe(s) d'une rubrique de la fiche ESMS (ancre name="data_descr"...)."""
    t = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf'name="{ancre}"></a>[^<]*</h3>(.*?)(?:<h3|</div>)', t, re.S)
    if not m:
        return None
    paras = [texte(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), re.S)]
    return " ".join(p for p in paras if p) or None


def ods(d: Docs, sid: str) -> None:
    b = d.b
    src = b.sources[sid]
    f = b.fichier(sid, "dataset.json")
    j = json.loads(f.path.read_text(encoding="utf-8"))
    m, dc = j["metas"]["default"], j["metas"].get("dcat") or {}
    pf, purl = d.page(sid, src.dataset, f"l'identifiant du jeu ({src.dataset})")
    d.ajouter(sid, "jeu", f, "dataset.json : metas.default.title, publisher, modified, description ; metas.dcat.created",
              titre=m["title"], identifiant=j["dataset_id"], url=purl, editeur=m.get("publisher"),
              date_publication=dc.get("created"), date_maj=(m.get("modified") or "")[:10] or None,
              extrait=premier_paragraphe(m.get("description") or ""), extrait_lang="fr")
    d.ajouter(sid, "page", pf, "page.html : <title>", titre=titre_html(pf.path), identifiant=src.dataset, url=purl)
    if m.get("license"):
        d.ajouter(sid, "licence", f, "dataset.json : metas.default.license, license_url", titre=m["license"],
                  identifiant=m["license"], url=m.get("license_url") or purl)
    else:  # rien n'est supposé : la licence absente des métadonnées est une lacune
        b.lacune("non_publie", f"Licence non publiée : {m['title']}",
                 "Le champ licence des métadonnées publiées de ce jeu est vide : ce site n'en affiche aucune.",
                 m.get("publisher") or src.editeur, f"dataset.json (metas.default.license) de la collecte {f.path.parent.name}",
                 source_id=sid, fichier_id=f.id)
    d.editeur(sid, ", ".join([m["publisher"], *(m.get("attributions") or [])]))


def eurostat_jeu(d: Docs, sid: str, cat: tuple[Fichier, dict]) -> None:
    b = d.b
    src = b.sources[sid]
    code = re.search(r"/data/([A-Za-z0-9_]+)/", src.url).group(1).lower()
    tf, t = cat
    e = t[code]
    b.controle(f"Fiche de métadonnées de « {sid} » = lien publié par le catalogue Eurostat", sid, 1.0,
               float(e["meta"] == src.extra.get("page")), 0.0, f"catalogue : {e['meta']} ; collecté : {src.extra.get('page')}")
    fiche = e["meta"].rsplit("/", 1)[1].removesuffix("_esms.htm")  # une fiche peut couvrir plusieurs jeux (gov_10dd)
    pf, purl = d.page(sid, f"({fiche})", f"le code de sa fiche ({fiche})")
    d.ajouter(sid, "jeu", tf, f"toc.xml : nt:leaf[nt:code={code}] nt:title (fr, en), nt:lastUpdate, nt:source, nt:metadata",
              titre=e["fr"], titre_en=e["en"], identifiant=code, url=e["meta"], editeur=e["source"],
              date_maj=jour_fr(e["maj"]))
    d.ajouter(sid, "metadonnees", pf, "page.html : <title>, rubriques 3.1 « Data description » et 3.6 « Statistical population »",
              titre=titre_html(pf.path), identifiant=code, url=purl,
              extrait=" ".join(x for x in (esms(pf.path, "data_descr"), esms(pf.path, "stat_pop")) if x) or None,
              extrait_lang="en")
    d.editeur(sid, e["source"])
    licence_eurostat(d, sid)


def eurostat_liste(d: Docs, sid: str) -> None:
    b = d.b
    f = b.fichier(sid, "structure.xml")
    cl = next(ET.parse(f.path).getroot().iter(f"{SDMX_S}Codelist"))
    noms = {n.get(XML_LANG): n.text for n in cl.findall(f"{SDMX_C}Name")}
    maj = next((a.findtext(f"{SDMX_C}AnnotationTitle") for a in cl.iter(f"{SDMX_C}Annotation")
                if a.findtext(f"{SDMX_C}AnnotationType") == "LAST_UPDATED"), None)
    url = json.loads((f.path.parent / "meta.json").read_text(encoding="utf-8"))
    url = next(x["url"] for x in url["fichiers"] if x["nom"] == "structure.xml")
    d.ajouter(sid, "jeu", f, "structure.xml : s:Codelist (id, version), c:Name (fr, en), annotation LAST_UPDATED",
              titre=noms.get("fr") or noms["en"], titre_en=noms.get("en"), identifiant=f"{cl.get('id')} v{cl.get('version')}",
              url=url, editeur="Eurostat", date_maj=(maj or "")[:10] or None)
    licence_eurostat(d, sid)


def assemblee(d: Docs, sid: str) -> None:
    b = d.b
    src = b.sources[sid]
    nom = src.extra["fichier"]
    f = b.fichier(sid, nom)
    chemin = urlparse(src.url).path
    pf, purl = d.page(sid, chemin, "le lien du fichier collecté")
    meta = json.loads((f.path.parent / "meta.json").read_text(encoding="utf-8"))
    lm = next(x for x in meta["fichiers"] if x["nom"] == nom)["http_headers"].get("last-modified")
    t = titre_html(pf.path)
    d.ajouter(sid, "jeu", pf, "page.html : <title> et lien du fichier ; en-tête HTTP Last-Modified du fichier",
              titre=re.sub(r"\s*-\s*Assemblée nationale\s*$", "", t), identifiant=chemin.split("/openData/repository/", 1)[-1], url=purl,
              editeur="Assemblée nationale" if "Assemblée nationale" in t else None,
              date_maj=parsedate_to_datetime(lm).date().isoformat() if lm else None)
    d.editeur(sid, "Assemblée nationale" if "Assemblée nationale" in t else t)
    m = re.search(r'<a href="([^"]*licence[^"]*)"[^>]*>([^<]*[Ll]icence[^<]*)</a>', pf.path.read_text(encoding="utf-8"))
    d.b.controle(f"Licence de « {sid} » relevée dans sa page officielle", sid, 1.0, float(bool(m)), 0.0)
    if m:
        d.ajouter(sid, "licence", pf, "page.html : lien de licence", titre=texte(m.group(2)), identifiant=m.group(1),
                  url=urljoin(purl, m.group(1)), editeur="Assemblée nationale")


def insee(d: Docs, sid: str) -> None:
    b = d.b
    pf, purl = d.page(sid, "definition/c", "des liens vers les définitions")
    t = titre_html(pf.path)
    contenu = pf.path.read_text(encoding="utf-8", errors="replace")
    d.ajouter(sid, "jeu", pf, "page.html : <title>", titre=t, identifiant="metadonnees/definitions", url=purl,
              editeur="Insee" if "Insee" in t else None)
    meta = json.loads((pf.path.parent / "meta.json").read_text(encoding="utf-8"))
    absentes = [x["nom"] for x in meta["fichiers"] if x["nom"].endswith(".fr.html")
                and f'definition/{x["nom"].split(".")[0]}"' not in contenu]
    b.controle("Chaque définition citée par le lexique figure dans la page des définitions de l'INSEE (absentes)", sid,
               0.0, float(len(absentes)), 0.0, ", ".join(absentes))
    for x in meta["fichiers"]:
        if x["nom"].endswith(".fr.html"):
            fd = b.fichier(sid, x["nom"])
            d.ajouter(sid, "reference", fd, f"{x['nom']} : <title>", titre=titre_html(fd.path),
                      identifiant=x["nom"].split(".")[0], url=x["url"], editeur="Insee")
    d.editeur(sid, "Insee" if "Insee" in t else t)
    fm = b.fichier(sid, "mentions.html")
    chemin = urlparse(url_de(fm)).path
    sans_lien = [x["nom"] for x in meta["fichiers"] if x["nom"].endswith(".fr.html")
                 and chemin not in b.fichier(sid, x["nom"]).path.read_text(encoding="utf-8", errors="replace")]
    b.controle("Chaque définition citée renvoie aux mentions légales de l'INSEE (pages sans ce lien)", sid,
               0.0, float(len(sans_lien)), 0.0, ", ".join(sans_lien))
    clause = paragraphe(fm.path, "Licence Ouverte")
    nom = re.search(r"Licence Ouverte / Open Licence version [\d.]+ \(Etalab\)", clause or "")
    b.controle("Licence de « insee_definitions » relevée dans les mentions légales de l'INSEE", sid, 1.0,
               float(bool(nom)), 0.0)
    d.ajouter(sid, "licence", fm, "mentions.html : paragraphe citant la Licence Ouverte",
              titre=nom.group(0) if nom else titre_html(fm.path), identifiant=chemin, url=url_de(fm), editeur="Insee",
              extrait=clause, extrait_lang="fr")


def insee_note(d: Docs, sid: str) -> None:
    """Une note publiée en PDF par l'INSEE : sa page (titre, lien du fichier), sa date (« Le 3 juin 2026 », en tête de
    la note) et la licence relevée dans les mentions légales, comme pour les définitions."""
    import pypdf
    b = d.b
    src = b.sources[sid]
    chemin = urlparse(src.url).path
    pf, purl = d.page(sid, chemin, "le lien du fichier collecté")
    f = b.fichier(sid, src.extra["fichier"])
    debut = re.sub(r"\s+", " ", pypdf.PdfReader(str(f.path)).pages[0].extract_text() or "")
    mois = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre",
            "décembre")
    m = re.search(r"Le (\d{1,2}) (" + "|".join(mois) + r") (\d{4})", debut)
    date = f"{m.group(3)}-{mois.index(m.group(2)) + 1:02d}-{int(m.group(1)):02d}" if m else None
    t = titre_html(pf.path)
    d.ajouter(sid, "jeu", pf, "note.pdf : date en tête de la note ; page.html : <title> et lien du fichier",
              titre=re.sub(r"\s*[|-]\s*Insee\s*$", "", t), identifiant=chemin, url=src.url,
              editeur="Insee" if "Insee" in t else None, date_maj=date)
    d.editeur(sid, "Insee" if "Insee" in t else t)
    fm = b.fichier(sid, "mentions.html")
    clause = paragraphe(fm.path, "Licence Ouverte")
    nom = re.search(r"Licence Ouverte / Open Licence version [\d.]+ \(Etalab\)", clause or "")
    b.controle(f"Licence de « {sid} » relevée dans les mentions légales de l'INSEE", sid, 1.0, float(bool(nom)), 0.0)
    d.ajouter(sid, "licence", fm, "mentions.html : paragraphe citant la Licence Ouverte",
              titre=nom.group(0) if nom else titre_html(fm.path), identifiant=urlparse(url_de(fm)).path, url=url_de(fm),
              editeur="Insee", extrait=clause, extrait_lang="fr")


def catalogue(d: Docs, sid: str, cat: tuple[Fichier, dict]) -> None:
    tf, t = cat
    racine = ET.parse(tf.path).getroot()
    cree = racine.findtext(f"{NT}creationDate")
    # Le fichier ne porte pas de titre : la citation est le nom exact du service d'Eurostat, tel qu'il figure dans l'adresse.
    d.ajouter(sid, "jeu", tf, "adresse du fichier ; toc.xml : nt:creationDate",
              titre=urlparse(d.b.sources[sid].url).path.split("/dissemination/", 1)[1], identifiant="catalogue/toc/xml",
              url=d.b.sources[sid].url, editeur="Eurostat", date_maj=(cree or "")[:10] or None)
    licence_eurostat(d, sid)


def load(b: Builder) -> None:
    d = Docs(b)
    cat = toc(b)
    for sid, src in b.sources.items():
        if src.type == "ods":
            ods(d, sid)
        elif src.type == "http_csv" and "/sdmx/2.1/data/" in src.url:
            eurostat_jeu(d, sid, cat)
        elif src.type == "http_csv" and "/codelist/" in src.url:
            eurostat_liste(d, sid)
        elif sid.startswith("an_"):
            assemblee(d, sid)
        elif src.type == "insee_definitions":
            insee(d, sid)
        elif sid == "insee_note_revisions":
            insee_note(d, sid)
        elif sid == "eurostat_catalogue":
            catalogue(d, sid, cat)
        else:
            raise ValueError(f"{sid} : aucune règle de relevé de document")
    b.con.execute("""UPDATE source SET titre = (SELECT d.titre || CASE WHEN substr(source.id, 1, 3) = 'an_'
                                                                THEN ' — ' || d.identifiant ELSE '' END
                                             FROM document d WHERE d.source_id = source.id AND d.role = 'jeu')
                     WHERE id IN (SELECT source_id FROM document WHERE role = 'jeu')""")
    sans = [r[0] for r in b.con.execute(
        """SELECT id FROM source WHERE id NOT IN (SELECT source_id FROM document WHERE role = 'jeu')
           OR (id NOT IN (SELECT source_id FROM document WHERE role = 'licence')
               AND id NOT IN (SELECT source_id FROM lacune WHERE titre LIKE 'Licence non publiée%'))""")]
    b.controle("Chaque source a son document officiel et sa licence relevés", "eurostat_catalogue",
               0.0, float(len(sans)), 0.0, ", ".join(sans))
