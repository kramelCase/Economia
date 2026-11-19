# Feuille de route

Ce document donne la **vision et les grands chantiers**. Le travail au jour le jour se suit dans les tickets GitHub
(onglet *Issues*) et le tableau (onglet *Projects*) : chaque chantier ci-dessous devient un ou plusieurs tickets.
Une tâche finie est retirée de ce document, pas cochée : l'historique est dans git. Voir [CONTRIBUER.md](CONTRIBUER.md).

## 1. Vision du produit

Economia est une plateforme publique, pédagogique et vérifiable pour explorer pas à pas les finances publiques françaises.
Elle doit permettre de passer naturellement :
- d'une question à un chiffre ;
- d'un chiffre à l'organisme qui le porte ;
- de l'organisme à ses flux ;
- des flux à la source officielle.

Elle répond à six questions, chacune dans la limite de ce que les documents publiés permettent d'établir :

| Question | Ce qu'elle couvre | Aujourd'hui |
|---|---|---|
| **Quoi ?** | Recettes, dépenses, solde, dette, politiques publiques (fonctions, missions) | Couvert au niveau agrégé |
| **Qui ?** | Organismes qui collectent, décident, financent et dépensent | 4 sous-secteurs, l'État, régions, départements ; aucun organisme individuel |
| **Où ?** | Territoires | Régions et départements ; pas de communes ; pas de déclinaison territoriale du national |
| **Quand ?** | Évolutions, versions, décisions datées | Séries 1995–2025 ; frise des gouvernements ; pas d'historique des révisions |
| **Comment ?** | Mécanismes de financement, flux entre organismes, consolidation | Absent (la machine 3D en est l'esquisse) |
| **Pourquoi ?** | Textes, décisions et contexte documentés, **jamais une causalité déduite** | Lexique cité, scrutins ; pas de lien décision → exécution |

Elle s'adresse d'abord au citoyen sans bagage économique, et propose aux journalistes, économistes, chercheurs et analystes des outils avancés dans la même application (`docs/vision/INTERFACE.md`, 8 profils).

## 2. Principes non négociables

1. **Aucune donnée inventée.** Tout chiffre, libellé officiel ou définition vient de `raw/` par un chargeur, ou d'une citation exacte et datée (`content/concepts.yaml`). Un trou est une `lacune` affichée, jamais un zéro.
2. **Aucune relation financière supposée.** Un flux entre deux organismes n'existe à l'écran que s'il est publié. On n'attribue jamais un euro d'impôt à une dépense sans affectation documentée.
3. **Aucune causalité affirmée.** Les décisions et responsables sont posés sur la frise du temps, jamais présentés comme la cause d'une variation.
4. **Aucune addition incompatible.** On ne somme ni des niveaux emboîtés (COFOG, agrégats OFGL), ni deux sources, ni deux stades (PLF, LFI, exécution), ni AE et CP, ni deux référentiels comptables (comptabilité nationale, budgétaire, générale). Une opération n'est permise que si ses conditions de compatibilité sont vérifiées dans le code.
5. **Dette, déficit, recettes et financement sont distincts.** Le solde est un écart entre deux flux ; la dette est un stock ; l'emprunt est un financement. Aucune vue ne les présente comme équivalents.
6. **Brut, dérivé, interprétation.** Toute valeur calculée par le site porte sa formule et la mention « calcul du site ». Le texte d'interface décrit les données sans affirmation factuelle non sourcée.
7. **Neutralité** (`docs/vision/economiste.md` §7) : pas de score de gestion, pas de projection maison, pas de simulateur, pas d'équivalence inventée, pas de vocabulaire militant.
8. **Bilinguisme FR/EN** ; adresses existantes préservées (sinon redirection) ; mobile d'abord (320 px).
9. **La base n'est ni décrite ni téléchargeable sur le site** (décision du user) ; on publie des fichiers par document (`/data/`), pas le SQLite.
10. **Collectes** : celles prévues ici sont autorisées par le user (2026-10-30), depuis des sources officielles ouvertes ; toute autre collecte lui est demandée.

## 3. Synthèse des phases

Les phases peuvent se chevaucher quand leurs dépendances le permettent (§5).

| Phase | Contenu | Chantiers | Sortie |
|---|---|---|---|
| **0 — Stabilisation** | Rendre l'existant vert et commité ; corriger ce qui est trompeur dans la machine ; première matrice de couverture | A, E, H | Suite de tests verte, base de départ commitée |
| **1 — Première publication** | Mettre en ligne le périmètre actuel, ses limites affichées | J (+ F badges) | Site public v1, daté |
| **2 — Navigation et fiche pilote** | Liens transversaux, une fiche thématique réellement alimentée, outil « pourquoi deux chiffres diffèrent » | B, C, F, A | Fiche « Enseignement » publiée, modèle généralisable |
| **3 — Organismes et flux** | Modèle des organismes, transferts publiés, consolidation | A, D, H | Fiches d'organismes, flux documentés |
| **4 — Outils d'analyse** | Socle commun des widgets, puis W1 à W17 par dépendances | G, H | Widgets partageables |
| **5 — Machine 3D avancée** | Trois niveaux, branchée sur les fiches et les flux | E | Explorateur progressif |
| **6 — Extension de la couverture** | Communes, Sécurité sociale détaillée, Europe, exécution pluriannuelle, hors-bilan | H, I, D | Matrice de couverture qui progresse |

**Pourquoi cet ordre.** La mise en ligne passe avant la refonte de la machine et avant les widgets : le site actuel est déjà utile s'il affiche ses limites. Attendre l'exhaustivité repousserait le lancement indéfiniment.
Les fiches thématiques passent avant le modèle des flux : elles relient des pages qui existent déjà avec des données déjà en base, alors que les flux dépendent de sources encore à identifier (§8).

## 4. Prochaines tâches, dans l'ordre

1. **En attente du user — identité et licences** : remplir `content/editeur.yaml` (éditeur, directeur de la publication, contact, hébergeur, licence du code, licence des fichiers `/data/`). La page `/fr/mentions` affiche « à compléter » d'ici là. → J
2. **Construire et tester l'image** (`docker compose up --build` en local) : Docker Desktop doit être lancé sur le poste. → J
3. **En attente du user — hébergeur et domaine** : choisir où héberger et sous quel nom de domaine, puis suivre `docs/EXPLOITATION.md`. → J
4. **En attente du user — dépôt distant** : créer le dépôt (GitHub ou autre) et autoriser le premier envoi ; la CI (`.github/workflows/ci.yml`, clone neuf → collecte → base → tests) y sera vérifiée au premier passage. Archive datée de `raw/` (550 Mo) chez l'hébergeur choisi. → J

## 5. Matrice des dépendances

Chaque ligne indique les chantiers dont elle dépend. **●** : bloquant. **○** : utile, mais on peut avancer sans.

| Chantier ↓ dépend de → | A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|---|
| **A** Fiabilité et modèle | | | | | | | | ○ | | |
| **B** Navigation | ○ | | ○ | | | ○ | | | | |
| **C** Fiches thématiques | ● | ● | | ○ | | ○ | ○ | ● | ○ | |
| **D** Organismes | ● | ○ | | | | | | ● | | |
| **E** Machine 3D | ● | ○ | ● | ● | | ○ | | | | |
| **F** UX et pédagogie | | ○ | | | | | | | | |
| **G** Widgets | ● | ○ | | | | ○ | | ○ | ○ | ○ |
| **H** Couverture | ● | | | | | | | | | |
| **I** Décisions | ● | | | | | | ○ | ● | | |
| **J** Publication | ○ | | | | | | | | | |

Lecture rapide :
- **A** est le socle de tout.
- **C** a besoin de la navigation (B) et de la matrice de couverture (H) pour afficher ses limites.
- **E**, aux niveaux 2 et 3, a besoin des fiches (C) et des organismes (D) : sans eux, la machine n'a nulle part où mener.
- **J** peut avancer en parallèle de tout.

## 6. Définition de « terminé »

Une ligne n'est cochée que si **tout** ce qui suit est vrai et vérifié, pas seulement présent dans le code :

1. La fonctionnalité marche dans le navigateur, sur desktop et à 320 px, sans défilement horizontal hors tableaux. Une route ou un composant qui existe ne suffit pas.
2. Chaque chiffre affiché remonte à son fichier et à sa ligne. Chaque calcul affiche sa formule et la mention « calcul du site ».
3. Les données manquantes ou non comparables sont affichées comme telles (lacune, mention de non-comparabilité).
4. Des tests couvrent le comportement : contrôle de bouclage, garde-fou, rendu FR et EN. `make build && make test` passe en entier.
5. Le texte d'interface existe en français et en anglais (`make i18n-extract`, `locales/en_strings.py`, `make i18n`).
6. Les adresses existantes répondent toujours, ou redirigent.
7. Une capture desktop et 320 px a été faite.
8. Elle est commitée, puis retirée de cette liste.

Une régression sur une tâche retirée redevient une tâche de cette liste.

## 7. Chantiers

### A — Fiabilité, provenance et modèle de données · P0 · XL

- **Objectif utilisateur.** Pouvoir faire confiance à chaque chiffre, savoir de quelle version il vient, et comprendre pourquoi deux chiffres officiels diffèrent.
- **État vérifié (2026-10-30).**
  - SQLite de 83 Mo : 535 484 montants, 31 sources, 111 fichiers collectés, 10 nomenclatures, 123 entités (État, 4 secteurs, 17 régions, 101 départements). Tout montant porte `fichier_id` et `ligne_source` (NOT NULL).
  - 92 contrôles de bouclage sur 92 au vert. 139 lacunes. 115 concepts, dont 111 cités et 4 à sourcer.
  - Bloc « Justesse » de l'ancienne feuille de route fait en entier (§9).
  - Tests : 391 sur 392 passent. Échec : `test_traductions_completes`.
  - Les collectes successives sont gardées dans `raw/` (2 à 3 par source) avec leur empreinte, mais la base ne charge que la dernière. On ne peut donc pas dire quelle valeur était affichée à une date donnée.
  - Le modèle ne connaît ni organismes individuels, ni transferts, ni référentiel comptable explicite. Le référentiel est seulement implicite dans la source.
  - 22 fichiers ne sont pas commités.
- **À conserver.** Le schéma strict (`db/schema.sql`), les contrôles de bouclage, `q.single` bloquant, la gestion des ruptures de périmètre, le statut provisoire lu dans la note de l'Insee, les lacunes comme contenu, les fichiers par document (`/data/`).
- **Travaux.**
  - Opération entre deux référentiels refusée par le code partout (déjà déclaré dans `sources.yaml`, affiché sur chaque montant, et respecté par l'outil de comparaison)
  - Identifiants stables et documentés pour les entités, indicateurs, nœuds et territoires (code officiel d'abord, sinon code du site déclaré comme tel). Table de correspondance quand une nomenclature change (M52 → M57, LOLF d'une année à l'autre).
  - Garde-fous de compatibilité centralisés (unité, stade, mesure, référentiel, niveau emboîté), appelés par toutes les vues et tous les widgets, avec un test par règle
  - Valeurs dérivées tracées : formule, opérandes (identifiants des montants), mention « calcul du site »
  - Versions et révisions : charger toutes les collectes conservées, garder pour chaque montant sa première et sa dernière collecte, montrer qu'une valeur a été révisée (ancienne valeur, date, fichier)
  - Version figée datée : une adresse rouvre l'état des données à une date de collecte donnée (partagé avec J)
  - Outil « Pourquoi ces deux chiffres diffèrent-ils ? » (`/fr/differences`, en ligne) : ajouter la définition citée de chaque poste, et un moyen de choisir soi-même les deux chiffres
  - Modèle des organismes (table `organisme`, classification statistique ≠ statut juridique ≠ tutelle) et des transferts publiés (émetteur, destinataire, nature, montant, période, source, traitement de consolidation) : **conception d'abord**, à faire valider par le user
  - Contrôle de consolidation : quand une source publie un total consolidé et ses composantes non consolidées, l'écart est affiché comme « transferts internes », jamais recalculé à la main
  - Détecteur de changement de schéma d'une source (colonnes, nomenclature) : il bloque le chargement avec un message clair
- **Dépendances.** Aucune pour les premières lignes. Le modèle des organismes et des transferts dépend de l'identification des sources (H, §8).
- **Critères d'acceptation.**
  - `make test` est vert.
  - Un test refuse la somme de deux référentiels.
  - Un test montre qu'une valeur révisée garde sa valeur précédente et sa date.
  - L'outil de comparaison affiche au moins trois paires réelles, par exemple « Enseignement » COFOG État face aux missions LOLF du même domaine.
- **Sources.** Celles déjà collectées. Pour les transferts : voir H et §8.
- **Risques.**
  - Gonflement de la base si l'on charge toutes les versions. Prévoir de ne stocker que les valeurs qui changent.
  - Rapprochement d'organismes entre classifications sans table officielle : il est interdit sans source.
- **Livrable.** Un schéma v2 documenté dans `docs/SCHEMA-BASE.md`, les garde-fous centralisés, l'outil de comparaison des définitions et l'historique des révisions.

### B — Architecture de l'information et navigation · P1 · M

- **Objectif utilisateur.** Aller d'une visualisation à un chiffre, puis à un organisme, à une comparaison et à la source, sans revenir au menu.
- **État vérifié.**
  - Le menu a 5 entrées (Comprendre, Vérifier, Ma collectivité, Explorer, Données), conçues avec `docs/vision/INTERFACE.md` et validées par le user.
  - La recherche globale (`/recherche`, `/suggest`, `cmd.js`) couvre les pages, le lexique, les territoires et les postes.
  - Les adresses anglaises existent, les anciennes adresses redirigent.
  - Les pages communiquent peu entre elles : chaque outil a sa porte d'entrée.
  - La machine n'est pas dans le menu.
- **À conserver.** Les 5 entrées, sauf décision contraire du user ; les adresses ; la liste unique des entrées (`api/portes.py`).
- **Travaux.**
  - Liens contextuels standard sur tout chiffre, sous forme de menu « ce chiffre » : voir l'évolution, comparer, ouvrir la fiche du thème, ouvrir dans l'atelier, voir la source
  - Liens retour : de la provenance, d'une ligne du tableau de travail ou d'un poste Eurostat vers la fiche du thème et vers le poste dans la machine
  - Recherche étendue aux fiches thématiques, aux organismes (après D) et aux documents officiels
- **Dépendances.** C pour les cibles « fiche » ; D pour les organismes.
- **Critères d'acceptation.**
  - Depuis 5 chiffres pris au hasard sur 5 pages différentes, on atteint en un clic la fiche du thème et la source.
  - Aucune adresse existante ne renvoie 404 (test).
- **Risques.** Changer un menu déjà validé : seulement sur décision du user.
- **Livrable.** Une note de décision sur le menu, les liens contextuels et une recherche élargie.

### E — Machine 3D et visualisation des flux · P1 (niveau 1), P2 (niveaux 2 et 3) · L

- **Objectif utilisateur.** Voir d'un coup d'œil comment l'argent entre, circule et sort, puis descendre dans le détail.
- **État vérifié (prototype).**
  - `/machine`, hors menu, publiée dans la démo.
  - Circuit hydraulique façon Phillips : recettes (catégories SEC), dépenses par fonction COFOG, dette en réservoir à part. La section des tuyaux est proportionnelle au montant publié.
  - Bâtiments Kenney (CC0) ; zoom à la molette, au pincement et aux boutons ; déplacement de la vue ; fiche centrée avec bouton de fermeture.
  - **Défaut de justesse** : le besoin de financement publié complète l'entrée, comme une recette.
  - Défauts de lecture : croisements de tuyaux, étiquettes qui se chevauchent, petits bâtiments.
  - Les fichiers Kenney et `maquettes.js` ne sont pas commités.
- **À conserver.** La métaphore hydraulique, l'identité isométrique, la proportionnalité aux montants publiés, l'absence de tuyau entre solde et dette.
- **Travaux.**
  - Sélection : les éléments sans rapport s'estompent ; la fiche mène à la fiche de l'organisme (D) quand il existera
  - Niveau 2 « Exploration » : isoler un sous-secteur ou une politique et ses flux publiés
  - Niveau 3 « Analyse » : flux documentés, montants, périodes, périmètres, consolidation, provenance (après A et D)
  - Alternative 2D accessible : diagramme de flux et tableau des mêmes montants
  - Performances vérifiées sur un téléphone d'entrée de gamme ; repli 2D si WebGL est absent
  - Entrée dans le menu, **sur décision du user**
- **Dépendances.** Le niveau 1 n'a pas de dépendance. Les niveaux 2 et 3 dépendent de C et D (cibles) et de A (transferts).
- **Critères d'acceptation.**
  - Aucun flux dessiné sans montant publié (test sur la scène).
  - Le besoin de financement n'est pas compté dans les entrées de recettes.
  - Aucune étiquette ne se chevauche à 375 px ni sur desktop.
  - La vue 2D affiche les mêmes valeurs.
- **Risques.**
  - Faire du décor au détriment de la lecture.
  - Inventer un tuyau pour « fermer » le circuit : interdit.
- **Livrable.** Une machine à trois niveaux, reliée aux fiches, avec son équivalent 2D.

### F — Expérience utilisateur et pédagogie · P1 · M

- **Objectif utilisateur.** Comprendre sans maîtriser le vocabulaire, et sans être noyé sous les badges.
- **État vérifié.**
  - L'identité graphique est cohérente : sombre, turquoise, verre, Plex Sans.
  - Les termes du lexique sont reliés automatiquement, avec une infobulle.
  - Un parcours de 6 étapes existe (`/comprendre/1-6`).
  - « Vérifier » part d'un thème.
  - Les badges `SOURCE` et `provisoire` sont très présents.
  - Les grands équilibres sont en colonnes 3D.
  - L'atelier expose d'emblée des filtres techniques. L'explorateur a déjà un panneau Quoi / Qui / Quand.
- **À conserver.** La direction graphique, le lexique relié, le parcours de 6 étapes et « Vérifier ».
- **Travaux.**
  - Explications progressives sous les indicateurs clés : « En bref » (définition citée courte), « Comprendre » (définition complète citée), « Approfondir » (source). **Uniquement des citations**, pas de texte rédigé par le site.
  - Vue 2D par défaut pour les mesures précises (dette 1995–2025 en courbe) ; la 3D reste pour la structure
  - Filtres harmonisés Quoi / Qui / Où / Quand sur l'atelier, le constructeur et le tableau de travail, sur le modèle de l'explorateur
  - Atelier : entrée par intention (« voir l'évolution de… », « comparer… », « quelle part… ») avant les réglages
  - Mode découverte et options avancées dans la même application (réglages repliés)
  - États vides et erreurs compréhensibles ; navigation clavier ; contrastes secondaires (audit d'accessibilité)
  - Parcours guidés : « page suivante » contextuelle entre les pages d'un même thème
- **Dépendances.** B pour les liens ; C pour les parcours par thème.
- **Critères d'acceptation.**
  - Un seul repère de source par valeur.
  - Audit clavier et contrastes passé.
  - Chaque explication progressive est une citation avec sa source.
- **Risques.** « Expliquer » sans écrire d'affirmation non sourcée : il faut des définitions citées assez nombreuses (4 concepts restent à sourcer).
- **Livrable.** Les badges allégés, des explications progressives, des filtres unifiés et un atelier par intention.

### J — Publication, exploitation et pérennité · P0 · L

- **Objectif utilisateur.** Un site public stable, rapide, daté, dont les chiffres cités restent vérifiables dans le temps.
- **État vérifié.**
  - Le site tourne en local seulement (port 8790). Une démo statique figée (sélection de pages) existe à part.
  - Pas de dépôt distant, pas de CI, pas de conteneur.
  - Les adresses inconnues renvoient la 404 de FastAPI, non traduite.
  - `raw/` fait 550 Mo, `data/` 65 Mo.
- **À conserver.** Les fichiers par document avec empreinte dans le nom (cache illimité possible) ; aucune requête libre vers le serveur (WIDGETS.md §4 bis).
- **Travaux** (ancien bloc « Mise en ligne », complété) :
  - Dépôt distant (décision du user), CI vérifiée au premier envoi, archive datée des fichiers bruts
  - Image construite et testée en local ; hébergeur et domaine choisis par le user, puis mise en ligne
  - Identité de l'éditeur et licences du code et des fichiers `/data/` dans `content/editeur.yaml` (décision du user)
  - Partage : balises Open Graph, image d'aperçu par vue, lien court, version figée datée
  - Collecte planifiée : comparaison d'empreintes, fraîcheur affichée par source
  - Alertes en cas d'échec de collecte ou de changement de schéma d'une source (avec A)
  - Vérification périodique des liens vers les documents officiels
  - Sauvegarde et restauration testée (base, `raw/`, `data/`)
  - Budget de performance : poids des pages, temps de rendu à 320 px, machine 3D sur un téléphone modeste
  - Stratégie de migration du schéma (scripts versionnés)
- **Dépendances.** Aucune bloquante. A pour la version figée.
- **Critères d'acceptation.**
  - Un clone neuf construit et teste le site en CI.
  - Une restauration depuis la sauvegarde est faite au moins une fois.
  - Le site public affiche la date de collecte de chaque source.
- **Risques.**
  - Le choix de l'hébergeur et du domaine revient au user.
  - Le coût de stockage de `raw/`.
- **Livrable.** Une v1 publique et un mode d'exploitation documenté.

## 8. Dépendances bloquées par les données

Ces travaux ne peuvent pas avancer tant qu'une source publiée n'est pas identifiée, puis collectée avec l'accord du user. Les sources marquées « à identifier » ne sont **pas vérifiées**.

| Besoin | Bloque | Source pressentie | Statut |
|---|---|---|---|
| Transferts entre administrations (État → collectivités, → sécurité sociale) | A (flux), D, E niveaux 2 et 3, C bloc « transferts » | Comptes nationaux détaillés par sous-secteur ; dotations dans les agrégats OFGL | À identifier |
| Liste des organismes classés en S13 | D | Insee | À identifier |
| Opérateurs de l'État | D | Annexe au PLF | À identifier |
| Sécurité sociale par branche ou régime | H, C (santé, retraites) | Commission des comptes de la Sécurité sociale, LFSS | À identifier |
| Exécution du budget de l'État sur plusieurs années | I, W9, W7 | Lois de règlement (data.economie.gouv.fr) | Repérée, non collectée |
| Modifications de crédits en cours d'année | I | — | À identifier |
| Engagements hors bilan, garanties | H | Compte général de l'État | À identifier (souvent en PDF) |
| Entreprises et participations publiques | D | Agence des participations de l'État, Insee | À identifier |
| Bénéficiaires finaux de la dépense | — | Rarement publiés de façon exhaustive | **Hors périmètre** : lacune affichée |
| Déclinaison territoriale des dépenses nationales | C (bloc territorial), B | Très partielle selon les politiques | Lacune par défaut |
| Déflateur, population nationale | W3, W13, euros constants | Eurostat ou Insee | Repérée, non collectée |
| Autres pays de l'UE | W10 | Mêmes jeux Eurostat | Repérée, non collectée |
| Strates de population, contours | W4, W6 | OFGL, IGN Admin Express | Repérée, non collectée |

## 9. Hors périmètre actuel

- Simulateur de réforme, chiffrage de programme, projection calculée par le site.
- Score ou note de « bonne gestion » ; classement synthétique.
- Attribution causale automatique (« sous tel gouvernement… »).
- Équivalences inventées (« = N hôpitaux »), compteur de dette « par seconde ».
- Attribution d'un euro d'impôt à une dépense sans affectation publiée.
- Reconstitution des bénéficiaires finaux.
- Console SQL ou requête libre ; téléchargement de la base SQLite.
- Langues autres que le français et l'anglais (la structure les permet, mais pas maintenant).

## 10. Plus tard

Rangés le 2026-10-31 à la demande du user : ces chantiers ajoutent surtout des pages, alors que la priorité est un site court et lisible (quatre entrées). Ils reviennent dans §7 seulement sur décision du user.

### D — Exploration institutionnelle et financière · P1 · XL

- **Objectif utilisateur.** Savoir qui collecte, qui décide, qui finance et qui dépense, organisme par organisme.
- **État vérifié.** On a les 4 sous-secteurs SEC (ensemble, centrales, locales, sécurité sociale), l'État (budget LOLF), les régions et les départements (OFGL), ainsi que les organes et personnes de l'Assemblée nationale (frise). On n'a ni opérateurs, ni organismes de sécurité sociale, ni communes, ni entreprises publiques.
- **À conserver.** Les fiches territoire. Elles deviendront un cas particulier de fiche d'organisme.
- **Travaux.**
  - Arbre institutionnel publié : S13 → S1311 / S1313 / S1314, chaque nœud avec sa définition citée et ses chiffres
  - Liste officielle des organismes classés en S13 (Insee, à identifier et collecter avec accord) : fiche minimale (classification, sous-secteur, années de présence)
  - Opérateurs de l'État (annexe au PLF, à identifier) : rattachement au programme, subvention pour charges de service public si elle est publiée
  - Fiche d'organisme générique : rôle (texte cité), classification statistique, statut juridique, tutelle, ressources, dépenses, transferts, évolution, sources. Chaque champ est affiché seulement s'il est publié.
  - Entreprises à participation publique **dans une rubrique distincte et marquée hors périmètre APU** : participations, dividendes, apports, garanties, si une source publiée existe
- **Dépendances.** A (modèle organismes), H (sources identifiées).
- **Critères d'acceptation.**
  - Classification statistique, statut juridique, tutelle et relation financière s'affichent dans quatre champs séparés, jamais fusionnés.
  - Une entreprise publique ne figure jamais dans un total APU (test).
- **Risques.**
  - Les catégories de la comptabilité nationale ne recoupent pas les catégories juridiques : aucun rapprochement sans table officielle.
  - Volume de collecte (communes, organismes).
- **Livrable.** Un arbre institutionnel, des fiches d'organismes et une rubrique entreprises publiques.

### G — Analyse, comparaisons et widgets · P1 · XL

- **Objectif utilisateur.** Composer, comparer et partager ses propres vues, toujours sourcées. Le catalogue est dans `docs/vision/WIDGETS.md`, validé le 2026-10-28. Les identifiants W1 à W17 sont conservés.
- **État vérifié.**
  - **Socle partiel.**
    - Fichiers par document avec empreinte et manifeste (`/data/manifest.json`) : fait.
    - État de l'atelier dans l'adresse : fait.
    - Bibliothèque de graphiques unique (Observable Plot) : non.
    - Garde-fous centralisés : non (voir A).
  - **W1 Atelier : partiel.** Fait : export PNG (1080 et 1200), SVG, base 100, pente, annotations. Pas fait : carte de chaleur, course de rangs, GIF ou vidéo, code d'intégration.
  - **Partiels.**
    - Le constructeur `/serie` et le tableau de travail `/comparer` couvrent une partie de W12 et de W4.
    - `/budget-etat` couvre une partie de W7, `/depenses-fiscales` de W11, `/contexte` de W14, `/grands-equilibres` de W15.
    - Aucun n'a été audité contre sa spécification.
  - W2, W3, W5, W6, W8, W9, W10, W13, W16 et W17 : absents.
- **À conserver.** Les 17 widgets, aucun supprimé ni compté comme fait sans audit. Les pages existantes deviennent des widgets ou les hébergent.
- **Travaux** (ordre fixé par les dépendances, pas par le §6 de WIDGETS.md) :
  - Audit de chaque page existante contre la spécification du widget correspondant (W1, W4, W7, W11, W12, W14, W15) : fait, partiel, manquant
  - Socle : garde-fous communs (A), bibliothèque de graphiques unique, état dans l'adresse partout, export réseaux, modèles prêts
  - W13 Calculs dérivés (barre d'outils commune), dont dépendent W3, W1 et W15
  - W1 Atelier complété
  - W8 Pour 1 000 €, W2 A/B, W3 Décomposition (données en base)
  - W15 Dette, solde, intérêts ; W7 Budget de l'État ; W11 Dépenses fiscales (compléter l'existant)
  - W4 Pairs, W5 Nuage de points (OFGL en base)
  - W6 Carte (contours IGN à collecter)
  - W14 Frise de contexte, branchée sur I
  - W12 Tableau croisé, W16 Récit, W17 Intégration
  - W9 Voté puis réalisé et W10 Europe, après les collectes de H
  - Chaque widget s'ouvre seul **et** depuis les fiches thématiques
- **Dépendances.** A (garde-fous), H (collectes), I (W14, W9).
- **Critères d'acceptation.** Ceux de chaque widget dans WIDGETS.md (ligne « Empêche ») sont testés. Chaque export porte la source et le lien.
- **Risques.** La dispersion. Un widget n'est commencé que si son socle est fini.
- **Livrable.** Des widgets partageables et intégrables.

### H — Couverture des finances publiques · P0 (matrice), P1-P2 (extensions) · XL

- **Objectif utilisateur.** Savoir exactement ce que le site couvre, ce qui est partiel et ce qui manque. L'exhaustivité est une **cible**, jamais présentée comme acquise.
- **État vérifié (base au 2026-10-30).**

| Domaine | Source collectée | Années | Granularité | État |
|---|---|---|---|---|
| Comptes des APU, grands postes | Eurostat `gov_10a_main` | 1995–2025 | 4 sous-secteurs, 13 postes | Intégré |
| Dépenses par fonction | Eurostat COFOG | 1995–2024 | 4 sous-secteurs, 80 nœuds | Intégré |
| Dépenses par fonction × nature | Eurostat | 1995–2024 | 100 nœuds | Chargé (`apu_detail.py`, non commité) |
| Prélèvements obligatoires détaillés | Eurostat | 1995–2025 | 10 postes | Chargé, non commité |
| Dette (Maastricht) et détenteurs | Eurostat | 1995–2025 ; détenteurs 2020–2025 | Ensemble | Intégré ; détenteurs non commités |
| Budget de l'État | DB, budget vert PLF 2026 ; PLF 2025 par destination | PLF 2024–2026, LFI 2025, exécution 2024 | Mission, programme, action | Partiel : une seule année d'exécution |
| Dépenses fiscales | DB, PLF 2026 | 2024–2026 | Par dépense | Intégré |
| Régions, départements | OFGL | 2012–2025 | 68 agrégats ; fonctions départementales 2020–2025 | Intégré |
| Contexte politique | Assemblée nationale | Législatures 14 à 17 | Organes, personnes, 70 scrutins | Intégré |
| Définitions | Insee, OFGL, Légifrance (relevé manuel) | — | 115 concepts | 4 à sourcer |
| Communes, intercommunalités | — | — | — | Absent |
| Sécurité sociale détaillée | — | — | — | Absent (seulement le sous-secteur S1314) |
| Transferts entre administrations | — | — | — | Absent |
| Organismes S13, opérateurs | — | — | — | Absent |
| Engagements hors bilan, garanties | — | — | — | Absent |
| Entreprises et participations publiques | — | — | — | Absent |
| Autres pays de l'UE | — | — | — | Absent (France seule) |
| Déflateur, population nationale | — | — | — | Absent |

- **À conserver.** Une source n'entre qu'avec son chargeur, ses contrôles de bouclage et ses lacunes.
- **Travaux.**
  - Déflateur du PIB et population (euros constants, par habitant national)
  - Autres pays de l'UE, mêmes jeux Eurostat (W10)
  - Exécution du budget de l'État sur plusieurs années (lois de règlement ou d'approbation des comptes)
  - Strates de population OFGL (pairs officiels, W4) ; contours IGN Admin Express (W6)
  - Communes et intercommunalités (OFGL), avec un passage à DuckDB si le volume l'exige
  - Sécurité sociale détaillée (branches, régimes), source à identifier
  - Transferts entre administrations publiés, source à identifier (§8)
  - Liste des organismes S13, opérateurs de l'État (D)
  - Engagements hors bilan et garanties, **rubrique séparée, jamais additionnée à la dette de Maastricht**, source à identifier
  - Projections officielles (retraites, etc.) : **seulement citées et marquées « projection publiée par… »**, jamais calculées par le site ; à décider avec le user
- **Dépendances.** A (référentiels, versions). Chaque collecte demande l'accord du user.
- **Critères d'acceptation.**
  - La matrice est générée, pas écrite à la main.
  - Chaque domaine « absent » renvoie à sa lacune.
  - Une nouvelle source passe ses contrôles de bouclage avant d'apparaître.
- **Risques.** Le volume (communes), les sources en PDF seulement, les formats changeants.
- **Livrable.** Une matrice publiée, qui s'enrichit à chaque collecte.

### I — Décisions publiques et contexte · P2 · L

- **Objectif utilisateur.** Suivre une décision : texte → crédits proposés → votés → modifiés → exécutés → écart, sans conclure à une cause.
- **État vérifié.** `/contexte` présente les gouvernements, ministres, lois et 70 scrutins avec les votes par groupe (Assemblée nationale, législatures 14 à 17). `/preuve` donne le texte justificatif. Les budgets disponibles : PLF 2024–2026, LFI 2025, exécution 2024 seulement.
- **À conserver.** Repères de présidence désactivés par défaut et mention de non-causalité ; posés comme des dates seulement.
- **Travaux.**
  - Chaîne d'un programme : PLF → LFI → exécution de la même année, avec les écarts (W9)
  - Modifications en cours d'année (lois de finances rectificatives, décrets), source à identifier
  - Explications officielles des écarts : rapports annuels de performance, citées seulement
  - Lien d'une loi de finances vers ses montants dans le site
- **Dépendances.** H (exécution pluriannuelle), A (stades jamais mélangés).
- **Critères d'acceptation.**
  - Aucune phrase générée n'attribue une variation à une personne ou à un texte (test sur les gabarits).
  - Les écarts ne sont calculés qu'à l'intérieur d'une même année et d'une même mesure.
- **Risques.** La tentation éditoriale. Les sources d'exécution infra-annuelle sont peu ouvertes.
- **Livrable.** Un suivi « voté puis réalisé » et une frise reliée aux montants.
