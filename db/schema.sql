-- Schéma déduit de docs/INVENTAIRE.md.
-- Règle d'or : tout chiffre (montant) et tout libellé ou définition affiché remonte à un `fichier`
-- collecté, à la ligne près. Pas de montant sans provenance : contraintes NOT NULL + clés étrangères.

PRAGMA foreign_keys = ON;

-- Source officielle déclarée dans sources.yaml (ou dans content/concepts.yaml pour les définitions).
CREATE TABLE source (
    id                  TEXT PRIMARY KEY,
    titre               TEXT NOT NULL,
    editeur             TEXT NOT NULL,
    licence             TEXT NOT NULL,
    perimetre           TEXT NOT NULL,
    document_reference  TEXT,
    url_portail         TEXT,
    page                TEXT,                   -- page officielle qui présente le jeu (sinon déduite du portail)
    dataset             TEXT
);

-- Une collecte brute précise (raw/<source>/<horodatage>/).
CREATE TABLE fichier (
    id          INTEGER PRIMARY KEY,
    source_id   TEXT NOT NULL REFERENCES source(id),
    collecte    TEXT NOT NULL,             -- horodatage UTC de la collecte
    url         TEXT NOT NULL,             -- URL exacte téléchargée
    sha256      TEXT NOT NULL,
    chemin      TEXT NOT NULL,             -- chemin relatif du brut
    octets      INTEGER NOT NULL,
    UNIQUE (source_id, sha256)
);

-- Qui dépense : État, ensemble des administrations publiques (et sous-secteurs), région, département.
CREATE TABLE entite (
    id          INTEGER PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,      -- ex. ETAT, APU-S13, REG-84, DEP-69
    niveau      TEXT NOT NULL CHECK (niveau IN ('etat', 'secteur_apu', 'region', 'departement')),
    nom         TEXT NOT NULL,
    code_insee  TEXT,
    siren       TEXT,
    parent_id   INTEGER REFERENCES entite(id)
);

-- Une nomenclature officielle (arbre de classement) : LOLF, COFOG, agrégats OFGL, fonctions départementales.
CREATE TABLE nomenclature (
    id          TEXT PRIMARY KEY,
    titre       TEXT NOT NULL,
    source_id   TEXT NOT NULL REFERENCES source(id)   -- qui définit cette nomenclature
);

CREATE TABLE noeud (
    id               INTEGER PRIMARY KEY,
    nomenclature_id  TEXT NOT NULL REFERENCES nomenclature(id),
    code             TEXT NOT NULL,
    parent_id        INTEGER REFERENCES noeud(id),
    niveau           INTEGER NOT NULL,
    libelle          TEXT NOT NULL,         -- libellé français tel que publié
    technique        INTEGER NOT NULL DEFAULT 0,  -- 1 = ligne technique (MP/MT, FDC/ADP...), pas une politique
    fichier_id       INTEGER NOT NULL REFERENCES fichier(id),
    ligne_source     INTEGER NOT NULL,
    UNIQUE (nomenclature_id, code)
);
CREATE INDEX noeud_parent ON noeud(parent_id);

CREATE TABLE noeud_traduction (
    noeud_id      INTEGER NOT NULL REFERENCES noeud(id),
    langue        TEXT NOT NULL,
    libelle       TEXT NOT NULL,
    statut        TEXT NOT NULL CHECK (statut IN ('officielle', 'non_officielle')),
    fichier_id    INTEGER REFERENCES fichier(id),      -- obligatoire si officielle
    ligne_source  INTEGER,
    PRIMARY KEY (noeud_id, langue),
    CHECK (statut = 'non_officielle' OR (fichier_id IS NOT NULL AND ligne_source IS NOT NULL))
);

-- Le fait chiffré. `stade` dit d'où vient le chiffre dans le cycle budgétaire.
CREATE TABLE montant (
    id            INTEGER PRIMARY KEY,
    entite_id     INTEGER NOT NULL REFERENCES entite(id),
    noeud_id      INTEGER NOT NULL REFERENCES noeud(id),
    exercice      INTEGER NOT NULL,
    stade         TEXT NOT NULL CHECK (stade IN ('plf', 'lfi', 'execution', 'compte')),
    mesure        TEXT NOT NULL,           -- ae, cp, cout_prevu, depense, agregat
    unite         TEXT NOT NULL CHECK (unite IN ('EUR', 'MIO_EUR', 'PC_TOT', 'PC_GDP', 'EUR_HAB')),
    valeur        REAL NOT NULL,
    provisoire    INTEGER NOT NULL DEFAULT 0,
    attributs     TEXT,                    -- JSON : facettes propres à la source (impôt, type de budget...)
    fichier_id    INTEGER NOT NULL REFERENCES fichier(id),
    ligne_source  INTEGER NOT NULL
);
CREATE INDEX montant_lookup ON montant(noeud_id, entite_id, exercice);
CREATE INDEX montant_entite ON montant(entite_id, exercice);

