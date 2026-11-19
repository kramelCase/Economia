# Regard de l'économiste : qui pose quelles questions, et comment y répondre sans tromper

Auteur : spécialiste finances publiques / analyse de données du groupe de conception. Date : 2026-10-27.
Lu avant d'écrire : `docs/vision/BRIEF.md`, `README.md`, `docs/INVENTAIRE.md`, `sources.yaml`,
`content/lacunes.yaml`, `content/concepts.yaml`. Les identifiants de jeux cités comme « vérifié » ont été
interrogés le 2026-10-27 (API Opendatasoft de data.ofgl.fr et data.economie.gouv.fr, catalogue SDMX
Eurostat, API SDMX BDM de l'INSEE, catalogue DREES). Aucun chiffre n'est donné ici : quand il en faudrait
un, il est écrit « [montant réel issu de …] ».

Légende données : **EN BASE** = déjà dans `comptes.sqlite` ; **À COLLECTER** = source officielle
identifiée (✔ = identifiant vérifié en ligne, ? = à confirmer avant d'écrire le chargeur).

---

## 0. Ce que l'économiste retient du brief en une page

Le produit a une valeur rare : **la traçabilité ligne à ligne**. Tous les autres sites (fipeco, OFCE,
Cour des comptes, data.gouv, Eurostat) donnent soit l'analyse sans la ligne, soit la ligne sans
l'analyse. Le « moteur d'exploration » ne vaut que s'il garde cette promesse **même quand la question
est floue**. Conséquence : le cœur du produit n'est pas un graphique, c'est un **résolveur de question**
qui, pour toute question, choisit (1) un indicateur officiel, (2) un périmètre, (3) un stade, (4) une
unité, (5) une comparaison légitime — et dit explicitement ce qu'il n'a pas pu faire.

Trois réalités contraignent tout le reste :
1. **Quatre périmètres qui ne s'additionnent pas** : APU (comptabilité nationale, Eurostat/INSEE), État
   (comptabilité budgétaire LOLF), Sécurité sociale (LFSS, régimes obligatoires de base + FSV),
   collectivités (comptabilité locale M14/M52/M57, OFGL). Le même mot « dépense » désigne quatre choses.
2. **Trois stades** : prévu (PLF), voté (LFI, LFR), réalisé (exécution / loi relative aux résultats de la
   gestion). Plus, pour les dépenses fiscales, des **estimations** même pour le passé.
3. **Des ruptures** : nomenclatures (M52→M57, missions LOLF recomposées), périmètres (fusions de régions
   2016, Collectivité européenne d'Alsace, collectivités uniques, transferts de compétences), bases
   des comptes nationaux, données provisoires (drapeau `p` Eurostat sur 2023-2024).

---

## 1. Profils utilisateurs

Format : *questions telles qu'il les taperait* → besoins → niveau → contexte d'usage. Les profils sont
regroupés par famille ; la dernière famille recense ceux auxquels on ne pense pas.

### 1.1 Professionnels de l'information

**Journaliste de desk (presse quotidienne, web)**
- « dépense publique France 2024 % PIB », « budget armées 2026 vs 2024 », « combien coûte le CIR »,
  « dette des départements », « hausse budget justice PLF 2026 ».
- Besoins : chiffre exact + phrase de contexte réutilisable + **libellé officiel** + lien de source
  citable ; évolution sur 5-10 ans ; « c'est beaucoup ou pas ? » (comparaison). Export PNG/CSV.
- Niveau : moyen ; confond souvent PLF/LFI, AE/CP, État/APU.
- Contexte : bureau, deadline de 30 min ; copie-colle dans un CMS. Veut une **URL stable** par réponse.

**Journaliste politique / éditorialiste**
- « qui a le plus augmenté la dette, Hollande ou Macron », « cadeaux fiscaux aux riches », « budget
  de l'Élysée ».
- Besoins : séries longues, attribution par période (avec avertissement : un gouvernement n'est pas
  l'unique cause d'une variation), catégories officielles neutres.
- Contexte : plateau, préparation d'interview la veille.

**Journaliste de plateau TV / radio, en direct**
- Tape trois mots pendant que l'invité parle : « dette 3000 milliards », « fonctionnaires coût ».
- Besoins : **vérification en < 10 s** ; un ordre de grandeur et la référence ; un verdict prudent.
- Niveau : faible à moyen. Contexte : **mobile, debout, une main**. Écran lisible à distance (régie).

**Fact-checkeur (cellules de vérification des médias, AFP, plateformes)**
- « est-ce vrai que la France est championne d'Europe des dépenses publiques », « l'État dépense
  plus pour la dette que pour l'éducation ? », « les niches fiscales coûtent 90 milliards ? ».
- Besoins : **reconstituer d'où vient le chiffre de l'affirmation** (quel périmètre, quelle année,
  quelle source), exposer les définitions concurrentes, citer la ligne. Archivage (permalien daté,
  version des données / sha256).
- Niveau : élevé sur la méthode, variable sur la compta publique. Contexte : bureau, travail de fond.

**Datajournaliste**
- « télécharger dépenses par fonction toutes années », « API OFGL départements », « séries COFOG
  tous pays ».
- Besoins : export CSV propre avec colonnes source/ligne/unité/stade, API documentée, notes de
  rupture. Niveau : élevé. Contexte : bureau, Python/R/Datawrapper.

**Presse locale / régionale**
- « budget du département de la Sarthe », « dette de ma région par habitant », « classement des
  départements investissement ».
- Besoins : fiche territoire, comparaison avec départements **comparables** (strate, ruralité), rang,
  évolution. Contexte : bureau, souvent seul sur le sujet ; veut une carte.

**Presse étrangère / correspondants**
- « French public debt to GDP compared to Italy », « France deficit procedure ».
- Besoins : EN, comparaisons UE harmonisées (Eurostat), lexique traduit officiellement.

### 1.2 Savoir et enseignement

**Économiste (think tank, institut de conjoncture, banque, notation)**
- « dépense de protection sociale % PIB France Allemagne Suède 1995-2024 », « solde primaire »,
  « charge d'intérêts », « écart PLF exécution mission par mission ».
- Besoins : séries harmonisées, unités multiples, décomposition, téléchargement, **drapeaux
  provisoire / révisé**, millésime. Niveau : expert ; il juge la crédibilité du site en 2 minutes sur
  le traitement des périmètres. Contexte : bureau, double écran.

**Chercheur (économie publique, science politique, géographie)**
- « dépenses sociales des départements 2020-2025 par fonction », « effet de la M57 sur les séries ».
- Besoins : données brutes avec provenance, documentation des ruptures, citation académique (DOI ou
  permalien + date de collecte + sha256). Niveau : expert.

**Étudiant (licence éco/droit, Sciences Po, IEP, master finances publiques)**
- « c'est quoi la différence entre déficit public et déficit de l'État », « part de l'éducation dans
  la dépense publique », « graphique dette depuis 1995 ».
- Besoins : définitions citées, schémas des périmètres, graphiques réutilisables (licence claire).
- Contexte : mobile la veille d'un partiel, ordinateur pour un mémoire.

**Candidat aux concours administratifs (INSP, IRA, attaché territorial, CRC, commissaire des armées…)**
— profil sous-estimé, gros volume, très motivé.
- « structure du budget de l'État missions », « ONDAM », « règles d'équilibre des collectivités »,
  « épargne brute définition ».
- Besoins : lexique juridique (LOLF, CGCT), ordres de grandeur à connaître, fiches imprimables.

**Enseignant (SES, histoire-géo/EMC, BTS, IUT GEA)**
- « activité élèves budget de l'État », « carte dépenses par habitant départements ».
- Besoins : parcours guidés, graphiques simples projetables, questions-réponses vérifiables, absence
  de parti pris politique (exigence institutionnelle). Contexte : vidéoprojecteur, salle info.

**Élève de lycée** : « à quoi servent les impôts », « combien coûte un élève ». Besoin : réponse
simple et juste, sans jargon, avec le lien vers la définition.

### 1.3 Décision publique

**Élu national / collaborateur parlementaire / administrateur des assemblées**
- « crédits programme 172 PLF 2026 vs LFI 2025 », « dépenses fiscales rattachées à la mission
  Agriculture », « coût des niches IS », « écart AE/CP ».
- Besoins : niveau programme/action, comparaison PLF/LFI/exécution, **dépenses fiscales rattachées
  à une mission** (déjà dans le budget vert), export pour amendements, citation exacte. Niveau : élevé.
  Contexte : bureau, période budgétaire octobre-décembre (pic d'usage à prévoir).

**Élu local (majorité ou opposition) / collaborateur de groupe**
- « dette de mon département comparée à la moyenne », « capacité de désendettement », « dépenses de
  personnel par habitant », « mon département investit-il moins que les autres ».
- Besoins : comparaison avec pairs, série longue, définitions OFGL, export pour une intervention en
  séance (débat d'orientation budgétaire). Contexte : bureau, veille de séance.

**Candidat à une élection (et son équipe programme)**
- « combien coûterait de … », « évolution des impôts locaux depuis 2012 », « où se situe ma ville ».
- Besoins : faits incontestables pour un tract, comparaisons, **pas de chiffrage de programme** (que
  l'outil ne doit pas faire : pas de modèle, pas de méthode inventée). Contexte : mobile en campagne.
- Risque : instrumentalisation ; d'où la neutralité et le permalien qui fige le contexte.

**Agent de collectivité (DAF, contrôleur de gestion, analyste financier)**
- « ratio dépenses de fonctionnement / habitant strate », « médiane épargne brute départements
  2024 », « fonction 4 action sociale évolution ».
- Besoins : benchmark rapide pour le rapport d'orientation budgétaire, séries consolidées vs budget
  principal, export. Niveau : expert du local, moins du national.

**Agent de l'État (préfecture, DDFiP, ministère)** : contrôle de cohérence, benchmark, « dépenses
de l'État dans ma région » (non disponible proprement : l'État ne publie pas d'exécution
territorialisée complète — **lacune à documenter**).

**Magistrat financier / auditeur (Cour des comptes, CRC) et inspections** : usage marginal mais
exigeant ; testera la fidélité aux définitions.

### 1.4 Société civile organisée

**Association de contribuables / think tank libéral** : « dépense publique record », « nombre de
fonctionnaires », « gaspillage ».
**Association altermondialiste / ONG de justice fiscale** : « niches fiscales des entreprises »,
« aides aux entreprises », « impôt sur les sociétés taux effectif ».
**ONG environnementale** : « dépenses défavorables à l'environnement » (budget vert : objet officiel
du jeu en base), « niches sur les énergies fossiles ».
**Syndicat (fonction publique, salariés)** : « masse salariale de l'État », « dépenses de personnel
des départements », « exonérations de cotisations ».
**Organisation patronale / chambre consulaire** : « prélèvements obligatoires France vs UE »,
« impôts de production ».
**Association d'usagers / de solidarité** : « dépenses RSA par département », « APA », « aide
sociale à l'enfance ».
- Besoins communs : un chiffre défendable devant un contradicteur. L'outil doit servir **les deux
  camps avec les mêmes catégories** (test de neutralité : une même page doit pouvoir être citée par
  les deux).

### 1.5 Monde économique

**Entreprise / expert-comptable / avocat fiscaliste** : « coût du crédit d'impôt recherche »,
« dépenses fiscales TVA taux réduit », « fiscalité locale CFE commune ».
**Investisseur obligataire / analyste crédit** : « dette négociable de l'État », « charge d'intérêts
», « besoin de financement » (sources AFT, hors base, à collecter).
**Consultant secteur public / éditeur de logiciels pour collectivités** : benchmark, API.

### 1.6 Grand public et créateurs

**Créateur de contenu (YouTube, TikTok, podcast, newsletter)**
- « graphique dette France depuis 1995 », « en quoi est dépensé 1000 € d'impôts », « comparaison
  pays dépense santé ».
- Besoins : visuel exportable aux formats vertical/carré **avec la source incrustée**, licence de
  réutilisation explicite, phrase de méthode courte. Contexte : bureau pour préparer, mobile pour
  publier.

**Utilisateur de réseaux sociaux face à une infographie virale**
- Colle un chiffre : « 1000 milliards de dette en 3 ans c'est vrai ? », « l'AME coûte plus que la
  justice ? ».
- Besoins : verdict compréhensible, en 1 écran, sans être infantilisé, partageable en retour.
- Contexte : **mobile, 30 secondes**, souvent depuis un lien. Niveau : faible ; méfiant envers les
  institutions → la ligne source est l'argument d'autorité.

**Citoyen contribuable**
- « où vont mes impôts », « pourquoi ma taxe foncière augmente », « combien doit chaque Français »,
  « budget de mon département ».
- Besoins : réponse personnelle (son territoire), sans jargon, lien vers le lexique ; savoir **à qui
  s'adresser** quand une donnée manque (principe 4).

**Retraité / parent / usager d'un service** : « dépense par élève de collège dans mon
département », « dépenses pour les routes ». Besoin : relier une compétence à la collectivité qui
l'exerce (qui fait quoi : collèges = département, lycées = région, écoles = commune).

**Membre d'un conseil citoyen / budget participatif / conseil de développement** : comprendre le
budget local avant de voter ; veut des ordres de grandeur.

### 1.7 Profils auxquels on ne pense pas

- **Agents IA et développeurs d'assistants** (LLM qui répondent à des questions budgétaires) : ils
  ont besoin d'une **API citable** renvoyant montant + périmètre + stade + ligne source. C'est
  potentiellement le premier « utilisateur » en volume et le meilleur vecteur de la promesse
  « chaque chiffre remonte à la ligne ». Exige : sorties structurées, URL de provenance stable.
- **Wikipédiens** : besoin de références stables et datées ; une page par indicateur et par année.
- **Documentalistes / bibliothécaires / CDI** : orientation, fiches de vocabulaire.
- **Traducteurs, interprètes, institutions européennes** : correspondances officielles FR/EN des
  termes (COFOG traduite officiellement, LOLF non).
- **Diplomates, ambassades, chercheurs étrangers** : comparaisons harmonisées.
- **Habitants d'Outre-mer** : collectivités uniques (Guyane, Martinique) et Mayotte, souvent cassent
  les comparaisons région/département ; ils doivent voir leur territoire traité, pas exclu.
- **Élus et agents de petites communes / intercommunalités** : dès que l'OFGL communal est collecté,
  le plus gros gisement d'utilisateurs locaux (≈ 35 000 communes).
- **Lanceurs d'alerte / militants anticorruption** : demandent la commande publique et les
  subventions (données DECP, « SCDL subventions ») — hors périmètre actuel, à signaler comme piste.
- **Agriculteurs, acteurs culturels, sportifs, monde associatif** : « combien l'État donne à mon
  secteur » → mission/programme, et dépenses fiscales rattachées ; attention, les fonds européens
  (PAC) ne sont pas dans le budget de l'État.
- **Formateurs d'élus, organismes de formation à la finance locale** : supports pédagogiques.
- **Personnes en litige ou en recours** (contentieux fiscal local) : taux votés (REI).

---

## 2. Catalogue des questions et analyses

Format de chaque ligne : **Question** · *indicateurs* · *comparaison pertinente* · **piège** ·
données.

### 2.1 Dépense publique (toutes administrations)

| Question | Indicateurs / comparaison | Piège méthodologique | Données |
|---|---|---|---|
| Combien dépense la France ? | Dépense totale S13, M€ et % PIB ; série 1995-2024 | % du PIB est un **ratio**, pas une part : la dépense inclut des transferts (pensions, prestations) qui ne sont pas « consommés par l'État » ; un PIB qui chute (2020) gonfle le ratio | EN BASE (COFOG `TOTAL`, S13) |
| Où va l'argent public ? | 10 divisions COFOG, % du total | Les crédits d'impôt restituables sont des dépenses en comptabilité nationale ; la protection sociale (GF10) inclut les retraites et pèse sur toute comparaison | EN BASE |
| Part de l'éducation / de la santé / de la défense | GFxx en % total et % PIB, évolution | **Ne pas confondre** avec la mission « Enseignement scolaire » (État seul, comptabilité budgétaire) ; COFOG = toutes APU | EN BASE |
| Qui dépense : État, collectivités, Sécu ? | S1311, S1313, S1314 | **La somme des sous-secteurs dépasse S13** (transferts entre administrations non consolidés) : à afficher comme tel, jamais additionné | EN BASE ; écart déjà contrôlé |
| La dépense augmente-t-elle ? | M€ courants, M€ constants, % PIB, € par habitant | En euros courants tout augmente (inflation) ; choix du déflateur (prix du PIB vs IPC) à annoncer | En base pour M€ et % PIB ; déflateur et population **À COLLECTER** (Eurostat `nama_10_gdp` ✔, `demo_pjan` ✔ / INSEE IPC BDM `001759970` ✔) |
| La France dépense-t-elle plus que les autres ? | % PIB par fonction, UE27 et pays choisis | Effet institutionnel : retraites par capitalisation privée (Pays-Bas…), santé par assurance privée obligatoire ; la comparaison porte sur la **dépense publique**, pas sur l'effort total d'un pays | **À COLLECTER** : même flux `gov_10a_exp` ✔ avec `geo` élargi (chargeur existant) |
| Combien par habitant pour la santé ? | M€ / population | Population au 1er janvier vs moyenne annuelle ; pour l'international, préférer % PIB ou SPA (standards de pouvoir d'achat) | Population **À COLLECTER** (`demo_pjan` ✔ ou `nama_10_pe` ✔) |
| Les chiffres 2023-2024 sont-ils définitifs ? | Drapeau `p` | Révisions annuelles ; changement de base INSEE (base 2020) peut réécrire le passé | EN BASE (drapeau) ; millésime à stocker |

### 2.2 Budget de l'État

| Question | Indicateurs / comparaison | Piège | Données |
|---|---|---|---|
| Budget d'une mission (armées, justice…) | CP par mission, PLF 2026 vs LFI 2025 vs exécution 2024 | **Stades** différents ; AE (engagements pluriannuels) ≠ CP (paiements de l'année) ; mesures de périmètre (MP/MT) faussent une évolution | EN BASE (budget vert, PLF 2025) |
| Détail d'un programme / d'une action | CP et AE par action, sous-action | Sous-action seulement au PLF 2025 (pas de LFI par destination : **lacune** déjà documentée) | EN BASE |
| Le budget voté a-t-il été dépensé ? | Taux d'exécution = exécuté / LFI de la même année | Le budget vert ne donne pas la LFI 2024 face à l'exécution 2024 ; reports, annulations, lois de finances rectificatives, fonds de concours | **À COLLECTER** : PLRG 2024 ✔ `plrg-2024` et PLRG 2025 ✔ (`projet-de-loi-relatif-aux-resultats-de-la-gestion-et-portant-approbation-des-comptes-de-lannee-plrg-2025`) sur data.economie.gouv.fr |
| Combien coûte la dette de l'État ? | Charge de la dette (mission « Engagements financiers de l'État ») | Charge budgétaire ≠ intérêts en comptabilité nationale (D41 APU) ; indexation sur l'inflation des OATi | Mission EN BASE ; intérêts APU **À COLLECTER** (`gov_10a_main` ✔) |
| Le budget général fait combien ? | BG, CAS, CCF, BA séparés | **BG + CAS + CCF ne s'additionnent pas** (logique propre, doubles comptes : CAS Pensions alimenté par le BG via T2_CAS) | EN BASE, avec drapeau « ne s'additionne pas » |
| Masse salariale de l'État | Titre 2 par mission | Le T2 inclut la contribution au CAS Pensions ; comparer hors CAS ou avec CAS, jamais mélangé | EN BASE (titre/catégorie PLF 2025) |
| Où en est le déficit de l'État cette année ? | Solde budgétaire mensuel cumulé | Saisonnalité forte (comparer au même mois de l'année précédente, jamais au mois précédent) ; **déficit de l'État ≠ déficit public** | **À COLLECTER** : `situations-mensuelles-budgetaires-series-longues` ✔ (séries 2013→, DGFiP) et `situation-mensuelle-de-l-etat` ✔ |
| Prélèvements sur recettes (UE, collectivités) | PSR par bénéficiaire | Ils ne sont **pas** des crédits de mission : « le budget de l'État » sans eux sous-estime ce qui sort | ? Voies et moyens tome I (jeu à identifier) |
| Le budget est-il « vert » ? | Cotation favorable/défavorable/neutre/mixte | Cotation officielle mais conventionnelle ; « neutre » et « non coté » ne sont pas la même chose | EN BASE |
| Bilan / patrimoine de l'État | Actif, passif, situation nette | Comptabilité générale (en droits constatés) ≠ budgétaire | **À COLLECTER** : `balances_des_comptes_etat` ✔ (bilan 2006-2024) |

