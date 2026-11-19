# Profil : PLF 2026 - Budget vert

- **id** : `etat_budget_vert_plf2026`
- **éditeur** : Direction du Budget (DB)
- **périmètre** : Budget de l'État : crédits budgétaires, dépenses fiscales et taxes affectées (exécution 2024, LFI 2025, PLF 2026)
- **collecte** : `2026-10-26T225311Z`, sha256 `1db81028ead28c07…`, 0.6 Mo
- **URL** : https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/plf-2026-budget-vert/exports/csv?delimiter=%3B&use_labels=false
- **lignes** : 1816 (largeur incohérente : 0)
- **séparateur** : `;`

| colonne | type | remplies | manquantes (marqueurs) | distinctes | min / max | valeurs fréquentes |
|---|---|---|---|---|---|---|
| `type_depense` | texte | 1816 | 0  | 3 |  | `Crédits budgétaires`×1269, `Dépenses fiscales`×483, `Taxes affectées plafonnées`×64 |
| `mission` | texte | 1816 | 0  | 46 |  | `Défense`×199, `Écologie, développement et mobilité dura`×186, `Cohésion des territoires`×143, `Économie`×95, `Travail, emploi et administration des mi`×87, `Enseignement scolaire`×82, `Agriculture, alimentation, forêt et affa`×78, `Investir pour la France de 2030`×71, `Recherche et enseignement supérieur`×70, `Solidarité, insertion et égalité des cha`×65, `Outre-mer`×52, `Sécurités`×51 |
| `numero_programme` | numérique | 1811 | 5 `(vide)`×5 | 156 | 101 / 848 |  |
| `programme` | texte | 1796 | 20 `(vide)`×20 | 153 |  | `Équipement des forces`×81, `Urbanisme, territoires et amélioration d`×80, `Développement des entreprises et régulat`×77, `Soutien de la politique de la défense`×66, `Compétitivité et durabilité de l'agricul`×56 |
| `code_action_si_credit_budgetaire` | texte | 1249 | 567 `(vide)`×567 | 730 |  | `MP/MT - PLF 2025`×76, `FDC/ADP`×69, `T2_CAS`×46, `146-07`×25, `146-09`×21 |
| `action_si_credit_budgetaire` | texte | 1249 | 567 `(vide)`×567 | 679 |  | `MP/MT - Mesure de périmètre/transfert - `×76, `Fonds de concours et attributions de pro`×69, `T2 - contribution au CAS`×46, `Commandement et maîtrise de l'informatio`×25, `Engagement et combat`×21 |
| `affectataire_si_taxe_affectee` | texte | 64 | 1752 `(vide)`×1752 | 37 |  | `Agence de financement des infrastructure`×9, `Agence nationale des titres sécurisés (A`×5, `Société des Grands Projets (SGP)`×5, `Agence nationale de sécurité sanitaire, `×4, `Agence nationale du sport (ANS)`×3, `Agence de services et de paiement (ASP)`×2, `Centre national de la musique (CNM)`×2, `Organismes mentionnés à l'Art. L.742-9 d`×2, `Chambres de commerce et d'industrie`×2, `France compétences`×2, `Agence nationale du contrôle du logement`×2, `Établissements publics fonciers (EPF : u`×1 |
| `impot_si_depense_fiscale` | texte | 483 | 1333 `(vide)`×1333 | 10 |  | `Impôt sur le revenu`×190, `Impôt sur le revenu et impôt sur les soc`×52, `Droits d'enregistrement et de timbre`×49, `Taxe sur la valeur ajoutée`×48, `Impôt sur les sociétés`×40, `Impôts locaux`×38, `Accise sur les énergies`×36, `Autres droits`×23, `Autres impôts directs`×6, `Taxe d'archéologie préventive`×1 |
| `code_depense` | texte | 1816 | 0  | 1487 | 40101 / 990301 | `MP/MT - PLF 2025`×76, `FDC/ADP`×69, `T2_CAS`×46, `MP/MT - LFI 2025`×18, `MP/MT - PLF 2026`×16 |
| `libelle` | texte | 1816 | 0  | 1536 |  | `MP/MT - Mesure de périmètre/transfert - `×76, `Fonds de concours et attributions de pro`×68, `T2 - contribution au CAS`×46, `MP/MT - Mesure de périmètre/transfert - `×18, `MP/MT - Mesure de périmètre/transfert - `×16 |
| `attenuation_climat` | numérique | 1689 | 127 `(vide)`×127 | 5 | -1 / 3 |  |
| `adaptation_climat` | numérique | 1689 | 127 `(vide)`×127 | 4 | 0 / 3 |  |
| `eau` | numérique | 1689 | 127 `(vide)`×127 | 4 | 0 / 3 |  |
| `dechets` | numérique | 1689 | 127 `(vide)`×127 | 5 | -1 / 3 |  |
| `pollutions` | numérique | 1689 | 127 `(vide)`×127 | 5 | -1 / 3 |  |
| `biodiversite` | numérique | 1689 | 127 `(vide)`×127 | 5 | -1 / 3 |  |
| `cotation_globale` | texte | 1689 | 127 `NC`×127 | 4 |  | `Neutre`×1346, `Favorable`×252, `Défavorable`×71, `Mixte`×20 |
| `2024_si_different_de_100` | numérique | 129 | 1687 `(vide)`×1687 | 88 | 0 / 1 |  |
| `2025_si_different_de_100` | numérique | 145 | 1671 `(vide)`×1671 | 96 | 0 / 1 |  |
| `2026_si_different_de_100` | numérique | 133 | 1683 `(vide)`×1683 | 88 | 0 / 1 |  |
| `categorie_generale` | texte | 1815 | 1 `(vide)`×1 | 19 |  | `Neutre - autres`×379, `Régalien`×365, `Dépenses fiscales`×356, `Non coté - autres`×101, `Éducation`×82, `Transports`×79, `Transferts sociaux, politiques sociales `×72, `Politiques de l'emploi`×71, `Bâtiments`×55, `Énergie`×44, `Industrie`×44, `Autres`×32 |
| `execution_2024_cp` | numérique | 1605 | 211 `(vide)`×211 | 1410 | -1.18116e+10 / 5.32289e+10 |  |
| `lfi_2025_cp_ou_prevision_2025_si_depense_fiscale` | numérique | 1401 | 415 `(vide)`×415 | 1178 | -1.29293e+10 / 5.45572e+10 |  |
| `plf_2026_cp_ou_prevision_2026_si_depense_fiscale` | numérique | 1374 | 442 `(vide)`×442 | 1170 | -1.3337e+10 / 5.47437e+10 |  |
| `depenses_fiscales_e_montant_inferieur_a_0_5_meur_nc_montant_non_calcule_en_prevision_2026` | vide | 0 | 1816 `(vide)`×1711, `nc`×63, `ε`×42 | 0 |  |  |
