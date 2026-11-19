# Direction artistique : Comptes publics, moteur d'exploration

*Contribution du directeur artistique. Lue avec `BRIEF.md`, `static/style.css` et `templates/base.html`. Aucun chiffre n'est
inventé : là où un montant apparaît dans une maquette, il est noté `[montant réel issu de …]`. Les valeurs OKLCH sont des
points de départ, à valider par un script de contraste (cible AA : 4,5:1 pour le texte courant, 3:1 pour le texte
≥ 24 px ou ≥ 18,66 px gras et pour les objets graphiques), pas des mesures déjà faites.*

## Le problème de forme, en une phrase

Le sujet n'a pas d'image : l'argent public n'est ni un billet, ni une pièce, ni une tirelire, ni un camembert. Il n'existe
que sous deux formes visibles : **des documents** (lois de finances, comptes, bleus budgétaires, tableaux Eurostat) et
**des lieux** (le collège, la route, l'hôpital, le département). Tout ce qui n'est ni l'un ni l'autre est décoration.
Les trois directions qui suivent prennent chacune un parti différent sur cette question.

---

## 1. Trois directions

### Direction A : « Le Registre »

**Idée-force.** Le site est une archive publique ouverte au lecteur : chaque chiffre est une pièce cotée, et la preuve
(source, fichier, ligne) fait partie de l'image au lieu d'être cachée dans une note.

**Références.** Le Monde Décodeurs pour la sobriété de la typographie et la façon d'afficher la source sous le chiffre ;
la rubrique « Notes » du Financial Times (filets fins, notes de bas de page qui font partie de la mise en page) ; les
inventaires des Archives nationales et les notices de Gallica (cote, provenance, date) ; les vieux registres de comptabilité
publique (colonnes réglées, totaux soulignés deux fois) ; les « bleus » et les « jaunes » budgétaires, ces annexes au
projet de loi de finances que tout parlementaire reconnaît à leur couverture.

**Typographie** (continuité avec l'existant, et c'est un atout) :
- *Source Serif 4* (Adobe, OFL), axe optique 8–60 : titres et chiffres vedettes en `opsz 60`, texte courant en `opsz` auto.
  Elle a des chiffres alignés et tabulaires (`lnum`, `tnum`).
- *IBM Plex Sans* (OFL) : interface, légendes, tableaux (avec `tnum`).
- *IBM Plex Mono* (OFL), **ajout** : uniquement pour la cote (identifiant de jeu de données, numéro de ligne, début de
  sha256). Le mono devient le signe visible de la traçabilité ; il n'est employé à rien d'autre.
- Échelle : rapport 1,25 en texte, saut à 1,5 pour les titres, le chiffre vedette hors échelle (voir §3).

**Couleur.** Papier, encre, une seule couleur d'action (bleu pétrole, celui de l'existant). Pas de couleur de catégorie
dans l'identité.

| Token | Clair | Sombre |
|---|---|---|
| `--paper` | `oklch(96.5% 0.010 85)` | `oklch(17.5% 0.008 85)` |
| `--ink` | `oklch(21% 0.006 85)` | `oklch(93% 0.014 85)` |
| `--accent` (action) | `oklch(40% 0.065 215)` | `oklch(78% 0.075 210)` |

*Ce qu'aucune couleur ne doit faire* : signifier une catégorie budgétaire, un jugement (bien/mal, hausse
bonne/mauvaise), ou une lacune. La couleur sert l'action, rien d'autre.

**Matière.** Papier non blanchi, filets à l'encre (0,5 px et 2 px), double filet sous les totaux comme dans un registre
comptable, appels de note numérotés. Pas de grain de papier simulé en image : la matière vient des filets, de la grille et
des vrais fac-similés.

**Imagerie.**
- **Fac-similés de documents budgétaires réels** : pages de lois de finances anciennes et du *Compte général de
  l'administration des finances* (Gallica, BnF ; réutilisation non commerciale libre, commerciale sous licence : à faire
  confirmer selon le statut du site), PDF actuels de budget.gouv.fr et des PAP (licence ouverte Etalab 2.0). La page
  d'où vient le chiffre, recadrée sur la ligne, est l'image la plus honnête possible.
