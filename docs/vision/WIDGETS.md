# Widgets : faire sa démonstration sur le site, et la partager

Statut : validé par le user le 2026-10-28, avec une correction : aucune requête libre exposée (pas de console SQL),
les données descendent par document et sont traitées dans le navigateur (§4 bis). Rien n'est construit.

## 0. Le principe

La source sert à deux choses : qu'on puisse **faire confiance** au chiffre et le **citer**. Elle n'est pas le produit.
Le produit, c'est l'atelier : un économiste, une journaliste, un collaborateur parlementaire ou un militant associatif
doit pouvoir **faire sa démonstration directement sur le site**, avec le graphique qu'il veut, puis la partager sur les
réseaux sociaux.

Chaque widget produit donc trois choses :
1. **une figure faite sur mesure** : type de graphique, période, périmètre, unité, annotations, titre, tous choisis par
   l'utilisateur ;
2. **un objet partageable** : une image aux formats des réseaux (carré, 16:9, vertical 9:16) avec la source écrite dans
   l'image, et un lien qui rouvre exactement la même vue ;
3. **la preuve, discrète** : la source en pied d'image, et un clic pour remonter à la ligne du fichier officiel.

Les garde-fous restent automatiques et sans sermon. On ne peut pas, par exemple, additionner des niveaux emboîtés ou
mettre deux sources sur un même axe : le choix est grisé et la raison est écrite dessous. Une rupture de série est
marquée sur le graphique. Tout calcul du site est signalé.

## 1. Ce que le site contient aujourd'hui (la matière des widgets)

| Données | Détail | Années |
|---|---|---|
| Dépenses de toutes les administrations, par fonction (COFOG) | 10 fonctions, 69 sous-fonctions ; 4 périmètres (ensemble, État et organismes centraux, administrations locales, sécurité sociale) ; M€, % du PIB, % du total | 1995–2024 |
| Grands postes des comptes publics | Recettes, dépenses, solde, dette, intérêts, 8 catégories de recettes ; 4 périmètres ; M€ et % du PIB | 1995–2025 |
| Régions et départements (OFGL) | 68 agrégats financiers (dépenses, recettes, épargne, dette, investissement…), en € et en €/habitant | 2012–2025 |
| Départements par fonction | Nomenclatures M52 et M57 (social, collèges, routes…), en € et en €/habitant | 2020–2025 |
| Budget de l'État | Missions, programmes, lignes ; stades PLF (2024–2026), LFI 2025, exécution 2024 ; AE et CP ; cotation « budget vert » (favorable, neutre, défavorable…) et catégorie | 2024–2026 |
| Budget de l'État détaillé | PLF 2025 jusqu'à l'action et la sous-action, avec le titre (personnel, fonctionnement, investissement…) | 2025 |
| Dépenses fiscales | Coût estimé de chaque dépense, impôt concerné, catégorie, cotation environnementale ; dépenses sans montant publié | PLF 2026 |
| Contexte politique | Gouvernements et ministres (1 766 personnes), 70 scrutins avec les votes par groupe | — |
| Lexique, lacunes | 114 définitions officielles citées, 139 données non disponibles | — |

Ce qui manque et qui débloquerait beaucoup de widgets (§5) : un déflateur (pour les euros constants), la population
nationale, les **autres pays de l'UE** (les mêmes jeux Eurostat, il suffit d'élargir la collecte), l'exécution du budget
de l'État sur plusieurs années, et les communes.

## 2. Qui fait quoi, au quotidien, avec ces données

Pour chaque profil : une **journée type**, les **démonstrations** qu'il veut faire, et les **widgets** qui lui servent
(numéros du §3).

### 2.1 Économiste, chercheur, analyste d'un think tank
- **Journée type** : il commente une publication (Insee, Eurostat, PLF), répond à une tribune, prépare une note ou un
  fil sur les réseaux. Il veut « montrer que » : la hausse vient surtout de telle fonction, telle part a reculé depuis
  2010, la France se situe à tel rang.
- **Démonstrations** : décomposer une variation, évolution de structure, comparaison de deux périodes, rang européen,
  ratios (intérêts rapportés aux recettes), euros constants.
