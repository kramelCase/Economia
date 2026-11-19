# UX / UI : le moteur d'exploration de Comptes publics

Spécialiste UX/UI (produits de recherche, d'exploration de données, journalisme de données).
Lu : `BRIEF.md`, `README.md`, `docs/INVENTAIRE.md`, `templates/*`, `api/main.py`. Base actuelle : 7 pages
thématiques à formulaires `<select>` + bouton « Afficher », badge `source` sur chaque chiffre, tableau jumeau
sous chaque courbe, infobulles du lexique, page `montant/{id}` qui relit la ligne brute. **Cette fondation
de provenance est l'atout n° 1 : la refonte la rend plus visible, elle ne la remplace pas.**

Abréviations des profils : **N** néophyte/citoyen · **J** journaliste/fact-checkeur · **É** économiste/chercheur ·
**C** créateur de contenu/réseaux sociaux · **L** élu/agent de collectivité · **P** enseignant/plateau TV.

---

## 1. Le modèle mental

### 1.1 Comment chacun passe d'une question à une réponse, puis à la suivante

| | Néophyte | Économiste |
|---|---|---|
| Point de départ | Une phrase vague, souvent militante ou entendue : « on paie trop pour la dette », « mon département gaspille » | Un objet précis : « GF0107, S13, 1995-2024, % PIB » |
| Ce qui le bloque aujourd'hui | Il ne sait pas *quelle* nomenclature contient sa question (APU ? État ? département ?) | Il doit deviner quel menu cache la série, puis la télécharger ligne par ligne |
| Ce qu'il attend de la réponse | Un chiffre, une phrase, un repère (« c'est beaucoup ? ») | Le périmètre, le stade, la série complète, le fichier |
| Sa question suivante | Presque toujours un **déplacement d'un cran** : plus près de chez moi, plus loin dans le temps, comparé à quoi, c'est quoi ce mot | Les mêmes déplacements, plus **l'export** et la **ligne source** |

Constat : les deux profils font **les mêmes gestes** (préciser, élargir, comparer, remonter le temps, vérifier),
à des profondeurs différentes. Une seule interface peut les servir si la profondeur est **divulguée
progressivement** et non séparée en « mode simple / mode expert ».

### 1.2 Concept central : **la phrase-requête**

> **Une question est une phrase faite d'entités. La phrase est l'URL. La réponse est une page composée
> automatiquement pour cette phrase. Chaque mot de la phrase est un bouton qui se remplace.**

```
 Combien  [l'éducation ▾]  coûte-t-elle à  [toutes les administrations ▾]  en  [2024 ▾]  en  [% du PIB ▾]
   vue        thème                              périmètre                    temps         mesure
```

