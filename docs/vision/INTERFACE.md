# Interface : un site pour les 8 profils validés

2026-10-28. Les profils de `USAGES.md` §1 sont validés par le user. Constat de départ, de sa part : « en tant que
citoyen curieux, je suis perdu ». Ce document dit pourquoi, puis propose une interface où chaque profil trouve sa porte
sans que le site change d'outil selon le public.

---

## 1. Pourquoi le citoyen curieux est perdu (tour fait le 2026-10-28, téléphone 375 px)

| Ce qu'il voit | Pourquoi ça perd |
|---|---|
| L'accueil s'ouvre sur « Où va la dépense publique ? », puis sur deux réglages (« Qui dépense ? » en 4 secteurs, « Unité » en 3 choix) **avant** le moindre chiffre | Il n'a pas forcément cette question ; on lui demande de choisir entre « administrations centrales » et « sécurité sociale » sans lui avoir dit ce que c'est |
| Le menu : 14 liens en 3 colonnes (« Solde et dette », « Contexte institutionnel », « Tableau de travail », « Dépenses fiscales »…) | Des noms d'outils et de jeux de données, pas des choses qu'on veut faire ; aucun ordre de lecture |
| Les libellés officiels bruts : « Services généraux des administrations publiques », « Production marchande, production pour usage final propre… » | Ils sont justes (et doivent rester), mais rien ne dit en mots simples de quoi il s'agit avant de les lire |
| Le constructeur s'ouvre sur un titre « Total » et une source « Comptes nationaux, par fonction » | « Total » de quoi ? Les choix sont rangés par jeu de données, pas par ce qu'on cherche |
| Aucune entrée « j'ai entendu un chiffre », « ma commune », « je débute » | Les trois raisons les plus probables de sa venue (`USAGES.md` §1) n'ont pas de porte |
| Les notions (périmètre, solde, dette) sont dans le lexique, page alphabétique | Il faut savoir quoi chercher pour les trouver |

Ce qui marche et qu'on garde : chaque chiffre a sa source, la phrase descriptive générée, la carte en cases, les
maquettes 3D, le lexique en infobulle, la recherche Ctrl K.

## 2. Le principe

1. **On entre par ce qu'on veut faire, pas par la source.** Cinq verbes couvrent les 8 profils : *comprendre*,
   *vérifier*, *situer* (ma collectivité), *explorer* (composer sa vue), *réutiliser* (télécharger).
2. **Un seul outil, trois profondeurs.** Lire (une phrase, un chiffre, une figure) → explorer (les 5 choix du
   constructeur) → les données (lignes sources, CSV, base). Chaque page commence au premier niveau et donne un lien vers le
   suivant ; personne n'est obligé de choisir un profil.
3. **D'abord des mots simples, ensuite le libellé officiel.** Chaque page et chaque bloc commencent par une question en
   langage courant écrite par le site (« Combien l'ensemble des administrations dépense-t-il en un an ? »), puis le
   chiffre avec son libellé officiel inchangé et sa source. Les questions décrivent ce qui est affiché ; elles
   n'affirment rien sur le monde (règle de neutralité, `USAGES.md` §6).

## 3. La structure proposée

### 3.1 Menu : 5 entrées au lieu de 14 liens

**Comprendre · Vérifier · Ma collectivité · Explorer · Données**

Les pages actuelles ne disparaissent pas : elles sont rangées sous ces entrées (tableau du §4).

### 3.2 Accueil

De haut en bas, sur téléphone :

1. **Une phrase** : ce qu'est le site (« Les comptes publics français, tels que publiés : chaque chiffre renvoie à sa
   source »).
2. **Une seule barre de recherche**, large : « Un mot, un territoire, un chiffre : dette, Gironde, TVA, 3 000 milliards ».
   C'est la palette Ctrl K actuelle, sortie de l'en-tête.
3. **Quatre chiffres repères**, dernière année publiée, en % du PIB : recettes, dépenses, solde, dette des
   administrations publiques (gov_10a_main, gov_10dd_edpt1). Chacun a sa source et un lien « Qu'est-ce que c'est ? »
   vers l'étape du parcours qui l'explique.
4. **Les cinq portes**, chacune avec une ligne qui dit ce qu'on y trouve et ce qu'on en emporte :
   - *Comprendre les bases* : 6 étapes courtes, de « qui sont les administrations publiques » à « la dette » ;
   - *Vérifier un chiffre entendu* : saisir un montant ou un pourcentage, voir les chiffres publiés qui s'en approchent ;
   - *Ma région, mon département* : saisir un nom, voir sa fiche ;
   - *Composer ma propre vue* : le constructeur ;
   - *Télécharger les données* : CSV, JSON, base SQLite, méthode.
5. **Plus bas, la carte de la dépense** actuelle, comme exemple de ce qu'on peut lire, sans réglages ouverts par défaut
   (les réglages « qui » et « unité » se déplient).

### 3.3 Comprendre : un parcours de 6 étapes

Une étape = une question en mots simples, une figure, la phrase générée, la définition officielle citée, « étape
suivante ». Les figures existent presque toutes déjà.