-- Ce qui manque : un trou est un contenu, jamais un zéro.
CREATE TABLE lacune (
    id            INTEGER PRIMARY KEY,
    type          TEXT NOT NULL CHECK (type IN ('non_publie', 'non_chiffre', 'sous_seuil', 'sans_definition',
                                                'publication_reportee', 'donnee_inexploitable')),
    titre         TEXT NOT NULL,
    description   TEXT NOT NULL,
    responsable   TEXT NOT NULL,           -- qui devrait publier
    constat       TEXT NOT NULL,           -- comment et quand on l'a constatée
    source_id     TEXT REFERENCES source(id),
    fichier_id    INTEGER REFERENCES fichier(id),
    ligne_source  INTEGER,
    noeud_id      INTEGER REFERENCES noeud(id),
    entite_id     INTEGER REFERENCES entite(id),
    exercice      INTEGER
);

-- Lexique. Une définition n'existe que citée mot pour mot depuis un texte officiel.
CREATE TABLE concept (
    id            TEXT PRIMARY KEY,
    statut        TEXT NOT NULL CHECK (statut IN ('cite', 'a_sourcer'))
);

-- Terme et définition dans une langue. Une définition présente = une citation avec sa provenance :
-- soit un fichier collecté automatiquement (INSEE, OFGL), soit un relevé manuel daté (Légifrance
-- bloque les robots ; le texte est relevé dans un navigateur, voir content/concepts.yaml).
CREATE TABLE concept_traduction (
    concept_id    TEXT NOT NULL REFERENCES concept(id),
    langue        TEXT NOT NULL,
    terme         TEXT NOT NULL,
    definition    TEXT,
    statut        TEXT NOT NULL CHECK (statut IN ('officielle', 'non_officielle')),
    source_url    TEXT,
    source_titre  TEXT,
    fichier_id    INTEGER REFERENCES fichier(id),
    ligne_source  INTEGER,
    releve        TEXT,
    PRIMARY KEY (concept_id, langue),
    CHECK (definition IS NULL OR (source_url IS NOT NULL AND (fichier_id IS NOT NULL OR releve IS NOT NULL)))
);

