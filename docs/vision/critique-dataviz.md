# Critique croisée — regard dataviz sur `economiste.md`, `ux.md`, `direction-artistique.md`

Renvois : « DV §x » = `dataviz.md`. Aucun chiffre n'est donné ici.

## (a) Ce qui produirait un graphique trompeur ou illisible, et la correction

1. **DA §3.7 : la barre hachurée « sans longueur (largeur fixe courte) » dans un classement.** Dans un classement, une barre courte se lit comme une petite valeur, même hachurée. *Correction* : aucune barre dans la piste. À la place de la barre, une pastille hachurée de 12 px (une clé de légende, pas une marque de valeur), suivie de « Non chiffré · qui devrait publier : … ». La ligne reste à sa place alphabétique, ou en fin de liste sous un intertitre « Non chiffrés », jamais triée comme un zéro.
2. **DA §3.7 : le bloc lacune « bordé d'un filet pointillé ».** Dans la grammaire des graphiques, le pointillé veut dire **prévision** (PLF, LFI, coût prévu : DV §2.6). Une lacune à bord pointillé se lirait comme « montant prévu ». *Correction* : filet plein fin ; le pointillé est réservé aux stades prévisionnels, partout sur le site.
3. **DA §4, Hero 1 : le « roulement de compteur » au changement de champ.** Pendant 300 ms, il affiche des valeurs intermédiaires qui n'existent dans aucune source, et une capture d'écran prise à ce moment-là montre un faux chiffre. *Correction* : fondu enchaîné de l'ancien chiffre vers le nouveau ; aucune valeur intermédiaire n'est rendue.
4. **Économiste §3.1 : euros constants « pré-sélectionnés » alors que le déflateur n'est pas collecté (UX A13 « plus tard »).** Afficher par défaut un point calculé avec un déflateur absent casserait la règle « chaque chiffre remonte à sa ligne ». *Correction* : appliquer la règle (d)3 ci-dessous, active seulement une fois le déflateur en base.
5. **UX §5.1 : le face-à-face « chiffre / trou » tiré au sort sur deux sujets sans rapport** (enseignement APU contre niches de l'État). En les mettant à poids égal, le lecteur compare un montant en € avec un **compte** de dépenses, sur deux périmètres différents. *Correction* : voir (d)4.
6. **Économiste §4.1 : la décomposition prix / population / volume.** Elle est acceptable sur un **total** avec un déflateur et une population nommés (waterfall, DV §1.8). Elle est trompeuse **par fonction**, faute de prix par fonction. Je corrige DV §1.8 dans ce sens : décomposition globale oui, par fonction non.
7. **Économiste §4.5 : « = x jours de dépense publique ».** Correct en texte, avec le calcul signalé. Il faut refuser d'en faire un calendrier visuel : c'est la « journée de l'impôt » par la petite porte (DV §6.2).

## (b) Ce qui manque

- **L'encodage visuel des stades.** L'économiste demande « voté = autre traitement », la DA n'en donne que les libellés texte. Je propose de fixer : réalisé = trait plein et point plein ; voté = point creux ; proposé = pointillé et point creux ; provisoire = point creux avec « p ». La DA doit en faire des tokens (DV §2.6).
- **Le marqueur de rupture** (registre de l'économiste, §4.4) n'a pas de forme graphique dans la DA. Proposition : filet vertical plein `--axis`, avec une étiquette en cote mono cliquable.
- **Les rampes séquentielle et divergente** pour la carte et l'écart à la médiane n'existent ni dans la DA ni dans `style.css`. Elles sont à poser en tokens, en clair et en sombre, et à valider au script contre le papier crème.
- **La sélection dans un tracé.** La DA interdit `--accent` dans un graphique : c'est juste. Il faut alors écrire que le territoire mis en emphase prend `--s1` dans le tracé, avec les autres en `--s0`, et que le filet encre + `--accent-2` reste réservé aux listes.
- **La règle d'axe** (zéro pour les niveaux, brisure dessinée sinon, année de base dans le titre de l'axe) n'apparaît chez aucun des trois. Elle est dans DV §2.3 et doit devenir une règle de produit au sens de l'économiste.
- **Les exports** : l'UX ne prévoit que le 4:5 et le 9:16. Il faut ajouter le 1:1 et le 1200×630 (aperçu de lien), et préciser que chaque format est **recomposé** par le serveur, pas recadré.

## (c) Ce que j'approuve sans réserve

- **UX** :
  - la phrase-requête, qui porte périmètre, stade et mesure : c'est ma grammaire (DV §2) sous forme d'interface ;
  - la garde de comparabilité K2 ;
  - les options grisées avec leur raison ;
  - la frise d'années touchable ;
  - le refus des animations A15 et de Leaflet M5 ;
  - la carte en tuiles sur mobile M3 : **validée**, c'est mon défaut mobile ;
  - les images sourcées générées côté serveur ;
  - le test qui échoue si un nombre n'a pas sa marque source.
- **Économiste** :
  - les blocages §3.2 et l'absence de ligne reliant un réalisé à une prévision ;
  - les totaux incomplets libellés « au moins » ;
  - médiane et quartiles plutôt que moyenne ;
  - le nuage de points sans droite causale ;
  - les quantiles affichés en légende de carte. J'y ajoute des **seuils fixes sur toute la période affichée**.
- **DA** :
  - les deux territoires étanches (pas d'accent dans le tracé, pas de couleur de série hors du tracé) ;
  - la sélection par baisse d'opacité des autres et non par changement de couleur ;
  - la cote incrustée dans l'export ;
  - surtout, **la lacune achromatique**. Elle a vu juste : la rouille `#9a4a12` est de la même famille que `--s2` et se confondrait avec une série.

## (d) Arbitrages, avec ma position

**1. « Un seul visuel » (UX §6.1) contre petits multiples et panneaux juxtaposés.** Un *visuel* = une question, un cadre, un titre, une ligne de source, un tableau jumeau. Des petits multiples à **axe commun** forment un seul visuel, comme une grille de dix courbes COFOG. Les cartes séparées de K2 ne sont pas une réponse graphique : c'est le **refus motivé de fusionner**, déjà prévu par l'UX elle-même. Ma règle :
- petits multiples autorisés jusqu'à 10 panneaux, en 2 colonnes à 320 px, valeur de fin seule étiquetée ; au-delà, une liste ;
- panneaux « non comparables » limités à 2, ou 3 au plus, empilés sur mobile, chacun avec son titre de périmètre, sous le bandeau K2 ;
- jamais deux visuels qui répondent à deux questions différentes sur la même page-réponse.

**2. Hachure à l'encre contre mon encodage des absences.** Je me range à la DA et **je corrige DV §3.3 et §4.1** : la hachure devient le signe unique de l'absence, partout, et non plus une texture réservée au mode `forced-colors`. C'est une marque sémantique, pas une décoration, donc compatible avec la méthode. Conditions :
- **courbe** : la ligne s'arrête ; une bande hachurée **sur toute la hauteur du tracé** couvre les années manquantes (une période, pas une valeur), avec l'étiquette « non publié » ;
- **carte et tuiles** : territoire hachuré, listé sous la carte ;
- **classement** : pastille hachurée et texte, sans barre (a1) ;
- **anneau et barre 100 %** : pas de part hachurée (on ne sait pas sa taille) ; la note « dont n postes non chiffrés » est obligatoire ;
- **marche des niches** : marches hachurées de hauteur **non proportionnelle**, légendées « coût inconnu » ;
- **partout** : contraste ≥ 3:1, filet plein, angle 135° seulement. En `forced-colors`, les séries passent aux étiquettes directes et la hachure reste à l'absence seule.

**3. Euros courants contre euros constants : une règle par type de vue.**

| Vue | Défaut | Alternative à un geste |
|---|---|---|
| Valeur ponctuelle, parts, classement, carte d'une même année | **courants**, aucun déflateur n'a de sens à date unique | — |
| Comparaison de deux années ou évolution ≤ 5 ans | **courants**, libellés « euros courants » | constants |
| Évolution > 5 ans en € ou €/hab (courbe, slope chart, base 100) | **constants** (règle de l'économiste), *une fois le déflateur collecté* ; d'ici là courants, avec mention et suggestion « % du PIB » | courants |
| Question de poids (« quelle part de la richesse ») | **% du PIB** publié | constants |
| Waterfall entre deux stades d'une même année | courants | — |

Garde-fous :
- le déflateur et l'année de base figurent dans l'unité de l'axe ;
- le badge « calculé par ce site » est affiché ;
- l'infobulle montre la valeur courante avec sa ligne source ;
- le CSV contient les deux colonnes ;
- `prix=` est inscrit dans le permalien ;
- jamais courants et constants dans un même graphique.

**4. Le face-à-face du hero.** Deux colonnes de registre séparées par un filet vertical, **sans axe commun ni barre** : la seule chose que le lecteur doit comparer, c'est « connu » et « inconnu ».
- **À gauche** : le chiffre vedette, son unité, son stade et sa cote.
- **À droite** : le bloc hachuré **de la même emprise** que le chiffre. Il contient « Non chiffré » en serif italique, puis le **compte** en corps de texte, pas en taille vedette : un compte en grand se lirait comme un montant. Viennent ensuite le responsable et la cote du constat.
- **Mêmes sujet et périmètre des deux côtés.** Ma recommandation par défaut : « Coût chiffré des dépenses fiscales [année, stade] : au moins [montant réel issu du budget vert PLF 2026] » face à « [n réel issu de `lacune`] dépenses non chiffrées ». On a alors un vrai « au moins … dont inconnu », et non deux sujets tirés au sort. Les paires du vivier sont relues par l'économiste.
- **Mobile** : le chiffre d'abord, la hachure dessous, à la même largeur.

**5. Typographie du chiffre vedette.** La méthode demande une sans-serif pour le chiffre héros ; la DA choisit la serif 700. J'accepte la serif **hors des graphiques** (hero, haut de page : c'est l'identité, pas la mesure). **Dans les tracés, les axes, les infobulles, les tableaux et la partie graphique des exports**, c'est Plex Sans : chiffres alignés, tabulaires seulement en colonne.
