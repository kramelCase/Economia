"""Interface : toutes les pages répondent en FR et EN, aucun terme technique n'est laissé sans lien,
toute chaîne est traduite, toute traduction non officielle est signalée."""

import re

import pytest

from pipeline.db import DB_PATH

pytestmark = pytest.mark.skipif(not DB_PATH.exists(), reason="lancer `make build` d'abord")

PAGES = ["", "bases", "bases/1", "bases/2", "bases/3", "bases/4", "bases/5", "bases/6", "verifier", "atelier", "territoires?nom=seine", "territoires?nom=zzqx", "verifier?n=3000+milliards&mot=dette", "verifier?n=5,8+%25&annee=2024", "verifier?n=abc", "verifier?n=1200+%E2%82%AC+par+habitant&mot=Gironde", "donnees", "comparer", "comparer?niveau=region&ref=2012&teinte=1", "comparer?jeu=fonctions&niveau=sous-fonction&ref=2014&unite=MIO_EUR", "?f=GF10&unite=MIO_EUR", "?secteur=S1313&annee=2000&unite=PC_GDP", "depenses-publiques", "recettes-publiques", "recettes-publiques?secteur=S1313&annee=2001&categorie=D5REC", "depenses-publiques?secteur=S1313&annee=2015&fonction=GF07", "budget-etat",
         "budget-etat?vue=0", "depenses-fiscales", "depenses-fiscales?annee=2024",
         "depenses-fiscales?impot=Taxe%20sur%20la%20valeur%20ajout%C3%A9e", "territoires",
         "territoires?niveau=region&indicateur=Encours%20de%20dette&unite=EUR", "territoires?indicateur=f57:4",
         "territoires?indicateur=f52:5&annee=2020", "territoires/REG-84", "territoires/DEP-69", "territoires/DEP-75",
         "lacunes", "lexique", "methode", "mentions", "theme", "theme/enseignement", "differences", "montant/1", "sources", "explorer?theme=GF09&qui=S13",
         "explorer?theme=GF07&qui=S1313", "explorer?theme=GF09&qui=ETAT", "explorer?theme=depenses-fiscales&qui=S13", "recherche?q=gironde", "recherche?q=zzzz", "serie", "serie?dom=ofgl", "serie?ind=GF09&forme=aires&unite=MIO_EUR", "serie?dom=ofgl&qui=REG-84,REG-11&forme=barres&unite=EUR",
         "serie?dom=apu", "serie?quand=annee", "serie?dom=ofgl&qui=@departement&quand=annee&annee=2020", "serie?dom=apu&ind=TR,TE&quand=annee&forme=tableau", "serie?dom=apu&ind=B9&qui=S13,S1311,S1313,S1314&quand=annee", "serie?dom=apu&ind=B9,GD&unite=MIO_EUR&reperes=1&de=2005", "comparer?jeu=comptes&ref=2016",
         "comparer?jeu=comptes&unite=MIO_EUR&ref=2019&tri=d:S13", "contexte", "contexte?de=1995&a=2025", "contexte?de=2017&a=2018", "grands-equilibres", "grands-equilibres?annee=2009"]


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api.main import app
    return TestClient(app)


@pytest.mark.parametrize("lang", ["fr", "en"])
@pytest.mark.parametrize("page", PAGES)
def test_page_repond_et_relie_les_termes(client, lang, page):
    from api.lexique import unlinked_terms
    from api.main import linker

    r = client.get(f"/{lang}/{page}")
    assert r.status_code == 200
    pattern, _ = linker(lang)
    restants = unlinked_terms(r.text, pattern)
    assert restants == [], f"termes non reliés au lexique : {sorted(set(restants))[:10]}"


def test_chaque_chiffre_porte_sa_source(client):
    r = client.get("/fr/depenses-publiques")
    assert r.text.count('class="src"') >= 20


def test_traductions_completes():
    from babel.messages.extract import extract_from_dir
    from babel.messages.pofile import read_po

    from pipeline.catalog import ROOT

    method_map = [("api/**.py", "python"), ("templates/**.html", "jinja2")]
    options = {"templates/**.html": {"extensions": "jinja2.ext.i18n"}}
    ids = {msg for _, _, msg, _, _ in extract_from_dir(str(ROOT), method_map, options) if isinstance(msg, str)}
    with (ROOT / "locales/en/LC_MESSAGES/messages.po").open("rb") as f:
        cat = read_po(f)
    traduits = {m.id for m in cat if m.id and m.string}
    assert sorted(ids - traduits) == []


