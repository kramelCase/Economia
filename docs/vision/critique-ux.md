# Critique croisée UX : économiste, DA, dataviz

Je juge selon quatre critères : simplicité, parcours, accessibilité, temps jusqu'à la première réponse (TTPR).
Cibles TTPR : **1 geste depuis le hero, < 10 s sur plateau (mobile, une main), première réponse affichée en
moins de 1,5 s en 4G.**

## (a) Ce qui alourdit ou casse un parcours, et la correction

1. **La cote en Plex Mono sous chaque chiffre (DA §3.6).** Je garde l'idée, mais pas sous cette forme. `↳ Eurostat · gov_10a_exp · ligne 48 213`
   est du jargon pour un néophyte. En 12 px `--muted`, l'AA reste à prouver. Répétée dans une liste de 101 lignes, elle
   gêne la lecture rapide, et sa forme dépliée déborde à 320 px. **Correction : la cote *est* ma marque source**, à trois niveaux.
   - Sous le chiffre-titre seulement : forme repliée **en clair**, en Plex Sans (« ↳ Eurostat, dépenses par fonction »).
   - Le mono est réservé aux identifiants, et seulement dans le popover et la fiche : jeu, ligne, sha256.
   - Dans les listes, les tableaux et les graphiques : une cote par bloc, en pied (la DA le prévoit déjà pour les tableaux). Le
     chiffre garde son lien via le tap.
2. **Le geste sur mobile n'est pas le même chez les trois.** La DA ouvre la fiche au toucher. La dataviz ouvre une infobulle épinglée,
   puis la source au 2ᵉ tap. Moi, j'ouvre un popover. **Il faut un seul geste partout (chiffre, cote, marque de graphique) :**
   le 1ᵉʳ tap ouvre le popover court (valeur, stade, éditeur, ligne), puis « Voir la ligne d'origine » ouvre la fiche.
   Naviguer dès le 1ᵉʳ tap fait perdre la lecture.
3. **Le hero « Le lieu » sur mobile (DA §4, hero 3).** Une orthophoto qui occupe 40 % de l'écran repousse le chiffre sous le pli à
   320 × 568, ce qui casse la couche 1. **Correction : sur mobile, la photo passe après le chiffre et sa cote**, ou en bandeau de
   120 px au plus. Le LCP (affichage du plus gros élément) doit toujours être du texte, jamais l'image.
