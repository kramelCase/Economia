"""Collecte brute immuable : raw/<source>/<horodatage>/ + meta.json.

Rien n'est transformé ici. `meta.json` liste chaque fichier téléchargé avec son URL exacte, son
sha256 et les en-têtes HTTP : c'est la preuve qu'un chiffre affiché vient bien de ce fichier.

Usage : python -m pipeline.fetch [id_source ...]
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx
import yaml

from pipeline.catalog import RAW_DIR, ROOT, Source, load_sources

TIMEOUT = httpx.Timeout(60.0, read=600.0)
KEPT_HEADERS = ("content-type", "last-modified", "etag", "date", "content-length")
CONCEPTS_FILE = ROOT / "content" / "concepts.yaml"
INSEE_LANGS = ("fr", "en")
PAGE_SCRUTIN = "https://www.assemblee-nationale.fr/dyn/{leg}/scrutins/{num}"


def ods_export_url(src: Source) -> str:
    params = {"delimiter": ";", "use_labels": "false"}
    if src.where:
        params["where"] = src.where
    return f"{src.portail}/api/explore/v2.1/catalog/datasets/{src.dataset}/exports/csv?{urlencode(params)}"


def ods_meta_url(src: Source) -> str:
    return f"{src.portail}/api/explore/v2.1/catalog/datasets/{src.dataset}"


def insee_definition_url(code: str, lang: str) -> str:
    return f"https://www.insee.fr/{lang}/metadonnees/definition/{code}"


def insee_codes() -> list[str]:
    data = yaml.safe_load(CONCEPTS_FILE.read_text(encoding="utf-8"))
    return [c["insee"] for c in data["concepts"] if c.get("insee")]


def _download(client: httpx.Client, url: str, dest: Path) -> dict:
    h = hashlib.sha256()
    size = 0
    with client.stream("GET", url) as r:
        r.raise_for_status()
        headers = {k: r.headers[k] for k in KEPT_HEADERS if k in r.headers}
        with dest.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
                h.update(chunk)
                size += len(chunk)
    return {"nom": dest.name, "url": url, "sha256": h.hexdigest(), "octets": size, "http_headers": headers}


def planned_downloads(src: Source) -> list[tuple[str, str]]:
    """(nom de fichier, URL) à télécharger pour une source."""
    if src.type == "ods":
        return [("data.csv", ods_export_url(src))]
    if src.type == "http_csv":
        return [("data.csv", src.url)]
    if src.type == "http_file":  # archive publiée telle quelle (ex. open data de l'Assemblée nationale)
        return [(src.extra["fichier"], src.url)]
    if src.type == "insee_definitions":
        return [(f"{code}.{lang}.html", insee_definition_url(code, lang))
                for code in insee_codes() for lang in INSEE_LANGS]
    raise ValueError(f"type inconnu : {src.type}")


def page_officielle(src: Source) -> str | None:
    """Page de l'éditeur qui présente le jeu ; collectée avec lui, elle prouve le lien (elle cite le fichier ou le code)."""
    if src.extra.get("page"):
        return src.extra["page"]
    if src.type == "ods":
        return f"{src.portail}/explore/dataset/{src.dataset}/"
    return None


def planned_extras(src: Source) -> list[tuple[str, str]]:
    """Page officielle (page.html) et métadonnées publiées à côté du jeu (`annexes` : nom -> URL)."""
    out = [("page.html", u)] if (u := page_officielle(src)) else []
    return out + list((src.extra.get("annexes") or {}).items())


def fetch_source(src: Source, client: httpx.Client) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    snap = RAW_DIR / src.id / stamp
    snap.mkdir(parents=True, exist_ok=False)

    if src.type == "ods":
        r = client.get(ods_meta_url(src))
        r.raise_for_status()
        (snap / "dataset.json").write_text(json.dumps(r.json(), ensure_ascii=False, indent=2), encoding="utf-8")
        data = (snap / "dataset.json").read_bytes()
        fichiers = [{"nom": "dataset.json", "url": ods_meta_url(src), "sha256": hashlib.sha256(data).hexdigest(),
                     "octets": len(data), "http_headers": {}}]
    else:
        fichiers = []
    for name, url in planned_downloads(src):
        fichiers.append(_download(client, url, snap / name))
        if src.type == "insee_definitions":
            time.sleep(0.5)  # politesse envers le site de l'INSEE
    for name, url in planned_extras(src):
        fichiers.append(_download(client, url, snap / name))
    if src.extra.get("pages_scrutins"):  # scrutins retenus par le chargeur, lus dans l'archive qui vient d'être collectée
        from pipeline.loaders.assemblee import classer, iter_scrutins
        for _, s in iter_scrutins(zipfile.ZipFile(snap / src.extra["fichier"])):
            if classer(s["titre"]):
                num = int(s["numero"])
                fichiers.append(_download(client, PAGE_SCRUTIN.format(leg=int(s["legislature"]), num=num),
                                          snap / f"scrutin_{num}.html"))
                time.sleep(0.5)  # politesse envers le site de l'Assemblée
    meta = {"source_id": src.id, "fetched_at": stamp, "type": src.type, "where": src.where or None,
            "fichiers": fichiers}
    (snap / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return snap


REPRISES = 4  # Eurostat répond 429 (trop de requêtes) quand on enchaîne les collectes : on attend puis on réessaie.


def _avec_reprise(src: Source, client: httpx.Client) -> Path:
    for essai in range(1, REPRISES + 1):
        try:
            return fetch_source(src, client)
        except (httpx.HTTPStatusError, httpx.TransportError) as e:
            code = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else None
            if essai == REPRISES or (code is not None and code != 429 and code < 500):
                raise
            attente = 20 * essai
            print(f"... {src.id} : {code or type(e).__name__}, nouvel essai dans {attente} s", file=sys.stderr)
            time.sleep(attente)
    raise AssertionError("inaccessible")


def main(argv: list[str]) -> int:
    sources = load_sources()
    if argv:
        wanted = set(argv)
        unknown = wanted - {s.id for s in sources}
        if unknown:
            print(f"sources inconnues : {sorted(unknown)}", file=sys.stderr)
            return 2
        sources = [s for s in sources if s.id in wanted]
    failures = 0
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True,
                      headers={"User-Agent": "comptes-publics/0.1 (transparence finances publiques)"}) as client:
        for src in sources:
            try:
                snap = _avec_reprise(src, client)
                meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
                total = sum(f["octets"] for f in meta["fichiers"])
                print(f"OK  {src.id:34} {len(meta['fichiers']):3} fichier(s) {total / 1e6:8.1f} Mo  "
                      f"{snap.relative_to(RAW_DIR.parent)}")
            except Exception as e:  # noqa: BLE001 - on continue les autres sources
                failures += 1
                print(f"ERR {src.id:34} {e}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