- **Widgets** : W1, W3, W5, W12, W13, W16, et plus tard W10 (international).

### 2.2 Journaliste data, vérificateur
- **Journée type** : une déclaration circule (« la dette a doublé en 15 ans », « les départements dépensent de plus en
  plus pour le social »). Il vérifie, puis publie un graphique en moins d'une heure, souvent sur mobile.
- **Démonstrations** : « voilà ce que dit la série officielle », avant / après, un chiffre remis dans son périmètre.
- **Widgets** : Vérifier (déjà fait), W1 avec annotations, W2, W14, W17 (intégrer le graphique dans un article).

### 2.3 Collaborateur parlementaire, analyste budgétaire
- **Journée type** : il prépare un amendement ou une question écrite, ou suit le PLF en séance. Il veut savoir combien
  pèse un programme, son évolution entre PLF et LFI, ce qui a été exécuté, et quelles dépenses fiscales touchent le même
  domaine.
- **Démonstrations** : treemap d'une mission, voté puis exécuté pour une même année, poids d'une dépense fiscale face à
  un programme, part « défavorable » du budget vert d'une mission.
- **Widgets** : W7, W8, W9, W11, W15.

### 2.4 Analyste de collectivité (direction des finances, élu, cabinet)
- **Journée type** : le débat d'orientation budgétaire, une réponse à la chambre régionale des comptes, une commission
  des finances. Il compare son département à des pairs et explique une évolution.
- **Démonstrations** : « nous sommes au 3e quartile pour le social par habitant », évolution sur 10 ans comparée à la
  médiane, carte de la région, relation entre deux indicateurs (dette par habitant et épargne brute).
- **Widgets** : W4, W5, W6, W12 (tableau prêt pour le rapport), W2.

### 2.5 Syndicat, association, collectif
- **Journée type** : une campagne, un tract, un post. Il veut un graphique simple et frappant, mais juste, sur un poste
  qui le concerne (santé, enseignement, logement, protection sociale).
- **Démonstrations** : une série longue sur la part du PIB, la place d'un poste dans le total, « pour 1 000 € de
  dépense publique ».
- **Widgets** : W1 avec modèles prêts, W8, W14, W16.

### 2.6 Enseignant, étudiant
- **Journée type** : préparer un cours, faire un exposé, un mémoire. Il veut une figure propre, citable, et des données
  à retravailler.
- **Démonstrations** : la structure de la dépense, l'évolution de la dette, la différence entre budget de l'État et
  dépense publique.
- **Widgets** : W1, W8, W12, W13, W16 (diaporama), parcours Comprendre (déjà fait).

### 2.7 Vulgarisateur, créateur de contenu
- **Journée type** : une vidéo, un carrousel Instagram, un fil. Il veut des visuels au format vertical, animés si
  possible, très lisibles sur un téléphone.
- **Démonstrations** : une course de barres sur 30 ans, une carte animée, une décomposition étape par étape.
- **Widgets** : W1 (format 9:16, export vidéo ou GIF), W4 animé, W5, W16.

### 2.8 Développeur, réutilisateur, agent IA
- **Journée type** : brancher une application ou un tableau de bord sur des données propres et stables.
- **Widgets** : W12 (requêtes), W17 (intégration), une API documentée (déjà prévue dans INTERFACE.md).

## 3. Le catalogue de widgets

Chaque fiche dit : ce que le widget fait, la liberté qu'il donne, les données qu'il utilise (✅ en base, ➕ à collecter),
et ce qu'il empêche.

### W1. Atelier de graphique (le cœur)
- **Fait** : n'importe quelle série du site, dans n'importe quel type de graphique pertinent. Types : courbe, aires,
  aires 100 %, barres groupées, barres empilées, barres horizontales classées, pente (deux années), course de rangs
  (bump), points (dot plot), petits multiples, carte de chaleur (années × postes).
