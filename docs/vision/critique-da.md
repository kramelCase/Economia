# Critique croisée : l'œil du directeur artistique

*Livrables lus : `economiste.md`, `ux.md`, `dataviz.md`. Aucun chiffre n'est donné ici.*

## (a) Ce qui rendrait le site générique ou « tableau de bord », et la correction

| Risque (où) | Pourquoi ça fait tableau de bord | Correction |
|---|---|---|
| **« Stat tile »** (dataviz §1, §2.2) | Le mot appelle une boîte avec un chiffre, soit la tuile KPI de tout tableau de bord. | Il n'y a pas de boîte. On compose une **ligne de registre** : chiffre en serif, ligne de lecture, cote, filet au-dessus. Pas de fond, pas d'ombre, pas de bordure. |
| **Badges de lecture** périmètre · stade · année · provisoire · calculé (UX A2) | Cinq pastilles côte à côte donnent une soupe de tags, signe classique d'une interface SaaS. | Le périmètre est déjà écrit dans la phrase (c'est le texte le plus gros de la page). Stade, année et « provisoire » forment **une ligne de lecture** en Plex Sans, séparée par des points médians, sans fond. « Calcul du site » va dans la cote. Aucune pastille. |
| **5 amorces avec chiffre-aperçu** (UX §5.1) | Si les chiffres sont gros et alignés, on retombe sur une bande de stats. | Ce sont des lignes de texte en serif, avec le chiffre dans le corps du texte, en encre, à la taille du texte. Les mettre en colonne ou en vignettes est interdit. |
| **4 portes d'exploration** sous le pli (UX §5.5) | Quatre blocs égaux font une grille de cartes, même sans numéros. | On les compose en **sommaire typographique**, comme une table des matières de rapport : titre en serif h2, une phrase, la phrase-requête d'entrée, filets horizontaux. |
| **Barre d'actions mobile à 4 icônes** (UX §3.3) | Barre d'onglets d'application générique. | Des mots seuls (Partager · Exporter · Épingler · Comparer), en Plex Sans 500, avec un filet au-dessus. Pas d'icônes. |
| **100 carrés colorés** (dataviz §6.1) | Une grille de couleurs vives hors de tout contexte, c'est l'infographie de réseau social. | Je la garde, mais **dans un graphique** : axe des libellés, valeurs en texte, pied de source. Jamais en décor de hero ni en fond de section. |

## (b) Ce que l'UX et la dataviz imposent et qui casse l'identité

1. **Le territoire choisi tracé « en couleur d'accent »** dans la bande de points (dataviz §1.7). Cela viole la règle d'étanchéité : le pétrole de l'accent se lirait comme une sixième série. Correction : le territoire sélectionné est tracé **à l'encre** (`--ink`, l'encre des annotations) et étiqueté en toutes lettres, les autres territoires en `--s0`.
2. **« Pas de donnée » = fond papier + filet + tiret, hachures seulement en mode `forced-colors` ou à l'impression** (dataviz §3.3). Deux problèmes :
   - le premier cran de la rampe séquentielle « se fond dans le papier » : sur une carte, **le territoire le plus bas et le territoire sans donnée se ressemblent** ;
   - une lacune qui ressemble à du vide contredit le principe 4.

   Ma position : **hachure encre partout où la marque fait au moins 24 px** (tuile, barre, zone de courbe, case du mur des absences), tiret « — » plus la raison dans les cellules de tableau et les marques trop petites. C'est la même hachure que dans l'identité, sur une seule définition CSS, au pas de 7 px.
3. **La paire divergente bleu ↔ orange.** Elle est compatible avec la suppression de la rouille `--gap` : la lacune étant devenue achromatique, l'orange ne désigne plus jamais un trou. Quatre conditions :
   - aucune vue ne mêle palette divergente et palette catégorielle (le même orange voudrait dire « au-dessus de la médiane » ici et une fonction COFOG là) ;
   - le milieu de la rampe est `--paper-2`, pas `--paper`, pour ne pas être confondu avec « pas de donnée » ;
   - le bleu de la rampe reste nettement distinct du pétrole de l'accent (écart de teinte à vérifier au validateur) ;
   - l'extrémité orange n'est jamais employée seule hors du tracé.
4. **« Deux familles de polices »** (UX F5) contre ma troisième, IBM Plex Mono pour la cote. Je maintiens Plex Mono : c'est la signature. Elle coûte un seul fichier woff2 (poids 400, sous-ensemble latin) et doit aussi être **embarquée dans les exports** (la liste de la dataviz §5.1 l'oublie).
5. **Le chiffre héros en sans-serif** (méthode dataviz). Mon arbitrage : sans-serif *dans les graphiques et les tableaux* (Plex Sans, chiffres tabulaires) ; **serif pour le chiffre vedette** du hero, de la page-réponse et des exports. Sans cela, l'éditorial disparaît exactement là où on le regarde.

## (c) Ce que j'approuve sans réserve