def test_traduction_non_officielle_signalee(client):
    from api import queries as q
    from api.main import con

    nb = con.execute("""SELECT COUNT(*) FROM concept_traduction WHERE langue='en' AND statut='non_officielle'
                        AND definition IS NOT NULL""").fetchone()[0]
    assert nb > 0
    page = client.get("/en/lexique").text
    assert page.count("Unofficial translation. Original text:") == nb
    assert len(q.concepts(con, "en")) == con.execute("SELECT COUNT(*) FROM concept").fetchone()[0]


def test_lacunes_visibles(client):
    page = client.get("/fr/depenses-fiscales").text
    assert "non chiffrées" in page


def test_zoom_mission_et_camemberts(client):
    """Chaque anneau a sa légende (version lisible), chaque part son badge source ; le zoom d'une mission répond."""
    import re
    r = client.get("/fr/budget-etat")
    m = re.search(r'href="(\?vue=2&amp;mission=\d+)#zoom"', r.text)
    assert m, "lien de zoom vers une mission absent"
    z = client.get("/fr/budget-etat" + m.group(1).replace("&amp;", "&"))
    assert z.status_code == 200 and 'id="zoom"' in z.text
    for page in ("depenses-publiques", "budget-etat", "depenses-fiscales", "territoires/DEP-69"):
        t = client.get(f"/fr/{page}").text
        assert t.count('class="chart donut-chart"') >= 1
        legende = t.split('class="legend"')[1].split("</ul>")[0]
        assert legende.count('data-slot="') <= 6, "un anneau ne doit pas dépasser 6 segments"


def test_filtre_impot_inconnu(client):
    assert client.get("/fr/depenses-fiscales?impot=inexistant").status_code == 404


def test_explorer_reponse_sourcee_ou_lacune(client):
    import re

    r = client.get("/fr/explorer?theme=depenses-fiscales&qui=ETAT")
    hero = r.text.split('id="reponse"')[1].split('</section>')[0]
    assert "Md€" in hero and 'class="src"' in hero and "x-gap" in hero
    r = client.get("/fr/explorer?theme=GF09&qui=S13")
    hero = r.text.split('id="reponse"')[1].split('</section>')[0]
    assert len(re.findall(r'class="src" href="/fr/montant/\d+"', hero)) >= 2  # montant et part publiée
    # Combinaison non publiée : pas de chiffre, la raison et la question voisine.
    r = client.get("/fr/explorer?theme=GF09&qui=ETAT")
    hero = r.text.split('id="reponse"')[1].split('</section>')[0]
    assert "Pas de réponse" in hero and "Md€" not in hero and "qui=S13" in hero
    assert client.get("/fr/explorer?theme=XX").status_code == 404


def test_suggestions_portent_leur_chiffre(client):
    r = client.get("/fr/suggest", params={"q": "gironde"}).json()
    assert r[0]["t"] == "Gironde" and "€/hab." in r[0]["fig"] and r[0]["href"].startswith("/fr/territoires/")
    r = client.get("/fr/suggest", params={"q": "enseignement"}).json()
    assert r[0]["g"].startswith("Fonction") and r[0]["fig"].endswith("Md€")
    assert any(o.get("gap") for o in client.get("/fr/suggest", params={"q": "peac"}).json())
    assert client.get("/fr/suggest", params={"q": "cp"}).json()[0]["href"] == "/fr/lexique#cp"  # sigle exact en tête
    assert client.get("/fr/suggest", params={"q": ""}).json() == []
    assert len(client.get("/fr/suggest", params={"q": "e"}).json()) <= 10


def test_rubans_et_recherche_sans_js(client):
    r = client.get("/fr/explorer?theme=GF09&qui=S13")
    assert 'class="x-pause"' in r.text  # le défilement peut être arrêté (WCAG 2.2.2)
    assert 'aria-hidden="true"><a href="/fr/territoires/' in r.text  # le doublon du ruban est caché
    r = client.get("/fr/recherche", params={"q": "gironde"})
    assert "/fr/territoires/DEP-33" in r.text and "€/hab." in r.text


