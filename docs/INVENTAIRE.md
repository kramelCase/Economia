# Inventaire des données (phase 0)

Lecture humaine des profils automatiques (`docs/profils/*.md`, régénérés par `make profile`).
Collecte du 2026-10-26. **Le schéma SQLite (`db/schema.sql`) se déduit de ce document.**

## 1. Ce que contient chaque source

### Budget de l'État — `etat_budget_vert_plf2026` (Direction du Budget)
- 1 816 lignes. `type_depense` vaut *Crédits budgétaires* (1 269), *Dépenses fiscales* (483) ou *Taxes affectées plafonnées* (64).
- Montants en euros sur trois colonnes : **exécution 2024** (réalisé), **LFI 2025** (voté) et **PLF 2026** (proposé). Pour les dépenses fiscales, les deux dernières colonnes sont des **prévisions** de coût.
- Rattachement : mission (46) → programme (156) → action (si crédit budgétaire). Pour les dépenses fiscales, on a aussi l'impôt concerné (IR, IS, TVA…).
- Lignes techniques à ne pas présenter comme des politiques : `MP/MT` (mesures de périmètre et transferts), `FDC/ADP` (fonds de concours), `T2_CAS` (contribution au CAS Pensions).
- Totaux (Md€, exéc. 2024 / LFI 2025 / PLF 2026) : crédits 468,7 / 469,8 / 479,5 ; taxes affectées 20,8 / 20,6 / 21,4 ; dépenses fiscales 89,4 / 91,8 / 88,3.
- Une même dépense peut occuper plusieurs lignes (23 codes) : elle est alors **ventilée** en parts (colonnes `% 2024/2025/2026 si différent de 100`, par ex. 0,8 + 0,2) et les montants sont déjà répartis. L'addition est donc juste, mais pour classer les dépenses on regroupe par `code_depense`.
- Cotation environnementale (favorable, neutre, défavorable, mixte, NC) : c'est l'objet officiel de ce jeu. On l'affiche telle quelle.

### Budget de l'État — `etat_plf2025_destination` (Direction du Budget)
- 2 404 lignes, toutes au stade `PLF`, avec l'arbre complet mission → programme → action → **sous-action**, plus le ministère, le titre et la catégorie (nature de la dépense).
- Types de budget : BG (budget général, 594,0 Md€ de CP), CAS (80,8), CCF (145,7), BA (2,5). **Ces montants ne s'additionnent pas** : les comptes spéciaux ont leur logique propre.

### Dépenses fiscales — `etat_depenses_fiscales_plf2024`
- 468 dépenses avec leur libellé, leur finalité et leur impôt, **mais aucune colonne de montant renseignée** : les colonnes `empty4` à `empty8` sont vides. Les en-têtes sont cassés (colonnes `empty*`).
- → Sert uniquement de **lacune documentée**. Les montants proviennent du budget vert 2026.

### Toutes administrations, par fonction — `eurostat_cofog_fr` (Eurostat / INSEE)
- 28 680 observations, de 1995 à 2024, en M€, en % de la dépense totale et en % du PIB.
- Secteurs : S13 (toutes APU), S1311 (centrales), S1313 (locales), S1314 (sécurité sociale).
- 80 codes COFOG : `TOTAL`, 10 divisions `GFxx` et leurs groupes `GFxxyy`.
- Drapeau `p` (provisoire) sur 2023 et 2024 : à afficher.
- Libellés officiels en FR et EN : `eurostat_cofog_libelles_fr` et `eurostat_cofog_libelles_en`.

### Régions et départements — `ofgl_regions`, `ofgl_departements` (OFGL, balances DGFiP)
- Comptes **consolidés** (budget principal + budgets annexes, flux internes retirés), de 2012 à 2025. 68 agrégats (dépenses de fonctionnement, frais de personnel, encours de dette…), en € et en €/habitant.
- Régions : 14 547 lignes, 17 régions ou CTU. Départements : 88 417 lignes, dont Paris, la Métropole de Lyon et l'Alsace.
- **Les agrégats sont emboîtés** (« Dépenses totales » contient « Dépenses de fonctionnement »). On ne les additionne jamais entre eux.

