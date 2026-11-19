# Profil : PLF 2025 - Dépenses 2025 selon destination

- **id** : `etat_plf2025_destination`
- **éditeur** : Direction du Budget (DB)
- **périmètre** : Budget de l'État : crédits prévus au PLF 2025 (AE/CP) par mission, programme, action, sous-action
- **collecte** : `2026-10-26T225312Z`, sha256 `dd09f3831f868d78…`, 0.5 Mo
- **URL** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/plf25-depenses-2025-selon-destination/exports/csv?delimiter=%3B&use_labels=false
- **lignes** : 2404 (largeur incohérente : 0)
- **séparateur** : `;`

| colonne | type | remplies | manquantes (marqueurs) | distinctes | min / max | valeurs fréquentes |
|---|---|---|---|---|---|---|
| `exercice` | numérique | 2404 | 0  | 1 | 2025 / 2025 |  |
| `loi` | texte | 2404 | 0  | 1 |  | `PLF`×2404 |
| `typebudget` | texte | 2404 | 0  | 4 |  | `BG`×2289, `CAS`×65, `BA`×34, `CCF`×16 |
| `ministere` | numérique | 2404 | 0  | 20 | 1 / 70 |  |
| `libelle_ministere` | texte | 2404 | 0  | 20 |  | `Armées et anciens combattants`×460, `Services du Premier ministre`×217, `Budget et comptes publics`×205, `Intérieur`×205, `Éducation nationale`×196, `Partenariat avec les collectivités terri`×140, `Économie, finances et industrie`×128, `Justice`×116, `Agriculture, souveraineté alimentaire et`×109, `Transition écologique, énergie, climat e`×106, `Culture`×100, `Enseignement supérieur et recherche`×83 |
| `mission` | texte | 2404 | 0  | 46 |  | `DA`×434, `EC`×214, `TA`×178, `RA`×134, `SB`×120, `JA`×116, `GA`×105, `DC`×88, `TB`×82, `AC`×74, `CB`×74, `DB`×66 |
| `libelle_mission` | texte | 2404 | 0  | 46 |  | `Défense`×434, `Enseignement scolaire`×214, `Écologie, développement et mobilité dura`×178, `Recherche et enseignement supérieur`×134, `Sécurités`×120, `Justice`×116, `Gestion des finances publiques`×105, `Direction de l'action du Gouvernement`×88, `Travail, emploi et administration des mi`×82, `Agriculture, alimentation, forêt et affa`×74, `Culture`×74, `Économie`×66 |
| `programme` | numérique | 2404 | 0  | 167 | 101 / 869 |  |
| `libelle_programme` | texte | 2404 | 0  | 167 |  | `Équipement des forces`×216, `Soutien de la politique de la défense`×146, `Enseignement scolaire public du second d`×63, `Préparation et emploi des forces`×54, `Police nationale`×51 |
| `action` | texte | 2404 | 0  | 694 |  | `146-07`×72, `146-09`×58, `146-08`×34, `146-10`×27, `212-67`×24 |
| `libelle_action` | texte | 2404 | 0  | 661 |  | `Commandement et maîtrise de l'informatio`×72, `Engagement et combat`×58, `Soutien`×43, `Projection - mobilité - soutien`×34, `Commandement, ressources humaines et log`×30 |
| `sous_action` | texte | 628 | 1776 `(vide)`×1776 | 289 |  | `152-04-01`×6, `212-08-01`×5, `308-06-03`×5, `158-01-01`×5, `308-06-01`×4 |
| `libelle_sous_action` | texte | 628 | 1776 `(vide)`×1776 | 280 |  | `Renseignement extérieur`×7, `Ressources humaines des forces aériennes`×6, `Renseignement d'intérêt militaire`×6, `Commandement, ressources humaines et log`×6, `Fonction santé`×6 |
| `categorie` | numérique | 2404 | 0  | 19 | 10 / 73 |  |
| `titre` | numérique | 2404 | 0  | 7 | 1 / 7 |  |
| `autorisation_engagement` | numérique | 2404 | 0  | 2158 | 0 / 1.26692e+11 |  |
| `credit_de_paiement` | numérique | 2404 | 0  | 2271 | 0 / 1.26692e+11 |  |