def test_serie_garde_fous_et_exports(client):
    import csv
    import io

    assert client.get("/fr/serie", params={"ind": "XX"}).status_code == 404
    assert client.get("/fr/serie", params={"dom": "ofgl", "unite": "PC_GDP"}).status_code == 404  # unité d'une autre source
    # Trois séries demandées en barres : la forme retombe sur la courbe (deux séries au plus).
    r = client.get("/fr/serie", params={"ind": "GF09,GF07,GF10", "forme": "barres"})
    assert '"forme": "courbe"' in r.text
    # Six combinaisons : cinq affichées, la sixième signalée.
    r = client.get("/fr/serie", params={"ind": "GF09,GF07,GF10", "qui": "S13,S1311"})
    assert "non affichée" in r.text
    rows = list(csv.DictReader(io.StringIO(client.get("/fr/serie.csv").text)))
    assert rows and all(r["fichier"] and r["sha256"] and r["ligne_source"] for r in rows)
    assert client.get("/fr/serie.json", params={"dom": "ofgl"}).json()["valeurs"]


def test_carte_accueil(client):
    r = client.get("/fr/")
    assert r.text.count('class="c-case"') == 10  # les dix fonctions COFOG
    # Chaque case figure dans le tableau jumeau avec son badge source.
    tableau = r.text.split('class="c-lignes"')[1].split("</ol>")[0]
    assert tableau.count('class="src"') == 10
    r = client.get("/fr/", params={"f": "GF10"})
    assert "← " in r.text and 'class="c-case is-feuille"' in r.text and 'class="c-fiche"' in r.text
    for bad in ({"f": "XX"}, {"f": "GF1001"}, {"secteur": "S1"}, {"unite": "EUR"}):
        assert client.get("/fr/", params=bad).status_code == 404


def test_comparer_tri_filtres_et_provenance(client):
    import csv
    import io

    r = client.get("/fr/comparer", params={"tri": "v:Frais de personnel", "sens": "asc", "q": "haute"})
    lignes = r.text.split("<tbody>")[1].split("</tbody>")[0]
    assert lignes.count("<tr data-key") >= 5 and all("haute" in n.lower() for n in
                                                     [x.split('data-nom="')[1].split('"')[0] for x in lignes.split("<tr ")[1:]])
    # Chaque valeur affichée est un lien vers son montant source.
    assert lignes.count('href="/fr/montant/') >= 4 * lignes.count("<tr data-key") - 4
    # Avant 2016, plusieurs budgets sous un même code régional : jamais additionnés, signalés.
    r = client.get("/fr/comparer", params={"niveau": "region", "annee": "2015"})
    assert 'class="k-multi"' in r.text and "ne les additionne pas" in r.text
    # Bornes : seules les lignes dans l'intervalle restent ; épinglées en tête.
    r = client.get("/fr/comparer", params={"min_v:Dépenses totales": "2000", "sel": "DEP-33"})
    corps = r.text.split("<tbody>")[1]
    assert corps.split('data-key="')[1].startswith("DEP-33") is False  # DEP-33 sous 2 000 €/hab. : filtré
    r = client.get("/fr/comparer", params={"sel": "DEP-33"})
    assert r.text.split("<tbody>")[1].split('data-key="')[1].startswith("DEP-33")
    rows = list(csv.DictReader(io.StringIO(client.get("/fr/comparer.csv", params={"ref": "2016"}).text)))
    assert rows and all(x["montant_id"] for x in rows if x["valeur"])
    assert client.get("/fr/comparer", params={"jeu": "x"}).status_code == 404


def test_socle_navigation_et_palette(client):
    r = client.get("/fr/lexique")
    # Quatre entrées dans le menu, la palette présente sur toutes les pages, son bouton utilisable sans JS.
    for entree in ("Accueil", "Thèmes", "Ma collectivité", "Sources"):
        assert f">{entree}</a>" in r.text
    assert '<dialog id="cmd"' in r.text and 'href="/fr/recherche" data-cmd-open' in r.text
    assert re.search(r'aria-current="page"><svg[^>]*>.*?</svg>Sources', r.text)  # le lexique est rangé sous « Sources »
    # Chaque objet trouvé porte ses actions : un territoire s'ouvre dans le comparateur, épinglé.
    hits = client.get("/fr/suggest", params={"q": "gironde"}).json()
    g = next(h for h in hits if h["t"] == "Gironde")
    assert {a["href"] for a in g["actions"]} >= {"/fr/comparer?niveau=departement&sel=DEP-33"}
    # Une fonction mène à sa fiche thématique, la carte reste une action.
    f = next(h for h in client.get("/fr/suggest", params={"q": "enseignement"}).json() if h["g"].startswith("Fonction"))
    assert f["href"] == "/fr/theme/enseignement" and "/fr/?f=GF09#carte" in {a["href"] for a in f["actions"]}


