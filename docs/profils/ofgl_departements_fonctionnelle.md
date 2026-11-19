# Profil : Comptes des départements 2012-2025 - Présentation fonctionnelle

- **id** : `ofgl_departements_fonctionnelle`
- **éditeur** : Observatoire des finances et de la gestion publique locales (OFGL), à partir des balances DGFiP
- **périmètre** : Départements : dépenses et recettes par fonction (social, routes, collèges...)
- **collecte** : `2026-10-26T225321Z`, sha256 `b065b08b884ed103…`, 105.1 Mo
- **URL** : https://data.ofgl.fr/api/explore/v2.1/catalog/datasets/ofgl-base-departements-fonctionnelle/exports/csv?delimiter=%3B&use_labels=false&where=exer+%3E%3D+date%272020%27
- **lignes** : 392027 (largeur incohérente : 0)
- **séparateur** : `;`

| colonne | type | remplies | manquantes (marqueurs) | distinctes | min / max | valeurs fréquentes |
|---|---|---|---|---|---|---|
| `exer` | numérique | 392027 | 0  | 6 | 2020 / 2025 |  |
| `outre_mer` | texte | 392027 | 0  | 2 |  | `Non`×381055, `Oui`×10972 |
| `reg_code` | numérique | 392027 | 0  | 15 | 1 / 93 |  |
| `reg_name` | texte | 392027 | 0  | 15 |  | `Auvergne-Rhône-Alpes`×53438, `Occitanie`×51397, `Nouvelle-Aquitaine`×46725, `Île-de-France`×45027, `Grand Est`×35144, `Bourgogne-Franche-Comté`×27297, `Provence-Alpes-Côte d'Azur`×24173, `Centre-Val de Loire`×20773, `Pays de la Loire`×20635, `Normandie`×20360, `Hauts-de-France`×19532, `Bretagne`×16554 |
| `dep_tranche_population` | numérique | 392027 | 0  | 5 | 0 / 4 |  |
| `dep_status` | texte | 392027 | 0  | 3 |  | `rural`×253097, `urbain`×127958, `urbain/rural`×10972 |
| `dep_code` | numérique (mixte) | 392027 | 0  | 97 | 1 / 976 | `75`×18217, `691`×6334, `67A`×5471, `73`×5297, `31`×4859 |
| `dep_name` | texte | 392027 | 0  | 97 |  | `Paris`×18217, `Métropole de Lyon`×6334, `Alsace`×5471, `Savoie`×5297, `Haute-Garonne`×4859 |
| `categ` | texte | 392027 | 0  | 3 |  | `DEPT`×367476, `PARIS`×18217, `ML`×6334 |
| `siren` | numérique | 392027 | 0  | 99 | 2.00047e+08 / 2.2985e+08 |  |
| `ident` | numérique | 392027 | 0  | 275 | 2.00047e+13 / 2.2985e+13 |  |
| `lbudg` | texte | 392027 | 0  | 288 |  | `VILLE DE PARIS`×7938, `MET DE LYON`×5579, `DEP SAVOIE`×4885, `DEP PUY-DE-DOME`×4674, `DEP EURE`×4486 |
| `type_de_budget` | texte | 392027 | 0  | 2 |  | `Budget principal`×362779, `Budget annexe`×29248 |
| `nomen` | texte | 392027 | 0  | 2 |  | `M57`×225509, `M52`×166518 |
| `agregat` | texte | 392027 | 0  | 17 |  | `Dépenses totales hors remb`×62307, `Dépenses de fonctionnement`×58300, `Achats et charges externes`×44415, `Dépenses d'intervention`×41983, `Dépenses d'investissement hors remb`×37120, `Subventions aux personnes de droit privé`×28035, `Autres dépenses de fonctionnement`×27454, `Subventions d'équipement versées`×26654, `Dépenses d'équipement`×24027, `Frais de personnel`×22024, `Autres dépenses d'investissement`×5711, `Frais d'hébergement`×4673 |
| `montant` | numérique | 392027 | 0  | >5000 | -1.80732e+07 / 2.73344e+09 |  |
| `ptot` | numérique | 392027 | 0  | 578 | 80049 / 2.64699e+06 |  |
| `euros_par_habitant` | numérique | 392027 | 0  | >5000 | -25.2503 / 1415.9 |  |
| `niveau_hierarchique` | numérique | 392027 | 0  | 4 | 1 / 4 |  |
| `fonctionnelle_1` | texte | 392027 | 0  | 340 |  | `0-Services généraux`×8754, `02-Administration générale`×7120, `3-Culture, vie sociale, jeunesse, sports`×6931, `31-Culture`×6538, `020-Administration générale de la collec`×6182 |
| `fonction` | numérique | 392027 | 0  | 285 | 0 / 7222 |  |
| `nom_fonction` | texte | 392027 | 0  | 264 |  | `Services communs`×25601, `Action sociale`×8493, `Administration générale`×7120, `Culture, vie sociale, jeunesse, sports e`×6931, `Culture`×6538 |
| `cbudg` | numérique | 392027 | 0  | 2 | 1 / 3 |  |
| `fonction2` | texte | 392027 | 0  | 285 |  | `F0`×8754, `F4`×7627, `F5`×7572, `F02`×7120, `F3`×6931 |
| `ptot_n` | numérique | 392027 | 0  | 97 | 80227 / 2.63688e+06 |  |
| `classement_fonctionnel_2` | texte | 392027 | 0  | 3 |  | `Autres`×381291, `62-Voirie`×5415, `221-Collèges`×5321 |
