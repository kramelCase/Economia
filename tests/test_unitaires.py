"""Briques de base, sans base de données."""

from api.lexique import Alias, compile_aliases, link_terms, unlinked_terms
from pipeline.db import num
from pipeline.loaders.budget_etat import is_technique
from pipeline.loaders.concepts import extract_insee


def test_absence_jamais_zero():
    assert num("") is None
    assert num("nc") is None
    assert num("ε") is None
    assert num("0") == 0.0
    assert num("12,5") == 12.5


def test_lignes_techniques():
    assert is_technique("MP/MT - PLF 2025")
    assert is_technique("FDC/ADP")
    assert is_technique("T2_CAS")
    assert not is_technique("110-02")
    assert not is_technique("320147")


def test_lien_des_termes():
    pattern, lookup = compile_aliases([Alias("cp", "crédits de paiement"), Alias("cp", "CP"), Alias("apu", "APU")])
    html = ('<p>Les Crédits de paiement et les CP. <a href="#">CP</a> capital</p>'
            '<div data-nolink>CP</div><script>var CP=1</script>')
    out, used = link_terms(html, pattern, lookup, "/fr/lexique")
    assert used == {"cp"}
    assert out.count('class="terme"') == 2           # « Crédits de paiement » et « CP » ; pas le lien, ni nolink
    assert "capital" in out and 'href="/fr/lexique#cp">capital' not in out
    assert unlinked_terms(out, pattern) == []
    assert unlinked_terms("<p>des CP</p>", pattern) == ["CP"]


def test_sigle_sensible_a_la_casse():
    pattern, lookup = compile_aliases([Alias("ae", "AE")])
    out, _ = link_terms("<p>ae AE</p>", pattern, lookup, "/l")
    assert out.count("terme") == 1


def test_extraction_insee():
    page = ('<main><h2 class="x">Définition</h2><div><p>Le <b>PIB</b> mesure la richesse produite '
            'par les unités résidentes au cours de la période.</p><p>Partager</p><p>Bluesky</p></div>'
            '<h2>Voir aussi</h2></main>')
    assert extract_insee(page, "fr") == ("Le PIB mesure la richesse produite par les unités résidentes "
                                         "au cours de la période.")