- **La Déclaration de 1789, articles 14 et 15** (texte du domaine public, cité via Légifrance avec sa référence) : le
  droit de « constater la nécessité de la contribution publique » et de demander compte à tout agent public. C'est le
  fondement juridique exact de la mission du site, pas un slogan.
- Typographie comme image : la nomenclature officielle elle-même (« Mission Enseignement scolaire », « 09 —
  Enseignement ») composée en grand, telle qu'elle est écrite dans la source.

**Motion.** Une seule animation porteuse de sens : **le dépliage de la cote**. Au survol ou au focus d'un chiffre, la
cote passe de `Eurostat · gov_10a_exp` à la chaîne complète (fichier, sha256 abrégé, ligne) en 200 ms, comme une fiche
qu'on tire d'un tiroir. Le reste ne bouge pas. `prefers-reduced-motion` : apparition sans déplacement.

**Hero.** Plein écran papier. En haut à gauche, la question en très grand serif. En dessous, le chiffre vedette
`[montant réel issu de Eurostat gov_10a_exp, France, total COFOG, dernière année]`, et collée sous lui sa cote en mono.
À droite (desktop seulement), le fac-similé de la page source, recadré, légendé. Sur mobile, le fac-similé passe sous la
cote, en bande pleine largeur.

**Signature.** **La cote** : sous chaque chiffre, une ligne mono fine, précédée d'un `↳`, qui dit d'où il vient. On la
reconnaît en une seconde dans une capture d'écran partagée sur un réseau social, et aucun autre site ne peut la copier
sans s'engager sur la même rigueur.

**Risques.** Paraître austère ou « administratif » au grand public ; surcharge de mono si la cote n'est pas disciplinée ;
droits Gallica à vérifier ; un fac-similé ancien qui suggère une continuité de nomenclature qui n'existe pas (il faut
dire « document de 18xx, nomenclature différente »).

**Test anti-générique.** Réussi : la cote et le fac-similé sont attachés au contenu réel ; on ne peut pas poser un autre
logo sans que la promesse (« chaque chiffre remonte à sa ligne ») devienne un mensonge visible.

---

### Direction B : « Le Terrain »

**Idée-force.** L'argent public se voit d'avion : chaque page part d'un territoire photographié (orthophoto IGN), et les
montants s'y posent comme des légendes de carte.

**Références.** Les grands récits cartographiques du NYT (*The Upshot*, récits sur les comtés), Reuters Graphics pour
l'usage de l'image satellite documentaire, Bloomberg CityLab, la carte de Cassini et les cartes d'état-major (IGN
« Remonter le temps »), la sémiologie graphique de Jacques Bertin (ressource française, crédible chez les économistes et
géographes).

**Typographie.**
- *Archivo* (Omnibus-Type, OFL), variable en largeur (62–125) et graisse : étiquettes de carte en étroit capitales
  espacées, titres en large. La variation de largeur sert la hiérarchie comme sur une carte topographique.
- *Literata* (TypeTogether, OFL), axe optique : texte de lecture, chapôs.
- Chiffres : Archivo `tnum` dans les tableaux ; chiffre vedette en Archivo large gras.

**Couleur.**

| Token | Clair | Sombre |
|---|---|---|
| `--paper` | `oklch(97% 0.004 230)` (blanc carte) | `oklch(16% 0.012 240)` |
| `--ink` | `oklch(22% 0.015 250)` | `oklch(94% 0.008 230)` |
| `--accent` | `oklch(45% 0.09 30)` (rouge de carte, routes) | `oklch(75% 0.10 35)` |

*Interdit* : teinter les photos en couleur de marque (duotone), colorer les territoires selon un jugement, utiliser le
vert « nature » pour signaler les dépenses vertes (la cotation du budget vert a ses propres catégories officielles,
elles vont dans la palette des graphiques, pas dans l'identité).

**Matière.** Le grain réel de l'orthophoto, les courbes de niveau, les limites administratives en tireté fin (ADMIN EXPRESS,
IGN). Pas de texture ajoutée.

**Imagerie.** BD ORTHO et ADMIN EXPRESS de l'IGN (licence ouverte Etalab 2.0 depuis 2021) ; Remonter le temps (cartes
anciennes, conditions à vérifier par couche) ; Wikimedia Commons pour les photos de bâtiments publics identifiables
(licence à vérifier fichier par fichier, attribution obligatoire). On montre le département vu du ciel, pas « un
hôpital » générique.