- **Liberté** : titre et sous-titre libres, annotations (texte, flèche, zone surlignée, ligne verticale à une date),
  marqueurs de gouvernements ou de législatures (W14), choix des couleurs dans une palette accessible, axe partant de
  zéro ou non (avec un avertissement visible si l'axe ne part pas de zéro), base 100 à l'année choisie, thème clair ou
  sombre.
- **Partage** : PNG aux formats 1080 × 1080, 1200 × 675 et 1080 × 1920, SVG, GIF ou vidéo animé (pour les séries
  longues), lien permanent, code d'intégration, phrase de citation.
- **Données** : ✅ tout ce qui est en base.
- **Empêche** : deux sources ou deux unités sur un même axe, l'addition de niveaux emboîtés, une ligne qui relie un
  réalisé à une prévision.

### W2. Comparateur A / B
- **Fait** : deux choses côte à côte, avec l'écart calculé. Deux années, deux collectivités, deux périmètres, deux
  fonctions, PLF face à LFI.
- **Liberté** : chaque côté se règle indépendamment ; on choisit la forme de l'écart (en valeur, en %, en points).
- **Données** : ✅.
- **Empêche** : la comparaison de deux périmètres qui ne s'emboîtent pas sans l'étiquette de chacun.

### W3. Décomposition d'une variation (cascade)
- **Fait** : entre deux années, ce que chaque fonction ou catégorie de recettes apporte à la variation du total.
  Exemple : de 2010 à 2024, la dépense publique a varié de X ; protection sociale +a, santé +b, défense −c.
- **Liberté** : choix du total, des années, du périmètre, du niveau de détail (fonction ou sous-fonction) ; tri par
  contribution.
- **Données** : ✅ COFOG et recettes. ➕ Ajouter le déflateur et la population pour séparer l'effet prix et l'effet
  population.
- **Empêche** : toute interprétation causale du résultat.

### W4. Comparateur de pairs (collectivités)
- **Fait** : tous les départements (ou toutes les régions) en essaim de points pour un indicateur, ma collectivité mise
  en avant, avec la médiane, les quartiles et le rang.
- **Liberté** : groupe de pairs choisi (même région, liste à la main) ; indicateur ; année ; animation dans le temps.
- **Données** : ✅ OFGL. ➕ Strates de population pour des pairs « officiels ».
- **Empêche** : un score synthétique ou une note de gestion.

### W5. Nuage de points (deux indicateurs croisés)
- **Fait** : chaque collectivité placée selon deux indicateurs, par exemple l'encours de dette par habitant et
  l'épargne brute par habitant ; la taille du point peut suivre la population.
- **Liberté** : choix des deux axes, de l'année, d'une trajectoire animée sur plusieurs années, des points étiquetés.
- **Données** : ✅ OFGL.
- **Empêche** : une droite de régression présentée comme une explication.

### W6. Carte
- **Fait** : régions ou départements colorés selon un indicateur, en classes de quantiles affichées.
- **Liberté** : indicateur, année, animation 2012–2025, classes (quantiles, seuils choisis), zoom sur une région.
- **Données** : ✅ OFGL. ➕ Contours officiels IGN (Admin Express, licence ouverte).
- **Empêche** : une carte en montants totaux, qui ferait ressortir les territoires les plus peuplés.

### W7. Explorateur du budget de l'État
- **Fait** : treemap ou icicle mission → programme → action, dans lequel on clique pour descendre.
- **Liberté** : stade (PLF, LFI, exécution), AE ou CP, coloration par cotation budget vert, par catégorie ou par titre
  (personnel, fonctionnement, investissement…) ; recherche d'un programme.
- **Données** : ✅ budget vert PLF 2026 et PLF 2025 détaillé.
- **Empêche** : l'addition de AE et CP, ou de stades différents.

### W8. Pour 1 000 € de dépense publique
- **Fait** : la répartition d'une somme choisie (100 €, 1 000 €, un montant libre) entre les fonctions COFOG, pour une
  année ; en treemap, barres ou unités.
- **Liberté** : année (animée de 1995 à 2024), périmètre, détail en sous-fonctions.
- **Données** : ✅.
- **Empêche** : le titre « où vont vos impôts » ; une ligne rappelle que la dépense n'est pas financée que par l'impôt.

### W9. Voté puis réalisé
- **Fait** : pour une mission ou un programme, PLF → LFI → exécution de la **même** année, avec les écarts.
- **Données** : ✅ partiel (PLF 2024 et exécution 2024 ; PLF et LFI 2025). ➕ Exécution sur plusieurs années (lois de
  règlement).
- **Empêche** : les mots « économie » ou « échec » pour parler d'un écart.

### W10. Comparaison européenne
- **Fait** : la France parmi les pays de l'UE, pour une fonction ou un grand poste, en % du PIB ; rang et évolution.
- **Données** : ➕ les mêmes jeux Eurostat (gov_10a_exp, gov_10a_main, gov_10dd_edpt1) en élargissant la collecte à tous
  les pays. Coût de collecte faible.
- **Empêche** : un pays mesuré par une source nationale à côté des autres mesurés par Eurostat.

### W11. Dépenses fiscales
- **Fait** : classement, répartition par impôt, par catégorie, par cotation environnementale ; mise en regard du
  programme budgétaire du même domaine (deux barres séparées, sans addition).
- **Liberté** : filtres combinés, recherche, seuil de montant.
- **Données** : ✅ PLF 2026.
- **Empêche** : compter comme zéro une dépense sans montant publié ; le mot « cadeau ». Le nombre de dépenses sans
  montant est toujours affiché.

### W12. Tableau croisé (pour les experts)
- **Fait** : lignes × colonnes × filtres libres sur les données d'un document, avec des calculs signalés (part, écart,
  taux de croissance annuel moyen, base 100, médiane), et le graphique du résultat en un clic. Tout est calculé dans le
  navigateur, sur le fichier du document chargé (§4 bis) ; aucune requête ne part vers le serveur.
