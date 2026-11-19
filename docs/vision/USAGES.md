# Pour qui, pour quoi : cadrage avant de construire d'autres pages

2026-10-28. Pourquoi ce document : jusqu'ici, les pages sont nées de questions choisies par nous (« Où va l'argent ? »,
« Qui dépense ? »…). Le but du site est autre : **chacun doit pouvoir faire ses propres recherches et présenter les
données comme il en a besoin**, à partir des seules sources officielles. Ce document part donc des publics et de
leurs besoins, en déduit les fonctions, puis juge chaque page existante à cette aune.

Les publics ci-dessous ont été **validés par le user le 2026-10-28** comme base de conception (aucun n'a encore été
interrogé : entretiens et statistiques de visite restent à faire).

---

## 1. Les publics et ce qu'ils viennent chercher

| Public | Ce qu'il cherche | Niveau | Ce qu'il emporte | Ce qui lui manque aujourd'hui |
|---|---|---|---|---|
| **Citoyen curieux** | Comprendre un chiffre entendu (dette, déficit, « l'État dépense X ») ; savoir ce que fait sa collectivité | Débutant | Une phrase juste, un graphique simple | Les notions de base expliquées avant les chiffres ; un point de départ qui ne présuppose pas la question |
| **Élève, étudiant, enseignant** (SES, droit public, Sciences Po, prépas) | Les concepts (périmètre, stades, flux et stock) et des séries longues pour un exposé ou un cours | Débutant à intermédiaire | Graphique citable, tableau, définition sourcée | Parcours « notions » ; export d'image avec source intégrée vérifié ; fiches imprimables |
| **Journaliste, vérificateur** | Vérifier une affirmation chiffrée vite et la citer | Intermédiaire | Le chiffre, sa source exacte, sa date, un lien permanent | Un mode « vérifier une affirmation » ; un lien vers l'état exact affiché (déjà partiel avec `?annee=`) |
| **Élu local, collaborateur, agent de finances d'une collectivité** | Situer sa collectivité (par habitant, dans le temps, face à la médiane de son niveau) | Intermédiaire à expert | Tableaux exportables, comparaisons, séries | Communes et intercommunalités (non chargées) ; plus d'agrégats OFGL ; comparaison à des collectivités choisies |
| **Parlementaire, collaborateur, groupe** | Le budget de l'État par mission et programme, entre projet, loi votée et exécution ; les votes | Expert | Tableaux détaillés, écarts entre stades | Lois de règlement (exécution complète), LFR, Sénat |
| **Association, syndicat, cercle de réflexion (de tous bords)** | Étayer un argument avec des chiffres incontestables | Intermédiaire | Graphique + source, série longue | Le même outil, sans qu'il prenne parti : c'est la condition pour qu'il serve à tous |
| **Chercheur, économiste, statisticien** | Données propres, traçables, avec leurs limites | Expert | CSV/JSON, provenance ligne à ligne, méthode | API documentée ; métadonnées des ruptures de série ; euros constants (déflateur publié) |
| **Développeur, data-journaliste réutilisateur** | Réutiliser la base | Expert | API, base SQLite, licences | API stable et documentée, export de la base |

**Ce que cela dit du site** : les publics se distinguent moins par leur sujet que par **leur niveau et ce qu'ils
emportent**. Il faut donc un même outil, avec plusieurs portes d'entrée (notions / recherche guidée / données brutes),
et non une page par question.

## 2. Les besoins communs, devenus fonctions

| Besoin | Fonction du site | Existe ? |
|---|---|---|
| Comprendre une notion avant le chiffre | **Notions** : courtes pages illustrées, définitions citées | Lexique (définitions) ; pas de parcours |
| Trouver un chiffre précis | **Recherche** (palette Ctrl K) | Oui |
| Composer sa propre vue | **Constructeur** : quoi × qui × quand × unité × forme | En partie : `/serie`, `/comparer` |
| Comparer des acteurs ou des territoires | Dans le constructeur | `/comparer`, `/territoires` |
| Vérifier une affirmation | **Vérifier** : saisir « X € / X % pour Y en Z » → les données publiées qui s'en approchent | Non |
| Citer, réutiliser | Lien permanent, export CSV/JSON/SVG/PNG avec source, API | Partiel (`/serie`) |
| Savoir ce qui manque | Données non disponibles, limites | Oui (`/lacunes`, handoff §3 bis) |
| Remonter à la preuve | Provenance ligne à ligne | Oui (lien « source ») |

## 3. Les notions essentielles (le cœur de « Comprendre »)

Ce qu'il faut avoir compris pour lire n'importe quel chiffre du site sans se tromper. Chaque notion doit reposer sur une
définition officielle citée ; la colonne « statut » dit où on en est.

| Notion | Pourquoi elle est indispensable | Statut de la définition | Forme visuelle adaptée |
|---|---|---|---|
| **Le périmètre** : APU = administrations centrales + locales + sécurité sociale ; l'État n'en est qu'une partie | La confusion la plus fréquente (« budget de l'État » ≠ « dépense publique ») | APU, APUL, ODAC citées (INSEE) ; APUC et ASSO à relever | Ensembles emboîtés, sans additionner (consolidation) |
| **Les stades** : projet (PLF), loi votée (LFI), rectificatives, exécution | Comparer un projet à une exécution est une erreur courante | PLF, LFI citées ; exécution à sourcer | Frise du calendrier budgétaire |
| **Recettes, dépenses, solde** | Le solde publié n'est pas un chiffre à part : c'est l'écart des deux | Déficit public cité | Deux colonnes et leur écart (fait, page Comprendre) |
| **Flux et stock** : déficit (une année) et dette (un encours) | « Le déficit baisse » ne veut pas dire « la dette baisse » | Dette au sens de Maastricht citée | Deux séries côte à côte, de même unité ; cascade seulement si les « autres flux » sont publiés |
| **Les unités** : euros courants, % du PIB, par habitant, euros constants | Une même série change de sens selon l'unité | PIB et population cités ; euros constants : déflateur à collecter | Même série affichée dans chaque unité, au choix |
| **Fonctions (COFOG) et missions (LOLF)** | Deux classements différents de la dépense, pour deux périmètres | COFOG, mission, programme cités | Carte en cases (existe), arbre |
| **Agrégats emboîtés et consolidation** | Additionner des agrégats emboîtés ou des sous-secteurs double-compte | Consolidation citée (OFGL) ; consolidation APU à relever | Montrer les deux chiffres publiés et leur écart |
| **Provisoire et définitif** | Les dernières années sont révisées | Mention « provisoire » de la source | Marque visuelle (existe) |
| **Dépenses fiscales, taxes affectées** | Des recettes en moins ou affectées, hors dépenses budgétaires | À sourcer (définition officielle non relevée) | Liste chiffrée + nombre sans montant (existe) |

