# Synthèse : le moteur d'exploration de Comptes publics

Arbitrage final après deux tours de travail des quatre spécialistes (économiste, UX/UI, directeur artistique,
dataviz) : livrables `economiste.md`, `ux.md`, `direction-artistique.md`, `dataviz.md`, puis critiques
croisées `critique-*.md`. Ce document les tranche ; en cas de contradiction, **il fait foi**.

## 0. La vision en cinq phrases

1. **On tape une question, le site la réécrit en une phrase dont chaque mot se change** : « Combien
   [l'enseignement] coûte-t-il à [toutes les administrations publiques] en [2024, réalisé], en [% du PIB] ? ».
   La phrase est l'URL, le titre, la légende de l'image partagée.
2. **La réponse est une page composée pour cette phrase** : un chiffre, sa source lisible, ce qu'on ne sait
   pas, un visuel choisi par le site (jamais par l'utilisateur), puis « et maintenant ? ».
3. **Le site refuse de mentir, sans jamais dire non** : ce qui ne se compare pas s'affiche côte à côte avec la
   raison ; ce qui n'existe pas apparaît barré, avec qui devrait le publier.
4. **Les trous sont aussi visibles que les chiffres** : même place, même poids, une hachure à l'encre.
5. **L'identité est celle d'un registre public** : papier, encre, une cote sous chaque chiffre. Aucun autre
   site ne peut copier ce look sans s'engager sur la même rigueur.

Ce n'est pas un tableau de bord : il n'y a ni tuiles KPI, ni menu de graphiques, ni onglets à apprendre.
C'est une grammaire de questions.

## 1. Ce que deviennent tes idées de départ

| Ton idée | Décision | Pourquoi |
|---|---|---|
| Hero plein écran | **Gardé, renforcé** | Il montre en une seconde la promesse : une question, un chiffre sourcé, et en face ce que l'État ne chiffre pas. |
| Recherche type Select2 | **Transformée** en autocomplétion typée maison | Les suggestions sont groupées par nature (département, fonction, mission, niche, mot du lexique) et **affichent déjà le chiffre**. Le multi-tags générique permettrait d'empiler des combinaisons absurdes (deux stades, trois unités). La lib Select2 (jQuery) est lourde et peu accessible sur mobile. |
| Tags qui défilent | **Transformés** en questions-amorces fixes qui changent à chaque visite | Le défilement automatique est illisible à 320 px et interdit par l'accessibilité (WCAG 2.2.2). Les amorces gardent la découverte et montrent leur vrai chiffre avant le clic. |
| Onglets thème / territoire / période / analyse | **Devenus les mots de la phrase** | On veut thème *et* territoire *et* période en même temps ; des onglets n'en montrent qu'un. Seul onglet conservé : Graphique · Tableau · Carte · Source à l'intérieur d'une réponse. |
| Comparateur universel | **Gardé, avec garde de comparabilité** | « + comparer » partout. Mais deux chiffres de périmètres ou de stades différents ne vont jamais sur le même axe : panneaux séparés + raison + comparaison légitime la plus proche. |
| Carte type store locator | **Gardée sans fond de carte** | Code postal → mon département ; carte SVG des contours (desktop), grille de tuiles égales (mobile), liste classée synchronisée. Pas de Leaflet : inutile pour 101 territoires, lourd, générique. |
| Exploration guidée | **Gardée** : « Et maintenant ? » sous chaque réponse, plus des fils relus | Chaque suggestion change un seul mot de la phrase et montre son chiffre. |
| Partage et export | **Gardé, v1** | Image recomposée par format (1:1, 4:5, 9:16, 1200×630) avec la source dans les pixels, CSV avec la ligne d'origine, citation prête à coller. |
| Sources et méthodologie | **Renforcées** | Un toucher sur n'importe quel chiffre ouvre sa provenance sans quitter la page. |

**Ce qu'on ajoute et que tu n'avais pas demandé** : le résolveur de périmètre (« éducation » existe dans
deux comptabilités), les options impossibles affichées comme lacunes, le mur des absences, la marche des
niches fiscales, le mode « j'ai lu ce chiffre » (coller une affirmation virale), l'API citable pour les
agents IA, le permalien figé au millésime des données.

**Ce qu'on refuse, malgré l'attrait** : chatbot, verdict vrai/faux, « où vont mes impôts » personnalisé,
constructeur de graphiques libre, compteur de dette, journée de libération fiscale, bar chart race, Sankey
recettes → dépenses, scores de « bonne gestion », projections maison. Chacun exige une méthode inventée ou
fabrique de faux chiffres.

## 2. Profils et besoins (condensé de `economiste.md` §1)

| Famille | Profils | Ce qu'ils viennent chercher | Contexte |
|---|---|---|---|
| Information | journaliste desk, plateau TV/radio, fact-checkeur, datajournaliste, presse locale, presse étrangère | vérifier une affirmation en < 10 s, libellé officiel, URL stable, citation, export | mobile une main (plateau) ; bureau 30 min (desk) |
| Savoir | économiste, chercheur, étudiant, candidat aux concours, enseignant, lycéen | séries harmonisées, ruptures documentées, définitions citées, CSV avec provenance | double écran ; mobile la veille d'un partiel ; vidéoprojecteur |
| Décision | collaborateur parlementaire, élu local, candidat, agent de collectivité, agent de l'État, magistrat financier | niveau programme/action, voté vs réalisé, comparaison à des pairs, export pour une séance | période budgétaire (oct.-déc.) |
| Société civile | ONG de justice fiscale, associations de contribuables, ONG environnementales, syndicats, patronat, associations d'usagers | **un chiffre défendable devant un contradicteur** : les deux camps doivent pouvoir citer la même page | bureau, campagne |
| Économie | entreprises, fiscalistes, analystes crédit, consultants | coût d'une niche, benchmark, API | bureau |
| Grand public | créateurs de contenu, utilisateurs face à une infographie virale, citoyens, parents, budgets participatifs | comprendre en un écran, son territoire, un visuel partageable sourcé, savoir à qui réclamer une donnée | mobile, 30 secondes, depuis un lien |
| Oubliés | agents IA, wikipédiens, documentalistes, traducteurs, Outre-mer, petites communes, lanceurs d'alerte | API citable, références datées, territoires « atypiques » traités et non exclus | — |

Le besoin commun à tous : **savoir de quelle dépense on parle** (périmètre, stade, unité) avant le chiffre.
C'est ce qui fonde la phrase-requête.

## 3. Catalogue classé des fonctionnalités

U = utilité, Cx = complexité, VA = valeur ajoutée (1 à 5). Données : ✅ en base · 📥 à collecter · — interface.

### Lot 1 : le cœur (sans lui, rien ne tient)
| Fonction | Pour | U | Cx | VA | Données |
|---|---|---|---|---|---|
| Phrase-requête à 5 emplacements (vue · thème · périmètre · temps+stade · mesure), URL = phrase | tous | 5 | 3 | 5 | — |
| Autocomplétion typée et groupée, **avec le chiffre dans la liste** | tous | 5 | 3 | 5 | ✅ |
| Analyse des phrases libres par règles (jamais de chiffre inventé), « Vous avez écrit… » | N J C | 5 | 3 | 5 | — |
| Résolveur de périmètre (deux lectures, jamais sur le même axe) | tous | 5 | 2 | 5 | ✅ |
| Synonymes militants → catégorie officielle la plus proche, **ou « pas de catégorie officielle »** | N C J | 4 | 2 | 5 | — |
| Options impossibles visibles, barrées, avec raison et responsable | tous | 5 | 3 | 5 | ✅ |
| Page-réponse : chiffre + ligne de lecture + cote + lacune bloquante + visuel + « pour bien lire » (≤ 3 notes déclenchées) + « et maintenant ? » | tous | 5 | 3 | 5 | ✅ |
| Marque source unique : 1ᵉʳ toucher = popover, 2ᵉ = ligne d'origine | tous | 5 | 2 | 5 | ✅ |
| Hachure encre = signe unique de l'absence, partout | tous | 5 | 2 | 5 | ✅ |
| Test automatique : aucun nombre affiché sans marque source | — | 5 | 2 | 4 | — |

### Lot 2 : comparer, situer, partager
| Fonction | Pour | U | Cx | VA | Données |
|---|---|---|---|---|---|
| « + comparer » (≤ 4 éléments) avec garde de comparabilité | J É L | 5 | 3 | 5 | ✅ |
| Thème vs thème, période vs période, stade vs stade | J É | 5 | 2 | 4 | ✅ |
| Territoire vs médiane / départements de sa région | L N | 5 | 2 | 4 | ✅ |
| Code postal → mes collectivités | N L | 5 | 2 | 4 | 📥 COG INSEE + base La Poste |
| Carte SVG (desktop) + tuiles (mobile) + liste synchronisée, €/hab seulement | N L C | 4 | 3 | 4 | 📥 contours OFGL/IGN |
| Image partageable recomposée par format, source dans les pixels | C J | 5 | 3 | 5 | — |
| CSV long avec sha256 et ligne ; citation prête à coller ; permalien figé `v=` | J É | 5 | 2 | 5 | ✅ |
| API JSON (mêmes URL + `.json`) | É, agents IA | 4 | 2 | 4 | ✅ |
| Mode « j'ai lu ce chiffre » : grille de lectures, pas de verdict | J N | 5 | 3 | 5 | ✅ (+ dette 📥) |

### Lot 3 : signatures (ce qui fait la réputation)
| Fonction | Verdict |
|---|---|
| **Marche des niches fiscales** : coût cumulé, puis escalier vide des non chiffrées « coût inconnu, pas nul » | v1, données en base |
| **Mur des absences** : jeux × années × stades, chaque case vide cliquable vers son responsable | v1, données en base |
| **100 € de dépense publique** (parts publiées Eurostat, jamais « de vos impôts ») | v1, données en base |
| **30 ans fonction par fonction** : petits multiples COFOG, axe commun | v1, données en base |
| **Pente des départements** 2012 → dernière année | v2, après le déflateur |
| **Arbre budgétaire** en icicle, un arbre par type de budget | v2 |
| **Voté vs réalisé** du même exercice | v2, après PLRG 2024/2025 |

### Lot 4 : plus tard
Épingles et mode plateau, fils guidés, « estimez avant de voir », euros constants (après déflateur),
communes et intercommunalités, comparaisons européennes (même chargeur Eurostat), flux des nouveautés,
interprétation des phrases par LLM en secours (sortie limitée à des identifiants existants), iframe.

## 4. Les arbitrages tranchés

| Désaccord | Décision |
|---|---|
| Euros courants ou constants | **La valeur publiée d'abord** : % du PIB pour une série nationale > 10 ans, €/hab pour le local, M€ courants pour les missions. Mention « inflation non déduite » collée à la courbe ; euros constants (prix du PIB) à un geste, signalés « calcul du site », une fois le déflateur collecté. Jamais courants et constants sur un même graphique. |
| Un seul visuel par réponse | Un visuel = une question, un titre, une source, un tableau. Les petits multiples à axe commun comptent pour un. **Témoin obligatoire** dans 3 cas : deux lectures de périmètre, un ratio % du PIB (numérateur en M€ à côté), un total incomplet (la queue des non chiffrés). |
| La cote : mono sous chaque chiffre ? | Sous le chiffre-titre : cote **lisible** (« ↳ Eurostat · dépenses par fonction »), IBM Plex Mono 13 px à l'encre secondaire (contraste AA). Une seule cote par bloc ailleurs. Identifiants (jeu, ligne, sha256) dans le popover. |
| Roulement de compteur dans le hero | **Refusé** : il affiche des montants qui n'existent pas, et une capture peut les figer. Fondu enchaîné. |
| Fac-similé du PDF comme « preuve » | **Illustration**, légendée « document de référence ». La preuve est la ligne du CSV. Collé au chiffre seulement si un contrôle vérifie que valeur et page concordent. Le PDF doit être collecté comme une source. |
| Face-à-face du hero | **Même sujet des deux côtés**, jamais deux sujets tirés au sort. Exemple par défaut : coût chiffré des niches (« au moins … ») face au bloc hachuré des niches non chiffrées (le compte en texte courant, pas en chiffre vedette). |
| Hachure : partout ou seulement en contraste forcé | **Partout** (filet plein, 135°, pas de pointillé : le pointillé veut dire « prévision »). Classement : pastille hachurée + texte, jamais de barre courte. |
| Sélection dans un graphique | Le territoire choisi prend `--s1`, les autres `--s0` ; l'accent pétrole ne rentre jamais dans un tracé. |
| Paire divergente | Bleu ↔ orange (le rouge se lit « mauvais » et « politique »), milieu `--paper-2`, à valider au script. |
| Typographie des chiffres | Serif pour le chiffre vedette hors graphique ; IBM Plex Sans dans les tracés, axes, infobulles, tableaux. |
| Stades | Écrits en toutes lettres : « Projet (PLF) », « Voté (LFI) », « Réalisé (exécution) », « Comptes nationaux ». Dans les tracés : plein = réalisé, point creux = provisoire, pointillé = prévision. |
| Libellés de périmètre | S1311 = « administrations centrales (État et organismes rattachés) », jamais « l'État ». « La France » n'est pas un périmètre. |
| « Aides aux entreprises », « cadeaux aux riches » | « Pas de catégorie officielle unique » + lectures partielles nommées (dépenses fiscales par impôt…) + lacune. |

## 5. Architecture

```
/{lang}/                 Accueil : hero « la question et son trou »
/{lang}/r?…              Page-réponse (vues : montant, part, évolution, classement, carte, comparer)
/{lang}/territoire/{c}   Fiche entité (aussi /fonction, /mission, /niche) : la page-réponse par défaut d'une entité
/{lang}/lacunes          Ce qui manque + mur des absences
/{lang}/lexique          Définitions citées
/{lang}/methode          Sources, contrôles, formules des calculs du site
/{lang}/montant/{id}     La ligne d'origine (existe)
```
Les pages actuelles deviennent des phrases préréglées (redirections 301, liens partagés préservés).
Rendu serveur partout, SVG dessiné par le serveur (même SVG pour la page, l'image, l'aperçu de lien et les
tests), JS d'interaction ≤ 30 Ko, aucune bibliothèque de graphiques. Fragments servis en ≤ 150 ms,
estompage seulement au-delà.

**Divulgation en trois couches** : (1) la réponse tient dans le premier écran à 320 × 568 ; (2) la lecture
(visuel, notes, et maintenant) en un défilement ; (3) la preuve (tableau complet, ligne brute, sha256) en
un toucher.

## 6. Parcours concrets (corrigés par la critique croisée)

1. **Plateau TV, 10 s, une main** : « dette plus que éducation ». Le site propose deux lectures. Budget de
   l'État : programme « Charge de la dette et trésorerie de l'État » face à la mission « Enseignement
   scolaire », chacun seul (jamais de somme de missions). Toutes administrations : COFOG « opérations
   concernant la dette publique » face à « enseignement ». Panneaux séparés, citation copiée.
2. **Créatrice TikTok** : « occitanie » → fiche → €/hab → « parmi les régions » → image 9:16 avec source
   non amovible. Elle tente « à quoi elle dépense » : option barrée « non publié pour les régions » →
   deuxième vidéo, sur la lacune.
3. **Chercheuse** : `GF0702` → évolution 1995-2024 en % du PIB, provisoires marqués → compare
   Sécurité sociale et administrations locales en petits multiples (note : sous-secteurs non consolidés) →
   CSV long, permalien figé `v=`.
4. **Citoyen** : « ce que fait mon département de mes impôts 69 » → Rhône ou Métropole de Lyon → message
   « les comptes publiés ne relient pas un impôt à une dépense » → répartition par fonction et recettes →
   comparaison à sa région.
5. **Élue** : Dordogne → investissement €/hab → « + comparer » départements de Nouvelle-Aquitaine →
   classement + tuiles → export pour la séance.
6. **Économiste** : « niches IS » → classement, lacune bloquante en tête (non chiffrées comptées, jamais
   zéro) → marche des niches → CSV avec `statut=nc`.
7. **Viral** : colle « les niches fiscales coûtent 90 milliards » → grille : même périmètre / autre année /
   autre stade, avec les valeurs réelles ; aucun verdict.
8. **Question politique** : « cadeaux aux milliardaires » → « pas de catégorie officielle par niveau de
   fortune dans les sources » → lectures partielles nommées + lacune ; aucun mot ajouté.

## 7. Direction artistique retenue : « le Registre »

- **Idée** : une archive publique ouverte ; chaque chiffre est une pièce cotée.
- **Typographie** : Source Serif 4 (questions, chiffres vedettes), IBM Plex Sans (interface, graphiques,
  tableaux), IBM Plex Mono (la cote seulement). Marianne exclue (marque de l'État).
- **Couleur** : papier chaud, encre, une seule couleur d'action (pétrole). Aucune couleur qui juge. La
  rouille des lacunes disparaît (trop proche de l'orange des séries) : la lacune devient achromatique.
- **Matière** : filets fins, double filet sous les totaux, angles vifs, ombre réservée aux objets flottants.
- **Image** : documents officiels réels (pages de PDF budgétaires, légendées « document de référence »),
  orthophotos IGN sur les seules fiches territoire. Interdits : billets, pièces, tirelires, drapeaux,
  bleu-blanc-rouge, illustrations, images générées, texte sur photo, cartes 01/02/03, bandes de stats.
- **Signature** : la cote `↳` sous le chiffre, et la hachure à la place du chiffre absent.

## 8. Première proposition d'interface

Prototype navigable : **`/{lang}/explorer`** (n'écrase pas l'accueil actuel), données réelles uniquement.
Il réalise le hero et l'entrée dans le moteur :
- **Hero « la question et son trou »** : la phrase-requête en grande serif, deux emplacements (thème,
  périmètre), le chiffre réel et sa cote ; en face, à poids égal, la lacune du même sujet, hachurée, avec son
  responsable. Changer un emplacement change la réponse en fondu.
- **Recherche typée** : autocomplétion groupée par nature (fonction, mission, programme, niche, région,
  département, mot du lexique), chiffre dans la liste, clavier complet (`/`, ↑↓, Entrée, Échap), ARIA combobox.
- **Questions-amorces** : 5 lignes de texte, tirées d'un vivier à chaque chargement, chacune avec son vrai
  chiffre ou sa mention « non publié ».
- **Sommaire sous le pli** : les quatre portes en table des matières, puis « ce qui manque ».

Non encore réalisé (dépend des données ou du lot 1) : page-réponse `/r`, bande documentaire (PDF à
collecter), carte (contours à collecter), exports image.

**État du prototype (2026-10-27)** : `api/main.py` (section « explorer », route `/suggest`),
`templates/explorer.html`, `static/explorer.{css,js}`. Vérifié à 320 × 568 (chiffre dans le premier écran,
aucun défilement horizontal) et sur desktop, en clair et en sombre, FR et EN. Tests :
`test_explorer_reponse_sourcee_ou_lacune`, `test_suggestions_portent_leur_chiffre`. Au passage, correction
d'un défaut réel : la connexion SQLite partagée entre threads se corrompait dès deux requêtes simultanées
(page + suggestions) ; `queries.connect()` ouvre désormais une connexion par thread.
**Inspiration « Encre et économie » (maquette d’interface, données fictives)** : repris le hero (papier
quadrillé, titre en trois temps dont le dernier en italique, grande barre de recherche, « Essayer : »),
les rubans de sujets et l'index « cinq façons d'entrer ». Les rubans défilent, ce que la synthèse refusait :
ils sont gardés parce que chaque étiquette mène à une réponse réelle et que le défilement s'arrête au
survol, au focus, par un bouton (WCAG 2.2.2) et disparaît si l'on réduit les animations. La phrase-requête
et le face-à-face passent sous le hero (`#question`). Repérés pour la suite : le panneau d'exploration
(indicateurs, territoires, période en pastilles ; courbe/aires/barres ; exports CSV/JSON/SVG/PNG),
« Vérifier une affirmation » décomposée en indicateurs, période et sources, la carte en tuiles avec
classement synchronisé. Non repris : les onglets de mode au-dessus de la recherche et la variation
« +104 % depuis 2000 » sans mention « calcul du site ».
Limites connues : les lacunes et les noms d'entités restent en français dans la version anglaise ; le
fondu entre deux réponses repose sur les View Transitions (Chrome, Edge, Safari récents ; ailleurs,
chargement normal).

## 9. Vérification : chaque fonction répond-elle à un besoin réel ?

| Fonction | Besoin servi (profil) | Simplicité préservée ? |
|---|---|---|
| Phrase-requête | savoir de quelle dépense on parle (tous) | oui : un seul concept, lisible à voix haute |
| Chiffre dans l'autocomplétion | réponse en < 10 s (plateau, viral) | oui : zéro page chargée |
| Résolveur de périmètre | éviter la confusion État / APU (journalistes, citoyens) | apparaît seulement si le terme est ambigu |
| Options barrées | voir les limites avant de choisir (tous) ; principe des lacunes | oui : pas de page vide, pas de refus |
| Garde de comparabilité | ne pas fabriquer de fausse info (fact-check) | elle montre la comparaison au lieu de la bloquer |
| Hachure unique | « un trou n'est pas un zéro » (citoyens, économistes) | un seul signe pour tout le site |
| « Et maintenant ? » | passer d'une question à l'autre (tous) | 5 suggestions max |
| Export sourcé | faire voyager le chiffre sans perdre sa source (créateurs, journalistes) | source non amovible |
| API JSON | agents IA, datajournalistes | invisible pour les autres |
| Marche des niches, mur des absences | question « cadeaux », pouvoir citoyen | ce sont des réponses, pas des menus |
| Carte / tuiles | « trouver mon territoire », motif spatial | vue d'une réponse, jamais la réponse à un classement |

Fonctions écartées faute de besoin réel ou parce qu'elles trompent : voir § 1, dernier paragraphe.
Plafonds de simplicité : 5 emplacements, 4 éléments comparés, 5 suggestions, 3 notes, 1 visuel principal.

## 10. Sources repérées (vérifiées le 2026-10-27 par l'économiste ; ordre de travail : `docs/ROADMAP.md`)

1. Eurostat `gov_10dd_edpt1` : dette et déficit (question n° 1, absente aujourd'hui).
2. Eurostat `gov_10a_exp` tous pays de l'UE (même chargeur que l'actuel).
3. Dénominateurs : Eurostat `nama_10_gdp` (PIB, déflateur), `demo_pjan` (population).
4. Eurostat `gov_10a_main`, `gov_10a_taxag` : recettes, intérêts, prélèvements obligatoires.
5. OFGL communes, intercommunalités, ensembles intercommunaux.
6. PLRG 2024 et 2025 (data.economie.gouv.fr) : voté vs réalisé.
7. Situations mensuelles budgétaires de l'État.
8. Contours OFGL (`departements_formes_geo_svg`, `regions_formes_geo_svg`) ou IGN ADMIN EXPRESS ; COG INSEE
   et base des codes postaux.
9. DREES : protection sociale, aide sociale départementale.
10. OFGL : fiscalité locale (REI) et dotations.

Nouvelles lacunes à instruire : LFSS sans jeu open data structuré, dépense de l'État non territorialisée,
absence de série officielle des aides aux entreprises, trajectoires de prévision non publiées en données.