def test_contexte_faits_dates_sans_lien_de_cause(client):
    r = client.get("/fr/contexte", params={"de": 2018, "a": 2019})
    # Le vote de la loi de finances pour 2019, avec son scrutin et la position de chaque groupe, relié à l'Assemblée.
    assert "projet de loi de finances</a> pour 2019" in r.text
    assert "https://www.assemblee-nationale.fr/dyn/15/scrutins/1429" in r.text
    assert "Vote des groupes" in r.text
    assert "aucun lien de cause" in r.text
    # Solde et dette de chaque exercice, chacun avec sa source.
    assert r.text.count('class="src"') >= 4
    # Ministres retenus par l'objet publié du ministère : le budget oui, le numérique non.
    assert "Gérald Darmanin" in r.text and "Cédric O" not in r.text
    # Avant 2012, l'absence de scrutins publiés est dite, jamais remplacée.
    r = client.get("/fr/contexte", params={"de": 2005, "a": 2006})
    assert "non publiés dans les données ouvertes" in r.text and "Avant mai 2007" in r.text


def test_comptes_apu_solde_et_ecart_en_montant(client):
    from api.contexte import objet
    assert objet("Secrétariat d'État auprès du ministre de l'économie et des finances, chargé du numérique") == "numérique"
    assert "finances" in objet("Ministère de l'économie, des finances et de la relance")
    r = client.get("/fr/comparer", params={"jeu": "comptes", "unite": "MIO_EUR", "ref": 2019})
    # Un solde change de signe : l'écart est un montant, jamais un pourcentage.
    assert " Md€</" in r.text or "Md€" in r.text
    r = client.get("/fr/serie", params={"dom": "apu", "ind": "B9", "reperes": "1", "de": 2005})
    assert '"reperes": [' in r.text and "Emmanuel Macron" in r.text
    hits = client.get("/fr/suggest", params={"q": "darmanin"}).json()
    assert any(h["href"].startswith("/fr/contexte?de=") for h in hits)


def test_constructeur_une_annee(client):
    """Une année : chiffre, classement ou tableau ; les formes impossibles sont grisées avec leur raison écrite."""
    import csv
    import io
    r = client.get("/fr/serie", params={"dom": "ofgl", "qui": "@region", "quand": "annee"})
    assert r.status_code == 200 and 's-rank' in r.text
    assert "la plus élevée est celle de" in r.text  # phrase descriptive générée
    assert "Chiffre seul : Il faut un seul indicateur" in r.text  # raison écrite, pas seulement en infobulle
    assert client.get("/fr/serie", params={"quand": "annee", "forme": "courbe"}).status_code == 404  # forme d'une période
    assert client.get("/fr/serie", params={"quand": "xx"}).status_code == 404
    r = client.get("/fr/serie", params={"dom": "apu", "ind": "TR", "quand": "annee", "annee": "2010"})
    assert "s-chiffre" in r.text and "En 2010," in r.text
    # Le lien permanent garde le jeton « toutes les régions », pas la liste développée.
    r = client.get("/fr/serie", params={"dom": "ofgl", "qui": "@region", "quand": "annee"})
    assert "qui=%40region" in r.text or "qui=@region" in r.text
    rows = list(csv.DictReader(io.StringIO(client.get("/fr/serie.csv", params={"dom": "ofgl", "qui": "@region", "quand": "annee", "annee": "2020"}).text)))
    assert rows and {r["annee"] for r in rows} == {"2020"}


def test_menu_quatre_entrees(client):
    """Quatre entrées (Accueil, Thèmes, Ma collectivité, Sources) ; l'entrée de la page courante est marquée."""
    import re
    r = client.get("/fr/budget-etat")
    menu = r.text[r.text.index('id="nav"'):r.text.index("</nav>", r.text.index('id="nav"'))]
    assert len(re.findall(r"<a ", menu)) == 4
    assert 'href="/fr/theme" aria-current="page"' in menu
    assert client.get("/fr/inexistant").status_code == 404
    r = client.get("/fr/")
    assert "a-reperes" in r.text and 'id="carte"' in r.text and "/fr/machine" in r.text
    # Les anciennes entrées mènent aux nouvelles.
    assert client.get("/fr/comprendre", follow_redirects=False).headers["location"] == "/fr/"
    assert client.get("/fr/explorer", follow_redirects=False).headers["location"] == "/fr/theme"
    r = client.get("/fr/sources")
    assert all(h in r.text for h in ("/fr/verifier", "/fr/differences", "/fr/lexique", "/fr/lacunes", "/fr/methode"))