- **Données** : ✅ tous les documents.
- **Empêche** : les mêmes mélanges que W1 ; les résultats exportés portent les réglages et les sources.

### W13. Calculs dérivés (une barre d'outils commune)
- **Fait** : sur toute série affichée : base 100, variation entre deux années, taux de croissance annuel moyen, part
  d'un total, moyenne mobile, cumul ; et, une fois le déflateur et la population collectés, euros constants et euros par
  habitant (national).
- **Données** : ✅ ; ➕ déflateur et population pour les deux derniers.
- **Empêche** : un calcul sans formule affichée.

### W14. Frise de contexte
- **Fait** : superposer à toute série les gouvernements, les législatures, les lois de finances et les scrutins, en
  bandes ou en repères.
- **Données** : ✅ (Assemblée nationale).
- **Empêche** : une attribution causale (« sous tel gouvernement, la dette a… ») générée par le site ; seules les
  dates sont posées.

### W15. Dette, solde, charge d'intérêts
- **Fait** : un tableau de bord des trois séries, avec des ratios calculés (intérêts rapportés aux recettes, solde
  rapporté aux dépenses) et leurs formules.
- **Données** : ✅.
- **Empêche** : un compteur de dette « par seconde » (une extrapolation présentée comme une mesure).

### W16. Récit partageable (« fil »)
- **Fait** : enchaîner plusieurs vues (W1 à W15) en une démonstration de 3 à 10 cartes, chacune avec sa phrase. Export
  en série d'images (fil X ou Bluesky, carrousel Instagram ou LinkedIn), en PDF ou en diaporama, et un lien qui rouvre
  le tout.
- **Données** : celles des vues.
- **Empêche** : rien de plus que ce qu'empêchent les vues ; le texte libre de l'auteur est signé comme le sien, et la
  page ne le présente pas comme celui du site.