- **Cinq emplacements typés**, toujours les mêmes, toujours dans le même ordre : *vue* (combien / quelle part /
  comment évolue / qui dépense le plus / comparé à), *thème* (fonction COFOG, mission-programme-action,
  niche, impôt, agrégat OFGL, fonction départementale M57/M52), *périmètre* (APU, État, administrations
  locales, Sécurité sociale, budget de l'État, une région, un département, tous les départements),
  *temps* (année + stade : exécution / LFI / PLF / comptes), *mesure* (M€, % du total, % du PIB, €/hab.).
- **Taper** une phrase libre, **cliquer** une question-amorce, **toucher** un chiffre n'importe où sur le site :
  les trois aboutissent à la même chose, une phrase-requête remplie, visible, modifiable.
- **Toucher un emplacement** ouvre un sélecteur qui ne propose que ce qui existe dans les données pour les
  autres emplacements, **et montre ce qui n'existe pas comme une lacune** (grisé + raison + responsable),
  au lieu de le cacher. Exemple : thème « répartition par fonction » + périmètre « une région » → l'option
  apparaît barrée « non publié par l'OFGL / DGFiP » avec lien vers `lacunes`. **Les trous deviennent visibles
  dans le geste même de la recherche** : c'est la traduction UX du principe 4.
- **La page-réponse** est composée de blocs dont le choix dépend de la phrase (cf. § 3.3) ; il n'y a pas de
  « pages » thématiques à apprendre, seulement des phrases.
- **« Et maintenant ? »** : chaque réponse propose 3 à 5 phrases voisines (un emplacement changé à la
  fois), calculées par règles sur le graphe des nomenclatures, jamais générées par un LLM.

Pourquoi ce concept plutôt qu'un autre :
- « Tout est un objet comparable » (modèle OWID) est puissant mais trompeur ici : la moitié des comparaisons
  naïves sont fausses (APU vs État, M52 vs M57, sous-secteurs non consolidés, PLF vs exécution). La phrase
  porte **le périmètre et le stade dans la question elle-même** ; on ne peut pas les oublier.
- « Une barre qui comprend tout » (Perplexity, Google) cache l'interprétation. Ici l'interprétation **est**
  l'interface (modèle Wolfram|Alpha « Interprétation : … / utiliser plutôt … ») : on voit ce que le site a
  compris, on corrige d'un geste.
- La phrase est lisible à voix haute, traduisible (EN : « How much does [education] cost [all government]
  in [2024] as [% of GDP] »), et sert de titre de page, de titre d'image partagée et de texte de citation.

### 1.3 Désambiguïsation par périmètre (le cœur de la fiabilité)

Quand une phrase libre est ambiguë entre sources (« la dette », « l'éducation », « le social »), le site ne
choisit pas en silence. La réponse s'ouvre sur **un sélecteur de lecture** :

```
« éducation » existe dans deux comptabilités différentes :
 ( ● ) Toutes administrations publiques — COFOG GF09, Eurostat, 1995-2024
 (   ) Budget de l'État — missions « Enseignement scolaire », « Recherche et enseignement supérieur »…, Direction du Budget, 2024-2026
 Les deux chiffres ne s'additionnent pas et ne se comparent pas directement. [Pourquoi ?]
```

La lecture par défaut = la plus large disponible (APU), l'autre reste à un geste. Sur grand écran, les deux
lectures peuvent être posées côte à côte, **chacune avec son propre titre de périmètre**, jamais dans le même
graphique.

### 1.4 Les pistes du porteur, challengées

| Piste | Verdict | Raison |
|---|---|---|
| **Recherche type Select2** (autocomplétion, multicritère) | **Transformée** | L'autocomplétion typée, oui. Le multi-select générique (une boîte où l'on empile des tags hétérogènes), non : il permet de composer des combinaisons absurdes (deux stades, trois unités) et ne dit pas *quel rôle* joue chaque tag. Remplacé par la phrase à emplacements typés, avec un combobox ARIA 1.2 maison (pas la lib Select2 : jQuery, accessibilité mobile médiocre, poids). |
| **Tags / questions qui défilent** | **Rejeté sous forme défilante, gardé en statique** | Le défilement automatique viole WCAG 2.2.2 (pause), se lit mal à 320 px, fait « template SaaS ». Gardé : 5-6 **questions-amorces** fixes, choisies parmi un vivier renouvelé à chaque chargement, chacune avec son **chiffre réel en aperçu**. Une amorce sans chiffre (lacune) est montrée comme telle : « Combien coûtent les 63 niches non chiffrées ? → Personne ne le publie. » |
| **Onglets thème / territoire / période / type d'analyse** | **Rejeté comme navigation, transformé en emplacements** | Ces quatre dimensions ne sont pas exclusives (on veut thème *et* territoire *et* période) : des onglets forcent à n'en voir qu'une. Elles deviennent les emplacements de la phrase. Seul usage d'onglets conservé : la **bascule de vue** à l'intérieur d'une réponse (Graphique · Tableau · Carte · Source), qui elle est bien exclusive. |
| **Comparateur universel** (pays, régions, villes, indicateurs, périodes) | **Gardé, avec garde de comparabilité** | Universel dans le geste (« + comparer » partout), pas dans le résultat : le site refuse de poser sur un même axe deux montants de sources, stades ou unités différents, et l'explique. Pays : après collecte Eurostat COFOG multi-pays. Villes : après collecte OFGL communes. |
| **Cartographie type « store locator »** | **Transformée** | Le bon morceau du store locator, c'est « je tape où j'habite → je trouve mon point » et la **liste synchronisée** avec la carte. On garde ça : saisie d'un code postal ou d'une commune → son département et sa région. On rejette le fond de carte zoomable à tuiles (lourd, inutile pour 101 polygones, problème d'accessibilité et de RGPD avec les fournisseurs de tuiles). Carte = choroplèthe statique SVG des départements/régions avec encarts outre-mer, **liste classée jumelle** toujours présente. |
| **Exploration guidée** | **Gardée, sous forme de « fils »** | Pas de récit éditorial qui affirme (CLAUDE.md : aucun texte factuel non sourcé). Un fil = une suite de 4-6 phrases-requêtes enchaînées avec des transitions qui *décrivent* (« même question, côté État »). Plus tard, après le cœur. |
| **Partage / export sourcé** | **Gardé, v1** | C'est ce qui fait voyager les chiffres vers TikTok, les rédactions et les mémoires de recherche. La source est imprimée dans l'objet exporté, pas à côté. |
| **Sources et méthodologie faciles d'accès** | **Gardé, renforcé** | Badge source à un geste de chaque chiffre (existe), popover court avant la page complète, et une section « Sources de cette réponse » en pied de chaque réponse. |

---

## 2. Catalogue des fonctionnalités UX

Notation 1-5. **U** = utilité pour les profils servis, **Cx** = complexité de réalisation, **VA** = valeur
ajoutée par rapport à l'existant ou aux sites concurrents. Données : *dispo* (en base), *à collecter*
(source exacte), *interface* (aucune donnée nouvelle).

### 2.1 Recherche et interprétation

| # | Fonctionnalité | Comment ça marche | Profils | U | Cx | VA | Données | Verdict |
|---|---|---|---|---|---|---|---|---|
| R1 | **Barre-phrase à emplacements typés** | Cf. § 1.2. Rendu serveur de la phrase depuis l'URL, chaque emplacement est un `<button>` ouvrant un sélecteur. Sans JS : la phrase reste un `<form>` de `<select>` (dégradation propre, l'existant). | tous | 5 | 3 | 5 | interface | **v1** |
| R2 | **Autocomplétion typée et groupée** | Suggestions regroupées par type avec icône-texte (« Département », « Fonction COFOG », « Mission », « Niche », « Agrégat OFGL », « Année », « Mot du lexique »). Index SQLite FTS5 construit au `make build` sur les libellés officiels FR et EN, les codes (`75`, `2A`, `GF09`, `P150`, code de dépense fiscale) et les noms des collectivités. Réponse < 50 ms, endpoint `/{lang}/api/suggest?q=`. | tous | 5 | 3 | 4 | dispo (nomenclatures, entités) | **v1** |
| R3 | **Réponse dans la liste** | La 1re suggestion affiche déjà le chiffre-titre et son badge (« Éducation · APU · 2024 · [montant réel issu d'Eurostat COFOG S13 GF09 2024] »). La moitié des questions est réglée sans charger de page. | N J C | 5 | 2 | 5 | dispo | **v1** |
| R4 | **Tolérance de saisie** | Sans accents, fautes d'une lettre, pluriels, sigles (IR, IS, TVA, RSA, APA, PCH), numéros de département, « Corse du sud » → `2A`. | N C | 4 | 2 | 3 | interface + table d'alias | **v1** |
| R5 | **Langage naturel → entités visibles (déterministe)** | Analyseur à règles : repère des mots-clés de vue (« combien », « part », « évolution », « plus que », « classement »), puis des entités par l'index R2, puis des années. Résultat **toujours** affiché en phrase-requête modifiable, avec « Vous avez écrit : … ». Si rien n'est reconnu : suggestions + lien lexique, jamais de réponse inventée. | N J C | 5 | 3 | 5 | `content/synonymes.yaml` (à écrire, relu) | **v1** |
| R6 | **Synonymes courants → catégories officielles** | « Cadeaux aux riches », « aides aux entreprises », « l'argent des chômeurs » → la catégorie officielle la plus proche (dépenses fiscales, mission « Travail et emploi », COFOG GF1005…) **avec la mention « Catégorie officielle la plus proche de votre recherche : … »**. Fichier versionné, chaque correspondance porte une justification (lien lexique). Neutralité : on ne reformule pas la question, on montre la catégorie. | N C J | 4 | 2 | 5 | `content/synonymes.yaml` | **v1** |
| R7 | **Sélecteur de lecture par périmètre** | Cf. § 1.3. Déclenché quand un terme a des correspondances dans ≥ 2 sources. | tous | 5 | 2 | 5 | dispo | **v1** |
| R8 | **Options impossibles affichées comme lacunes** | Dans chaque sélecteur, les combinaisons sans donnée sont visibles, barrées, avec la raison (non publié / non collecté / non chiffré) et le responsable. | tous | 5 | 3 | 5 | table `lacune` + matrice de disponibilité calculée au build | **v1** |
| R9 | **Zéro résultat utile** | « Rien sur *pouvoir d'achat* : ce site ne le collecte pas encore. Source officielle : INSEE [jeu exact]. » Liste tenue dans `content/non_collecte.yaml`. | N J | 4 | 1 | 4 | interface | **v1** |
| R10 | **Code postal / commune → mes collectivités** | Saisie « 33000 » ou « Pessac » → Gironde + Nouvelle-Aquitaine, puis réponse « Que dépense [Gironde] ». | N L | 5 | 2 | 4 | à collecter : COG INSEE (communes, départements, régions) + base officielle des codes postaux (La Poste, data.gouv.fr) | **v1** |
| R11 | **Géolocalisation** | Bouton « près de moi » (opt-in navigateur), conversion locale en département. | N | 2 | 3 | 2 | géométries IGN | **plus tard** (R10 suffit) |
| R12 | **Interprétation par LLM** (OpenRouter, modèle gratuit) | Uniquement quand R5 échoue. Sortie contrainte à un JSON d'identifiants d'entités existants, validée côté serveur ; affichée comme R5 avec la mention « interprétation automatique ». Le LLM ne produit **jamais** de chiffre ni de texte affiché. | N C | 3 | 3 | 3 | interface | **plus tard** (mesurer d'abord le taux d'échec de R5 sur de vraies requêtes) |
| R13 | **Recherche dans le lexique** | Les mots du lexique sont des entités de la barre (« déficit », « LFI », « épargne brute ») : la réponse est la définition citée + les chiffres qui l'utilisent. | N É | 4 | 1 | 3 | dispo | **v1** |

### 2.2 La page-réponse

| # | Fonctionnalité | Comment ça marche | Profils | U | Cx | VA | Données | Verdict |
|---|---|---|---|---|---|---|---|---|
| A1 | **Chiffre-titre + phrase-réponse générée** | Gabarit déterministe : « En [2024], [l'ensemble des administrations publiques] a dépensé [montant] pour [l'enseignement], soit [x % du PIB]. » Chaque valeur est un chiffre de la base avec son badge ; la phrase n'affirme rien d'autre. Gabarits traduits (gettext). | tous | 5 | 2 | 5 | dispo | **v1** |
| A2 | **Badges de lecture** | Sous le chiffre : périmètre · stade (Exécution / LFI / PLF / Comptes) · année · `provisoire` · `calculé par ce site`. Texte, pas couleur seule. | É J | 5 | 1 | 4 | dispo | **v1** |
| A3 | **Un seul visuel principal, choisi par la vue** | répartition → barres horizontales ou anneau ≤ 6 parts ; évolution → courbe ; classement → rangs ; carte → choroplèthe + liste ; comparaison → barres appariées ou petits multiples. | tous | 5 | 3 | 4 | dispo | **v1** |
| A4 | **Bascule de vue** Graphique · Tableau · Carte · Source | Onglets ARIA ; le tableau est le jumeau exact du graphique (existe déjà en `<details>`). « Carte » n'apparaît que si le périmètre est un ensemble de territoires. | É J | 5 | 2 | 3 | dispo | **v1** |
| A5 | **Modification sur place** | Changer année, unité, stade depuis la réponse sans retour à la recherche ; l'URL se met à jour (`history.replaceState` pour les petits réglages, `pushState` pour un changement de thème/périmètre). Rendu par fragments HTML serveur, pas de framework. | tous | 5 | 3 | 4 | interface | **v1** |
| A6 | **Frise d'années** | Rangée d'années touchables (pas de curseur glissant, imprécis au doigt) ; années provisoires marquées ; années absentes **visibles** et grisées. | N C | 4 | 2 | 3 | dispo | **v1** |
| A7 | **Trous visibles dans les graphiques** | Une année ou une valeur `nc` / `ε` / non publiée = interruption de la courbe + hachure + libellé, jamais une interpolation ni un zéro. | tous | 5 | 2 | 5 | dispo | **v1** |
| A8 | **« Pour bien lire » contextuel** | 1 à 3 notes maximum, **déclenchées par la phrase** (sous-secteurs non consolidés si périmètre = État ou local ; M52/M57 si fonction départementale ; intérêts dans GF01 si thème = dette ; comptes spéciaux si budget de l'État). Le reste en `<details>`. Remplace les blocs « À savoir » fixes actuels. | tous | 5 | 2 | 5 | `content/notes.yaml` (règles + texte relu) | **v1** |
| A9 | **Fil de nomenclature** | Mission › Programme › Action › Sous-action ; COFOG Division › Groupe ; chaque niveau touchable pour remonter. | É J | 4 | 1 | 3 | dispo | **v1** |
| A10 | **« Et maintenant ? »** | 3-5 phrases voisines, un emplacement changé à chaque fois, dans cet ordre de priorité : descendre d'un niveau · même thème autre périmètre · évolution · comparer (voisin, même niveau) · la lacune liée · le mot du lexique central. Chaque suggestion affiche son chiffre-aperçu. | N J C | 5 | 3 | 5 | dispo | **v1** |
| A11 | **Infobulles et panneau lexique** | Existe (infobulle). Ajout : toucher « Voir dans le lexique » ouvre un panneau latéral (feuille du bas sur mobile) sans quitter la réponse. | N | 4 | 2 | 3 | dispo | **v1** |
| A12 | **Repères d'échelle publiés** | « C'est beaucoup ? » : on n'invente pas de repère (« = 3 porte-avions »), on propose les **mesures publiées** (% du PIB, % du total, €/hab.) et la position dans la série (min/max de la série, signalé « calculé par ce site »). | N C | 4 | 2 | 4 | dispo | **v1** |
| A13 | **Euros constants** | Bascule « euros courants / constants ». | É | 4 | 3 | 3 | à collecter : indice des prix INSEE (IPC, série identifiée) ou déflateur du PIB ; calcul signalé | **plus tard** |
| A14 | **Base 100 / taux de variation** | Pour comparer des séries d'ordres de grandeur différents. Marqué « calculé par ce site ». | É J | 3 | 2 | 3 | dispo | **plus tard** |
| A15 | **Lecture animée de l'évolution** (barres qui courent, carte qui défile) | — | C | 2 | 3 | 1 | — | **rejeté** (spectaculaire, illisible, mauvais en accessibilité ; la frise A6 suffit) |

### 2.3 Comparer

| # | Fonctionnalité | Comment ça marche | Profils | U | Cx | VA | Données | Verdict |
|---|---|---|---|---|---|---|---|---|
| K1 | **« + comparer » sur tout chiffre** | Ajoute la phrase courante à un tiroir de comparaison (max 4 éléments, au-delà illisible à 320 px). | J É L | 5 | 2 | 4 | interface | **v1** |
| K2 | **Garde de comparabilité** | Avant d'afficher : même source, même stade, même unité, même périmètre de nature ? Sinon : affichage en **cartes séparées** côte à côte, chacune avec son titre de périmètre, et le bandeau « Ces chiffres ne se comparent pas directement : [raison] ». Jamais sur un même axe. | tous | 5 | 3 | 5 | métadonnées dispo (source, stade, unité) | **v1** |
| K3 | **Territoire vs territoires** | Un département contre la médiane (déjà calculée), contre les départements de sa région (v1), contre ses voisins (après géométries). | L N | 5 | 2 | 4 | dispo ; voisinage : à collecter (IGN Admin Express, adjacence calculée au build) | **v1** (région) / **plus tard** (voisins) |
| K4 | **Collectivités semblables** | Même strate de population. | L É | 4 | 3 | 4 | à collecter : populations légales INSEE (ne pas déduire la population de € ÷ €/hab.) | **plus tard** |
| K5 | **Thème vs thème** | « Dette vs éducation » dans un même périmètre et stade (COFOG GF0107 vs GF09 ; ou mission vs mission). | J C | 5 | 2 | 5 | dispo | **v1** |
| K6 | **Période vs période** | Deux années pointées sur la même série ; écart en valeur et en %, marqué calculé. | J É | 4 | 1 | 3 | dispo | **v1** |
| K7 | **Stade vs stade** | Exécution 2024 / LFI 2025 / PLF 2026 sur une mission : c'est **la** comparaison légitime du budget vert, et elle est rarement montrée. | É J | 4 | 2 | 4 | dispo | **v1** |
| K8 | **France vs autres pays** | COFOG multi-pays, en % du PIB. | É J C | 5 | 2 | 5 | à collecter : Eurostat `gov_10a_exp` pour les pays de l'UE (même jeu que l'actuel) | **plus tard — priorité n° 1 de collecte** |
| K9 | **Sommer une sélection** (« additionner ces 3 missions ») | — | — | 2 | 2 | 1 | — | **rejeté** (méthode inventée hors nomenclature ; seuls les totaux de nomenclature sont proposés) |

### 2.4 Carte

| # | Fonctionnalité | Comment ça marche | Profils | U | Cx | VA | Données | Verdict |
|---|---|---|---|---|---|---|---|---|
| M1 | **Choroplèthe départements / régions** | SVG statique simplifié (< 150 Ko), classes de valeur discrètes, encarts outre-mer à taille lisible, territoires sans donnée **hachurés** et listés. Toucher un territoire = sa fiche ; survol/focus = valeur + badge. | N L C | 4 | 3 | 4 | à collecter : IGN Admin Express COG (simplifié au build), Licence ouverte | **v1** |
| M2 | **Liste classée jumelle synchronisée** | La liste existante (`rank`) reste la vue primaire accessible ; sélection partagée avec la carte. | tous | 5 | 2 | 3 | dispo | **v1** |
| M3 | **Carte en tuiles (grille de carrés)** sur mobile | À 320 px, une choroplèthe géographique rend l'Île-de-France invisible ; une grille de 101 tuiles égales est lisible et touchable. À arbitrer avec la dataviz. | N C | 4 | 2 | 4 | interface (grille à dessiner une fois) | **v1 si validé par la dataviz** |
| M4 | **Communes / intercommunalités** | — | N L | 5 | 4 | 5 | à collecter : OFGL comptes des communes et des GFP | **plus tard** |
| M5 | **Fond de carte zoomable à tuiles** (Leaflet/OSM) | — | — | 1 | 3 | 1 | — | **rejeté** |

### 2.5 Partager, exporter, citer

| # | Fonctionnalité | Comment ça marche | Profils | U | Cx | VA | Données | Verdict |
|---|---|---|---|---|---|---|---|---|
| S1 | **Permalien d'état** | L'URL contient toute la phrase (§ 3.4) ; copier l'adresse suffit. Bouton « Copier le lien ». | tous | 5 | 1 | 4 | interface | **v1** |
| S2 | **Image partageable sourcée** | Rendu serveur PNG (format 4:5 et 9:16) : phrase-requête en titre, chiffre, visuel, **ligne de source imprimée** (éditeur, jeu, stade, date de collecte), URL courte du permalien, mention provisoire. Pas d'image sans source. | C J | 5 | 3 | 5 | interface | **v1** |
| S3 | **Aperçu Open Graph** dynamique | La même image sert d'aperçu sur X, Bluesky, LinkedIn, WhatsApp. | C J | 4 | 1 | 4 | interface | **v1** (vient avec S2) |
| S4 | **Citation prête à coller** | « [Montant] ([périmètre], [stade], [année]). Source : [éditeur], [jeu], via Comptes publics, [permalien]. » En FR ou EN. | J É | 5 | 1 | 4 | dispo | **v1** |
| S5 | **Export CSV avec provenance** | Colonnes : valeur, unité, entité, nomenclature, code, exercice, stade, provisoire, source, fichier, sha256, ligne, URL de collecte. Un fichier `LISEZMOI` en tête de l'archive. | É J | 5 | 2 | 5 | dispo | **v1** |
| S6 | **API JSON lecture seule** | Mêmes données que S5, mêmes URLs + `.json`. | É | 3 | 2 | 3 | dispo | **plus tard** |
| S7 | **Intégration (iframe)** | Pour les rédactions. | J | 3 | 3 | 3 | interface | **plus tard** |
| S8 | **Export XLSX / SVG** | — | É C | 2 | 2 | 2 | — | **plus tard** |

### 2.6 Mémoire et présentation

| # | Fonctionnalité | Comment ça marche | Profils | U | Cx | VA | Données | Verdict |
|---|---|---|---|---|---|---|---|---|
| E1 | **Épingles** | Épingler une réponse (pas un chiffre isolé, pour garder son contexte). Stocké en `localStorage`, partageable en un lien `/{lang}/epingles?r=…` qui liste les phrases (aucun compte). | J É P | 4 | 2 | 4 | interface | **v1** |
| E2 | **Fil de la session** | Les 5 dernières phrases visitées en bas de la recherche ouverte ; le bouton « retour » du navigateur fonctionne toujours (états d'URL propres). | J É | 3 | 1 | 3 | interface | **v1** (léger) |
| E3 | **Mode plateau / présentation** | `?presenter=1` : plein écran, chiffre géant, source toujours à l'écran, épingles en diapositives au clavier (← →), contraste renforcé, aucun survol nécessaire. | P J | 4 | 2 | 4 | interface | **plus tard** (v1.5, réutilise E1) |
| E4 | **Fils guidés** | Cf. § 1.4. | N P | 4 | 2 | 3 | `content/fils.yaml` | **plus tard** |
| E5 | **« Estimez avant de voir »** | Le lecteur place son estimation (part de l'éducation), puis voit le chiffre (modèle « You Draw It » du NYT). Pédagogique, non éditorial. | N P C | 3 | 3 | 3 | dispo | **plus tard** |
| E6 | **Comptes utilisateurs, tableaux de bord personnels** | — | — | 1 | 4 | 1 | — | **rejeté** |
| E7 | **Flux des nouveautés** (Atom) | Nouvelle collecte, lacune comblée, nouvelle lacune. | J É | 3 | 1 | 3 | dispo (dates de collecte) | **plus tard** |

### 2.7 Fondations (non optionnelles)

| # | Fonctionnalité | Comment ça marche | Profils | U | Cx | VA | Verdict |
|---|---|---|---|---|---|---|---|
| F1 | **Clavier complet** | `/` focalise la barre ; ↑↓ dans les suggestions, Entrée choisit, Échap ferme ; Tab parcourt les emplacements de la phrase ; ← → dans la frise d'années et les onglets de vue ; focus toujours visible. Combobox conforme ARIA APG. | tous | 5 | 2 | 4 | **v1** |
| F2 | **Lecteurs d'écran** | Tableau jumeau pour tout graphique (existe) ; `aria-live="polite"` annonce « 12 suggestions » puis le chiffre-titre après changement ; la phrase-requête est un vrai texte lisible. | tous | 5 | 2 | 4 | **v1** |
| F3 | **FR/EN partout** | Recherche sur les libellés des deux langues (COFOG EN officiel) ; libellés FR seuls marqués « FR » (existe) ; permaliens équivalents (hreflang). | tous | 5 | 2 | 4 | **v1** |
| F4 | **320 px** | Phrase-requête qui revient à la ligne, emplacements ≥ 44 px de haut, aucun défilement horizontal hors tableaux. | tous | 5 | 2 | 3 | **v1** |
| F5 | **Performance** | Rendu serveur, JS < 60 Ko sans framework, premier chiffre affiché < 1 s en 4G ; police : 2 familles, sous-ensembles. | tous | 5 | 2 | 3 | **v1** |
| F6 | **Mesure d'audience sans cookie** | Compteurs agrégés côté serveur (requêtes R5 non comprises = matière pour R6/R12). Pas de bandeau cookies car pas de cookie. | — | 3 | 1 | 3 | **v1** |
| F7 | **Mouvement réduit** | `prefers-reduced-motion` respecté ; aucune animation porteuse de sens. | tous | 4 | 1 | 2 | **v1** |

### 2.8 Rejetés explicitement (et pourquoi)

- **Chatbot conversationnel** : produit des phrases non sourcées, invérifiables, et une interface qui ressemble à tous les autres sites. La phrase-requête donne la même facilité d'entrée sans le risque.
- **Verdict « vrai / faux »** sur une affirmation : éditorialisation ; on donne les chiffres, les périmètres et les lacunes, le lecteur conclut.
- **« Où vont mes impôts » personnalisé** (je saisis mon revenu, j'obtiens « 312 € pour la défense ») : exige d'affecter des recettes à des dépenses, ce qu'aucune nomenclature publiée ici ne fait → méthode inventée. Réouvrable seulement si une ventilation **officielle** est publiée et collectée.
- **Constructeur de graphiques libre** (axes, séries, agrégations au choix, façon Flourish) : il permet précisément les additions et mélanges interdits.
- **Bandeaux de statistiques d'accueil** (« 530 000 montants · 12 sources ») : remplissage, détesté par le porteur ; l'existant est à retirer.
- **Ticker / carrousel automatique**, fonds animés, parallaxe : cf. § 1.4.

---

## 3. Architecture de l'information

### 3.1 Les écrans

```
Accueil (hero)                         /{lang}/
 └─ Page-réponse                       /{lang}/r?…            ← l'écran où l'on passe 90 % du temps
     ├─ vue Comparaison (même écran)   /{lang}/r?…&vs=…
     ├─ vue Carte (même écran)         /{lang}/r?…&vue=carte
     └─ Source d'un chiffre            /{lang}/montant/{id}    (existe)
 Fiches entité                         /{lang}/territoire/{code} · /fonction/{code} · /mission/{code}
                                       /niche/{code} · /indicateur/{clé}
 Ce qui manque (lacunes)               /{lang}/lacunes[?responsable=…&source=…]
 Lexique                               /{lang}/lexique · /{lang}/lexique/{terme}
 Méthode et sources                    /{lang}/methode · /{lang}/source/{id}
 Épingles                              /{lang}/epingles?r=…
```

- **Pas d'écran « comparateur » ni « carte » séparé** : ce sont des vues de la page-réponse. Un seul concept à apprendre.
- **Fiche entité** = la page-réponse « par défaut » d'une entité (un département : dépenses totales €/hab., répartition par fonction, évolution, position parmi les départements, lacunes propres). Elle sert de point d'atterrissage pour les moteurs de recherche externes (« budget département Gironde ») et doit donc avoir une URL stable et lisible.
- **Les pages thématiques actuelles** (`depenses-publiques`, `budget-etat`, `depenses-fiscales`, `territoires`) deviennent des **phrases préréglées** : redirection 301 vers la phrase équivalente, en conservant les paramètres existants (`secteur`, `annee`, `fonction`, `niveau`, `indicateur`, `unite`). Les liens déjà partagés ne cassent pas.

### 3.2 Navigation

- **En-tête** (toutes pages sauf l'accueil) : marque · **barre-phrase compacte** (repliée en une ligne lisible, s'ouvre au toucher) · FR/EN · menu.
- **Menu** (tiroir sur mobile, ligne sur desktop) — 5 entrées, pas plus : *Explorer* (4 portes : Toutes les administrations · Budget de l'État · Niches fiscales · Régions et départements) · *Ce qui manque* · *Lexique* · *Méthode et sources* · *Épingles* (si non vide).
- **« Ce qui manque » reste au premier niveau** du menu : c'est un parti pris du produit, pas une page technique.
- **Pied de page** : la règle « rien sans source » en une phrase (existe), licence, date de dernière collecte.

### 3.3 Hiérarchie de la page-réponse (ordre mobile, de haut en bas)

1. **Phrase-requête** (emplacements modifiables), collante en haut, repliée au défilement.
2. **Sélecteur de lecture** (R7) si la phrase est ambiguë.
3. **Chiffre-titre** + badge source · **phrase-réponse** · badges de lecture (périmètre, stade, année, provisoire, calculé).
4. **Lacune bloquante** si la réponse est partielle (« 63 niches non chiffrées ne sont pas dans ce total ») — **ici, pas en bas de page**.
5. **Visuel principal** + bascule Graphique · Tableau · Carte · Source + frise d'années.
6. **Pour bien lire** : 1-3 notes déclenchées.
7. **Et maintenant ?** : 3-5 phrases voisines avec chiffre-aperçu.
8. **Détail** : sous-niveaux de nomenclature, autres lectures (périmètres), tableau complet.
9. **Actions** : Copier le lien · Image · Citation · CSV · Épingler · + Comparer (sur mobile, une barre d'actions fixe en bas à 4 icônes-texte : Partager · Exporter · Épingler · Comparer).
10. **Sources de cette réponse** : liste dédoublonnée des fichiers (éditeur, jeu, date, sha256 court) → `methode#src-…`.

Sur desktop (≥ 1024 px) : 1 en haut ; 3-4-5 dans la colonne principale ; 6-7 dans une colonne latérale qui reste visible ; 8-10 en dessous.

### 3.4 États d'URL

Une URL = une phrase. Paramètres courts, stables, lisibles, identiques en FR et EN (seul le préfixe de langue change) :

| Param | Valeurs | Exemple |
|---|---|---|
| `vue` | `montant` (défaut) · `part` · `evolution` · `classement` · `carte` · `comparer` | `vue=evolution` |
| `theme` | `<nomenclature>:<code>` : `cofog:GF09`, `etat:M-150` (mission), `etat:P-150` (programme), `niche:<code>`, `impot:IR`, `ofgl:<clé agrégat>`, `m57:<fonction>` | `theme=cofog:GF0107` |
| `qui` | `apu` (S13) · `etat-apu` (S1311) · `local` (S1313) · `secu` (S1314) · `budget-etat` · `reg:<code>` · `dep:<code>` · `deps` · `regs` | `qui=dep:33` |
| `an` | année ; `an=1995-2024` pour une plage | `an=2024` |
| `stade` | `execution` · `lfi` · `plf` · `compte` | `stade=lfi` |
| `unite` | `meur` · `pct-total` · `pct-pib` · `eur-hab` · `eur` | `unite=pct-pib` |
| `vs` | une ou plusieurs phrases encodées `theme|qui|an` séparées par `,` (max 3) | `vs=cofog:GF09` |
| `lecture` | choix explicite du périmètre quand R7 a proposé plusieurs lectures | `lecture=budget-etat` |
| `v` | millésime des données (date de collecte) ; ajouté **seulement** au lien copié, à l'export et à l'embed, pour figer la vue citée | `v=2026-10-26` |
| `q` | texte libre saisi (conservé pour « Vous avez écrit : … », jamais indexé) | |

Règles : paramètres absents = valeurs par défaut documentées (dernière année publiée, stade le plus définitif, unité publiée) **et la page affiche toujours les valeurs effectives dans la phrase** (jamais de défaut invisible) ; URL canonique triée ; `replaceState` pour unité/année, `pushState` pour thème/périmètre/vue ; toute URL est rendue côté serveur (partage, robots, sans JS). Aucune donnée personnelle dans l'URL (le code postal saisi en R10 est converti en `qui=dep:…` avant navigation).

---

## 4. Parcours utilisateurs

### P1 — Journaliste, mobile, 60 s : « L'État dépense plus pour la dette que pour l'éducation »
1. (0 s) Ouvre le site depuis un lien, tape dans le hero : `dette plus que éducation`.
2. (5 s) R5 reconnaît une vue *comparer* et deux thèmes. Le sélecteur de lecture (R7) s'affiche : *Budget de l'État* (missions « Engagements financiers de l'État » / programme charge de la dette vs « Enseignement scolaire » + « Recherche et enseignement supérieur ») ou *Toutes administrations* (COFOG GF0107 « Opérations concernant la dette publique » vs GF09 « Enseignement »). Elle choisit *Budget de l'État*, car l'affirmation dit « l'État ».
3. (15 s) Réponse : barres appariées, stade *Exécution 2024* par défaut, deux chiffres avec badges [montants réels issus du budget vert PLF 2026, colonne exécution 2024]. Note déclenchée : « La mission Enseignement scolaire ne couvre pas tout l'effort d'éducation ; la charge de la dette est en intérêts, pas en remboursements » (texte relu, lien lexique).
4. (30 s) Touche le stade → *PLF 2026* : l'écart change ou non, elle le voit. Touche « Et maintenant ? » → *même question, toutes administrations* : deuxième lecture, autre ordre de grandeur, bandeau « ne se compare pas à la lecture précédente ».
5. (50 s) « Citation » → copie le texte avec les deux périmètres et le permalien. Elle publie « l'affirmation dépend du périmètre » avec les deux chiffres sourcés.

### P2 — Créatrice TikTok : un visuel sourcé de sa région
1. Hero, tape `occitanie`. R3 affiche dans la liste « Occitanie · région · dépenses totales 2025 · [montant réel issu de l'OFGL] ». Entrée.
2. Fiche territoire. Elle veut « par habitant » : touche l'emplacement unité → `€/hab.`.
3. « Et maintenant ? » propose *Occitanie parmi les régions* → classement + carte (M1/M3) avec l'Occitanie surlignée.
4. « Image » → format 9:16. Aperçu : phrase-requête en titre, carte, chiffre, pied « Source : OFGL, comptes consolidés des régions, collecté le … · comptespublics…/r?… ». Elle ne peut pas retirer la ligne de source (elle peut choisir le fond clair/sombre).
5. Elle cherche ensuite « à quoi elle dépense » : le sélecteur montre *Répartition par fonction* barré « non publié pour les régions par l'OFGL / DGFiP ». Elle en fait une deuxième vidéo, sur la lacune : l'image « Ce qui manque » est elle aussi exportable.

### P3 — Chercheuse : exporter une série longue
1. Tape `GF0702` (code COFOG) : reconnu directement comme sous-fonction « Services hospitaliers ».
2. Phrase réglée : vue *évolution*, `qui=apu`, `an=1995-2024`, `unite=pct-pib`. Années 2023-2024 marquées provisoires sur la courbe.
3. Change `qui` → *Sécurité sociale (S1314)* puis ajoute `+ comparer` *Administrations locales (S1313)* : petits multiples, avec la note « sous-secteurs non consolidés : leur somme dépasse le total APU ».
4. « CSV » → archive avec les deux séries, une ligne par observation, colonnes de provenance (fichier, sha256, ligne). Elle cite le permalien dans sa note de bas de page ; le lien rejouera la même phrase dans deux ans (version des données affichée : date de collecte).

### P4 — Citoyen : « Qu'est-ce que mon département fait de mes impôts ? »
1. Hero, tape `ce que fait mon département de mes impôts 69`. R5 : `69` → Rhône **et** Métropole de Lyon (deux collectivités sur ce territoire) : le site propose les deux, avec une phrase du lexique sur la Métropole.
2. Il choisit Rhône. R6 a repéré « mes impôts » : message « Les comptes publiés ne relient pas un impôt à une dépense. Voici ce que dépense le département, et ce qu'il perçoit. » Deux réponses : *Répartition par fonction* (M57, avec la note M52/M57) et *Recettes fiscales* (agrégat OFGL publié).
3. Survole « action sociale » : infobulle lexique ; touche → la fonction en détail, puis « Et maintenant ? » → *Rhône comparé aux départements de sa région, en €/hab.*
4. Il découvre la médiane « calculée par ce site » et la liste des départements sans donnée pour cette nomenclature (pas cachés).

### P5 — Élue départementale : se comparer à ses voisins
1. Tape `Dordogne`, fiche entité. Touche « + comparer » sur *Dépenses d'investissement €/hab.*
2. Le tiroir de comparaison propose : *Départements de Nouvelle-Aquitaine* (v1), *Voisins* (après géométries), *Départements de taille comparable* (après populations INSEE, grisé « non collecté » d'ici là).
3. Vue *classement* sur 12 départements, frise 2012-2025, médiane du groupe. Elle bascule *Carte*.
4. Épingle trois réponses (investissement, dette, épargne brute), ouvre `epingles`, lance le mode plateau (v1.5) en commission ; chaque diapositive garde sa source à l'écran.

### P6 — Économiste : les niches fiscales non chiffrées
1. Tape `niches IS` → vue *classement* des dépenses fiscales rattachées à l'impôt sur les sociétés, stade PLF 2026 (prévision), regroupées par `code_depense`.
2. Lacune bloquante en tête : « N dépenses de cette liste sont *non chiffrées* (nc) ou *< 0,5 M€* (ε) : elles ne sont pas des zéros et ne sont pas dans le total. » Les `nc` apparaissent dans le classement en bas, en ligne hachurée, avec la Direction de la législation fiscale comme responsable.
3. Bascule stade : exécution 2024 / LFI 2025 / PLF 2026 (K7). Export CSV, les `nc` y sont explicites (`valeur` vide, `statut=nc`).

### P7 — Question politique : « combien coûtent les cadeaux aux milliardaires ? »
1. R6 : « Catégorie officielle la plus proche de votre recherche : *dépenses fiscales* (lexique : définition citée). Ce site ne classe pas les dépenses selon leurs bénéficiaires par niveau de fortune : cette donnée n'est pas publiée dans les sources collectées. »
2. Réponse : total des dépenses fiscales chiffrées + nombre de non chiffrées, par impôt. Aucun mot ajouté au-delà des catégories officielles. La lacune « répartition par bénéficiaire » figure dans `lacunes` si une source officielle pertinente est identifiée (à instruire par l'économiste).

### P8 — Enseignant de SES, vidéoprojecteur
1. Prépare 5 épingles la veille (part de la protection sociale dans la dépense APU ; évolution 1995-2024 ; comparaison avec un pays européen quand K8 existera ; dépenses fiscales ; une lacune).
2. En classe, « Estimez avant de voir » (plus tard) sur la première, puis mode plateau. Les élèves rouvrent le lien des épingles sur leur téléphone : même état, même chiffres.

---

## 5. Le hero plein écran

### 5.1 La première seconde

Plein cadre (`100svh`), rendu serveur, aucune requête JS nécessaire pour l'afficher. On voit, dans cet ordre de lecture :

1. **Une question en très grand**, en serif éditoriale, qui est aussi une vraie phrase-requête du site, tirée au sort parmi un vivier relu : *« Combien la France dépense-t-elle pour l'enseignement ? »*. Sous elle, **sa réponse en chiffre** [montant réel issu d'Eurostat COFOG, S13, GF09, dernière année] avec son badge source et la mention de l'année/provisoire. La première seconde montre donc ce que fait le site : *une question, un chiffre, une source*.
2. **En face, à poids égal, un trou** : *« Combien coûtent les dépenses fiscales que l'État ne chiffre pas ? »* — *« Non publié. 63 dépenses. Responsable : Direction du Budget. »* [nombre réel issu de la table `lacune`]. Le chiffre et le trou côte à côte = la promesse du site en une image, impossible à confondre avec un autre site (test anti-générique).
3. **La barre-phrase**, large, au centre optique, avec un texte d'invite qui est une question réelle (« Essayez : *dette ou éducation, qui coûte le plus à l'État ?* ») et le raccourci `/` affiché sur desktop.
4. **5 questions-amorces** sous la barre, en lignes de texte (pas des cartes), chacune suivie de son chiffre-aperçu ou de sa mention « non publié ». Elles couvrent les 4 familles de données + 1 lacune, et changent à chaque chargement.
5. En bas du cadre, une ligne discrète : « Sources : Direction du Budget · INSEE · Eurostat · OFGL — dernière collecte le … » (lien Méthode). Pas de bandeau de statistiques.

La matière visuelle (photo, papier, document officiel, typographie) est l'affaire de la DA ; contrainte UX : le fond ne porte aucune information, n'anime rien, et garde un contraste AA sur la barre et les chiffres.

### 5.2 Sans scroller, on peut

- Taper une question (Entrée = meilleure interprétation ; la liste montre déjà les chiffres, R3).
- Toucher la question géante, son chiffre, le trou, ou une amorce → page-réponse.
- Toucher le badge source du chiffre → popover de provenance, sans quitter l'accueil.
- Changer de langue ; ouvrir le menu.
- Taper un code postal (« 33000 ») → sa collectivité.

### 5.3 Comportement mobile (320-430 px)

- La question géante passe à ~2rem, 3-4 lignes maximum ; le chiffre et le trou s'empilent (chiffre d'abord), chacun sur ≤ 3 lignes.
- La barre est dans la moitié basse de l'écran (zone du pouce). Au toucher, elle s'ouvre en **feuille plein écran** : champ en haut, clavier en bas, suggestions entre les deux, fil de session (E2) quand le champ est vide, bouton « Fermer » explicite.
- Amorces : 3 visibles, liste verticale (jamais de défilement horizontal) ; « Plus de questions » révèle les 2 autres.
- Le hero ne dépasse pas l'écran : ce qui ne tient pas descend sous le pli, pas l'inverse.

### 5.4 Un geste jusqu'à la première réponse

- Geste 1 = toucher une amorce, la question géante ou le chiffre → page-réponse complète (rendu serveur, < 1 s).
- Ou geste 1 = taper + Entrée ; même la frappe seule donne la réponse dans la liste (zéro page chargée).
- La page-réponse s'ouvre **avec la phrase visible en tête** : le lecteur apprend la grammaire du site en lisant sa propre question.

### 5.5 Sous le pli (accueil)

Les 4 portes d'exploration (Toutes les administrations · Budget de l'État · Niches · Régions et départements), chacune = un titre, une phrase de description du jeu de données, une phrase-requête d'entrée — **pas de cartes numérotées ni d'icônes**. Puis « Ce qui manque » (les 3 lacunes les plus récentes). Puis les trois règles (existe), en une ligne chacune avec lien Méthode.

---

## 6. Garde-fous de simplicité

### 6.1 Ce qu'on refuse d'ajouter

- Un second concept d'interaction : tout passe par la phrase-requête et la page-réponse. Pas de « mode expert », pas de tableau de bord, pas d'écran comparateur à part.
- Plus de **5 emplacements** dans la phrase, plus de **4 éléments** comparés, plus de **5 suggestions** « et maintenant ? », plus de **3 notes** « pour bien lire » visibles, plus d'**un visuel principal** par réponse.
- Tout réglage qui permet une addition, un mélange de stades ou d'unités hors nomenclature.
- Animation porteuse de sens, défilement automatique, parallaxe, carrousel.
- Comptes, notifications, cookies, pop-ups.
- Tout texte d'interface qui affirme un fait non issu d'un chiffre de la base (règle CLAUDE.md), y compris dans les amorces et les notes.
- Toute fonctionnalité dont la donnée n'est pas collectée : l'emplacement existe, grisé « non collecté — source : … », mais on ne bricole pas d'approximation.

### 6.2 Règle de divulgation progressive : trois couches, un geste entre chacune

| Couche | Contenu | Doit tenir |
|---|---|---|
| **1. Réponse** | Phrase-requête, chiffre-titre, badge source, phrase-réponse, badges de lecture, lacune bloquante éventuelle | dans le premier écran mobile (320 × 568) |
| **2. Lecture** | Visuel, frise, « pour bien lire », « et maintenant ? » | un défilement |
| **3. Preuve** | Tableau complet, sous-niveaux, autres périmètres, ligne brute, méthode, sha256 | un toucher (onglet *Tableau* / *Source*, `<details>`, page `montant`) |

Test de validation : un néophyte doit pouvoir s'arrêter à la couche 1 avec une réponse juste ; un économiste doit pouvoir atteindre la couche 3 en ≤ 2 gestes depuis n'importe quel chiffre.

### 6.3 Chaque chiffre garde son lien source, sans encombrer

- **Marque source unique et constante** : le badge `source` actuel devient une petite marque typographique attachée au chiffre (forme à définir par la DA), toujours au même endroit, toujours un lien, cible tactile ≥ 24 px (WCAG 2.5.8) sans élargir la ligne.
- **Popover court au premier toucher** (éditeur · jeu · stade · année · ligne n° · collecté le) → « Voir la ligne d'origine » ouvre `montant/{id}`. Pas de sortie de page pour vérifier.
- **Dans les graphiques** : la source de chaque point est dans l'infobulle et dans le tableau jumeau ; le graphique lui-même ne porte qu'une ligne de source en pied (« Eurostat, COFOG, collecté le … »).
- **Chiffres calculés** (parts, médianes, écarts) : marque distincte « calculé » + popover qui liste les chiffres sources utilisés (`provenance?ids=…`, existe).
- **Pied de réponse** : « Sources de cette réponse », dédoublonnées.
- **Exports** : la source est dans l'objet (image, CSV, citation), jamais seulement à côté.
- Contrôle automatique : un test échoue si un nombre rendu dans une page-réponse n'est pas suivi d'une marque source (extension du test lexique existant).

---

## Ce que je demande aux autres spécialistes

**À l'économiste**
1. Valider la **table des lectures** (R7) : pour chaque terme ambigu courant (dette, éducation, santé, social, sécurité, culture, aides aux entreprises, retraites), les entités exactes dans chaque source et la lecture par défaut.
2. Rédiger et sourcer les **notes déclenchées** (A8) et leurs règles de déclenchement ; dire lesquelles sont indispensables en couche 1.
3. Écrire la **matrice de comparabilité** (K2) : quelles paires source × stade × unité × périmètre sont comparables sur un même axe, lesquelles seulement côte à côte, lesquelles jamais.
4. Arbitrer les **synonymes courants → catégories officielles** (R6), notamment les questions politiques (P7), et dire quand répondre « pas de catégorie officielle ».
5. Prioriser les collectes : Eurostat multi-pays (K8), COG + codes postaux (R10), IGN (M1), populations légales (K4), IPC/déflateur (A13), communes OFGL (M4).

**Au directeur artistique**
1. La **matière du hero** et le face-à-face *chiffre / trou* : comment le trou a autant de présence que le chiffre sans couleur d'alerte.
2. La **phrase-requête** comme objet typographique : distinguer les emplacements modifiables du texte fixe sans pastilles « tags » génériques, lisible à 320 px et au clavier (focus).
3. La **marque source** et la marque « calculé », discrètes mais reconnaissables à l'œil nu, et le traitement des badges de stade (Exécution / LFI / PLF) et « provisoire ».
4. Le gabarit des **images partageables** 4:5 et 9:16 : identité forte, ligne de source non amovible et lisible sur un téléphone.

**Au spécialiste dataviz**
1. La **table vue → visuel** (A3) avec ses limites (nombre de parts, de séries, de territoires) et le comportement à 320 px.
2. Le **rendu des lacunes** dans chaque type de graphique (courbe interrompue, barre hachurée, territoire hachuré, `nc` dans un classement) et en tableau.
3. **Carte géographique ou carte en tuiles** sur mobile (M3), encarts outre-mer, classes de valeur.
4. Le **comparateur** : barres appariées, petits multiples ou cartes séparées selon le verdict de comparabilité, et comment rendre visible « pas le même axe ».
5. Les graphiques qui **tiennent dans une image partagée** sans perdre leur source, et ceux qui doivent être refusés à l'export.
