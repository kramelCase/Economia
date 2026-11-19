# Architecture

## 1. Du fichier officiel à la page

Rien n'est saisi à la main : tout part d'un fichier téléchargé, gardé tel quel, puis chargé dans une base SQLite.

```mermaid
flowchart LR
  S[sources.yaml<br>liste des sources] --> F[make fetch<br>pipeline/fetch.py]
  F --> R[(raw/<br>fichiers bruts<br>+ meta.json sha256)]
  R --> B[make build<br>pipeline/build.py<br>+ loaders/]
  C[content/*.yaml<br>lexique, lacunes, thèmes] --> B
  B -->|contrôles de bouclage| D[(comptes.sqlite)]
  B --> X[data/<br>fichiers des graphiques]
  D --> A[api/<br>FastAPI + Jinja]
  X --> A
  A --> P[Pages HTML<br>templates/ + static/]
```

- **raw/** n'est jamais modifié : chaque collecte crée un dossier daté. C'est la preuve de provenance.
- **make build** échoue si un total recalculé ne correspond pas au total publié par la source.
- **data/** contient des fichiers précalculés pour les graphiques interactifs. Aucune requête libre n'atteint la base.

## 2. La base de données

Tout `montant` pointe vers un `fichier` et une `ligne_source` (colonnes obligatoires). C'est ce qui permet de
remonter de n'importe quel chiffre jusqu'à la ligne du fichier brut.

```mermaid
erDiagram
  source ||--o{ fichier : "collecté en"
  source ||--o{ nomenclature : "définit"
  nomenclature ||--o{ noeud : "contient (arbre)"
  noeud ||--o{ noeud : "parent"
  noeud ||--o{ noeud_traduction : "traduit"
  entite ||--o{ entite : "parent"
  entite ||--o{ montant : "concerne"
  noeud ||--o{ montant : "classe"
  fichier ||--o{ montant : "ligne_source"
  fichier ||--o{ noeud : "ligne_source"
  source ||--o{ lacune : "manque dans"
  concept ||--o{ concept_traduction : "défini par"
  concept ||--o{ concept_alias : "aussi appelé"

  montant {
    int entite_id
    int noeud_id
    int exercice
    text stade "plf, lfi, execution, compte"
    text mesure "ae, cp, depense, agregat..."
    text unite "EUR, MIO_EUR, PC_GDP..."
    real valeur
    int fichier_id "obligatoire"
    int ligne_source "obligatoire"
  }
  entite {
    text code "ETAT, APU-S13, DEP-33..."
    text niveau
  }
  noeud {
    text code "mission, fonction COFOG, poste..."
    text libelle "tel que publié"
  }
  lacune {
    text type "non_publie, non_chiffre..."
    text responsable "qui devrait publier"
  }
```

| Table | Rôle |
|---|---|
| `source`, `fichier` | Qui publie quoi, et chaque téléchargement (URL, date, sha256) |
| `entite` | L'État, les administrations publiques et leurs sous-secteurs, les régions, les départements |
| `nomenclature`, `noeud` | Les classements officiels en arbre : missions du budget, fonctions COFOG, postes comptables |
| `montant` | Les chiffres, chacun avec son stade, sa mesure, son unité et sa ligne d'origine |
| `lacune` | Ce qui manque, avec l'organisme qui devrait le publier |
| `concept` | Le lexique : définitions citées mot pour mot, avec leur source |

Détail colonne par colonne : [SCHEMA-BASE.md](SCHEMA-BASE.md). Définition exacte : `db/schema.sql`.

## 3. Le code

```mermaid
flowchart TB
  subgraph pipeline [pipeline/ : construire la base]
    fetch[fetch.py<br>télécharge] --> build[build.py<br>orchestre]
    build --> loaders[loaders/<br>un chargeur par source]
    build --> export[export_donnees.py<br>fichiers data/]
  end
  subgraph api [api/ : servir le site]
    main[main.py<br>application, rendu, aides partagées] --> pages[un module par page<br>depenses, recettes, territoires,<br>machine, fiches, provenance...]
    main --> lexique[lexique.py<br>relie chaque terme technique]
    main --> i18n[i18n.py<br>FR / EN]
    pages --> queries[queries.py<br>requêtes SQL]
  end
  build --> db[(comptes.sqlite)]
  db --> queries
  pages --> tpl[templates/ + static/]
```

| Dossier | Contenu |
|---|---|
| `pipeline/` | Collecte, profilage, chargeurs, construction de la base |
| `api/` | FastAPI : `main.py` (application) et un module par page |
| `templates/`, `static/` | Pages rendues côté serveur, CSS et JS (graphiques, machine 3D) |
| `content/` | Lexique (`concepts.yaml`), lacunes, thèmes, informations éditeur |
| `locales/` | Traductions anglaises (`en_strings.py`, puis compilées) |
| `tests/` | Provenance, bouclages, lacunes, traductions, parcours navigateur |
