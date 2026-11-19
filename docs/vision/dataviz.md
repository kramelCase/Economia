# Vision dataviz : formes, grammaire du comparateur, carte, lacunes, export, signatures

Auteur : spécialiste visualisation de données (journalisme de données, statistique publique).
Lu avant d'écrire : `BRIEF.md`, `docs/INVENTAIRE.md`, `db/schema.sql`, `static/charts.js`,
`templates/_macros.html`, `templates/territoires.html`, la section « Graphiques » de `static/style.css`, et la
méthode dataviz (`references/choosing-a-form.md`, `anti-patterns.md`, `interaction.md`,
`marks-and-anatomy.md`, `palette.md` ; le fichier `SKILL.md` n'existait pas à l'emplacement indiqué, seules
les références étaient présentes).

Aucun chiffre n'est inventé ici. Les seuils qui suivent (poids en Ko, nombre de séries) sont des **budgets
ou des règles de conception**, pas des mesures.

---

## 0. Ce qui existe, et ce que j'en garde

| Existant | Verdict | Pourquoi |
|---|---|---|
| Anneau ≤ 5 parts + « Autres » (slot 0, gris), légende = version lisible, couleur fixée par entité | **Garder**, restreindre à son seul usage : une part d'un tout, une entité, une date | La méthode l'autorise (part-à-tout d'un coup d'œil, ≤ 6 segments). Il trompe dès qu'on compare deux anneaux (`.duo`) : l'œil compare mal des angles. |
| Courbe SVG + tableau jumeau `<details class="twin">`, `null` = trou dans la ligne, mention « provisoire » | **Garder, c'est la colonne vertébrale** | Déjà juste sur l'essentiel : la ligne est coupée là où la donnée manque (pas d'interpolation), le tableau affiche « — ». |
| Classement en barres + repère de médiane « calculée par ce site » | **Garder** pour ≤ ~30 lignes ; au-delà, le compléter par une bande de points (beeswarm, §1.7) | 101 barres sur 320 px = un mur que personne ne lit. |
| Tableaux triables, filtres qui soumettent le formulaire, affichage précédent estompé pendant le rechargement | **Garder** | Conforme à la méthode (pas de squelette, pas de saut). |
| Palette catégorielle 5 slots validée + `--s0` « Autres », textes jamais dans la couleur d'une série | **Garder**, et **ajouter** une rampe séquentielle (bleue, 5 classes) et une paire divergente (§3.3) | Nécessaires pour la carte et l'écart à la médiane. |
| Graphiques dessinés en JS à partir du HTML serveur, aucun chiffre calculé côté client | **Garder le principe**, mais **déplacer le dessin SVG côté serveur** (§7) | C'est la clé de l'export d'image honnête, du rendu sans JS et de la performance. |

---

## 1. La bonne forme pour chaque type de question

Règle d'entrée (méthode « Is it even a chart? ») : **une seule valeur → un chiffre**, pas un graphique. Un
stat tile (valeur + unité + stade + badge « source ») vaut mieux qu'une barre seule ou un anneau à 2 parts.

### 1.1 Part d'un tout (« où vont 100 € de dépense publique ? »)
- **Meilleure forme** : barre empilée horizontale unique à 100 % (ou anneau existant) avec ≤ 5 parts + « Autres » dépliable, parts **publiées** (`PC_TOT` COFOG) affichées telles quelles, parts calculées signalées « calculée par ce site ».
- **Alternative** : barres horizontales triées (lecture exacte des écarts, libellés longs COFOG lisibles sur mobile) ; grille de 100 carrés (« 100 € ») pour l'édition grand public (§6.1).
- **Comparer deux compositions** (État vs collectivités, 2 départements) : **deux barres 100 % superposées**, mêmes couleurs par poste, ou un **dot plot des parts** (une ligne par poste, un point par entité). **Proscrire deux anneaux côte à côte** (`.duo` actuel) : comparaison d'angles.
- **Proscrire** : camembert 3D, anneau > 6 parts, anneau dont les parts ne somment pas à un total de contrôle publié (ex. additionner S1311 + S1313 + S1314 : l'inventaire montre que cela ne donne pas S13 — écart de consolidation).

### 1.2 Évolution d'une grandeur
- **Meilleure forme** : courbe (2 px, point final, valeur en bout de ligne), année en abscisse à pas régulier.
- **Alternatives** : colonnes si ≤ ~8 années et que chaque année est un « exercice » discret qu'on veut comparer ; sparkline dans un stat tile pour le contexte.
- **Règles** : axe à zéro pour un niveau en € (le drapeau `zero` existe dans `charts.js`, il doit devenir le défaut pour les niveaux) ; axe libre autorisé pour un indice ou un ratio, avec la ligne de référence (100, 0 ou médiane) tracée.
- **Proscrire** : double axe Y (méthode : invente une corrélation) → indice base 100 sur un seul axe, ou petits multiples ; aire empilée pour des agrégats OFGL **emboîtés** (« Dépenses totales » contient « Dépenses de fonctionnement » : les empiler double-compte).

### 1.3 Comparaison de territoires (2 à 5)
- **Meilleure forme** : **dot plot de Cleveland** — une ligne par indicateur (ou par territoire), un point par territoire, même échelle, la médiane du niveau en repère gris. Lit des écarts fins sans l'effet « barre pleine ».
- **Alternatives** : barres groupées (≤ 3 territoires × ≤ 5 indicateurs) ; courbes superposées si la question est temporelle (§2).
- **Proscrire** : radar/toile d'araignée (aires sans signification, ordre des axes arbitraire qui change l'impression) ; jauges ; barres en € totaux pour comparer un petit et un grand département (on compare des populations, pas des politiques) → €/hab publié par l'OFGL.

### 1.4 Classement (« quels départements dépensent le plus par habitant ? »)
- **Meilleure forme** : liste en barres triée (existant) avec valeur au bout de chaque barre, médiane en repère, recherche, et **le territoire de l'utilisateur toujours visible** (épinglé en tête ou surligné).
- **Alternative pour 101 entités** : bande de points (beeswarm, §1.7) au-dessus, liste en dessous, synchronisées.
- **Garde-fou** : un rang sans valeur exagère des écarts minuscules (le 40ᵉ et le 60ᵉ peuvent être quasi identiques). Toujours afficher la valeur ; ne jamais titrer « 12ᵉ sur 101 » seul.
- **Proscrire** : podium/médailles, couleur verte/rouge sur le haut/bas du classement (dépenser plus n'est ni bien ni mal : neutralité du brief).

### 1.5 Composition qui change dans le temps (« la part de la santé a-t-elle grossi depuis 1995 ? »)
- **Meilleure forme** : **petits multiples** — une petite courbe par fonction COFOG (10 divisions), **même axe Y partagé** (en % du total ou % du PIB, publiés par Eurostat), ordre par taille. Chaque panneau lisible seul ; la comparaison reste juste.
- **Alternatives** : barres 100 % à 3–4 dates choisies (1995 / 2008 / dernière année définitive) ; courbes d'une seule fonction en emphase, les autres en gris.
- **Quand l'aire empilée est acceptable** : ≤ 4 couches d'une nomenclature qui somme réellement (contrôle passé dans l'inventaire : somme des 10 fonctions = TOTAL S13 à l'arrondi près), et seulement pour la couche du bas et le total ; les couches médianes sont illisibles (base qui ondule).
- **Proscrire** : streamgraph (base centrée qui ondule, aucune lecture possible), aire empilée à 10 couches, petits multiples à axes Y indépendants **sans le dire** (si un panneau a son propre axe, il porte l'étiquette « échelle propre »).

### 1.6 Prévision vs exécution (PLF / LFI / exécution)
- **Le piège de fond** : le budget vert PLF 2026 donne *exécution 2024*, *LFI 2025*, *PLF 2026* — **trois stades ET trois années différentes**. Les mettre sur une courbe fabrique une « évolution » qui mélange natures de montant. La comparaison prévision ↔ réalisé honnête exige **le même exercice** à deux stades (LFI 2024 vs exécution 2024), ce qui n'est pas en base.
- **Meilleure forme (ce qu'on a)** : **trois points par mission sur une même ligne** (dot plot), chaque point étiqueté par stade et année (« exéc. 2024 », « LFI 2025 », « PLF 2026 »), forme du point = stade (plein = réalisé, creux = voté, creux pointillé = proposé). Pas de segment reliant les points (un segment suggère une trajectoire).
- **Meilleure forme (à terme)** : **dumbbell** voté → réalisé pour un même exercice, écart signé en texte. Données à collecter : le rapport « budget vert » annexé au PLF 2025 (Direction du Budget), qui devrait contenir LFI 2024 et exécution 2023 — *à vérifier sur data.economie.gouv.fr* ; à défaut, les rapports annuels de performance (RAP, exécution) et les LFI par destination, dont l'absence est déjà une lacune documentée.
- **Pointillé** : réservé à un **montant prévisionnel** (PLF, LFI, coût prévu d'une dépense fiscale). Une donnée **provisoire** (drapeau `p` d'Eurostat 2023-2024) n'est pas une prévision : trait plein, point final creux, mention « provisoire ».
- **Proscrire** : barres empilées mêlant stades ; total « 2024-2026 » additionnant exécution + LFI + PLF.

### 1.7 Écart à la médiane (« mon département est-il atypique ? »)
- **Meilleure forme** : **beeswarm / bande de points** horizontale — les 101 départements (ou 17 régions) en points sur l'axe €/hab, médiane en trait vertical (« calculée par ce site sur N collectivités »), le territoire choisi en couleur d'accent et étiqueté, les autres en gris (emphase). Montre à la fois la position, la dispersion et les valeurs extrêmes. Disposition calculée côté serveur (déterministe), points r ≥ 4 avec zone de survol ≥ 24 px (couche « point le plus proche »).
- **Alternative** : barres divergentes partant de la médiane (écart signé), triées ; utile pour 17 régions, trop long pour 101.
- **Garde-fous** : l'écart s'exprime dans l'unité publiée (« +[x] €/hab au-dessus de la médiane »), jamais en % d'écart sans le dire ; un petit dénominateur (département peu peuplé) produit mécaniquement des €/hab extrêmes → afficher la population à côté dans l'infobulle et le tableau. Paris, la Métropole de Lyon et la Collectivité européenne d'Alsace ont des compétences mêlées : les signaler par une note sur leur point plutôt que les exclure en silence.
- **Proscrire** : z-scores, « indice de performance », couleurs bien/mal.

### 1.8 Variation décomposée (« pourquoi le budget passe de LFI 2025 à PLF 2026 ? »)
- **Meilleure forme** : **waterfall (cascade)** : barre de départ (total LFI 2025), une marche par mission (hausse / baisse, triées par taille absolue, les petites regroupées en « autres missions »), barre d'arrivée (total PLF 2026). Couleurs : deux teintes neutres opposées (hausse / baisse), **pas** vert/rouge.
- **Conditions d'honnêteté** : même source, même périmètre, la somme des marches = l'écart des totaux publiés (contrôle de bouclage affiché ; sinon pas de waterfall). Lignes techniques (MP/MT, FDC/ADP, T2_CAS) en marche à part étiquetée « mesures de périmètre / techniques » : c'est souvent là que se cache une « hausse » qui n'en est pas une.
- **Alternative** : barres divergentes des contributions, triées (plus robuste sur mobile que la cascade, qui exige une longue largeur).
- **Proscrire** : waterfall entre stades d'exercices différents présenté comme « évolution » ; décomposition prix/volume **par fonction** (aucun prix par fonction : méthode inventée). Sur un **total**, une décomposition prix / population / volume avec déflateur et population nommés est acceptable (révisé après critique croisée).

### 1.9 Lacunes (« qu'est-ce qu'on ne sait pas ? »)
Voir §4 pour l'encodage dans chaque graphique. Comme sujet à part entière :
- **Meilleure forme** : **grille de couverture** (« le mur des absences ») — lignes = jeux ou indicateurs, colonnes = exercices / stades ; case pleine = publié (lien source), case vide encadrée = non publié (lien vers la lacune et son **responsable**), case marquée « nc » = non chiffré, « ε » = sous le seuil. C'est une heatmap qualitative à 3–4 états, avec légende textuelle.
- **Proscrire** : un pourcentage de « complétude » unique (mélange des natures d'absence, chiffre fabriqué).

### 1.10 Géographie
Voir §3. En résumé : **une carte répond à « où ? », pas à « combien ? » ni « qui est premier ? »**. Si la question est un classement ou une comparaison de deux territoires, la carte est la mauvaise forme.

### 1.11 Flux « d'où vient / où va l'argent »
- **Sankey : à proscrire avec les données actuelles.** Un Sankey affirme une **conservation** (ce qui entre = ce qui sort) et des **liens observés**. Or : (a) les recettes ne sont pas collectées ; (b) les sous-secteurs COFOG ne sont pas consolidés (S1311 + S1313 + S1314 ≠ S13) : un Sankey État → collectivités → fonctions double-compterait les transferts entre administrations ; (c) relier un impôt à une dépense est une affectation inventée (le budget de l'État obéit à l'universalité : pas d'affectation recette → dépense, sauf exceptions comme les taxes affectées, qui sont en base).
- **Ce qui est honnête aujourd'hui** : un **arbre** (mission → programme → action → sous-action) dessiné en **icicle / barres imbriquées**, qui n'est pas un flux mais une hiérarchie qui somme. Séparément pour chaque type de budget (BG, CAS, CCF, BA) : l'inventaire précise que **ces montants ne s'additionnent pas**.
- **Sankey acceptable un jour** si une source publie la matrice de flux elle-même : par exemple les transferts entre sous-secteurs d'administrations publiques dans les comptes nationaux de l'INSEE (opérations de transferts courants/en capital entre APU — *tableau exact à identifier avec l'économiste*), ou un tableau officiel « recettes → affectations » pour les taxes affectées. On dessine alors **les flux publiés**, avec le lien de chaque ruban vers sa ligne.
- **Marimekko (mosaïque)** : tentant pour « poids de chaque mission × répartition de sa cotation environnementale ». Il trompe parce que l'œil lit des **aires** (largeur × hauteur) qu'il évalue mal, et que les colonnes étroites deviennent illisibles sur mobile. Préférer des barres horizontales 100 % triées par taille, avec le montant de la mission en texte.

### 1.12 Niches fiscales très inégales en taille
Les coûts estimés s'étalent sur plusieurs ordres de grandeur, avec 63 « nc » et 42 « ε » en prévision 2026 (inventaire).
- **Meilleure forme** : **courbe de concentration cumulée** (« la marche des niches », §6.3) : dépenses triées de la plus coûteuse à la moins coûteuse en abscisse (rang), coût cumulé en ordonnée (en Md€ publiés). On lit directement « les [n] premières représentent [x] du total chiffré » — ratio **calculé par ce site**, signalé. Les « nc » sont ajoutées **après** la courbe comme une file de marches de hauteur inconnue (zone vide encadrée, étiquette « 63 dépenses non chiffrées : coût inconnu, pas nul »), jamais comme des zéros.
- **Alternatives** : liste en barres des 20 premières + « [n] autres » dépliable ; **treemap** pour « montrer l'écrasement » (les aires très inégales sont justement le message) — acceptable seulement si chaque rectangle cliquable mène à sa ligne et si les « nc » ont une zone grise hachurée de taille **non proportionnelle** explicitement légendée « taille inconnue ».
- **Proscrire** : échelle logarithmique pour le grand public (elle écrase visuellement l'inégalité qu'on veut montrer et se lit comme linéaire) — tolérée seulement dans une vue « expert » avec mention « échelle logarithmique » dans le titre de l'axe ; bulles proportionnelles (aires mal lues, recouvrements) ; un anneau des 483 dépenses.

### 1.13 Unités : « par habitant » vs « en € »
| Question | Unité juste | Pourquoi |
|---|---|---|
| Poids d'une collectivité dans la dépense publique, contribution à un total | € (ou M€) | On parle de masses ; sur une carte, c'est une carte de population. |
| Comparer des territoires, carte, classement, médiane | **€/hab publié** (OFGL) | Neutralise la taille ; seule unité admise sur une choroplèthe. |
| Comparer dans le temps long (1995-2024) ou entre pays | **% du PIB** (Eurostat) ou % du total | Neutralise l'inflation et la croissance ; publié, pas calculé. |
| Évolution en € sur 10 ans et plus | € constants **en option**, défaut € courants | Le déflateur n'est pas en base (§2.4). |

Le **€/hab de l'OFGL** est publié : on l'affiche tel quel. Si le site calcule un €/hab lui-même (ex. dépense APU / population), il le dit et cite la population utilisée (source INSEE, millésime) — *l'économiste doit fixer laquelle : population municipale, totale, ou DGF, qui ne donnent pas le même résultat*.

---

## 2. Grammaire unifiée du « comparateur universel »

Une vue = **(question) × (entités 1..N) × (période 1..N) × (unité) × (stade) × (source)**. La forme se
déduit de ces paramètres ; l'utilisateur ne choisit jamais « un type de graphique ».

### 2.1 La règle d'unicité (non négociable)
**Un graphique = une source × un stade × une unité.** Si la sélection mélange (ex. dépenses des
départements OFGL et sous-secteur S1313 COFOG), le comparateur bascule en **panneaux juxtaposés**, chacun avec
son titre, son unité, son périmètre et sa source, **jamais sur le même axe**. Le bandeau de la vue dit
pourquoi : « Ces deux séries ne mesurent pas le même périmètre : affichées séparément. »

### 2.2 Table de bascule de forme
| Entités \ Années | 1 année | 2 années | ≥ 3 années |
|---|---|---|---|
| **1** | chiffre (stat tile) + position dans la bande de points de ses pairs | chiffre + écart signé (« de [a] à [b] ») | courbe + bande grise min–max ou médiane de ses pairs |
| **2–5** | dot plot (une ligne par indicateur) ou barres groupées | **slope chart** (deux colonnes d'années, une pente par entité) ou dumbbell | courbes superposées, couleurs par entité, étiquettes en bout de ligne |
| **6–20** | barres triées + médiane | slope chart en **emphase** (choisies en couleur, autres en gris) | courbes en emphase (spaghetti gris + sélection colorée) ou petits multiples |
| **Tous (17 / 101)** | bande de points + liste, ou carte (si €/hab) | slope chart des 101 en gris, sélection colorée | petits multiples **par sélection** seulement ; sinon courbe médiane + interdécile *calculés par ce site* |

Plafonds couleur (méthode) : ≤ 5 séries colorées (5 slots existants), **≤ 3** pour les formes « toutes paires »
(nuage, carte, petits multiples côte à côte). Au-delà : emphase ou facettes, jamais une 6ᵉ teinte.

**Couleur par entité, stable** : un territoire garde son slot quand on en retire un autre (anti-pattern
« recolor-on-filter »). Impossible de fixer un slot pour 118 collectivités : le slot est attribué **dans
l'ordre de sélection** et **inscrit dans l'URL** (`t=DEP-69:1,DEP-13:2`), donc stable au partage.

### 2.3 Axes et échelles
- **Niveaux en € ou €/hab** : axe à zéro par défaut (barres toujours). Un bouton « zoomer sur la variation » lève le zéro, et l'axe porte alors une brisure visible + la mention « axe ne partant pas de zéro ».
- **Indice base 100** : obligatoire dès qu'on compare des **évolutions** d'entités de tailles différentes en €. L'année de base est **dans le titre de l'axe** (« base 100 en 2012 ») et la ligne 100 tracée. Interdit de prendre pour base une année **provisoire** ou **de rupture** (le sélecteur les grise avec la raison). L'indice est un calcul du site : badge « calculé par ce site ».
- **% du PIB** : disponible **seulement là où la source le publie** (COFOG national). Pour une région, le bouton est **visible mais désactivé** avec la raison (« PIB régional non collecté — source : comptes régionaux de l'INSEE »). Cacher une option rend la lacune invisible ; la désactiver avec sa raison respecte le principe 4.
- **Échelle commune** dans les petits multiples par défaut ; « échelle propre » est une option explicite, signalée sur chaque panneau.
- **Jamais** de double axe, jamais d'échelle log par défaut, jamais de lissage (moyennes mobiles) : ce serait une méthode.

### 2.4 Euros courants vs constants
- Défaut : **euros courants** (c'est ce que publient les sources ; chaque point remonte à sa ligne).
- Option « euros constants [année] » : division par un déflateur **cité** — candidats : indice des prix à la consommation (INSEE) ou déflateur du PIB (INSEE, comptes nationaux) ; *le choix revient à l'économiste* (ils ne racontent pas la même chose). Non collecté à ce jour.
- Affichage : l'unité change partout (« M€ constants 2024 »), badge « calculé par ce site », l'infobulle montre les deux valeurs (« [courant] → [constant] »), le tableau jumeau garde la colonne en euros courants avec la source de la ligne et ajoute la colonne déflateur avec **sa** source. Pour 1995-2024 national, suggérer d'abord « % du PIB » (publié) plutôt que constant (calculé).

### 2.5 Ruptures de série
- Marque : **filet vertical fin plein** à l'année de rupture, étiquette courte au sommet (« M52 → M57 », « fusion des régions », « création de la CeA ») cliquable vers l'explication. La ligne **reste continue** si la source garantit la continuité ; elle est **coupée** si le périmètre change (l'entité avant n'est pas l'entité après).
- Ruptures connues à documenter (*liste à valider par l'économiste*) : passage M52 → M57 dans la présentation fonctionnelle des départements (signalé par l'inventaire) ; réforme territoriale de 2016 (13 régions métropolitaines) — vérifier si l'OFGL reconstitue 2012-2015 au nouveau périmètre ; Métropole de Lyon (2015) ; collectivités territoriales uniques de Guyane et Martinique (2016), de Corse (2018) ; Collectivité européenne d'Alsace (2021) ; transferts de compétences (loi NOTRe, transports aux régions). **On ne fusionne jamais deux séries soi-même** (ex. Bas-Rhin + Haut-Rhin avant 2021) : ce serait additionner hors source.
- Une rupture interdit l'indice base 100 enjambant la rupture sans avertissement.

### 2.6 Valeurs provisoires et prévisionnelles
| Statut | Marque | Texte |
|---|---|---|
| Définitif | trait plein, point plein | — |
| **Provisoire** (`provisoire = 1`) | trait plein, **point creux**, segment final en teinte un cran plus claire | « p » au point + « provisoire » en infobulle et tableau (macro existante) |
| **Prévision** (stade PLF/LFI, coût prévu) | **pointillé**, point creux | stade et année (« PLF 2026 ») |
| **Absent** | rien (trou) | voir §4 |

Le pointillé n'est **jamais** décoratif ni utilisé pour une grille (la méthode interdit les grilles en
tirets précisément parce que le tiret signifie « projection »).

### 2.7 Ce que chaque vue affiche toujours (anatomie fixe)
1. **Titre-question** (« Combien les départements dépensent-ils par habitant pour le personnel ? »), jamais un titre-conclusion éditorialisé.
2. **Sous-titre technique** : périmètre · stade · unité · années · prix courants/constants.
3. Le graphique (légende si ≥ 2 séries, étiquettes directes sélectives).
4. **Pied** : « Source : [éditeur], [jeu], collecté le [date] » + nombre de valeurs absentes + badges « calculé par ce site » éventuels + lien « tableau / CSV / partager ».
5. Tableau jumeau (déjà le cas) — l'équivalent accessible.

---

## 3. La carte

### 3.1 Faut-il une carte ?
**Oui, mais comme porte d'entrée et vue de contexte, pas comme graphique principal.** Elle sert trois
besoins réels : (a) « trouver mon territoire » sans connaître son nom officiel ou son code ; (b) voir un
**motif spatial** (gradient nord/sud, littoral, couronnes) qu'aucun classement ne montre ; (c) la
reconnaissance immédiate qui donne envie d'explorer (le « hero » du brief). Elle ne sert **pas** à comparer
deux valeurs précises (une liste ou un dot plot le fait mieux).

### 3.2 Les pièges de la choroplèthe (et les parades)
| Piège | Parade |
|---|---|
| **Biais de surface** : les grands départements peu peuplés dominent visuellement, l'Île-de-France est un point | Proposer en vis-à-vis la **grille de tuiles** (§3.4) où chaque département a la même surface ; le bouton « carte / tuiles » est au même niveau que le choix d'indicateur |
| **Montants en € totaux** : c'est une carte de la population | **Normalisation obligatoire** : seules les unités intensives (€/hab, %) sont proposées sur la carte. Le bouton « € » est désactivé en mode carte, avec la raison |
| **Classes qui changent d'une année à l'autre** : la couleur bouge sans que la valeur bouge | **Seuils fixes** sur la période affichée (calculés sur l'ensemble des années), pas des quantiles annuels |
| Quantiles vs seuils « ronds » | Par défaut **5 classes de quantiles** (20 % des territoires chacune, lecture « parmi les plus élevés ») sur toute la période ; option « seuils réguliers ». La légende affiche les bornes en €/hab **et** le nombre de territoires par classe |
| Rampe arc-en-ciel | **Une teinte, clair → foncé** (rampe bleue de la méthode). Ne jamais réutiliser une couleur catégorielle |
| L'outre-mer oublié ou rapetissé | Encarts DROM **de même taille que les tuiles métropolitaines**, toujours présents, jamais « hors cadre » |
| Petites populations → valeurs extrêmes | Population dans l'infobulle et la liste ; note de méthode sur la volatilité des petits dénominateurs |

### 3.3 Palettes à ajouter (tokens dans `:root`, clair et sombre)
- **Séquentielle** (carte, heatmap de couverture) : 5 crans de la rampe bleue de la méthode (de « près de zéro » qui se fond dans le papier à foncé) ; à re-valider avec `scripts/validate_palette.js` contre **le papier crème du site** (les surfaces de référence de la méthode ne sont pas celles du site).
- **Divergente** (écart à la médiane) : la méthode documente bleu ↔ rouge avec milieu gris. **Je recommande bleu ↔ orange** (aussi chaud/froid, donc lisible comme opposés) : le rouge se lit « mauvais » et le couple bleu/rouge a une connotation politique droite/gauche en France — incompatible avec la neutralité du brief. À valider au validateur.
- **« Pas de donnée »** : hachure à l'encre à 135° (signe unique de l'absence, aligné sur la DA, voir `critique-dataviz.md` (d)2), filet plein, légende « non publié → voir la lacune ». Marque sémantique, pas décorative.

### 3.4 Alternatives à la choroplèthe géographique
- **Grille de tuiles carrées des départements** (une case par département, disposée pour rappeler la géographie) : surface égale, étiquette lisible (code ou nom court) dans chaque case, parfaite à 320 px, tactile (cases ≥ 24 px). **C'est ma recommandation par défaut sur mobile**, la carte géographique par défaut sur desktop. Disposition à dessiner une fois (fichier versionné dans le dépôt, ce n'est pas une donnée mais une mise en page — le dire dans la méthode). Carrés plutôt qu'hexagones : alignement plus simple, libellés plus lisibles ; les hexagones « font » plus France mais déforment autant.
- **Grille des 17 régions** : la carte géographique suffit (peu d'entités, surfaces moins disproportionnées) ; tuiles en option.
- **Cartogramme continu** (surfaces déformées par la population) : à **proscrire** en vue principale — formes méconnaissables, et il faut une population sourcée par année ; tolérable en « signature » ponctuelle.
- **Symboles proportionnels** (cercles) : la bonne forme **pour des € totaux** sur fond de carte (là où la choroplèthe est interdite) ; aires mal lues → valeur en infobulle et liste.

### 3.5 Interaction « store locator »
- **Liste synchronisée** à côté de la carte (en dessous sur mobile) : triée par valeur, recherche par nom, **code postal ou numéro de département** ; survol/focus d'un élément de liste ↔ surlignage de la tuile, et inversement ; tap sur mobile = sélection (pas de survol au doigt), second tap ou bouton « ouvrir » = page du territoire.
- **« Mon territoire »** sans géolocalisation (respect de la vie privée et pas de demande d'autorisation) : saisie du code postal → commune → département/région via le **Code officiel géographique (INSEE)** et la **base officielle des codes postaux (La Poste, sur data.gouv.fr)**. La géolocalisation du navigateur, si proposée, reste un bouton explicite et la position n'est jamais envoyée au serveur (résolution locale sur les contours).
- **Pas de fond de carte tuilé** (Leaflet/MapLibre + tuiles OSM/IGN) : on n'a pas besoin de routes ni de zoom à la rue ; cela coûterait du poids, des requêtes tierces et un style générique. La carte est un **SVG** de contours.
- Clavier : chaque tuile/contour est focusable (ordre = liste triée par nom), Entrée = ouvrir.

### 3.6 Données de géométrie
- **Source** : **IGN, ADMIN EXPRESS** — prendre la déclinaison **« COG CARTO »** (contours généralisés pour la cartographie, alignés sur le millésime du Code officiel géographique), couches DEPARTEMENT et REGION, **France entière avec DROM** (l'IGN fournit des emprises séparées par territoire ; vérifier la variante avec DROM rapprochés). Diffusion sur geoservices.ign.fr et data.gouv.fr, **Licence Ouverte Etalab 2.0** (*à confirmer au moment de la collecte, comme toute source : URL exacte, sha256, millésime dans `sources.yaml`*).
- **Traitement** (étape de build, pas au runtime) : reprojection (Lambert-93 pour la métropole, projection adaptée par encart DROM), **simplification** (mapshaper, en conservant la topologie pour éviter les trous entre voisins), puis **pré-calcul des chemins SVG** côté serveur. Le navigateur reçoit des `<path d>` prêts, sans bibliothèque de projection.
- **Jointure** par code INSEE (`entite.code_insee`) ; contrôler que chaque entité OFGL a un contour et inversement (contrôle affiché sur la page Méthode, comme les autres). Les entités à statut particulier (Métropole de Lyon vs Rhône, CeA vs Bas-Rhin/Haut-Rhin, Paris) exigent un **découpage cohérent avec l'OFGL** : la Métropole de Lyon n'est pas un département dans ADMIN EXPRESS — *à résoudre explicitement* (contour communal agrégé depuis ADMIN EXPRESS communes, ce qui est une opération géométrique documentée, pas comptable).
- **Poids** : budget cible ≤ 80 Ko gzip pour départements + régions simplifiés, à **mesurer** après simplification (pas une valeur connue) ; les tuiles carrées pèsent quasiment rien. Chargement **différé** (la carte n'est demandée qu'à l'ouverture de la vue), mise en cache longue (le millésime est dans le nom du fichier).

---

## 4. Montrer les lacunes et la provenance sans surcharger

### 4.1 Absence ≠ zéro, dans chaque forme
| Forme | Valeur absente (`lacune`, `nc`, non publié) | Sous le seuil (`ε`) |
|---|---|---|
| Courbe | **trou** dans la ligne (déjà fait) ; si le trou est en fin de série, petite étiquette « [année] : non publié » en bout | point creux sur l'axe zéro **interdit** ; étiquette « < 0,5 M€ » |
| Barres / classement | ligne présente à son rang alphabétique ou en fin, **sans barre**, texte « non chiffré — [responsable] » cliquable | barre minimale non proportionnelle **interdite** ; texte « < 0,5 M€ » |
| Anneau / barre 100 % | les absents ne sont **pas** dans le total ; note sous la figure « [n] postes non chiffrés exclus du total » avec lien | idem |
| Carte / tuiles | tuile hachurée à l'encre + filet plein, listée sous la carte | — |
| Waterfall | marche « non chiffré » en encadré vide, hors bouclage | — |
| Beeswarm | absents listés sous la bande (« non publiés : [noms] ») | — |
| Tableau jumeau | « — » + raison (`non chiffré`, `non publié`, `ε`) + lien lacune | « ε » |

Le **compteur d'absences** fait partie de l'anatomie fixe (§2.7) : « 3 valeurs non publiées sur 42 ».
Une absence ne disparaît jamais en silence, y compris dans un export.

### 4.2 Provenance de chaque marque
- **Clic/tap sur une marque → sa source.** Déjà en place (`/montant/{id}` pour un montant unique, `/provenance?ids=` pour une somme). À généraliser à toutes les formes : chaque `<path>`/point porte son `href`.
- Sur mobile : **premier tap = infobulle épinglée** (valeur, libellé, stade, « source › »), second tap sur « source › » = navigation. Ne jamais naviguer au premier tap (frustrant, le lecteur voulait lire la valeur).
- **Hiérarchie de la mention** (pour ne pas surcharger) : (1) dans le graphique, *rien* de plus que les marques ; (2) dans l'infobulle et le tableau, le lien par valeur ; (3) au pied, **une ligne de source par fichier** (en pratique 1 ou 2 fichiers par vue). Pas d'icône par point.
- **Calculs du site** (parts, médianes, indices, euros constants, cumul) : badge textuel « calculé par ce site » une fois au pied et sur la valeur concernée dans l'infobulle, avec lien vers la formule (page Méthode). Distinguer visuellement une **part publiée** (`PC_TOT` Eurostat, lien vers sa ligne) d'une part calculée (déjà fait dans la légende de l'anneau : à conserver partout).

---

## 5. Export et partage

### 5.1 Image d'un graphique
- **Contenu non amputable** (dessiné dans l'image, pas en légende HTML) : titre-question, sous-titre technique (périmètre · stade · unité · années · prix), graphique, **compteur d'absences**, mentions « provisoire » / « prévision » / « calculé par ce site », ligne de source (éditeur, jeu, date de collecte), **date d'export**, **lien permanent court** (et QR facultatif sur le format vertical), nom du site. La licence des données (Licence Ouverte) en petit.
- **Formats** : 1200×1200 (carré), 1080×1350 (4:5 portrait, fils d'actualité), 1080×1920 (9:16, stories : graphique en haut, chiffre clé et source en bas, zone sûre en haut et en bas), 1200×630 (aperçu de lien, OpenGraph). PNG pour les réseaux ; **SVG** pour journalistes et chercheurs (retouchable, vectoriel).
- **Mise en page par format, pas par recadrage** : le serveur recompose (moins de graduations, étiquettes directes repositionnées, légende sous le graphique en vertical). Un recadrage d'écran perd la source : interdit.
- **Génération** : côté serveur, à partir du **même SVG** que la page (§7), rasterisé (par exemple `resvg` ou `cairosvg` — à départager sur la fidélité du rendu des polices), polices Source Serif 4 et IBM Plex Sans **embarquées** (licence OFL, redistribution autorisée). Mise en cache par clé d'état (URL) + millésime de données.
- L'image d'aperçu OpenGraph de chaque permalien **est** cet export 1200×630 : un lien partagé sur un réseau affiche le graphique avec sa source.

### 5.2 CSV de la série
- Format **long (tidy)**, une ligne par valeur : `entite_code, entite_nom, indicateur_code, indicateur_libelle, exercice, stade, mesure, unite, valeur, provisoire, statut_absence, calcule_par_le_site, formule, source_editeur, source_jeu, fichier_url, fichier_sha256, ligne_source, lien_permanent`. Les absences sont des **lignes** avec `valeur` vide et `statut_absence` renseigné (jamais 0).
- Deux variantes : CSV standard (UTF-8, virgule, point décimal) et « CSV pour Excel français » (point-virgule, virgule décimale, UTF-8 avec BOM). En-tête de commentaire évité (casse les outils) : métadonnées dans un fichier `README` joint si ZIP, ou colonnes ci-dessus.
- Les valeurs **calculées** sont exportées à côté des valeurs sources, pas à leur place.

### 5.3 Intégration (embed)
- `<iframe src="/embed/…">` : même SVG, même pied de source **non désactivable**, lien vers la vue complète. Hauteur adaptative (message `postMessage` de taille), aucun cookie, aucun traceur.
- **Figé ou vivant ?** Par défaut **figé au millésime** (`v=2026-10-26` dans l'URL : les données révisées ne changent pas un article déjà publié) ; option « toujours la dernière version » avec mention « mis à jour le [date] » dans l'image. Quand une version figée est obsolète (révision INSEE des provisoires), l'embed affiche un bandeau discret « données révisées depuis — voir la version à jour ».
- Accessibilité de l'embed : le tableau jumeau reste accessible dans l'iframe.

### 5.4 Ce qui rend l'export honnête hors contexte (liste de contrôle)
1. Le titre ne conclut pas ; il pose la question et le périmètre.
2. L'unité et le stade sont lisibles sans légende externe.
3. L'axe des niveaux part de zéro, ou la brisure est dessinée et écrite.
4. Les absences sont comptées et visibles ; les provisoires et prévisions marqués.
5. Les calculs du site sont nommés.
6. La source et la date de collecte sont dans les pixels.
7. Le lien permanent reconstruit **exactement** la vue (état complet dans l'URL : entités + slots, indicateur, unité, années, base, prix, stade, millésime).
8. Un export d'une vue qui mélangerait sources ou stades est impossible (la vue elle-même l'est, §2.1).

---

## 6. Visualisations « signature » — avis franc

### 6.1 « Une année de dépense publique en 100 € » — **utile, à faire en premier**
Grille de 100 carrés (10×10) ou barre de 100 pièces, une couleur par fonction COFOG (≤ 5 + « Autres » dépliable, ou emphase d'une fonction à la fois), à partir des **parts publiées** (`PC_TOT`, S13, dernière année définitive, provisoire signalé). Pour qui : le citoyen, les réseaux sociaux. Garde-fous : l'arrondi à l'euro entier est un **calcul du site** (méthode du plus fort reste, dite et sourcée) ; les fonctions sous 0,5 € n'ont pas de carré mais restent listées avec leur part exacte ; titre « Sur 100 € de dépense publique (toutes administrations) en [année] » — **pas** « sur 100 € de vos impôts » (dépense ≠ recette ; le déficit existe). Variante par département (fonctions OFGL, budget principal) seulement si la présentation par budget le permet sans double compte.

### 6.2 « La journée de l'impôt » (jour de libération fiscale) — **gadget trompeur, à refuser**
Convertit un ratio (prélèvements / revenu) en date du calendrier : le dénominateur est un choix éditorial, la « date » suggère que le contribuable « travaille pour l'État » jusqu'à ce jour (récit militant), et les recettes ne sont pas collectées. Contraire à la neutralité et aux « méthodes inventées ». Si l'on veut une métaphore temporelle neutre : « si la dépense publique de [année] tenait en une journée de 24 h, la protection sociale en occuperait [x] » — même donnée que 6.1, à n'utiliser que si 6.1 ne suffit pas.

### 6.3 « La marche des niches fiscales » — **utile, très forte, signature probable**
Courbe de concentration (§1.12) : chaque dépense fiscale est une marche, de la plus coûteuse à la plus petite ; puis le **plateau d'inconnu** des 63 non chiffrées, dessiné comme un escalier vide qui ne se referme pas (« coût inconnu »), chaque marche cliquable vers sa ligne et son responsable (DLF / Direction du Budget). Filtres : impôt (IR, IS, TVA…), cotation environnementale. Lecture : « les [n] premières font [x] du coût chiffré » (calculé par ce site). Elle répond sans éditorialiser à la question politique « cadeaux » par les catégories officielles. Risque : le cumul ne doit additionner que des coûts **du même stade et de la même année** (prévision 2026 seule, par exemple) et regrouper par `code_depense` (dépenses ventilées sur plusieurs lignes, inventaire §1).

### 6.4 « L'arbre budgétaire zoomable » — **utile si icicle ; gadget si cercles**
Mission → programme → action → sous-action (PLF 2025 par destination). Forme recommandée : **icicle / barres imbriquées** (longueurs comparables, libellés horizontaux lisibles, se déplie en liste à 320 px), zoom = clic sur un nœud qui devient la racine, fil d'Ariane. **Un arbre par type de budget** (BG, CAS, CCF, BA ne s'additionnent pas). Lignes techniques grisées et étiquetées. Proscrire : circle packing (aires mal lues, place perdue), sunburst (angles + anneaux externes minuscules), treemap zoomable sur mobile (rectangles illisibles sous ~40 px). Limite à dire : les données sont au stade **PLF 2025** ; pas d'arbre LFI tant que la lacune n'est pas comblée.

### 6.5 « Le mur des absences » — **utile, signature citoyenne, unique**
Grille de couverture (§1.9) de tout ce que le site devrait pouvoir montrer : jeux × années × stades, cases vides cliquables avec **qui devrait publier** et depuis quand on l'a constaté. Aucune autre plateforme ne montre ses trous ; c'est l'incarnation du principe 4 et du « pouvoir au peuple ». Données : table `lacune` + catalogue des montants (disponible).

### 6.6 « 30 ans de dépense publique, fonction par fonction » — **utile**
Petits multiples des 10 divisions COFOG en % du PIB, 1995-2024, axe commun, provisoires marqués, ruptures de méthode Eurostat annotées si elles existent (*à vérifier par l'économiste*). Option : la France en couleur, 2 ou 3 pays européens en gris quand Eurostat sera collecté pour d'autres pays (même source, même nomenclature — comparaison légitime).

### 6.7 « La pente des départements » — **utile avec garde-fous**
Slope chart des 101 départements, €/hab d'un agrégat, 2012 → dernière année : les pentes en gris, le département choisi et la médiane en couleur. Garde-fous : euros courants = l'inflation fait monter toutes les pentes → proposer l'option euros constants (calculée, sourcée) ou l'indice base 100 ; ruptures de périmètre (Lyon, Alsace, collectivités uniques) traitées par trou, pas par raccord.

### 6.8 « Budget vert : la couleur des crédits » — **utile, forme à choisir avec soin**
Par mission, barres horizontales 100 % de la cotation (favorable / neutre / défavorable / mixte / NC), triées par montant total de la mission (montant en texte). Marimekko tentant mais proscrit (aires, §1.11). Couleurs de cotation : **pas** vert/rouge moral — la cotation est l'objet officiel, on l'affiche telle quelle, mais avec des teintes catégorielles neutres et la légende officielle ; NC en gris « Autres » avec mention « non coté ».

### 6.9 Autres idées écartées
- **Horloge de la dette / compteur qui défile** : fausse précision (extrapolation à la seconde d'un chiffre annuel), anxiogène, données non collectées. **Refuser.**
- **« Ce que vous coûte X par an »** (dépense nationale / population) : division correcte mais lecture fausse (« ma part » ≠ ce que je paie). Acceptable seulement titré « dépense moyenne par habitant », jamais « votre part ».
- **Globe 3D, carte en relief, animation « bar chart race »** : spectaculaires, illisibles, non accessibles. La « course » en particulier empêche toute lecture des valeurs. **Refuser.**
- **Scrollytelling** (récit guidé au défilement) : utile pour 1 ou 2 récits éditoriaux par an (« le PLF en 5 étapes »), avec un graphique final explorable ; coûteux à maintenir, à ne pas généraliser.

---

## 7. Performance et architecture de rendu

### 7.1 Ce qui reste (et devient) serveur
- **Le dessin SVG statique de toutes les formes** : courbes, barres, dot plots, slope charts, waterfall, petits multiples, tuiles, carte (chemins pré-calculés), beeswarm (disposition calculée en Python, déterministe). Raisons : (1) même SVG pour la page, l'export image, l'embed et l'OpenGraph — une seule vérité ; (2) lisible sans JS et immédiatement à l'affichage (pas de « flash » de graphique vide) ; (3) testable (on peut vérifier en test que chaque marque porte un `href` vers une ligne source et qu'aucune absence n'est dessinée comme zéro).
- Tous les calculs (parts, médianes, indices, déflation, cumul, classes de carte) : déjà la règle (« aucun chiffre n'est calculé ici »), à conserver.
- Le tableau jumeau, les légendes, les pieds de source, le compteur d'absences.

### 7.2 Ce qui peut être JS (amélioration progressive)
- Infobulles, réticule, surlignage croisé liste ↔ graphique ↔ carte, épinglage au tap, tri/recherche (existant), redimensionnement (re-demander au serveur un SVG à la nouvelle largeur ou utiliser `viewBox` + `vector-effect: non-scaling-stroke` pour ne pas épaissir les traits).
- Le changement d'état du comparateur (entités, unité, années) : requête serveur qui renvoie le fragment SVG + tableau (HTML partiel), mise à jour de l'URL (`history.replaceState`), affichage précédent estompé pendant le chargement (déjà la règle). Pas de calcul côté client.

### 7.3 Budget de poids (cibles, à mesurer en CI)
- JS total ≤ 30 Ko compressé pour le cœur (aujourd'hui `charts.js` fait environ 11,7 Ko non minifié) ; la carte chargée à la demande.
- Géométries ≤ 80 Ko compressé (§3.6), cache longue durée.
- Une vue courante (SVG + tableau) ≤ 60 Ko compressé hors polices ; polices déjà chargées par le site.
- Vérification à 320 px et sur une connexion lente émulée, comme le reste du site.

### 7.4 Bibliothèques
- **Aucune bibliothèque de graphiques côté client.** Chart.js, ECharts, Plotly, Highcharts : lourds, rendu canvas (pas de `href` par marque, accessibilité faible), esthétique générique — l'inverse du test « anti-logo » du brief. Observable Plot / D3 complet : excellents mais inutiles si le SVG est fait serveur.
- **Côté build/serveur, petites briques acceptables** : `mapshaper` (simplification topologique des contours, étape de build), éventuellement une fonction de projection (pyproj) au build seulement ; un algorithme de treemap « squarified » ou de beeswarm se code en quelques dizaines de lignes Python (préférable à une dépendance) ; `resvg` ou `cairosvg` pour la rasterisation des exports.
- Pas de Leaflet/MapLibre (§3.5).

---

## Ce que je demande aux autres spécialistes

**À l'économiste**
1. Le **déflateur** pour l'option « euros constants » (IPC ou prix du PIB, identifiant de série INSEE exact) et la phrase qui explique pourquoi celui-ci.
2. La **population de référence** pour tout €/hab calculé par le site (municipale, totale, DGF ; millésime) et ce qu'utilise exactement l'OFGL pour ses €/hab publiés.
3. La **liste validée des ruptures de série** (OFGL 2012-2025, M52→M57, réforme régionale de 2016 et reconstitution éventuelle des séries, Lyon, Alsace, collectivités uniques, transferts NOTRe ; ruptures méthodologiques Eurostat COFOG).
4. La source officielle d'une **matrice de flux entre administrations** (transferts entre sous-secteurs APU dans les comptes nationaux INSEE) — sans elle, pas de Sankey.
5. Confirmer que le **budget vert annexé au PLF 2025** permet un vrai « voté vs réalisé » sur un même exercice, sinon la source qui le permet (RAP ?).
6. Les comparaisons de territoires **illégitimes** à bloquer dans le comparateur (compétences différentes : Paris, Lyon, CeA, collectivités uniques).

**Au spécialiste UX/UI**
1. Le **modèle d'état du comparateur** et son encodage d'URL (entités + slots, indicateur, unité, années, base, prix, stade, millésime) — je fournis les contraintes §2, j'ai besoin du parcours.
2. Le comportement **tactile** : tap = infobulle épinglée, second tap = source ; et le geste pour ajouter/retirer un territoire depuis la carte ou la liste.
3. Où vivent les **options désactivées avec raison** (% PIB régional, € sur carte) pour qu'elles informent sans frustrer.
4. Le placement du **mur des absences** et de la carte dans le hero plein écran, sans que la carte devienne la réponse à des questions de classement.

**Au directeur artistique**
1. La **typographie dans les graphiques** : la méthode impose la sans-serif (IBM Plex Sans) pour les chiffres et le chiffre héros ; la serif éditoriale (Source Serif 4) pour les titres-questions — à confirmer, et à tenir dans les exports.
2. Le **gabarit d'export** (carré, 4:5, 9:16, 1200×630) : où vont titre, source, lien, date, sans « bandes de stats de remplissage ».
3. Les teintes **séquentielle et divergente** (bleu ↔ orange plutôt que bleu ↔ rouge) ajustées au papier crème et au mode sombre, puis passées au validateur de palette.
4. Le dessin de la **grille de tuiles des départements** (carrés, encarts DROM) et du signe « non publié » (papier + filet + tiret), qui doivent avoir du caractère sans devenir décoratifs.
5. La matière éditoriale autour des signatures (« 100 € », « marche des niches », « mur des absences ») : photo ou texture réelle autour, jamais dans le graphique.

**Au porteur du projet (collecte)**
IGN ADMIN EXPRESS COG CARTO (départements, régions, DROM) ; COG INSEE ; base officielle des codes postaux (La Poste) ; déflateur INSEE ; populations INSEE ; budget vert PLF 2025 ; Eurostat COFOG d'autres pays pour les comparaisons européennes.