- **La phrase-requête** (UX §1.2). C'est mon hero « la phrase » ; l'UX lui donne sa grammaire, je lui donne sa typographie. Chaque emplacement est écrit au corps de la phrase, souligné d'un filet encre de 2 px avec un ▾ ; au focus, contour de 3 px ; hauteur tactile d'au moins 44 px. Pas de pastilles.
- **La lacune bloquante placée juste sous le chiffre** (UX §3.3, point 4) et **« au moins … »** pour un total incomplet (économiste §3.4).
- **L'économiste demande que le libellé officiel et le périmètre aient le même poids que le montant.** C'est résolu par la composition : le périmètre est *dans la question*, qui est plus grosse que le chiffre.
- **Illustration documentaire et neutre** (économiste, demande 2) : c'est la définition même du Registre.
- **SVG dessiné côté serveur, partagé par la page, l'export, l'iframe et l'aperçu de lien** (dataviz §7) : une seule identité partout.
- **Le mur des absences et la marche des niches** : ce sont les deux signatures graphiques du site, et toutes deux reposent sur la hachure.
- **Les refus** : ticker, carrousel, Sankey, horloge de la dette, bar chart race, Leaflet, comptes utilisateurs.
- **Les tuiles carrées sur mobile** (dataviz §3.4 ; UX M3) : carrés à angle vif, 2 px de papier entre les tuiles, code ou nom court en Plex Sans à chiffres tabulaires, encarts des DROM à taille égale.

## (d) Arbitrages, avec ma position

**1. Le hero fusionné : « la question et son trou »**

Composition unique. Un vivier de paires (question A avec réponse chiffrée, question B sur une lacune) est relu à la main ; le serveur en choisit une à chaque chargement.

*Desktop (≥ 1024 px, 100svh).*
- Bandeau haut : marque et kicker.
- Colonnes 1 à 6 : **question A, qui est la phrase-requête elle-même** (serif 600, `--t-hero-q`, thème et périmètre modifiables). Dessous : le chiffre vedette `[montant réel issu de …]`, sa ligne de lecture (stade · année · provisoire), sa cote.
- Colonnes 7 à 12, **à poids égal** (même corps, même hauteur de bloc) : la question B, puis un **bloc hachuré de la hauteur exacte du chiffre A**, « Non chiffré » en serif italique, « Qui devrait publier : [responsable issu de la table `lacune`] », et la cote du document qui constate l'absence.
- En dessous, sur toute la largeur : une ligne « Ou posez votre question… », avec le raccourci `/`, qui ouvre la saisie libre.
- Puis la **bande documentaire à fond perdu** (environ 30 % de la hauteur), décrite au point 2 ; le bloc hachuré B y descend par un filet encre.
- Dernière ligne : « Sources · dernière collecte le … ».

*Mobile (320 × 568).*
- Kicker sur une ligne.
- Question A en 1,5 rem, au plus 3 lignes ; chaque emplacement modifiable sur sa propre ligne.
- Chiffre en `--t-figure` (minimum 2,5 rem), cote repliée.
- Question B au **même corps** que A, puis le bloc hachuré de **même hauteur** que le chiffre et la ligne « Qui devrait publier ».
- Champ libre dans la moitié basse, zone du pouce.
- La bande documentaire commence sous le pli et en dépasse d'environ 48 px pour inviter au défilement. Mesurer à 320 px que A, B et le champ tiennent ; sinon le champ passe sous B, jamais A ni B sous le pli.

*Ce qui bouge.*
- Changer un emplacement de A fait rouler les chiffres verticalement, une seule fois (300 ms), et la cote se met à jour au même instant.
- **B ne s'anime jamais** : un trou ne se compte pas.
- Avec `prefers-reduced-motion` : remplacement sans déplacement.

**2. Le plein cadre de l'accueil : ce qu'on voit concrètement**

Pas d'orthophoto sur l'accueil : elles sont réservées aux pages région et département. La bande à fond perdu montre **la page imprimée du document officiel où la lacune B est constatée**. Par exemple, pour une paire sur les dépenses fiscales : la page de l'annexe *Voies et moyens, tome II* au PLF, où les colonnes de coûts portent « nc ».
- La page est rendue en haute définition depuis le PDF officiel, recadrée sur les colonnes, et la ligne « nc » est cerclée d'un filet encre (pas de surligneur).
- Pas de duotone, pas d'inversion en mode sombre.
- **L'image porte sa propre cote** (fichier, sha256, page).

C'est une image réelle, plein cadre, qui *prouve* au lieu de décorer. Condition : le PDF doit être collecté dans `sources.yaml` comme toute source. Une paire dont la lacune n'a pas de document imprimé n'entre pas dans le vivier du hero.

**3. Lacunes : hachure encre et non tiret seul**, dans l'identité comme dans les graphiques (voir b.2). Je demande à la dataviz d'adopter le motif commun.

**4. Sélection dans un graphique : encre**, jamais l'accent (voir b.1).

**5. Langage des stades** (demande 3 de l'économiste). Hors graphique, le stade est **toujours écrit en toutes lettres** dans la ligne de lecture : « Exécution », « Loi de finances initiale », « Projet de loi de finances », « estimation », « provisoire ». Dans les graphiques, on suit le code de la dataviz : plein pour le réalisé, point creux pour le provisoire, pointillé pour la prévision. Aucune couleur, donc imprimable en noir et blanc.

**6. Cible tactile de la cote** : 24 px au minimum (WCAG 2.5.8, comme le demande l'UX), **44 px visés** en mobile grâce au `padding-block`, sans grossir le texte.