def test_parcours_comprendre(client):
    """Six étapes, chacune avec sa phrase tirée des valeurs, ses définitions citées et l'étape suivante."""
    for n in range(1, 7):
        r = client.get(f"/fr/comprendre/{n}")
        assert r.status_code == 200 and "pc-phrase" in r.text and 'aria-current="step"' in r.text
        assert ("/fr/comprendre/%d" % (n + 1) in r.text) if n < 6 else ("Retour à l'accueil" in r.text)
    assert client.get("/fr/comprendre/7").status_code == 404 and client.get("/fr/comprendre/0").status_code == 404
    assert "/fr/comprendre/1" in client.get("/fr/").text
    assert "ne les soustrait pas" in client.get("/fr/bases/6").text


def test_constructeur_parle_de_ce_qu_on_cherche(client):
    """Sources nommées par leur contenu, jamais un titre « Total » seul, points de départ, unité et forme repliées."""
    r = client.get("/fr/serie")
    assert "<h1>Dépenses, toutes fonctions</h1>" in r.text and "<h1>Total</h1>" not in r.text
    assert 'class="s-depart"' in r.text
    assert r.text.count('<details class="s-pli">') == 2
    assert "Catégories de recettes" in client.get("/fr/serie", params={"dom": "apu"}).text


def test_verifier_un_chiffre(client):
    """Le nombre saisi est lu, puis comparé aux valeurs publiées les plus proches, chacune avec sa source."""
    from api.verifier import lire
    assert lire("3 000 milliards", "fr") == {"x": 3e12, "famille": "eur"}
    assert lire("5,8 %", "fr") == {"x": 5.8, "famille": "pct"}
    assert lire("1,200 € per capita", "en") == {"x": 1200, "famille": "hab"}
    assert lire("148,6 Md€", "fr")["x"] == 148.6e9 and lire("rien", "fr") is None
    r = client.get("/fr/verifier?n=3000+milliards&mot=dette")
    assert r.status_code == 200 and r.text.count('class="src" href="/fr/montant/') >= 1
    assert "Dette" in r.text and ("au-dessous du nombre saisi" in r.text or "au-dessus du nombre saisi" in r.text)
    r = client.get("/fr/verifier?n=5,8+%25&annee=2024")
    assert "% pt" not in r.text and " pt " in r.text
    assert "vrai ou faux" in r.text and "Nombre lu" in r.text
    r = client.get("/fr/verifier?n=1&mot=zzqx")
    assert "aucune valeur n'est montrée" in r.text and 'class="src"' not in r.text.split("Pour aller plus loin")[0].split("Valeurs des vignettes")[1]
    # Revue chef de projet : un déficit entendu sans signe trouve le besoin de financement publié négatif ;
    # une valeur trop éloignée n'est pas proposée comme « proche ».
    r = client.get("/fr/verifier?n=5,8+%25&mot=d%C3%A9ficit&annee=2024")
    assert "identique au nombre saisi · valeur publiée négative" in r.text
    r = client.get("/fr/verifier?n=60+milliards&mot=%C3%A9ducation")
    assert "-95" not in r.text and "−95" not in r.text