### 2.3 Fiscalité et dépenses fiscales (« niches »)

| Question | Indicateurs / comparaison | Piège | Données |
|---|---|---|---|
| Combien coûtent les niches ? | Somme des dépenses fiscales chiffrées 2024-2026, nombre de non chiffrées | Le coût est une **estimation** (même pour le passé) contre une norme fiscale conventionnelle ; l'additionner est la pratique officielle mais **ce n'est pas une recette récupérable** (effets de comportement) ; 63 `nc` et 42 `ε` : un total est toujours un **minorant** | EN BASE ; lacunes EN BASE |
| Les plus grosses niches | Classement par `code_depense` | Regrouper les lignes ventilées ; changement de périmètre d'une niche d'une année à l'autre ; une niche peut être déclassée (sortie de la liste) sans disparaître | EN BASE |
| Niches par impôt (IR, IS, TVA) | Somme par impôt | Rapporter au **produit de l'impôt** exige les recettes fiscales (même année, même stade) | Recettes **À COLLECTER** |
| « Cadeaux aux riches / aux entreprises » | Catégories officielles : dépenses fiscales par impôt et par bénéficiaire quand la source le dit ; exonérations de cotisations sociales | Il n'existe pas, à notre connaissance, de **série statistique officielle unique** des « aides aux entreprises » (estimations ponctuelles de commissions parlementaires) : le dire, ne pas en fabriquer une | Partiel EN BASE ; exonérations : LFSS annexe 4 (? à identifier) |
| Combien rapporte l'impôt sur le revenu / la TVA ? | Recettes par impôt | **Brut vs net** (remboursements et dégrèvements) ; recette de l'État vs recette de toutes APU (la TVA est partagée avec la Sécu et les collectivités) | **À COLLECTER** : Eurostat `gov_10a_taxag` ✔ (APU, par impôt, UE) ; SMB pour l'État |
| Taux de prélèvements obligatoires | PO / PIB | Définition INSEE (concept déjà au lexique) vs « recettes publiques » (plus large) ; comparaison UE : traitement des crédits d'impôt | **À COLLECTER** (`gov_10a_taxag` ✔) |
| Pourquoi ma taxe foncière augmente ? | Taux votés (commune, intercommunalité), base (revalorisation forfaitaire nationale) | Décomposer **taux** (décision locale) et **base** (revalorisation légale + évolution physique) ; plusieurs collectivités votent un taux sur la même feuille | **À COLLECTER** : OFGL `rei` ✔ (recensement des éléments d'imposition, DGFiP) |

### 2.4 Dette et déficit

| Question | Indicateurs / comparaison | Piège | Données |
|---|---|---|---|
| Combien la France doit-elle ? | Dette de Maastricht APU, M€ et % PIB | **Brute, en valeur nominale** ; ≠ dette nette ; ≠ dette négociable de l'État (AFT) ; « par habitant » est une division du site, à signaler, et ne dit rien de la capacité de remboursement | **À COLLECTER** : Eurostat `gov_10dd_edpt1` ✔ (notification PDE, UE, par sous-secteur) ; trimestriel `gov_10q_ggdebt` ✔ |
| Le déficit public | Besoin de financement APU (B9) % PIB | **Déficit public ≠ déficit de l'État** (le premier inclut Sécu et collectivités, en comptabilité nationale) | `gov_10dd_edpt1` ✔ |
| Qui porte la dette ? | Dette par sous-secteur S1311/S1313/S1314 | La dette de la Sécu inclut la CADES ; consolidation entre sous-secteurs | `gov_10dd_edpt1` ✔ |
| Le déficit est-il dû aux intérêts ? | Solde primaire = solde − charges d'intérêts (D41) | Calcul du site sur une même source : légitime mais signalé | `gov_10a_main` ✔ |
| Quel président a « fait » le plus de dette ? | Variation de la dette sur la période | Attribution ≠ causalité (crise, taux, héritage) ; choisir le bornage (mandat commence en mai) ; présenter M€, % PIB et € constants côte à côte | `gov_10dd_edpt1` ✔ |
| Prévision gouvernementale vs réalisé | Trajectoire du PLF / programme de stabilité vs notification | Prévision = document politique ; ne jamais tracer comme une série observée | ? (rapports, rarement en open data structuré) → lacune |

### 2.5 Collectivités territoriales

| Question | Indicateurs / comparaison | Piège | Données |
|---|---|---|---|
| Budget de mon département / ma région | Dépenses totales, fonctionnement, investissement, € et €/hab | Agrégats **emboîtés** (jamais additionnés) ; consolidé vs budget principal | EN BASE (OFGL consolidé) |
| Mon département est-il endetté ? | Encours de dette, €/hab, capacité de désendettement (encours / épargne brute) | Comparer à des **pairs** (strate, profil) ; un ratio de solvabilité vaut mieux qu'un encours brut | EN BASE (si agrégats présents) |
| Comparer deux départements | Ratios €/hab ; rang ; médiane | Paris, Métropole de Lyon, Alsace (CEA depuis 2021), collectivités uniques : compétences différentes ; population de référence (celle de l'OFGL, à afficher) | EN BASE |
| Combien pour le social / les collèges / les routes ? | Fonctions des départements | **M52 → M57** : continuité par code à vérifier ; données **par budget, non consolidées** ; transferts de compétences (recentralisation du RSA à titre expérimental dans certains départements, à documenter depuis la source) | EN BASE (2020-2025) |
| Ma commune / mon intercommunalité | Mêmes agrégats | Communes et intercommunalités se partagent des compétences : comparer une commune seule est trompeur → proposer « bloc communal » (commune + groupement) **si l'OFGL le publie** (base « ensembles intercommunaux » `ofgl-base-ei` ✔) | **À COLLECTER** : `ofgl-base-communes-consolidee` ✔, `ofgl-base-gfp-consolidee` ✔, `ofgl-base-ei` ✔ |
| Dotations de l'État à ma collectivité | DGF et autres dotations | Les dotations sont aussi des dépenses (prélèvements sur recettes) de l'État : ne pas compter deux fois dans une vue « toutes APU » | **À COLLECTER** : `dotations-communes` ✔, `dotations-departements` ✔, `dotations-regions` ✔, `dotations-gfp` ✔ (data.ofgl.fr) |
| Régions : dépenses de lycées / transports | — | **Lacune** : pas de présentation fonctionnelle régionale (déjà documentée) | — |
| Évolution 2012-2025 des régions | Agrégats | **Fusion des régions 2016** : avant 2016, périmètre reconstitué ou non ? À vérifier dans la source et afficher | EN BASE |
| Les collectivités sont-elles en déficit ? | Épargne, besoin de financement | Règle d'or locale (équilibre de la section de fonctionnement) ≠ déficit en comptabilité nationale (S1313 peut être en besoin de financement) | EN BASE (local) + `gov_10dd_edpt1` ✔ |

### 2.6 Sécurité sociale et protection sociale

| Question | Indicateurs / comparaison | Piège | Données |
|---|---|---|---|
| Combien coûtent les retraites / la santé ? | COFOG GF10, GF07 ; prestations par risque | COFOG (APU) ≠ LFSS (régimes obligatoires de base) ≠ comptes de la protection sociale (DREES, inclut complémentaires) | COFOG EN BASE ; **À COLLECTER** DREES `305_les-comptes-de-la-protection-sociale` ✔ ; Eurostat ESSPROS `spr_exp_func` ✔ |
| Le « trou de la Sécu » | Solde des régimes obligatoires de base + FSV | Solde LFSS ≠ solde S1314 en comptabilité nationale ; prévision LFSS vs réalisé (Commission des comptes) | ? LFSS / CCSS : pas de jeu open data structuré identifié → **lacune candidate** (responsable : Direction de la Sécurité sociale) |
| ONDAM | Objectif voté vs réalisé | Objectif (plafond) ≠ dépense ; changements de périmètre annuels | ? même remarque |
| Aide sociale départementale (RSA, APA, PCH, ASE) | Dépenses et bénéficiaires | Les montants DREES et OFGL ne sont pas mesurés pareil (enquête vs balances) | **À COLLECTER** : DREES `376_les-depenses-d-aide-sociale-departementale` ✔, `apa-et-pch-montants-verses` ✔ |

### 2.7 Comparaisons internationales

| Question | Indicateurs | Piège | Données |
|---|---|---|---|
| France vs UE : dépense, dette, déficit, PO | % PIB, SPA par habitant | Uniquement sur sources harmonisées (Eurostat SEC 2010) ; ne jamais mélanger une source nationale et une source Eurostat dans une même comparaison ; moyenne UE pondérée (agrégat Eurostat) ≠ moyenne des pays | `gov_10a_exp` ✔, `gov_10dd_edpt1` ✔, `gov_10a_taxag` ✔, `gov_10a_main` ✔ |
| Classement « champion des dépenses » | Rang % PIB | Rang instable aux décimales près : montrer l'écart, pas seulement le rang ; pays de taille différente | idem |
| Hors UE (États-Unis, Japon) | — | Eurostat ne couvre pas ; OCDE oui, mais autre méthode → le signaler, ne pas superposer | ? OCDE (Data Explorer), à évaluer plus tard |

### 2.8 Inégalités, pouvoir d'achat, contexte économique

| Question | Indicateurs | Piège | Données |
|---|---|---|---|
| L'inflation | IPC (INSEE) / IPCH (Eurostat) | IPC ≠ déflateur du PIB ; choix à annoncer pour tout « euros constants » | **À COLLECTER** : INSEE BDM `001759970` ✔ ; Eurostat `prc_hicp_aind` ✔ |
| Pouvoir d'achat | Pouvoir d'achat du revenu disponible brut des ménages, par unité de consommation | Agrégé ≠ ressenti individuel ; par ménage vs par UC | ? INSEE BDM (identifiant de série à relever) |
| Inégalités | Gini, taux de pauvreté | Avant/après redistribution ; millésime de l'enquête (décalage de 2 ans) | **À COLLECTER** : Eurostat `ilc_di12` ✔ ; territorial : INSEE Filosofi (? jeu à identifier) |
| Le PIB | PIB nominal, volume | Révisions ; base | `nama_10_gdp` ✔ |
| Emploi public | Effectifs par versant | Effectifs ≠ ETP ≠ ETPT (LOLF) | ? INSEE SIASP / DGAFP (à identifier) |

### 2.9 Questions transverses (le vrai différenciateur)

- **« Est-ce beaucoup ? »** → toujours trois repères : par rapport au total de la même source, par
  rapport au PIB, par rapport au passé (même périmètre). Jamais par rapport à un autre périmètre.
- **« Pourquoi ça a augmenté ? »** → décomposition (§4.1).
- **« Ce chiffre que j'ai lu est-il juste ? »** → vérification d'affirmation (§4.2).
- **« Qui est responsable de cette dépense ? »** → carte des compétences (qui fait quoi) + périmètre.
- **« Qu'est-ce qu'on ne sait pas ? »** → lacunes avec responsable (principe 4), y compris les
  questions **sans réponse officielle** (aides aux entreprises, dépense de l'État par territoire).

---

## 3. Règles de rigueur que l'interface doit imposer

Ce sont des **règles de produit** (codées), pas des conseils.

### 3.1 Choix de l'unité
- **Euros courants** : unité par défaut d'une valeur ponctuelle (un montant, une année). Toujours
  libellé « euros courants » dès qu'une série couvre plus de 3 ans.
- **Euros constants** : proposés (et pré-sélectionnés) pour toute évolution de plus de 5 ans. Le
  déflateur est nommé (« prix du PIB » pour les agrégats publics, IPC si la question porte sur le
  pouvoir d'achat) avec l'année de référence. C'est un **calcul du site** : signalé.
- **% du PIB** : par défaut pour toute comparaison internationale et pour dette, déficit, PO.
  Interdit (ou fortement averti) pour un montant local (un département rapporté au PIB national n'a
  pas de sens). Quand le PIB varie brutalement (2009, 2020), afficher le numérateur à côté.
- **€ par habitant** : par défaut pour comparer des collectivités entre elles ; à éviter pour
  l'international (préférer % PIB ou SPA). La population utilisée (millésime, définition) est
  affichée. Quand la source fournit déjà l'€/hab (OFGL), **on prend le sien, on ne recalcule pas**.
- **% du total** : seulement à l'intérieur d'une même source, d'un même stade et d'une même année.

### 3.2 Ce qui ne se compare pas (blocage, pas seulement avertissement)
1. Un montant APU (COFOG) et un montant État (mission) sur le même axe sans étiquette de périmètre
   distincte et visible.
2. PLF d'une année et exécution d'une autre année présentés comme une « évolution » sans mention.
3. Des agrégats OFGL emboîtés empilés ou additionnés ; des nœuds COFOG de niveaux différents.
4. BG + CAS + CCF ; sous-secteurs COFOG additionnés pour retrouver S13.
5. Une série qui traverse une rupture (M52/M57, fusion 2016, CEA 2021, changement de base) sans
   marqueur de rupture sur le graphique.
6. Un pays sur source nationale contre d'autres pays sur Eurostat.
7. Une commune seule comparée à une autre quand leurs intercommunalités exercent des compétences
   différentes, sans le signaler.
8. Des dépenses fiscales « nc » ou « ε » traitées comme zéro dans un total, un classement ou une
   carte.

### 3.3 Prévision face à exécution
- Code visuel du **stade** porté par chaque valeur (pas seulement par la légende) : réalisé = trait
  plein ; voté = autre traitement ; proposé = encore un autre ; estimation (dépenses fiscales) =
  marqué « estimation ». Les drapeaux `p` (provisoire) restent visibles jusqu'au point.
- Un graphique mêlant stades est autorisé **uniquement** quand c'est le sujet (« voté vs réalisé »)
  et dans une même année.
- Jamais de ligne continue qui relie un réalisé à une prévision.

### 3.4 Parler des lacunes
- Un trou est rendu comme un trou (case marquée, barre absente avec mention), avec **qui devrait
  publier** et la date du constat.
- Tout total incomplet est libellé « au moins … » ou « total des seules valeurs chiffrées », avec le
  nombre d'éléments manquants.
- Quand une question n'a pas de réponse officielle, la page de réponse **existe quand même** : elle
  explique pourquoi, quelles approximations circulent et qui les a produites, sans les endosser.

### 3.5 Traçabilité et neutralité
- Toute vue a un **permalien figé** (version des données, sha256, date de collecte) : un journaliste
  doit pouvoir retrouver dans 2 ans le chiffre qu'il a cité.
- Tout calcul du site (part, ratio, médiane, euros constants, variation, rang) porte un marqueur
  « calcul » distinct du marqueur « publié par la source », avec la formule en une ligne.
- Vocabulaire : uniquement les libellés officiels ; une requête militante (« gaspillage »,
  « cadeaux ») est **reformulée** en catégories officielles, la reformulation étant montrée.
- Pas d'adjectif évaluatif (« record », « explosion ») dans le texte généré ; « plus haut niveau de
  la série » est un fait vérifiable, « record » non.
- Arrondis : pas plus de précision que la source ; ne jamais afficher « 1 671 793,8 M€ » quand on
  écrit « 1,67 Md€ »… mais garder la valeur exacte au survol / dans la provenance.

### 3.6 Statistiques descriptives
- Comparaison à des pairs : **médiane** plutôt que moyenne (Paris écrase les moyennes), avec
  dispersion (quartiles) ; rang toujours accompagné de l'écart.
- Cartes : classes fondées sur des quantiles affichés, légende chiffrée ; pas de carte en valeurs
  absolues pour des territoires de populations différentes (sauf symboles proportionnels).
- Corrélation entre deux indicateurs : affichable (nuage de points) mais **sans droite causale** ni
  texte interprétatif.

---

## 4. Fonctionnalités analytiques recommandées

Notation : utilité (U), complexité (C), valeur (V) sur 3. ⚠ = ce qui serait trompeur ou gadget.

### 4.1 Décomposition d'une variation — U3 C2 V3
Pour une hausse entre deux années : part due aux **prix** (déflateur), à la **population**, au
**périmètre** (lignes MP/MT, transferts de compétences), au **volume par habitant** ; pour un total
COFOG, contribution de chaque fonction (effet structure). Données : en base + déflateur + population.
⚠ N'est valable que sur un même périmètre et une même source ; pas de « effet politique »
résiduel interprété.

### 4.2 Vérificateur d'affirmation chiffrée — U3 C3 V3
L'utilisateur colle « les niches fiscales coûtent 90 milliards » ; l'outil identifie l'indicateur
candidat, l'année, le stade, le périmètre, et répond par une **grille** et non un vrai/faux :
*correspond à [montant réel issu de …]* / *ordre de grandeur juste mais autre périmètre* / *année
différente* / *non vérifiable avec des données officielles*. Montre les définitions concurrentes.
⚠ Une analyse automatique de texte peut se tromper : toujours montrer l'interprétation retenue et la
laisser corriger ; ne jamais produire un chiffre qui n'est pas une ligne ou un calcul signalé.

### 4.3 Résolveur de périmètre (« de quelle dépense parlez-vous ? ») — U3 C2 V3
Une question ambiguë (« budget de l'éducation ») ouvre côte à côte les réponses par périmètre :
COFOG GF09 (APU), mission Enseignement scolaire (État, PLF/LFI/exécution), collèges (départements),
avec un schéma d'emboîtement. C'est **la** fonctionnalité qui distingue le site.

### 4.4 Détecteur et registre de ruptures de série — U3 C2 V3
Registre déclaratif (fichier versionné, sourcé) des ruptures : changement de nomenclature,
fusion, création de collectivité, transfert de compétence, changement de base, lignes MP/MT. Les
graphiques l'interrogent et posent un marqueur. Détection automatique **en assistance** (saut
anormal d'une série OFGL ou d'une fonction M57) qui propose une rupture à documenter, jamais publiée
sans source. ⚠ Une détection statistique seule n'est pas une explication.

### 4.5 Équivalences sourcées — U2 C1 V2
Exprimer un montant **dans les unités d'une même source** : « = x % de la mission », « = x jours de
dépense publique totale » (montant / dépense annuelle S13 × 365, calcul signalé), « = x € par
habitant ». ⚠ **Gadget / trompeur** : « = N hôpitaux / N salaires d'infirmière » (coût unitaire
inventé ou d'une autre source), compteur de dette « par seconde » (extrapolation présentée comme
mesure).

### 4.6 Comparateur de pairs pour les collectivités — U3 C2 V3
« Mon département face aux départements comparables » : pairs définis par critère officiel affiché
(strate de population, ou groupe choisi par l'utilisateur), médiane, quartiles, rang, évolution.
Données : en base (régions, départements), communes à collecter. ⚠ Pas de score synthétique ni de
« note de gestion » (méthode inventée).

### 4.7 Mode « voté vs réalisé » — U3 C2 V3
Pour une mission/programme : PLF → LFI → exécution de la **même** année, écart en M€ et en %.
Exige les PLRG (à collecter). ⚠ Une sous-exécution n'est pas une « économie » ni un « échec » :
texte neutre, rappel des mécanismes (reports, annulations, gel).

### 4.8 Carte des compétences « qui paie quoi » — U3 C2 V2
Pour un service (collège, RSA, TER, école), dire quelle administration l'exerce et où se trouve la
dépense dans chaque source. Données : texte sourcé (CGCT, Légifrance) + liens vers les montants.
⚠ Ne pas tenter d'additionner les étages.

### 4.9 Structure de 1 000 € de dépense publique — U2 C1 V2
Répartition COFOG S13 d'un montant fictif de 1 000 €. Pédagogique et très partageable.
⚠ Ne pas l'intituler « où vont **vos** impôts » : l'argent est fongible et les impôts ne financent
pas toute la dépense (déficit) ; le dire en une ligne.

### 4.10 Lecture « niches face à l'impôt » — U2 C2 V2
Coût des dépenses fiscales rapporté au produit de l'impôt concerné, même année, avec les `nc`
comptés. Exige recettes par impôt (État, même stade). ⚠ Ne pas présenter comme « recettes perdues ».

### 4.11 Export et citation automatique — U3 C1 V3
CSV avec colonnes `valeur, unité, stade, périmètre, source, fichier_sha256, ligne`, image avec
source incrustée (formats horizontal/vertical), **phrase de citation** générée (« Source : … , jeu …
, collecté le …, ligne … »). API JSON pour agents IA.

### 4.12 Fil « nouvelles données » — U2 C1 V2
Signaler ce qui a changé à chaque collecte (nouveau millésime, révision d'une valeur publiée,
passage de provisoire à définitif). Données : sha256 déjà stockés. Les révisions sont un contenu
(« Eurostat a révisé 2023 »).

### 4.13 Explorateur de la question ouverte (autocomplétion) — U3 C2 V3
L'autocomplétion propose des **questions résolubles** (indicateur + périmètre connus) et, en bas,
les questions « sans donnée officielle » liées aux lacunes. Évite la page vide « aucun résultat ».

### Fonctionnalités à refuser
- **Simulateur de réforme fiscale / chiffrage de programme** : exige un modèle de microsimulation
  (méthode non officielle au sens du site). Renvoyer vers les outils publics existants qui le font,
  sans les intégrer comme résultat.
- **Projections / prévisions maison** (tendance prolongée) : interdit par le principe 3.
- **Score ou classement synthétique de « bonne gestion »** : pondération inventée.
- **Attribution causale automatique** (« grâce à la réforme X ») : hors données.

---

## 5. Priorités de collecte (10 jeux, par valeur pour les questions)

| # | Jeu | Producteur / identifiant exact | Questions débloquées |
|---|---|---|---|
| 1 | Déficit et dette des APU (notification PDE), tous pays UE, par sous-secteur | Eurostat `gov_10dd_edpt1` ✔ (API SDMX `https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/gov_10dd_edpt1/…`) ; complément trimestriel `gov_10q_ggdebt` ✔ | Dette, déficit, « qui porte la dette », comparaisons UE — les questions les plus posées et les plus mal citées |
| 2 | COFOG pour tous les pays UE | Eurostat `gov_10a_exp` ✔, même requête que `eurostat_cofog_fr` avec `geo` élargi (EU27_2020 + pays) | « La France dépense plus que… » ; coût nul (chargeur existant) |
| 3 | Dénominateurs : PIB, déflateur, population | Eurostat `nama_10_gdp` ✔, `demo_pjan` ✔ (ou `nama_10_pe` ✔) ; INSEE BDM IPC `001759970` ✔ (`https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/001759970`) | Euros constants, € par habitant, % PIB pour l'État : conditions des règles §3.1 |
| 4 | Recettes et dépenses totales APU ; recettes par impôt | Eurostat `gov_10a_main` ✔ et `gov_10a_taxag` ✔ | Prélèvements obligatoires, intérêts, solde primaire, produit des impôts, comparaisons UE |
| 5 | Communes, intercommunalités et ensembles intercommunaux consolidés | data.ofgl.fr `ofgl-base-communes-consolidee` ✔, `ofgl-base-gfp-consolidee` ✔, `ofgl-base-ei` ✔ | « Ma commune » : le plus grand gisement d'utilisateurs locaux |
| 6 | Exécution de l'État (lois relatives aux résultats de la gestion) | data.economie.gouv.fr `plrg-2024` ✔, `projet-de-loi-relatif-aux-resultats-de-la-gestion-et-portant-approbation-des-comptes-de-lannee-plrg-2025` ✔ | Voté vs réalisé, taux d'exécution, série d'exécution |
| 7 | Situations mensuelles budgétaires de l'État | data.economie.gouv.fr `situations-mensuelles-budgetaires-series-longues` ✔ (2013→) et `situation-mensuelle-de-l-etat` ✔ (DGFiP) | Déficit de l'État en cours d'année, recettes fiscales nettes de l'État, actualité |
| 8 | Géométries des territoires | data.ofgl.fr `regions_formes_geo_svg` ✔, `departements_formes_geo_svg` ✔, `communes_formes_geo_svg` ✔ (codes cohérents avec les comptes OFGL) ; alternative IGN ADMIN EXPRESS (data.gouv.fr) | Carte, sélection géographique, « store locator » |
| 9 | Protection sociale | DREES `305_les-comptes-de-la-protection-sociale` ✔ et `376_les-depenses-d-aide-sociale-departementale` ✔ (data.drees.solidarites-sante.gouv.fr) ; Eurostat ESSPROS `spr_exp_func` ✔ pour l'UE | Retraites, santé, RSA/APA par département, comparaisons ; la LFSS elle-même : lacune candidate (DSS) |
| 10 | Fiscalité locale et dotations | data.ofgl.fr `rei` ✔ (taux et bases, DGFiP) ; `dotations-communes` ✔, `dotations-departements` ✔, `dotations-regions` ✔, `dotations-gfp` ✔ | « Pourquoi ma taxe foncière augmente », « ce que l'État verse à ma collectivité » |

Suivants : Eurostat `ilc_di12` ✔ (inégalités) et `prc_hicp_aind` ✔ ; bilan de l'État
`balances_des_comptes_etat` ✔ ; département par fonction pour 2012-2019 (même jeu, filtre levé, pour
documenter la rupture M52/M57) ; INSEE Filosofi, pouvoir d'achat (identifiants à relever) ; Voies et
moyens tome I (recettes et prélèvements sur recettes, jeu à identifier) ; exonérations de cotisations
(annexe LFSS, jeu à identifier).

Lacunes nouvelles à inscrire (après vérification) : LFSS sans jeu open data structuré (DSS) ;
dépense de l'État non territorialisée (DB/DGFiP) ; absence de série officielle des aides publiques
aux entreprises ; trajectoires de prévision (programme de stabilité / plan budgétaire) non publiées
en données structurées.

---

## Ce que je demande aux autres spécialistes

### À l'UX/UI
1. **Le périmètre et le stade ne sont jamais facultatifs** : chaque réponse les affiche à côté du
   chiffre, dans le premier écran, y compris à 320 px. Pas dans une infobulle seulement.
2. La recherche ne renvoie jamais « aucun résultat » : elle propose le résolveur de périmètre ou la
   lacune correspondante.
3. Le comparateur universel **refuse** les comparaisons interdites (§3.2) et explique pourquoi ; un
   comparateur qui accepte tout est un générateur de fausses infos.
4. Les choix d'unité (€ courants / constants / % PIB / €/hab) ont des **défauts imposés par le
   contexte** (§3.1), modifiables, mais le défaut est la version honnête.
5. Permalien figé et phrase de citation accessibles en un geste sur mobile.
6. Une requête militante est reformulée en catégorie officielle, et la reformulation est visible.
7. Les questions des profils pressés (plateau, réseaux sociaux) : réponse lisible en < 10 s, une
   main, sans connexion à un compte.

### Au directeur artistique
1. L'éditorial ne doit pas produire d'emphase : pas de typographie de « une » sur un chiffre sans son
   périmètre ; la hiérarchie typographique met **libellé officiel + périmètre** au même niveau
   d'attention que le montant.
2. Les photos et la matière ne doivent pas suggérer une interprétation (pas d'image d'hôpital
   délabré à côté de la dépense de santé) : l'illustration est documentaire et neutre.
3. Un langage visuel stable et accessible (AA) pour **réalisé / voté / proposé / estimé / provisoire /
   lacune / calcul du site**, valable en clair et en sombre, imprimable en noir et blanc.
4. La lacune a une dignité visuelle égale à la donnée : c'est un contenu, pas un état d'erreur.

### Au spécialiste dataviz
1. Jamais d'axe qui mélange périmètres ou stades sans encodage distinct ; jamais de ligne reliant un
   réalisé à une prévision.
2. Marqueur de rupture de série obligatoire, alimenté par le registre (§4.4).
3. Aucun empilement d'agrégats emboîtés (OFGL) ni de sous-secteurs COFOG ; les treemaps/sunbursts ne
   sont autorisés que sur les arbres où les montants sont aux feuilles (missions/programmes/actions,
   divisions/groupes COFOG d'un même secteur et d'une même année).
4. `nc` et `ε` visibles comme tels, jamais à zéro, jamais interpolés ; un total incomplet dit « au
   moins ».
5. Axe à zéro pour les barres ; pour les séries en % PIB, montrer le numérateur sur demande ; échelle
   identique entre petits multiples comparés.
6. Cartes : €/hab ou ratios, classes quantiles affichées, Paris/Lyon/Alsace/collectivités uniques/
   Outre-mer traités explicitement (encadrés, note de compétences), pas effacés.
7. Chaque graphique exporté embarque titre, unité, stade, périmètre, source, date de collecte ; s'il
   est recadré pour un réseau social, ces mentions survivent au recadrage.