4. **Les 8 comparaisons bloquées de l'économiste (§3.2) risquent de mener à des « refus ».** Pour les incarner sans frustrer :
   - **On empêche en amont, on ne refuse pas après coup.** Additionner (cas 3, 4 et 8) n'existe pas dans l'interface : aucun bouton
     « additionner », aucun empilement d'emboîtés, les `nc` jamais à 0. Ces cas sont structurels, l'utilisateur ne les rencontre pas.
   - **Le reste devient « pas sur le même axe »** (cas 1, 2, 5, 6, 7). La comparaison est bien rendue, mais en panneaux séparés,
     avec un marqueur de rupture ou une note. Le bandeau tient en une ligne : *ce qu'on fait à la place* + « Pourquoi ? ».
     Jamais de fenêtre modale, jamais de page vide.
   - **Les options impossibles restent visibles, barrées, avec leur raison** (mon R8, l'« option désactivée » de la dataviz).
     L'utilisateur voit la limite *avant* de choisir.
   - **Chaque blocage propose la comparaison légitime la plus proche** (« même question dans une seule source : … »).
5. **Les défauts d'unité.** L'économiste présélectionne les euros constants au-delà de 5 ans ; la dataviz garde les euros courants. Les
   euros constants par défaut font du premier chiffre un **calcul du site** (déflateur non collecté, et en plus un pas de
   provenance). Correction : voir l'arbitrage d4.
6. **Le roulement de compteur du hero (DA).** Il est acceptable s'il ne se déclenche qu'après une action et si `aria-live` annonce la
   **valeur finale** seulement. Il est désactivé par `prefers-reduced-motion`.
7. **Le beeswarm de 101 points à 320 px (dataviz §1.7).** Avec des cibles de 24 px, les points se chevauchent. Il faut une couche
   « point le plus proche » (prévue) et **la liste classée comme vue primaire sur mobile**. Le beeswarm sert de contexte, jamais de
   seule interface.

## Le SVG rendu côté serveur (dataviz §7) : impact sur l'interactivité

J'approuve, et c'est la bonne base : même SVG pour la page, l'export, l'aperçu OpenGraph et les tests ; aucun graphique vide au
chargement ; fonctionne sans JS. Ce qu'on perd : chaque changement d'état demande un aller-retour au serveur (des transitions animées
seraient impossibles, mais on les a rejetées). Les conditions pour que ça reste fluide :
- un endpoint de fragments (SVG + tableau) qui répond en **≤ 150 ms côté serveur**, mis en cache par clé d'URL et millésime ;
- un **préchargement** des voisins probables : années adjacentes de la frise et suggestions « et maintenant ? », au survol ou au
  repos ;
- l'estompage pendant le chargement **seulement après 150 ms**, sinon la page clignote ;
- **deux largeurs de rendu** (≤ 480 px et desktop) : un `viewBox` desktop réduit à 320 px rend les libellés illisibles ;
- les infobulles lues dans des attributs `data-*` posés sur chaque marque (pas de JSON à recalculer) ;
- pour le clavier, un **roving tabindex** (un seul arrêt Tab par graphique, puis les flèches), et non 101 arrêts Tab.

## (b) Ce qui manque

- **Les états** : chargement, erreur réseau, rendu sans JS, résultat partiel. Aucun livrable ne les dessine.
- **Les budgets mesurés** : TTPR, LCP, poids des images du hero (le fac-similé ≤ 60 Ko en AVIF à 320 px) et une vérification
  automatique en CI.
- **Le permalien figé** (économiste et dataviz) **sans alourdir la navigation** : le paramètre `v=millésime` n'est ajouté qu'à la
  copie de lien, à l'export et à l'embed. L'URL de navigation reste « dernière version ». J'ajoute `v` à mon tableau d'URL.
- **Le registre des ruptures sur mobile** : le marqueur se touche et ouvre une explication en une phrase, plus un lien. Rien n'est
  spécifié.
- **Les règles vue → forme** : la table de bascule de la dataviz (§2.2) doit devenir **le moteur de mon emplacement « vue »**, et il
  faut écrire la correspondance mot de la question → vue (« qui… le plus » → classement, « où » → carte, « depuis » → évolution).
- **Un test utilisateur** : 5 tâches chronométrées (mes parcours P1, P2, P4, P5, P6), avec 2 néophytes et 2 experts, avant de figer.

## (c) Ce que j'approuve

- **DA** :
  - le Registre comme système ;
  - la lacune achromatique qui occupe la place du chiffre ;
  - l'étanchéité accent / couleurs de séries ;
  - Marianne exclue ;
  - la phrase-champ en serif dans le hero, compatible avec ma phrase-requête ;
  - les états désactivés « avec leur raison écrite ».
- **Dataviz** :
  - « l'utilisateur ne choisit jamais un type de graphique » ;
  - l'anatomie fixe d'une vue ;
  - les tuiles par défaut sur mobile ;
  - le store locator sans géolocalisation ni tuiles de carte ;
  - les exports recomposés par format ;
  - le CSV au format long avec des lignes d'absence ;
  - la « marche des niches » et le « mur des absences ».
- **Économiste** :
  - le résolveur de périmètre, qui est mon R7 ;
  - « jamais aucun résultat » ;
  - la reformulation visible des requêtes militantes ;
  - le refus des simulateurs et des scores ;
  - l'exigence que le périmètre et le stade soient visibles dès le premier écran à 320 px. C'est déjà ma couche 1.

## (d) Arbitrages à trancher, avec ma position

| # | Question | Ma position |
|---|---|---|
| d1 | Cote sous chaque chiffre, ou par bloc ? | Sous le chiffre-titre plus une par bloc ; libellé en clair ; mono seulement dans la forme dépliée |
| d2 | 1ᵉʳ tap : fiche ou infobulle ? | Popover court partout ; la fiche au 2ᵉ geste |
| d3 | Comparaisons interdites : refus ou panneaux séparés ? | Additions supprimées de l'interface ; le reste en panneaux séparés avec une alternative proposée |
| d4 | Unité par défaut d'une évolution longue | **La valeur publiée d'abord** : % du PIB (national), €/hab (local), M€ courants (missions) ; une note en une ligne « l'inflation n'est pas retirée » avec le bouton « euros constants » (calcul signalé) |
| d5 | Lacune hachurée partout, ou seulement en mode contraste forcé (dataviz §3.3) ? | **Partout**, en hachure légère sur les tuiles : un seul signe de lacune sur tout le site |
| d6 | « 100 € » (dataviz) ou « 1 000 € » (économiste) | 100 € : grille 10×10, arrondi plus simple, et le titre « de dépense publique », jamais « de vos impôts » |
| d7 | Hero : chiffre + trou (UX) ou chiffre + fac-similé (DA) | Les deux sur desktop (fac-similé = preuve du chiffre, colonne de droite). Sur mobile : question, chiffre, cote, trou, barre ; le fac-similé passe sous le pli |
| d8 | Nombre d'emplacements dans le hero | 2 dans le hero (thème, périmètre — « toutes les administrations », pas « France », qui est ambigu) ; les 5 sur la page-réponse, défauts visibles |
| d9 | Permalien figé par défaut ? | Non pour la navigation ; oui pour la copie, l'export et l'embed (`v=`) |

## Ce qu'on dira au porteur : la « découverte » sans tags qui défilent ni onglets

Son intention reste servie, et plus fort que ce qu'il avait imaginé :
- **Ses onglets sont devenus les mots de la phrase.** Thème, territoire, période et type d'analyse sont exactement les
  emplacements de la phrase-requête. Ils se combinent, alors que des onglets en montrent un seul à la fois.
- **Ses tags sont devenus des questions-amorces.** Elles ne bougent pas toutes seules (illisible, non accessible), mais **changent
  à chaque visite**, couvrent les quatre familles de données plus une lacune, et montrent leur vrai chiffre avant le clic.
- **La découverte continue après la première réponse** : « Et maintenant ? » propose 3 à 5 questions voisines sous chaque
  réponse, chacune avec son chiffre. C'est un enchaînement sans fin, que ni des tags ni des onglets ne donnent.
- **Les impasses deviennent aussi des découvertes** : les options barrées, avec leur raison et leur responsable, et le mur des
  absences font découvrir ce que l'État ne publie pas.
- **La barre vide n'est jamais muette** : elle propose des questions variées et le fil de la session. Sous le hero, trois
  signatures servent de portes d'entrée : la grille des 100 €, la marche des niches, le mur des absences.