def test_ma_collectivite_cherche_par_nom(client):
    """Une seule correspondance mène à la fiche ; plusieurs sont listées ; les communes absentes sont annoncées."""
    r = client.get("/fr/territoires?nom=Gironde", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/fr/territoires/DEP-")
    assert client.get("/fr/territoires?nom=33", follow_redirects=False).status_code == 303
    r = client.get("/fr/territoires?nom=seine")
    assert "collectivités correspondent" in r.text and "communes" in r.text
    assert "Aucune région ni aucun département" in client.get("/fr/territoires?nom=zzqx").text




def test_site_anglais_sans_interface_francaise(client):
    """Le test des traductions vérifie le catalogue ; celui-ci vérifie le rendu : une macro importée sans contexte ou un
    nom codé en dur laisse du français sur /en/ (revue chef de projet du 2026-10-28). Les libellés officiels publiés
    en français seulement (agrégats OFGL, citations juridiques) ne sont pas concernés."""
    import re
    interdits = ("mise à jour du", "Ensemble des administrations publiques", "Administrations publiques locales",
                 "non publié", "Voir la source", "calcul du site")
    pages = PAGES + ["contexte", "lacunes", "methode", "lexique", "territoires", "territoires/REG-44?annee=2014",
                     "recettes-publiques", "depenses-publiques"]
    for page in pages:
        r = client.get("/en/" + page)
        if r.status_code != 200:
            continue
        t = re.sub(r'<(\w+)[^>]*lang="fr"[^>]*>.*?</\1>', " ", r.text, flags=re.S)  # contenu publié en français, balisé
        t = re.sub(r"<script.*?</script>|<[^>]+>", " ", t, flags=re.S)
        for mot in interdits:
            assert mot not in t, (page, mot)


def test_plusieurs_budgets_jamais_choisis(client):
    """Grand Est 2014 : le fichier publie les anciennes régions sous REG-44. Aucune n'est affichée comme « la » valeur,
    aucune n'entre dans la médiane ni dans le classement (revue économiste du 2026-10-28)."""
    import sqlite3
    from api import queries as q
    from api.main import con
    racine = q.noeud(con, "ofgl_agregats", "Dépenses totales")
    f = q.Filtre("REG-44", 2014, "compte", "agregat", "EUR")
    assert len(q.lignes(con, racine["id"], f)) > 1
    try:
        q.single(con, racine["id"], f)
        raise AssertionError("single doit refuser de choisir")
    except q.Plusieurs as e:
        assert len(e.rows) > 1
    r = client.get("/fr/territoires/REG-44?annee=2014")
    assert r.status_code == 200 and "budgets publiés sous ce code" in r.text and "Pas de point pour" in r.text
    r = client.get("/fr/territoires?niveau=region&annee=2014")
    assert "Plusieurs budgets publiés sous un même code" in r.text
    # Chaque fiche se rend, à la première et à la dernière année publiée.
    for e in q.entites(con, "region") + q.entites(con, "departement"):
        ans = q.years(con, "ofgl_agregats", e["code"], "compte", "agregat", "EUR")
        for a in {ans[0], ans[-1]} if ans else ():
            assert client.get(f"/fr/territoires/{e['code']}?annee={a}").status_code == 200, (e["code"], a)



def test_ruptures_et_statuts_particuliers(client):
    """Revue économiste : Ville de Paris (2019) et collectivité de Corse (2018) publiées sous l'ancien code avec un
    autre SIREN ; Paris, Métropole de Lyon et collectivités territoriales uniques hors médiane (marqueurs OFGL)."""
    from api import queries as q
    from api.main import con
    racine = q.noeud(con, "ofgl_agregats", "Dépenses totales")
    assert q.ruptures(q.series_provenance(con, racine["id"], "DEP-75", "compte", "agregat", "EUR")) == [2019]
    assert q.ruptures(q.series_provenance(con, racine["id"], "REG-94", "compte", "agregat", "EUR")) == [2018]
    assert q.ruptures(q.series_provenance(con, racine["id"], "DEP-69", "compte", "agregat", "EUR")) == [2015]
    assert q.ruptures(q.series_provenance(con, racine["id"], "DEP-976", "compte", "agregat", "EUR")) == []
    assert "La population publiée pour ce code passe de" in client.get("/fr/territoires/DEP-69").text
    r = client.get("/fr/territoires/DEP-75?annee=2024")
    assert "autre numéro SIREN" in r.text and "Statut particulier publié" in r.text
    r = client.get("/fr/serie?dom=ofgl&qui=DEP-75&unite=EUR&de=2012&a=2024")
    assert r.status_code == 200 and "autre numéro SIREN" in r.text
    r = client.get("/fr/territoires?niveau=departement&annee=2024")
    assert "statut particulier" in r.text and "sans statut particulier" in r.text
    # Le lexique cite la population utilisée pour « par habitant ».
    assert "population totale INSEE" in client.get("/fr/lexique").text



def test_statut_des_comptes_recents(client):
    """Eurostat ne marque pas les années récentes des APU : leur statut vient de la note de révision INSEE collectée
    (compte provisoire, semi-définitif, définitif), affiché et relié à la note (revue économiste du 2026-10-28)."""
    import json
    from api.main import con
    rows = {r["exercice"]: r for r in con.execute(
        """SELECT m.id, m.exercice, m.provisoire, m.attributs FROM montant m JOIN noeud n ON n.id=m.noeud_id
           JOIN entite e ON e.id=m.entite_id WHERE n.nomenclature_id='apu_agregats' AND n.code='TE'
           AND m.unite='MIO_EUR' AND e.code='APU-S13'""")}
    statuts = {a: json.loads(r["attributs"])["statut du compte (Insee)"] for a, r in rows.items() if r["attributs"]}
    assert sorted(statuts.values()) == ["compte définitif", "compte provisoire", "compte semi-définitif"]
    for a, st in statuts.items():
        assert rows[a]["provisoire"] == (st != "compte définitif"), (a, st)
    r = client.get(f"/fr/montant/{rows[max(statuts)]['id']}")
    assert "compte provisoire" in r.text and "/fr/source/insee_note_revisions" in r.text


def test_donnees_sans_base_publique(client):
    """La base SQLite reste interne : la page Données n'en parle pas et le fichier n'est pas servi."""
    r = client.get("/fr/donnees")
    assert r.status_code == 200 and "sqlite" not in r.text.lower() and "sha256" not in r.text
    assert client.get("/fr/donnees/comptes-publics.sqlite").status_code == 404


def test_donnees_des_widgets(client):
    """Un fichier statique par document, listé au manifeste ; rien d'autre n'est servi (docs/vision/WIDGETS.md §4 bis)."""
    import gzip, json
    m = client.get("/data/manifest.json").json()
    assert {"cofog", "apu", "ofgl-departement"} <= set(m["documents"])
    d = m["documents"]["apu"]
    f = d["parties"]["tout"]["fichier"]
    r = client.get("/data/" + f, headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200 and "immutable" in r.headers["cache-control"]
    x = r.json()
    assert len(x["cols"]["v"]) == d["parties"]["tout"]["lignes"] and set(x["sources"]) <= {"eurostat_apu_principaux", "eurostat_dette_maastricht"} | set(x["sources"])
    assert all(isinstance(i, int) for i in x["cols"]["id"])
    for chemin in ("/data/apu/tout.json", "/data/apu/..%2F..%2Fcomptes.sqlite", "/data/../comptes.sqlite", "/data/x/" + f.split("/")[1]):
        assert client.get(chemin).status_code == 404
    assert m["documents"]["cofog"]["empilable"] and not m["documents"]["ofgl-departement"]["empilable"]


def test_atelier(client):
    r = client.get("/fr/atelier?doc=cofog&n=1;DROP%20TABLE&t=<script>")
    assert r.status_code == 200 and 'id="at-l"' in r.text and "plot-0.6.16" in r.text
    # L'URL n'est reprise que dans le lien de langue, échappée ; le serveur ne la lit pas.
    assert "t=<script>" not in r.text


def test_adresses_par_langue(client):
    """Une adresse par nom de menu, dans la langue de la page : /en/check sert Vérifier, /en/verifier y redirige,
    les anciennes adresses /bases mènent au parcours (revue chef de projet du 2026-10-28)."""
    import re
    from api.adresses import EN
    r = client.get("/en/check")
    assert r.status_code == 200 and r.url.path == "/en/check"
    r = client.get("/en/verifier?q=60", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"] == "/en/check?q=60"
    assert client.get("/fr/bases/3", follow_redirects=False).headers["location"] == "/fr/comprendre/3"
    assert client.get("/en/understand", follow_redirects=False).headers["location"] == "/en/"
    assert client.get("/fr/comprendre?annee=2009", follow_redirects=False).headers["location"].startswith("/fr/grands-equilibres?")
    for page in ("/en/", "/en/topic", "/en/sources", "/en/territories/DEP-75", "/en/series?dom=ofgl&qui=DEP-75&unite=EUR"):
        t = client.get(page).text
        assert client.get(page).status_code == 200, page
        francais = re.findall(r'(?<=["\'(=\s])/en/(' + "|".join(EN) + r')(?![\w-])', t)
        assert not francais, (page, francais[:5])
        assert 'hreflang="fr" href="/fr/' in t
    t = client.get("/fr/territoires").text
    assert 'href="/en/territories"' in t


def test_verifier_par_theme_et_outils_par_intention(client):
    """Vérifier part d'un thème (sans connaître de chiffre)."""
    r = client.get("/fr/verifier")
    assert r.text.count('name="theme"') == 8 and r.text.count("v-theme-v") == 8
    r = client.get("/fr/verifier?theme=dette")
    assert 'class="v-tab"' in r.text and r.text.count('href="/fr/montant/') >= 20
    r = client.get("/fr/verifier?theme=dette&n=3000+milliards")
    assert "Dette brute" in r.text and "au-dessus du nombre saisi" in r.text or "au-dessous du nombre saisi" in r.text


def test_machine(client):
    """La machine : une page par langue, chaque montant listé avec sa source, « autres recettes » = somme des autres."""
    import json
    for lang in ("fr", "en"):
        r = client.get(f"/{lang}/machine")
        assert r.status_code == 200 and "machine.js" in r.text and f'class="src" href="/{lang}/' in r.text
        assert "Niveau de lecture" in r.text or "Reading level" in r.text
    r = client.get("/fr/machine?annee=2010")
    d = json.loads(re.search(r'<script id="mc-data" type="application/json">(.*?)</script>', r.text, re.S).group(1))
    assert d.get("decF") == 6
    a = d["ans"]["2010"]
    assert len(a["sorties"]) == 10 and a["entrees"][-1]["k"] == "AUTRES"
    assert abs(sum(e["v"] for e in a["entrees"]) - a["TR"]["v"]) < 1  # catégories + autres = recettes totales publiées


def test_couverture_lue_dans_la_base(client):
    """La page Données liste chaque source qui a des montants chargés, avec ses années lues dans la base."""
    from api.main import con

    rows = con.execute("""SELECT f.source_id, MIN(m.exercice), MAX(m.exercice) FROM montant m
                          JOIN fichier f ON f.id = m.fichier_id GROUP BY 1""").fetchall()
    for lang in ("fr", "en"):
        page = client.get(f"/{lang}/donnees").text
        assert 'class="couv"' in page
        for sid, de, a in rows:
            assert f"/{lang}/source/{sid}" in page
            assert (str(de) if de == a else f"{de}–{a}") in page


def test_exploitation(client):
    """Page 404 du site dans la bonne langue, robots.txt, sitemap.xml et sonde de santé."""
    for lang, mot in (("fr", "Page introuvable"), ("en", "Page not found")):
        r = client.get(f"/{lang}/nexiste-pas/vraiment")
        assert r.status_code == 404 and mot in r.text
    assert client.get("/data/x/y.json").status_code == 404
    r = client.get("/robots.txt")
    assert r.status_code == 200 and "Sitemap:" in r.text and "Disallow: /fr/recherche" in r.text
    s = client.get("/sitemap.xml").text
    assert "/fr/territoires/DEP-33" in s and "/en/territories/DEP-33" in s and "/en/understand/1" in s
    assert client.get("/sante").json() == {"etat": "ok"}


@pytest.mark.parametrize("lang", ["fr", "en"])
def test_toutes_les_fiches_thematiques(client, lang):
    """Chaque thème de content/themes.yaml répond, et chaque mission et fonction rattachée existe dans la base
    (une faute de libellé ferait disparaître le bloc en silence)."""
    from api import queries as q
    from api.fiches import con, themes
    for cle, t in themes().items():
        assert client.get(f"/{lang}/{'theme' if lang == 'fr' else 'topic'}/{cle}").status_code == 200, cle
        for m in t.get("missions", []):
            assert q.noeud(con, "budget_vert_plf2026", f"CB|{m}") is not None, (cle, m)
        if t.get("m57"):
            assert q.noeud(con, "fonctions_dep_m57", t["m57"]) is not None, cle


def test_referentiel_de_chaque_source_chiffree():
    """Toute source qui porte des montants déclare son cadre comptable (sources.yaml, clé `referentiel`)."""
    from api.differences import con, noms, referentiels
    chiffrees = {r[0] for r in con.execute("SELECT DISTINCT fi.source_id FROM montant m JOIN fichier fi ON fi.id = m.fichier_id")}
    assert chiffrees <= set(referentiels()), chiffrees - set(referentiels())
    assert set(referentiels().values()) <= set(noms("fr")["referentiel"])


def test_pourquoi_deux_chiffres_different(client):
    from api.fiches import paire_etat
    p = paire_etat("enseignement", "fr")
    assert p and {c["cle"] for c in p["crit"] if c["differe"]} >= {"referentiel", "entite", "stade"}
    r = client.get(p["href"])
    assert r.status_code == 200 and "Comptabilité nationale (SEC 2010)" in r.text and "Écart A" not in r.text
    assert 'id="differences"' in client.get("/fr/theme/enseignement").text
    assert "Cadre comptable" in client.get(p["a"]["href"]).text
    assert client.get("/fr/differences?a=m0&b=m1").status_code == 404
    assert client.get("/fr/differences?a=zz&b=m1").status_code == 404


def test_fil_d_ariane(client):
    """Chaque page hors accueil situe la page : accueil, entrée du menu, page d'entrée, titre."""
    t = client.get("/fr/theme/sante").text
    assert re.search(r'<nav class="ariane".*?href="/fr/".*?href="/fr/theme".*?aria-current="page">', t, re.S)
    assert 'class="ariane"' not in client.get("/fr/").text
    assert 'class="ariane"' in client.get("/en/topic/sante").text