## 4. Le constructeur : laisser chacun présenter les données comme il veut

Un formulaire unique, en cinq choix, toujours dans le même ordre ; chaque choix ne propose que ce qui existe vraiment
dans les sources pour les choix précédents.

1. **Quoi** : un indicateur (dépense par fonction, recettes, solde, dette, intérêts, crédits d'une mission, agrégat
   OFGL, dépense fiscale…), regroupé par famille, avec sa définition en infobulle.
2. **Qui** : un acteur ou un territoire (APU, sous-secteur, État, région, département ; plusieurs pour comparer).
3. **Quand** : une année, ou une période.
4. **Unité** : seules celles que la source publie (ou qu'on calcule avec un dénominateur publié, marqué « calcul du
   site »).
5. **Forme** : chiffre seul, courbe, barres, classement, carte, tableau ; seules les formes justes pour ce qu'on a
   choisi (une composition → barres 100 % ; une évolution → courbe ; un seul chiffre → pas de graphique).

Le résultat : la figure, son tableau jumeau, **une phrase descriptive générée** (« En 2024, la dépense des APU pour
l'enseignement est de X, soit Y % du total publié »), les sources, l'export et un lien permanent qui reproduit
exactement la vue.

**Garde-fous intégrés** (les règles du site deviennent des contraintes du formulaire, expliquées à l'utilisateur) :
- une combinaison impossible est grisée avec sa raison (« Répartition par fonction : non publiée pour les régions »,
  lien vers la lacune) ;
- jamais d'addition d'agrégats emboîtés ni de sous-secteurs ; jamais deux unités sur un axe ; une source et un stade
  par graphique ;
- toute valeur calculée (part, écart, par habitant) est marquée « calcul du site ».

**Points de départ plutôt que questions imposées** : des préréglages sans parti pris, décrits par ce qu'ils montrent
(« Une série depuis 1995 », « Comparer des départements », « Un budget entre projet, loi et exécution »), et des
préréglages par public (« Pour un cours », « Pour vérifier un chiffre », « Pour ma collectivité »).

`/serie` et `/comparer` font déjà 80 % de ce travail : le constructeur est leur fusion, avec les dépenses fiscales, le
budget de l'État et les territoires branchés dessus.

## 5. Les pages actuelles, jugées à cette aune

| Page | Question posée aujourd'hui | Verdict | Pourquoi |
|---|---|---|---|
| Accueil (carte en cases) | « Où va la dépense publique ? » | **Garder**, comme une porte parmi d'autres | Bonne entrée pour un débutant ; mais elle impose le seul angle « dépense » : ajouter les portes Notions, Constructeur, Vérifier |
| `/depenses-publiques` | « Où va l'argent public ? » | **Fusionner** avec l'accueil ou le constructeur | Même donnée que la carte (COFOG), autre forme |
| `/budget-etat` | « Que finance le budget de l'État ? » | **Garder**, reformuler en « Budget de l'État : crédits par mission » | Utile aux publics experts ; le titre-question suppose une lecture |
| `/depenses-fiscales` | « Combien coûtent… » → corrigé en « Dépenses fiscales : montants publiés » | **Garder** dans le constructeur | Voir §6 : mise en avant à rééquilibrer |
| `/territoires`, fiche territoire | « Que dépense ma région, mon département ? » | **Garder** | Besoin réel (citoyens, élus, agents) ; à étendre aux communes |
| `/comprendre` | « Recettes, dépenses et solde » ; « Qui dépense ? » ; « La dette » | **Transformer en Notions** | « Qui dépense ? » répond mal : il faut d'abord la notion de **périmètre** (qui sont les APU, pourquoi la somme des sous-secteurs dépasse le total). Recettes/dépenses/solde et flux/stock sont de vraies notions |
| `/explorer` | Questions tirées au hasard | **Remplacer** par les points de départ du constructeur | C'est exactement le « présenter des trucs aléatoirement » |
| `/serie`, `/comparer` | Outils | **Fusionner** dans le constructeur | Base du constructeur |
| `/contexte` | Fonctions et votes budgétaires | **À trancher** (§6) | Factuel, mais la juxtaposition avec les chiffres peut suggérer une causalité |
| `/lacunes`, `/methode`, `/lexique`, `/source`, preuves | Vérifier | **Garder** | Socle de confiance pour tous les publics |

## 6. Neutralité et factualité : ce qui a été vérifié, ce qui reste à trancher

**Vérifié le 2026-10-28** (517 chaînes d'interface relues, avec recherche de termes évaluatifs) :
- « coût » des dépenses fiscales remplacé par **« montant publié »** : le jeu source ne parle pas de coût, il publie une
  « prévision 2026 si dépense fiscale » ; le titre « Combien coûtent les dépenses fiscales ? » devient « Dépenses
  fiscales : montants publiés » ;
- « les plus importantes » (jugement) remplacé par **« celles dont le montant est le plus élevé »** ;
- les phrases « À savoir pour bien lire » ne décrivent que les données ou la méthode du site, sans affirmation sur le
  monde ;
- passe précédente (2026-10-27) : grille de termes neutres, handoff §4.1.

**À trancher (choix éditoriaux, pas des erreurs de fait)** :
1. **Le site ne montre que la dépense.** Les recettes (impôts, cotisations, par catégorie) n'ont aucune page ; les
   dépenses fiscales sont mises en avant sur l'accueil. Un site centré sur « où va l'argent » sans « d'où il vient »
   donne une vue partielle. Proposition : collecter les recettes des APU par catégorie (Eurostat `gov_10a_taxag`) et
   donner aux deux côtés le même poids.
2. **Contexte institutionnel.** Afficher présidents, gouvernements et partis à côté des soldes est factuel, mais invite
   à attribuer les chiffres à un camp. Proposition : le garder en couche optionnelle du constructeur (repères de
   dates), jamais par défaut, avec la mention déjà présente « aucun lien de cause n'est établi ».
3. **Noms d'acteurs saisis à la main** (« État et administrations centrales », « Collectivités locales »…) : remplacer
   par les libellés publiés (codelist des secteurs d'Eurostat, à collecter).
4. **Choix des préréglages** : toute sélection de « questions » est un choix éditorial. Les préréglages doivent décrire
   une forme (« une série depuis 1995 ») et non un sujet chargé ; leur liste doit être publique et justifiée.

**Règles pour tout nouveau texte** (en plus de la grille du handoff) : vocabulaire de la source plutôt que le nôtre ;
pas d'adjectif de grandeur (« important », « lourd », « massif ») ; pas de verbe d'évolution chargé (« explose »,
« dérape ») ; une variation est un nombre, signé et marqué « calcul du site » ; aucune causalité.