### Départements par fonction — `ofgl_departements_fonctionnelle`
- 392 027 lignes (filtre : exercices 2020 à 2025), **par budget** (non consolidé). Arbre fonctionnel sur 4 niveaux (`fonction`, `nom_fonction`, `niveau_hierarchique`), 17 agrégats de dépense.
- Deux nomenclatures comptables coexistent (M52 → M57) : la continuité des fonctions est à vérifier par code.

### Définitions officielles — `ofgl_definitions_agregats`
- 92 agrégats, chacun avec son **chemin** (ex. « Dépenses totales > Dépenses de fonctionnement ») et un commentaire qui le définit. C'est la source du lexique pour les agrégats locaux.

## 2. Contrôles déjà passés sur le brut
| Contrôle | Résultat |
|---|---|
| COFOG S13 2024 : somme des 10 fonctions = TOTAL | 1 671 794,0 contre 1 671 793,8 M€ (écart d'arrondi 0,2) ✔ |
| COFOG : somme des groupes GF09xx = GF09 | ✔ (écart ≤ 0,1) |
| COFOG : S1311 + S1313 + S1314 = S13 ? | **Non** : 1 778,5 contre 1 671,8 Md€. Écart de consolidation (transferts entre administrations), **à expliquer, pas à corriger** |
| Agrégats OFGL ayant une définition officielle | 65/68. Il manque : *Crédits de trésorerie*, *Fonds de roulement*, *Produit des cessions d'immobilisations* |
| Dépenses fiscales « nc » ayant un montant | 0 ✔ (le marqueur est cohérent) |

## 3. Pièges qui contraignent le modèle
1. **Stades budgétaires** : PLF (proposé), LFI (voté) et exécution (réalisé) sont des natures de montant différentes, jamais mélangées dans un même graphique sans étiquette.
2. **Périmètres** : budget de l'État ≠ APU. Le total de l'éducation dans la COFOG (S13) ≠ la mission « Enseignement scolaire ». Chaque montant porte le périmètre de sa source.
3. **Doubles comptes** : les agrégats OFGL sont emboîtés ; les sous-secteurs COFOG ne sont pas consolidés ; la présentation fonctionnelle des départements est donnée par budget, sans consolidation. (Les dépenses fiscales sur plusieurs lignes ne posent pas ce problème : elles sont ventilées, voir §1.) Règle : **on n'additionne que le long d'une nomenclature officielle, au sein d'une même source**, et seulement quand la source fournit le total de contrôle.
4. **Absences** : `nc` (non chiffré) et `ε` (< 0,5 M€) ne sont **pas des zéros**. Ce sont des lacunes ou des valeurs qualitatives.
5. **Lignes techniques** (MP/MT, FDC/ADP, T2_CAS) : on les conserve, marquées « ligne technique ».

## 4. Lacunes constatées (premières entrées de la table `lacune`)
| Lacune | Responsable | Constat |
|---|---|---|
| Pas de jeu « dépenses selon destination » publié pour la LFI 2024, 2025 ou 2026 sur data.economie.gouv.fr (le dernier est le PLF 2025) | Direction du Budget | recherche dans le catalogue, 2026-10-26 |
| Dépenses fiscales PLF 2024 publiées **sans montants** en open data | Direction du Budget | profil `etat_depenses_fiscales_plf2024` |
| 63 dépenses fiscales « non chiffrées » (nc) et 42 « inférieures à 0,5 M€ » (ε) en prévision 2026 | Direction du Budget / DLF | profil `etat_budget_vert_plf2026` |
| Pas de présentation fonctionnelle des comptes **régionaux** sur data.ofgl.fr (il y en a une pour les départements) | OFGL / DGFiP | recherche dans le catalogue, 2026-10-26 |
| Tableaux INSEE COFOG 3.301-3.307 de l'édition 2025 reportés à décembre 2026 | INSEE | page insee.fr/fr/statistiques/8988847 |
| 3 agrégats OFGL sans définition officielle publiée | OFGL | comparaison des jeux |
