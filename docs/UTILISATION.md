# Utilisation

## Installer

Prérequis : Python 3.12 ou plus, `make`, et [uv](https://docs.astral.sh/uv/) :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Puis, dans le dossier du projet :

```bash
make setup
```

`make setup` fait trois choses :
1. `make install` crée `.venv/` et installe les dépendances de `pyproject.toml` (versions figées dans `uv.lock`).
2. `make fetch` télécharge les sources officielles listées dans `sources.yaml` vers `raw/` (plusieurs minutes,
   environ 550 Mo).
3. `make build` construit `comptes.sqlite` et les fichiers de `data/`. La commande échoue si un total recalculé ne
   correspond pas au total publié : c'est voulu, la source a sans doute changé de format.

## Lancer le site

```bash
make serve
```

Le site s'ouvre sur http://127.0.0.1:8790. La commande compile aussi les traductions, et le serveur se recharge tout
seul quand on modifie le code.

## Toutes les commandes

| Commande | Rôle |
|---|---|
| `make setup` | Première installation complète (install + fetch + build) |
| `make install` | Environnement Python et dépendances |
| `make fetch` | Télécharge les sources (`make fetch SOURCES=id` pour une seule) |
| `make profile` | Décrit chaque fichier collecté dans `docs/profils/` |
| `make build` | Construit la base et les fichiers des graphiques |
| `make serve` | Lance le site sur le port 8790 |
| `make test` | Lance les tests |
| `make test-setup` | Une fois : installe le navigateur des tests de parcours |
| `make i18n-extract` | Repère les nouvelles phrases à traduire |
| `make i18n` | Compile les traductions |

## Tester

```bash
make test-setup   # une seule fois
make test
```

Les tests vérifient : qu'aucun chiffre n'est sans source, que les totaux bouclent, que les trous sont affichés comme
des trous, que chaque terme du lexique est relié, que tout est traduit, et que les pages s'affichent à 320 px.

## Mettre à jour les données

```bash
make fetch && make build
```

Chaque collecte crée un nouveau dossier daté dans `raw/` ; les anciennes restent, comme preuve.

## Ajouter une source

1. Ajouter une entrée dans `sources.yaml` (type `ods` pour data.economie.gouv.fr et data.ofgl.fr, `http_csv` sinon).
2. `make fetch SOURCES=mon_id && make profile SOURCES=mon_id`, puis lire `docs/profils/mon_id.md`.
3. Écrire le chargeur dans `pipeline/loaders/`, avec un contrôle de bouclage si la source publie un total.
4. Noter les lacunes constatées dans `content/lacunes.yaml`, ou les faire détecter par le chargeur.
