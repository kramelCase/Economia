"""Sources : lacunes, lexique, méthode, fiche d'une source, et la provenance d'un chiffre jusqu'à la ligne du fichier.

Détaché de api/main.py. Importé à la fin de api/main.py, avant api/portes.py.
"""

from __future__ import annotations

import json

from fastapi import HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from api import queries as q
from api.i18n import translations
from api.main import app, con, concepts_index, label, render, source_info
from pipeline.catalog import ROOT
from pipeline.rawio import iter_records


# --- Lacunes, lexique, méthode ---
@app.get("/{lang}/lacunes", response_class=HTMLResponse)
def lacunes(request: Request, lang: str):
    rows = q.lacunes(con)
    catalogue = [l for l in rows if l["fichier_id"] is None]
    lignes = [l for l in rows if l["fichier_id"] is not None]
    par_type: dict[str, int] = {}
    for l in lignes:
        par_type[l["type"]] = par_type.get(l["type"], 0) + 1
    return render(request, lang, "lacunes.html", catalogue=catalogue, lignes=lignes, par_type=par_type,
                  sources_lignes=sorted({l["source_id"] for l in lignes if l["source_id"]}))


@app.get("/{lang}/lexique", response_class=HTMLResponse)
def lexique(request: Request, lang: str):
    items = list(concepts_index(lang).values())
    items.sort(key=lambda c: c["terme"].lower())
    return render(request, lang, "lexique.html", items=items,
                  a_sourcer=[c for c in items if c["statut"] == "a_sourcer"])


@app.get("/{lang}/source/{sid}", response_class=HTMLResponse)
def source_page(request: Request, lang: str, sid: str):
    s = con.execute("SELECT * FROM source WHERE id=?", (sid,)).fetchone()
    if s is None:
        raise HTTPException(404)
    return render(request, lang, "source.html", s=s, info=source_info(sid), fichiers=q.fichiers(con, sid),
                  nb=con.execute("SELECT COUNT(*) FROM montant m JOIN fichier fi ON fi.id=m.fichier_id WHERE fi.source_id=?",
                                 (sid,)).fetchone()[0])


@app.get("/{lang}/methode", response_class=HTMLResponse)
def methode(request: Request, lang: str):
    srcs = [{"s": s, "fichiers": q.fichiers(con, s["id"])} for s in q.sources(con)]
    controles = q.controles(con)
    return render(request, lang, "methode.html", sources=srcs, controles=controles,
                  sources_controles=sorted({c["source_id"] for c in controles}))


# --- Provenance : d'un chiffre affiché jusqu'à la ligne du fichier officiel ---
def raw_record(chemin: str, ligne: int, has_header: bool = True) -> dict[str, str] | None:
    path = ROOT / chemin
    for n, rec in iter_records(path, has_header):
        if n == ligne:
            return rec
    return None


@app.get("/{lang}/montant/{montant_id}", response_class=HTMLResponse)
def montant(request: Request, lang: str, montant_id: int):
    m = q.montant_detail(con, montant_id)
    if m is None:
        raise HTTPException(404)
    no_header = m["source_id"].startswith("eurostat_cofog_libelles")
    rec = raw_record(m["chemin"], m["ligne_source"], not no_header)
    from api.colonnes import icone
    _ = translations(lang).gettext
    unites = {"MIO_EUR": _("millions d'euros"), "EUR": _("euros"), "EUR_HAB": _("euros par habitant"),
              "PC_GDP": _("pour cent du PIB"), "PC_TOT": _("pour cent du total")}
    return render(request, lang, "montant.html", m=m, rec=rec, attributs=json.loads(m["attributs"] or "{}"),
                  label=label(m["noeud_id"], lang), icone=icone, unite_brute=unites.get(m["unite"], m["unite"]))


@app.get("/{lang}/provenance/noeud/{noeud_id}", response_class=HTMLResponse)
def provenance_noeud(request: Request, lang: str, noeud_id: int, entite: str, exercice: int, stade: str,
                     mesure: str, unite: str):
    f = q.Filtre(entite, exercice, stade, mesure, unite)
    v, n, prov = q.total(con, noeud_id, f)
    rows = q.contributions(con, noeud_id, f)
    return render(request, lang, "provenance.html", label=label(noeud_id, lang), total=v, nb=n, rows=rows, f=f,
                  ent=q.entite(con, entite))


@app.get("/{lang}/provenance", response_class=HTMLResponse)
def provenance_ids(request: Request, lang: str, ids: str = Query(...)):
    id_list = [int(x) for x in ids.split(",") if x.isdigit()][:500]
    rows = [q.montant_detail(con, i) for i in id_list]
    rows = [r for r in rows if r is not None]
    if not rows:
        raise HTTPException(404)
    return render(request, lang, "provenance.html", label=label(rows[0]["noeud_id"], lang),
                  total=sum(r["valeur"] for r in rows), nb=len(rows), rows=rows, f=None, ent=None)