**Motion.** Zoom continu France → région → département quand on choisit un territoire (le cadre se resserre, la légende
reste lisible) ; c'est la seule animation, et elle explique l'emboîtement des échelons. Réduction de mouvement : fondu
enchaîné.

**Hero.** Bande d'orthophoto plein écran du territoire choisi (ou, par défaut, une mosaïque des 101 départements en
vignettes carrées, toutes au même cadrage). Le chiffre en étiquette de carte posée sur un cartouche papier opaque (jamais
de texte directement sur la photo). Mobile : photo en haut sur 40 % de l'écran, cartouche dessous.

**Signature.** **Le cartouche** : le rectangle blanc à filet noir des cartes topographiques, avec échelle, nord, source et
date, transposé pour chaque chiffre (« Échelle : département · Source : OFGL · Exercice : [année] »).

**Risques.** Données nationales (COFOG, budget de l'État, niches fiscales) qui n'ont pas de lieu : la direction s'effondre
hors des pages territoires. Poids des images (performances mobiles). Biais visuel : une photo de campagne ou de ville
oriente la lecture d'un montant. Les géométries ne sont pas encore collectées.

**Test anti-générique.** Réussi sur les territoires, échoué sur le national : une mosaïque d'orthophotos est un motif
qu'on a déjà vu ailleurs si elle n'est pas reliée aux données.

---

### Direction C : « L'Affiche »

**Idée-force.** La question du citoyen est l'image : chaque écran est une affiche typographique où la phrase posée et
la réponse officielle occupent toute la surface.

**Références.** The Pudding (pages où le texte est l'interface), les affiches de la typographie suisse, la signalétique
publique française des années 1970 (Jean Widmer, Centre Pompidou, signalisation autoroutière), les couvertures
typographiques de Bloomberg Businessweek.

**Typographie.**
- *Bricolage Grotesque* (OFL), variable en largeur, graisse et taille optique : titres monumentaux en `opsz 96`
  condensé, très serré. Caractère marqué, légèrement irrégulier.
- *Atkinson Hyperlegible Next* (Braille Institute, OFL) : texte et interface ; le choix se justifie par l'accessibilité.
- Chiffres : Bricolage en chiffres tabulaires dans les tableaux ; le chiffre vedette en noir 900, hauteur d'écran.

**Couleur.**

| Token | Clair | Sombre |
|---|---|---|
| `--paper` | `oklch(98% 0 0)` | `oklch(14% 0 0)` |
| `--ink` | `oklch(15% 0 0)` | `oklch(97% 0 0)` |
| `--accent` | `oklch(55% 0.20 265)` (bleu électrique) | `oklch(72% 0.15 265)` |

*Interdit* : bleu-blanc-rouge, et tout fond plein de couleur (le brief les refuse).

**Matière.** Aucune, volontairement : noir et blanc, typographie, blanc tournant. C'est précisément ce qui contredit le
goût du porteur.

**Imagerie.** Aucune photo ; les libellés officiels et les chiffres composés en très grand.

**Motion.** Texte cinétique : la question s'écrit, la réponse s'assemble mot à mot au défilement.

**Hero.** Une phrase-champ en très grand : « Combien coûte [ ________ ] ? », le champ est la phrase. La réponse occupe
l'écran suivant.

**Signature.** Le texte trou : la phrase à compléter.

**Risques.** Graves. Une affiche, c'est la forme du slogan : poser « cadeaux aux milliardaires » en 200 px, c'est
éditorialiser même avec une réponse neutre. Le texte cinétique nuit à la lecture et à l'accessibilité. Tendance « grosse
typo » déjà très répandue. Pas de matière.

**Test anti-générique.** Échoué : une phrase géante sur fond blanc se transpose à n'importe quel produit. On en garde
une seule idée, la phrase-champ.

---

## 2. Recommandation : le Registre, avec le terrain comme second registre d'image

Je recommande **A « Le Registre » comme système**, avec **deux emprunts** :
- à **B**, l'orthophoto IGN et le cartouche **uniquement sur les pages territoires** (une région, un département), où
  la photo est la vérité du lieu et pas une ambiance ;
- à **C**, la **phrase-champ** dans le hero (la recherche composée comme une phrase), mais en serif à taille éditoriale,
  pas en affiche.

Pourquoi :
- **Public très large.** Le citoyen comprend une question et un document qu'on lui montre ; l'économiste reconnaît
  une cote, un code COFOG, un stade budgétaire. La même ligne sert les deux : le chiffre en grand pour l'un, la cote en
  petit pour l'autre, sans deux interfaces.
- **Crédibilité et neutralité.** La preuve visible est la seule forme de neutralité qu'un lecteur méfiant accepte. Le
  Registre ne prend aucun parti esthétique sur le contenu (pas de couleur de jugement, pas d'image d'ambiance) ; il en
  prend un sur la méthode, et c'est le bon.
- **Goût du porteur.** Éditorial, matière (filets, fac-similés, orthophotos réelles), caractère (la cote mono, le double
  filet, le hachuré). Pas de cartes numérotées, pas de bande de stats, pas d'aplats, pas d'illustrations.
- **Accessibilité AA.** Encre sur papier = contrastes très élevés ; une seule couleur d'action ; les lacunes passent par la
  texture et le texte, pas par la couleur (lisibles par tous les daltoniens) ; aucune animation nécessaire à la
  compréhension.
- **Continuité.** Source Serif 4 et IBM Plex Sans restent : on capitalise sur l'existant au lieu de rebâtir une identité.
  La refonte se voit dans la composition, pas dans un changement de police.

---

## 3. Système de la direction recommandée

### 3.1 Couleurs (OKLCH)

Identité = papier, encre, une action. Les valeurs reprennent la teinte chaude de l'existant (`#f6f3ec`, `#1b1a17`,
`#0e4d5c`), converties et ajustées ; à valider par script.

| Token | Rôle | Clair | Sombre |
|---|---|---|---|
| `--paper` | fond | `oklch(96.5% 0.010 85)` | `oklch(17.5% 0.008 85)` |
| `--paper-2` | fond secondaire, survol de ligne | `oklch(92.5% 0.014 85)` | `oklch(22% 0.010 85)` |
| `--paper-3` | cartouche, fac-similé encadré | `oklch(89% 0.016 85)` | `oklch(26% 0.011 85)` |
| `--ink` | texte, filets forts, chiffres | `oklch(21% 0.006 85)` | `oklch(93% 0.014 85)` |
| `--ink-2` | texte secondaire | `oklch(39% 0.012 85)` | `oklch(84% 0.016 85)` |
| `--muted` | légendes, cote | `oklch(50% 0.014 85)` (≥ 4,5:1 à vérifier) | `oklch(70% 0.016 85)` |
| `--rule` | filets fins | `oklch(84% 0.020 85)` | `oklch(33% 0.012 85)` |
| `--accent` | liens, focus, sélection | `oklch(40% 0.065 215)` | `oklch(78% 0.075 210)` |
| `--accent-2` | fond de sélection | `oklch(91% 0.020 215)` | `oklch(28% 0.035 215)` |
| `--hatch` | trait des lacunes | `= --ink` à 55 % d'opacité | `= --ink` à 50 % |

**Changement assumé : `--gap` (rouille) disparaît comme couleur.** L'actuel `#9a4a12` est de la même famille de teinte
que `--s2` (`#eb6834`) de la palette des graphiques : dans un graphique, une lacune « orange » se confond avec une série
orange. La lacune devient **achromatique** : hachure à l'encre + texte. Elle reste reconnaissable par tous, en clair, en
sombre et en impression noir et blanc.

### 3.2 Coexistence avec la palette des graphiques (--s0..--s5)

Deux territoires étanches :
1. **Dans le tracé** (zone de graphique, pastilles de légende) : uniquement `--s0..--s5`, `--grid`, `--axis`, et
   l'encre pour les annotations. **Jamais** `--accent` dans un tracé (il serait lu comme une sixième série).
2. **Hors du tracé** : uniquement papier, encre, accent. **Jamais** une couleur de série en fond, en filet, en
   soulignement de titre ou en icône. Une couleur de série ne sort du graphique que sous forme de pastille à côté du
   libellé qu'elle désigne (comme l'existant, `.sw`).