| Étape | Question | Figure (existante ou à faire) | Notion (`USAGES.md` §3) |
|---|---|---|---|
| 1 | Qui sont les administrations publiques ? | Ensembles emboîtés : État et administrations centrales, collectivités locales, sécurité sociale (à faire, sans additionner) | Périmètre |
| 2 | Combien entre, combien sort ? | Recettes, dépenses, solde (3D existante) | Recettes, dépenses, solde |
| 3 | D'où vient l'argent ? | Anneau des recettes (page existante) | Catégories de recettes |
| 4 | Où va l'argent ? | Carte en cases (accueil actuel) | Fonctions COFOG |
| 5 | Qu'est-ce que la dette ? | Déficit d'une année et dette en cours, côte à côte (3D existante) | Flux et stock |
| 6 | Le budget de l'État, c'est la même chose ? | Budget de l'État face aux dépenses de toutes les administrations, avec les stades projet, loi, exécution | Périmètre, stades |

Chaque étape propose aussi « Voir ce chiffre dans le temps » (constructeur préréglé) : le passage vers l'exploration.

### 3.4 Vérifier un chiffre (nouveau)

Formulaire en une ligne : *un nombre* (« 3 000 milliards », « 5,8 % ») + *un mot facultatif* (« dette », « éducation »)
+ *une année facultative*. Réponse : les valeurs publiées les plus proches, chacune avec ce qu'elle mesure (périmètre,
unité, stade, année) et sa source. Le site ne dit jamais « vrai » ou « faux » : il montre ce qui est publié et en quoi
cela diffère du chiffre saisi (périmètre, unité, année : « valeur publiée la plus proche : dette de l'ensemble des
administrations publiques, en euros courants, année N »). Pour le journaliste, le citoyen, les associations.

### 3.5 Ma collectivité

La page Collectivités actuelle, avec une recherche par nom en tête, puis la fiche. Les communes ne sont pas chargées :
la page le dit (lien vers la lacune) au lieu de laisser chercher en vain.

### 3.6 Explorer (le constructeur)

- Les sources renommées par ce qu'elles contiennent : « Dépenses par fonction », « Recettes, dépenses, solde, dette »,
  « Régions et départements » ; le nom du jeu reste en petit.
- Le titre dit toujours de quoi on parle : jamais « Total » seul (« Dépenses, toutes fonctions »).
- **Points de départ** en tête, décrits par leur forme : « Une série depuis 1995 », « Classer les départements »,
  « Comparer les administrations », « Un budget entre projet, loi et exécution ».
- Les étapes 4 et 5 (unité, forme) repliées par défaut sur téléphone, avec le choix courant visible.
- Le tableau de travail (`/comparer`) reste accessible depuis l'étape 5.

### 3.7 Données

Méthode et sources, données non disponibles, lexique, exports, base SQLite téléchargeable, API documentée (à faire).
Pour le chercheur et le développeur ; c'est aussi la preuve pour tous les autres.

## 4. Chaque profil, sa porte

| Profil | Porte d'entrée | Ce qu'il emporte | Pages |
|---|---|---|---|
| Citoyen curieux | Accueil → chiffres repères → Comprendre ; ou Vérifier | Une phrase juste, un chiffre sourcé | Parcours, Vérifier, carte |
| Élève, étudiant, enseignant | Comprendre (parcours complet) → Explorer | Figure citable, définition, série | Parcours, constructeur, export image |
| Journaliste, vérificateur | Vérifier, recherche | Chiffre, source, date, lien permanent | Vérifier, constructeur |
| Élu, agent de collectivité | Ma collectivité | Fiche, comparaison, tableau exportable | Collectivités, tableau de travail |
| Parlementaire, collaborateur | Explorer → budget de l'État ; Contexte | Tableaux par mission et stade | Budget de l'État, contexte, tableau de travail |
| Association, syndicat, cercle | Vérifier, Explorer | Graphique + source, série longue | Constructeur, exports |
| Chercheur, économiste | Données, Explorer | CSV/JSON, provenance, méthode | Données, méthode, lacunes |
| Développeur, réutilisateur | Données | Base, API, licences | Données |

Rangement des pages actuelles : Comprendre = parcours (avec `/comprendre`, `/recettes-publiques`, l'accueil-carte,
`/depenses-publiques`, `/budget-etat`, `/depenses-fiscales`) ; Vérifier = nouveau + recherche ; Ma collectivité =
`/territoires` ; Explorer = `/serie`, `/comparer`, `/contexte` ; Données = `/methode`, `/lacunes`, `/lexique`,
`/source`.

## 5. Ce que ça demande en données

Rien de nouveau pour 3.1 à 3.3 et 3.5 à 3.7. Vérifier (3.4) se contente des montants déjà chargés. Hors de portée
sans nouvelle collecte : la recherche par code postal et les communes (COG INSEE, OFGL communes), les euros constants
(déflateur).

## 6. Ordre de construction proposé

1. Menu à 5 entrées et accueil (§3.1, §3.2).
2. Parcours Comprendre, 6 étapes (§3.3).
3. Constructeur : libellés, titre, points de départ, repli (§3.6).
4. Vérifier (§3.4).
5. Ma collectivité et Données (§3.5, §3.7).

Chaque étape est vérifiée en se mettant à la place du citoyen curieux sur téléphone (320 px) : sait-il où cliquer,
comprend-il ce qu'il lit, repart-il avec une phrase juste ?