### W17. Intégration
- **Fait** : n'importe quel widget intégrable dans un article ou un blog (iframe ou script), interactif, mis à jour à
  chaque collecte ou figé à une version (au choix de l'auteur).
- **Données** : celles du widget.

## 4. Le socle commun (à construire une fois, pour tous les widgets)

1. **L'état complet dans l'URL** : tout réglage se rouvre à l'identique ; une version figée (date de collecte) est
   possible, pour qu'un chiffre cité reste vérifiable dans deux ans.
2. **Export image** aux trois formats des réseaux, avec titre, source et lien court incrustés ; SVG pour les
   graphistes ; GIF ou vidéo pour les séries animées.
3. **Des fichiers de données par document** (§4 bis), documentés sur la page Données : c'est l'« API » des widgets.
4. **Une bibliothèque de graphiques** unique : Observable Plot (sur D3) pour la liberté des types, d3-geo pour les
   cartes. Rendu mobile d'abord, au toucher.
5. **Les garde-fous** dans le code, communs à tous les widgets : unités compatibles, niveaux non emboîtés, ruptures de
   série, stades, dépenses sans montant.
6. **Des modèles prêts** : chaque widget s'ouvre sur un exemple utile, jamais sur une page vide.

## 4 bis. Sécurité et charge du serveur (exigence du user)

- **Aucune requête libre** : pas de console SQL, pas de paramètre qui deviendrait un morceau de requête. Côté serveur,
  toute requête reste écrite d'avance, avec des valeurs passées en paramètres (`?`) et des noms (table, colonne, unité)
  pris dans des listes fermées ; une valeur hors liste donne une erreur 404.
- **Les données descendent par document** : `make build` écrit, pour chaque document source, un fichier statique
  compact (colonnes plutôt que lignes, compressé), découpé par indicateur quand le document est gros (OFGL). Le nom du
  fichier contient son empreinte : le navigateur et un éventuel CDN le gardent en cache sans limite, et le serveur ne
  calcule rien quand on ouvre un widget.
- **Les calculs se font dans le navigateur** : tri, filtres, tableau croisé, base 100, écarts, décomposition. Le
  serveur ne sert que des fichiers.
- **Un manifeste** liste les fichiers, leur document source, leurs colonnes, leur taille et leur empreinte : les
  widgets ne chargent que ce qu'ils affichent, et la page Données le publie pour les réutilisateurs.
- **L'état d'un widget dans l'URL** est relu dans le navigateur avec la même liste fermée : une valeur inconnue est
  ignorée, jamais transmise.
- **Un test** vérifie qu'aucune requête SQL du code n'est construite avec une valeur reçue de l'utilisateur.

## 5. Données à ajouter, par nombre de widgets débloqués

| Collecte | Source | Débloque |
|---|---|---|
| Autres pays de l'UE (mêmes jeux) | Eurostat | W10 ; les classements et les rangs dans W1 et W3 |
| Déflateur du PIB et population | Eurostat ou Insee | euros constants et par habitant (W3, W13, W1) |
| Contours des régions et départements | IGN Admin Express | W6 |
| Exécution du budget de l'État sur plusieurs années | Lois de règlement (data.economie.gouv.fr) | W9 complet, séries longues dans W7 |
| Communes et intercommunalités | OFGL | W4, W5 et W6 à l'échelle communale |
| Strates de population des collectivités | OFGL | pairs officiels dans W4 |

## 6. Ordre proposé

> Depuis le 2026-10-30, l'ordre de construction suit les dépendances du chantier G de `docs/ROADMAP.md` : audit des pages existantes, socle et garde-fous, puis W13 avant W1, W3 et W15. L'ordre ci-dessous reste la proposition d'origine. Les identifiants W1 à W17 et leurs spécifications sont inchangés.

1. **Socle** (§4) et **W1** (l'atelier de graphique) : c'est lui qui rend tout le reste partageable.
2. **W3** (décomposition), **W8** (pour 1 000 €), **W2** (A / B) : trois démonstrations très demandées, sur des données
   déjà en base.
3. **W4**, **W5**, **W6** (collectivités : pairs, nuage de points, carte).
4. **W7**, **W11**, **W15** (État, dépenses fiscales, dette).
5. **W12** (tableau croisé), **W16** (récit), **W17** (intégration).
6. Collectes du §5, puis **W10** et **W9**.

## 7. Ce qu'on refuse (inchangé par rapport à `economiste.md`)

Simulateur de réforme ou chiffrage de programme, projections maison, score de « bonne gestion », attribution causale
automatique, équivalences inventées (« = N hôpitaux »).