3. Les textes restent en encre (règle déjà écrite dans `style.css`, maintenue).
4. Sélection d'une série : on ne change pas sa couleur, on baisse l'opacité des autres (déjà fait pour le donut) et on
   épaissit son trait.
5. Lacune dans un graphique : hachure encre sur la plage manquante (pas d'interpolation de la courbe à travers le trou ;
   la ligne s'arrête et reprend). À valider avec le spécialiste dataviz.

### 3.3 Typographie

```css
--serif: "Source Serif 4", Georgia, serif;     /* opsz 8..60, wght 400..700 */
--sans:  "IBM Plex Sans", system-ui, sans-serif; /* 400, 500, 600 */
--mono:  "IBM Plex Mono", ui-monospace, monospace; /* 400 seulement, la cote */

--t-cote:   0.75rem;                                   /* 12 px, mono, interlettre 0 */
--t-small:  0.8125rem;                                 /* 13 px, légendes */
--t-body:   clamp(1rem, 0.96rem + 0.2vw, 1.0625rem);   /* 16 → 17 px */
--t-lede:   clamp(1.125rem, 1rem + 0.6vw, 1.375rem);   /* chapô, serif */
--t-h3:     clamp(1.125rem, 1.05rem + 0.35vw, 1.3rem);
--t-h2:     clamp(1.375rem, 1.15rem + 1.1vw, 2rem);
--t-h1:     clamp(2rem, 1.4rem + 3vw, 3.75rem);         /* serif opsz 60, -0.02em */
--t-hero-q: clamp(1.75rem, 1.1rem + 3.4vw, 4.25rem);   /* question du hero, serif 600 */
--t-figure: clamp(2.5rem, 1rem + 8vw, 8.5rem);         /* chiffre vedette, serif 700 opsz 60 */
```

- Interlignage : 1,6 texte ; 1,15 titres ; 0,95 chiffre vedette.
- Longueur de ligne : 66 caractères max pour la prose (`max-width: 38rem`).
- Chargement : ajouter `IBM+Plex+Mono:wght@400` au lien Google Fonts existant (un seul poids, peu coûteux) ;
  `display=swap` conservé. Auto-hébergement envisageable plus tard pour la performance et la vie privée.
- **Marianne est exclue** : c'est la police de la marque de l'État, réservée aux services de l'État. L'employer
  ferait passer le site pour un service officiel.

### 3.4 Espacements, rayons, ombres

```css
--sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px; --sp-4: 16px; --sp-5: 24px;
--sp-6: 32px; --sp-7: 48px; --sp-8: 72px; --sp-9: clamp(72px, 10vw, 144px);
--gutter: 16px;  /* 24px dès 640px : autorité unique dans .wrap, comme aujourd'hui */
--section: var(--sp-9);  /* même respiration pour toutes les sections */

--r-0: 0;     /* défaut : filets et blocs à angle vif, c'est un registre */
--r-1: 2px;   /* badges, champs */
--r-2: 6px;   /* infobulles, menu de suggestions (objets flottants seulement) */

--shadow-float: 0 1px 0 var(--rule), 0 10px 28px oklch(0% 0 0 / 0.16); /* uniquement objets flottants */
```

Pas d'ombre sur les blocs posés dans la page. La profondeur vient des filets : `0.5px --rule` entre lignes, `2px --ink`
au-dessus d'une section, **double filet** (`border-bottom: 3px double var(--ink)`) sous un total officiel.

### 3.5 Traitement des chiffres

**Chiffre vedette (hero, haut de page).**
- Serif 700, `opsz 60`, `font-variant-numeric: lining-nums`, interlettre `-0.025em`, `--t-figure`.
- L'unité (`M€`, `% du PIB`, `€/hab.`) en serif 400 à 40 % de la taille, alignée sur la ligne de base, jamais en exposant.
- Espace insécable fine (U+202F) comme séparateur de milliers en français, virgule décimale ; en anglais, virgule de
  milliers et point décimal. Le formatage est une affaire de locale, pas de style.
- Immédiatement dessous : la phrase de lecture en sans (« dépenses de toutes les administrations publiques, [année],
  exécution »), puis la cote. Le stade (PLF, LFI, exécution) est toujours écrit en clair à côté du chiffre : c'est la
  confusion la plus fréquente.
- Un calcul du site (part, médiane) porte la mention « calcul du site » dans la cote, en mono également.

**Tableaux.** Plex Sans 400, `font-variant-numeric: tabular-nums lining-nums`, alignés à droite, unité dans l'en-tête de
colonne et non dans chaque cellule, en-têtes en petites capitales espacées (existant), total en 600 avec double filet.
Survol de ligne en `--paper-2`. Première colonne figée au défilement horizontal sur mobile.

### 3.6 La cote (badge « source »)

Remplace le badge actuel `.src` (pastille colorée) :

```
↳ Eurostat · gov_10a_exp · ligne 48 213 · sha256 3f9a…   ← forme dépliée (exemple de format, valeurs à lire en base)
↳ Eurostat · gov_10a_exp                                  ← forme repliée
```

- Mono 400, `--t-cote`, couleur `--muted`, précédée d'un `↳` à l'encre. Pas de fond, pas de bordure : c'est une ligne de
  registre, pas un bouton décoratif.
- Toute la ligne est un lien vers la fiche source ; zone cliquable portée à 44 px de haut par un `padding-block`
  (le texte reste petit, la cible ne l'est pas).
- Survol / focus : soulignement à l'accent, dépliage de la forme repliée vers la forme complète (motion §A).
- Sur mobile, toujours repliée ; un toucher ouvre la fiche, pas une infobulle.
- Dans un tableau : la cote va **une fois** en pied de tableau (« ↳ toutes les lignes : … »), plus une cote par
  ligne seulement si les sources diffèrent.
- Dans une capture partagée (export image), la cote est incrustée en bas, même typographie : c'est la signature qui
  voyage.

### 3.7 Les lacunes

Un trou doit occuper **la place que le chiffre aurait occupée**. C'est ce qui le rend fort sans le rendre alarmant.

- **Le bloc hachuré** : là où le chiffre manquerait, un rectangle de la taille du chiffre attendu, rempli d'une hachure à
  45° à l'encre (`repeating-linear-gradient(135deg, var(--hatch) 0 1px, transparent 1px 7px)`), bordé d'un filet
  pointillé encre. Le hachuré est la convention des cartes et des plans pour « non relevé » : il se lit sans légende,
  il est sérieux, il n'est pas rouge.
- **Dans le bloc**, en serif italique 600, taille h3 : « Non chiffré » / « Non publié » (libellé exact de la source quand
  il existe, par exemple les dépenses fiscales « non chiffrées » du PLF). Dessous, en sans : **« Qui devrait publier :
  [administration citée par la source] »**, et la cote du document qui constate l'absence.
- Interdit pour les lacunes : rouge, orange, icône d'alerte, point d'exclamation, mot « manquant » seul, et surtout `0`.
- Dans une liste ou un classement : ligne présente, à sa place logique, avec une barre hachurée sans longueur (largeur
  fixe courte + texte), jamais retirée de la liste, jamais triée en fin comme un zéro.
- Dans une somme : si un élément est hachuré, le total porte « dont [n] postes non chiffrés » (n compté en base), jamais
  un total présenté comme complet.
- Contraste : la hachure est un objet graphique (3:1 minimum par rapport au papier) ; le texte posé dessus est sur un
  cartouche `--paper` opaque, pas directement sur les traits.

### 3.8 États d'interaction

| État | Traitement |
|---|---|
| Lien au repos | encre `--accent`, soulignement 1px, décalage `.18em` (existant) |
| Survol | soulignement 2px ; une ligne de tableau ou de liste passe en `--paper-2` |
| Focus clavier | contour 3px `--accent`, décalage 2px (existant), visible en clair et sombre |
| Actif / pressé | fond `--ink`, texte `--paper` (boutons segmentés existants) |
| Sélectionné (territoire, série, filtre) | filet de 3px `--ink` à gauche + fond `--accent-2` ; jamais une couleur de série |
| Page courante | filet 2px sous le libellé (existant) |
| Chargement | le contenu reste lisible à 50 % d'opacité (existant) ; pas de squelettes gris animés |
| Désactivé | `--muted`, curseur par défaut, raison écrite à côté (« pas de données pour cette année ») |
| Terme du lexique | soulignement pointillé (existant) ; infobulle `--ink` sur `--paper` avec la référence de la définition |

### 3.9 Mode sombre

- Pas un négatif : une « salle de lecture le soir ». Papier brun très sombre légèrement chaud, encre crème.
- Les **fac-similés et orthophotos ne sont jamais inversés** ni filtrés en couleur : ce sont des objets réels. On les pose
  sur `--paper-3` avec un filet, on peut baisser leur luminosité de 8 à 10 % (`filter: brightness(.9)`) pour éviter
  l'éblouissement.
- La hachure reste à l'encre (devenue claire) : elle s'inverse naturellement.
- La palette des graphiques garde ses valeurs sombres validées (existant), indépendantes de l'identité.
- Bascule manuelle clair/sombre conservée (`data-theme`), en plus du réglage système.

---

## 4. Le hero plein écran

Trois compositions. Règles communes : hauteur `100svh` (pas `100vh`, pour la barre d'adresse mobile) ; aucun texte
posé sur une image ; le champ de recherche visible sans défilement à 320 px ; tout chiffre accompagné de sa cote dès le
premier affichage ; `prefers-reduced-motion` supprime tout déplacement.

### Hero 1 : « La phrase » (accueil, recommandé par défaut)

*Desktop (≥ 960 px).* Grille 12 colonnes. Colonnes 1–8 : kicker en petites capitales (« Finances publiques de la
France, chaque chiffre relié à sa source »), puis la **phrase-champ** en serif 600 `--t-hero-q` :
« Où va l'argent public pour **[ l'éducation ▾ ]** en **[ France ▾ ]** ? ». Les deux crochets sont des champs à
autocomplétion, soulignés d'un filet `--ink` 2px, au corps de la phrase. Sous la phrase, la réponse déjà calculée pour les
valeurs par défaut : chiffre vedette `[montant réel issu de Eurostat COFOG, fonction 09, dernière année]`, phrase de
lecture, cote. Colonnes 9–12 : le **fac-similé** de la page du document source (ou, à défaut, la table Eurostat
composée en Plex Mono comme un extrait de fichier), légendé « Document d'origine : … », filet encre.
En pied de hero, une ligne de questions-suggestions en serif (pas des cartes, pas des pastilles : du texte souligné
séparé par des filets verticaux), tirées des questions réellement couvertes par les données.

*Mobile 320 px.* Une colonne, gouttière 16 px. Kicker (2 lignes max) → phrase-champ en `--t-hero-q` (≈ 28 px), les champs
passent à la ligne entière chacun (« pour » / « [ l'éducation ▾ ] » / « en » / « [ France ▾ ] ») pour rester tactiles
(44 px) → chiffre vedette (≈ 40 px ; vérifier qu'un montant à 7 chiffres plus l'unité tient sur 288 px, sinon l'unité
passe sous le chiffre) → cote repliée. Le fac-similé passe **sous la ligne de flottaison**, en bande pleine largeur.

*Ce qui bouge, et pourquoi.* Quand on change un champ, seul le chiffre change : les chiffres défilent verticalement
(roulement de compteur, 300 ms, une seule fois) et la cote se met à jour au même instant. Le mouvement dit « c'est la même
question, une autre réponse » et lie visuellement le chiffre à sa source. Pas d'animation au chargement.

### Hero 2 : « La pièce » (page d'un chiffre, d'une mission, d'une niche fiscale)

*Desktop.* Le document occupe le fond de la moitié droite : fac-similé de la page du bleu budgétaire ou de l'annexe
Voies et moyens, recadré sur la ligne exacte, la ligne cernée d'un filet `--ink` (pas un surligneur jaune). Moitié gauche :
libellé officiel en serif h1 (tel qu'écrit dans la nomenclature, avec son code), chiffre vedette, stade, cote dépliée
par défaut sur cette page. Si le coût n'est pas chiffré, le chiffre est remplacé par le **bloc hachuré** à la même taille,
et le fac-similé montre la mention « nc » ou équivalente de la source.

*Mobile 320 px.* Libellé → chiffre (ou hachure) → cote → fac-similé recadré en bande de 160 px de haut, touchable pour
agrandir.

*Ce qui bouge.* Au chargement, le fac-similé glisse de quelques pixels pour centrer la ligne citée (le regard va du
chiffre à sa preuve). Rien d'autre.

### Hero 3 : « Le lieu » (pages région et département uniquement)

*Desktop.* Bande d'orthophoto IGN du territoire sur toute la largeur, 55 % de la hauteur, avec les limites
administratives en tireté fin (ADMIN EXPRESS). Sous la photo, **le cartouche** papier opaque à filet noir, aligné à gauche :
nom du territoire en serif h1, chiffre vedette OFGL `[montant réel issu de OFGL, agrégat …, €/hab., dernière année]`,
« Médiane des départements : [calcul du site] », cote. Crédit photo et date de prise de vue dans le cartouche.

*Mobile 320 px.* Photo 40 % de hauteur, cartouche dessous pleine largeur. Image servie en AVIF/WebP à la taille de
l'écran (`srcset`), poids cible à fixer avec l'UX.

*Ce qui bouge.* Changement de territoire : la photo se resserre ou s'élargit (zoom de cadrage, 500 ms) pour dire
« on change d'échelle » quand on passe de la région au département. Réduction de mouvement : fondu.

*Prérequis données.* Géométries et orthophotos non collectées : ce hero attend l'intégration IGN (ADMIN EXPRESS pour
les contours, BD ORTHO ou ses flux WMTS/Géoplateforme pour l'image). D'ici là, le Hero 1 sert aussi les territoires.

---

## 5. Interdit

- Billets, pièces, tirelires, lingots, symboles €, mains qui tiennent de l'argent, Marianne, drapeaux, Hémicycle en photo
  d'ambiance.
- Bleu-blanc-rouge dans l'identité ; police Marianne ; tout ce qui imite la marque de l'État.
- Couleur qui juge (rouge pour une baisse, vert pour une hausse, vert « écolo » hors catégories officielles).
- Couleur de série hors d'un graphique ; couleur d'accent dans un graphique.
- Lacune en rouge, en orange, avec une icône d'alerte, ou affichée comme `0`.
- Texte posé directement sur une photo.
- Cartes numérotées 01/02/03, bandes de stats décoratives, compteurs animés au chargement, aplats de couleur, dégradés,
  glassmorphisme, illustrations SVG ou images générées.
- Chiffre sans cote, chiffre sans stade, chiffre arrondi sans le dire.
- Animation en boucle, parallaxe, défilement détourné.

---

## Ce que je demande aux autres spécialistes

**À l'économiste.**
- Quel chiffre vedette par défaut pour l'accueil (agrégat, stade, année, unité) qui ne soit ni trompeur ni militant ?
- La conversion d'unité M€ → Md€ pour l'affichage en grand est-elle acceptable si la cote le signale, ou faut-il rester
  dans l'unité de la source ?
- Liste des formulations « stade » à imposer à côté de chaque chiffre (PLF, LFI, exécution, comptes) et de leurs
  équivalents anglais officiels.
- Pour les fac-similés anciens : quels documents historiques sont pertinents sans induire une fausse comparabilité ?

**À l'UX/UI.**
- La phrase-champ (deux ou trois champs inclus dans une phrase) tient-elle au lecteur d'écran et au clavier ? Je propose
  un `<form>` avec de vrais `<label>` masqués et la phrase en `aria-describedby`.
- Valider la cible de 44 px de la cote en mobile sans grossir le texte.
- Budget de poids des images du hero (fac-similé, orthophoto) à 320 px sur réseau lent.
- Où vit la bascule clair/sombre et la langue dans la nouvelle navigation.

**Au spécialiste dataviz.**
- Accepter que `--gap` devienne achromatique (hachure encre) pour ne plus concurrencer `--s2`, et définir la hachure
  dans les graphiques (ligne interrompue, barre hachurée, zone de carte hachurée) avec le même motif que l'identité.
- Confirmer la règle d'étanchéité : accent jamais dans le tracé, séries jamais hors du tracé.
- Le roulement de chiffres du hero et la cote incrustée dans les exports image : format et emplacement communs à tous
  les graphiques partagés.
- Pour les cartes à venir : une échelle séquentielle qui ne réutilise pas les teintes des séries catégorielles ni le
  pétrole de l'accent, et l'état « pas de donnée » en hachure.