-- Formes du terme à relier automatiquement dans les textes (AE, autorisations d'engagement...).
CREATE TABLE concept_alias (
    concept_id    TEXT NOT NULL REFERENCES concept(id),
    langue        TEXT NOT NULL,
    alias         TEXT NOT NULL,
    PRIMARY KEY (langue, alias)
);

-- Contrôles de bouclage, affichés sur la page Méthode.
CREATE TABLE controle (
    id            INTEGER PRIMARY KEY,
    nom           TEXT NOT NULL,
    source_id     TEXT NOT NULL REFERENCES source(id),
    attendu       REAL NOT NULL,
    obtenu        REAL NOT NULL,
    tolerance     REAL NOT NULL,
    ok            INTEGER NOT NULL,
    detail        TEXT
);

-- Vie institutionnelle (open data de l'Assemblée nationale). Des faits datés : qui exerçait quelle fonction, quels
-- textes budgétaires ont été soumis au vote et comment chaque groupe a voté. Le site n'établit aucun lien de cause
-- entre ces faits et les montants. `entree` situe l'enregistrement dans l'archive collectée (chemin du JSON, ou
-- chemin#numéro quand une législature est publiée en un seul fichier).
CREATE TABLE organe (
    uid           TEXT PRIMARY KEY,        -- identifiant de l'Assemblée nationale (PO...)
    type          TEXT NOT NULL,           -- PRESREP, GOUVERNEMENT, MINISTERE, GP, PARPOL, ASSEMBLEE
    libelle       TEXT NOT NULL,
    abrege        TEXT,
    debut         TEXT,
    fin           TEXT,
    fichier_id    INTEGER NOT NULL REFERENCES fichier(id),
    entree        TEXT NOT NULL
);

CREATE TABLE personne (
    uid           TEXT PRIMARY KEY,        -- PA...
    nom           TEXT NOT NULL,
    fichier_id    INTEGER NOT NULL REFERENCES fichier(id),
    entree        TEXT NOT NULL
);

-- Une fonction exercée : présidence, ministère (qualité publiée : Premier ministre, Ministre, Ministre délégué...),
-- rattachement à un parti politique.
CREATE TABLE fonction (
    id            INTEGER PRIMARY KEY,
    personne_uid  TEXT NOT NULL REFERENCES personne(uid),
    organe_uid    TEXT NOT NULL REFERENCES organe(uid),
    qualite       TEXT,
    debut         TEXT NOT NULL,
    fin           TEXT,
    fichier_id    INTEGER NOT NULL REFERENCES fichier(id),
    entree        TEXT NOT NULL
);
CREATE INDEX fonction_organe ON fonction(organe_uid);

-- Scrutin public sur l'ensemble d'un texte budgétaire. `texte` est déduit du titre publié, `exercice` aussi
-- (« loi de finances pour 2019 » -> 2019).
CREATE TABLE scrutin (
    uid           TEXT PRIMARY KEY,        -- VTANR5L15V1429
    legislature   INTEGER NOT NULL,
    numero        INTEGER NOT NULL,
    date          TEXT NOT NULL,
    titre         TEXT NOT NULL,
    sort          TEXT NOT NULL,           -- adopté / rejeté, tel que publié
    texte         TEXT NOT NULL CHECK (texte IN ('lf', 'lfr', 'reglement', 'lfss', 'lfssr', 'acss')),
    exercice      INTEGER NOT NULL,
    lecture       TEXT,
    votants       INTEGER,
    pour          INTEGER NOT NULL,
    contre        INTEGER NOT NULL,
    abstentions   INTEGER NOT NULL,
    fichier_id    INTEGER NOT NULL REFERENCES fichier(id),
    entree        TEXT NOT NULL,
    dossier_uid   TEXT REFERENCES loi(dossier_uid),  -- dossier législatif qui cite ce scrutin (voteRef)
    page_url      TEXT     -- page d'analyse de l'AN, seulement si la page collectée porte ce numéro et cet identifiant
);
CREATE INDEX scrutin_exercice ON scrutin(exercice);

CREATE TABLE scrutin_groupe (
    scrutin_uid   TEXT NOT NULL REFERENCES scrutin(uid),
    groupe_uid    TEXT NOT NULL REFERENCES organe(uid),
    membres       INTEGER,
    position      TEXT,                    -- position majoritaire publiée (pour, contre, abstention)
    pour          INTEGER NOT NULL,
    contre        INTEGER NOT NULL,
    abstentions   INTEGER NOT NULL,
    non_votants   INTEGER NOT NULL,
    PRIMARY KEY (scrutin_uid, groupe_uid)
);

-- Documents officiels cités : chaque champ est relevé dans un fichier collecté (`fichier_id`), à l'endroit dit par
-- `releve`. Rien n'y est saisi à la main. Rôles : le jeu lui-même, sa page officielle, une fiche de métadonnées, une
-- entrée de catalogue, un document de référence cité par l'éditeur.
CREATE TABLE document (
    id                INTEGER PRIMARY KEY,
    source_id         TEXT NOT NULL REFERENCES source(id),
    role              TEXT NOT NULL CHECK (role IN ('jeu', 'page', 'metadonnees', 'catalogue', 'reference', 'licence')),
    titre             TEXT NOT NULL,
    titre_en          TEXT,
    editeur           TEXT,
    identifiant       TEXT NOT NULL,           -- code du jeu, nom du fichier publié, version...
    date_publication  TEXT,
    date_maj          TEXT,
    url               TEXT NOT NULL,
    extrait           TEXT,                    -- citation exacte (description publiée par l'éditeur)
    extrait_lang      TEXT,
    fichier_id        INTEGER NOT NULL REFERENCES fichier(id),
    releve            TEXT NOT NULL
);
CREATE INDEX document_source ON document(source_id, role);

-- Lois promulguées, telles que publiées dans les dossiers législatifs de l'Assemblée nationale.
CREATE TABLE loi (
    dossier_uid     TEXT PRIMARY KEY,          -- DLR5L17N50198
    legislature     INTEGER NOT NULL,
    titre_dossier   TEXT NOT NULL,
    code_loi        TEXT,                      -- 2025-127
    titre_loi       TEXT,                      -- « de finances pour 2025 »
    date_jo         TEXT,
    num_jo          TEXT,
    nor             TEXT,
    url_legifrance  TEXT,                      -- tel que publié dans le dossier
    fichier_id      INTEGER NOT NULL REFERENCES fichier(id),
    entree          TEXT NOT NULL
);
