.PHONY: help setup install fetch profile build serve test test-setup i18n i18n-extract

help:
	@echo "make setup       - première installation : install + fetch + build"
	@echo "make install     - environnement Python et dépendances (uv)"
	@echo "make fetch       - télécharge les sources officielles dans raw/ (SOURCES=id pour une seule)"
	@echo "make profile     - décrit les fichiers collectés dans docs/profils/"
	@echo "make build       - construit comptes.sqlite (échoue si un contrôle de bouclage échoue)"
	@echo "make serve       - lance le site sur http://127.0.0.1:8790"
	@echo "make test-setup  - une fois : navigateur des tests de parcours"
	@echo "make test        - lance les tests"

setup: install fetch build

install:
	@command -v uv >/dev/null || { echo "uv manquant : curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
	uv sync

fetch:
	uv run python -m pipeline.fetch $(SOURCES)

profile:
	uv run python -m pipeline.profile $(SOURCES)

build:
	uv run python -m pipeline.build

serve: i18n
	uv run uvicorn api.main:app --host 127.0.0.1 --port 8790 --reload

# Traductions : extraire les chaînes FR, mettre à jour locales/en/.../messages.po, puis compiler.
i18n-extract:
	uv run pybabel extract -F babel.cfg -o locales/messages.pot --no-location --omit-header .
	uv run pybabel update -i locales/messages.pot -d locales -l en --no-fuzzy-matching

i18n:
	uv run python -m locales.en_strings
	uv run pybabel compile -d locales --statistics

test-setup:
	uv run playwright install chromium

test: i18n
	uv run pytest -q
