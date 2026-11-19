# Structure du site : refonte (2026-10-27)

Demande du user : « fais le tour du site et repense toute sa structure, en t'inspirant d'outils existants dans des
domaines variés, pour des interfaces pratiques et intelligentes ». Ce document fait foi pour la navigation ; il
complète `SYNTHESE.md` (vision) et `HANDOFF.md` (état).

## 1. Le tour : ce qui ne va pas

| Constat | Où | Effet |
|---|---|---|
| Le site est rangé **par source** (une page Eurostat, une page budget de l'État, une page dépenses fiscales, une page OFGL) | menu | Le lecteur doit savoir qui publie quoi avant de chercher. |
| **10 entrées de menu au même niveau** : questions, outils et références mélangés | en-tête | Rien ne hiérarchise ; sur téléphone le menu défile hors de l'écran. |
| **Doublons** : carte de l'accueil et anneau de `/depenses-publiques` ; classement `/territoires` et comparateur ; prototype `/explorer`, recherche et accueil | partout | Trois façons de faire la même chose, aucune complète. |
| **La recherche n'existe que sur `/explorer`** | en-tête | Le moyen le plus rapide d'aller quelque part est absent des pages. |
| Un objet (Gironde, Enseignement, mission Défense) **n'a pas de fiche unique** : il apparaît dans plusieurs pages sans lien entre elles | pages | On ne peut pas « suivre » un objet. |
| Chaque page a **ses propres réglages** (listes déroulantes, pastilles, onglets) | pages | Il faut réapprendre l'interface à chaque page. |
| La **page « source d'un chiffre »** est excellente (ligne relue dans le fichier brut) mais isolée | `/montant/{id}` | Le meilleur atout du site est caché derrière un petit badge. |

## 2. Ce qu'on emprunte ailleurs

| Domaine | Outil | Ce qu'il fait bien | Ce qu'on en fait ici |
|---|---|---|---|
| Cartographie | Google Maps / Earth | Zoom sémantique ; **toute chose a sa fiche** (lieu, horaires, photos, itinéraire) | Accueil-carte (fait) ; **fiche universelle** pour territoire, fonction, mission, dépense fiscale |
| Encyclopédie | Wikipédia / Wikidata | Infobox normalisée, identifiant stable (Q-id), « pages liées » | Bandeau de fiche identique pour tous les objets ; code officiel affiché (DEP-33, GF09) comme identifiant |
| Développement | VS Code, Linear, Raycast | **Palette de commandes** (Ctrl+K) : tout est à trois touches | Palette sur toutes les pages : aller à un objet, lancer une action (comparer, tracer la série) |
| Développement | GitHub | Permalien vers une ligne, « blame » = d'où vient chaque ligne | La page source d'un chiffre devient un **panneau latéral** ouvert depuis n'importe quel chiffre |
| Statistique publique | Our World in Data (Grapher) | Chaque graphique a les mêmes onglets : graphique, tableau, carte, sources, téléchargement | Un seul composant « figure » partout : Graphique · Tableau · Source · Télécharger |
| Finance de marché | Bloomberg, Koyfin, Google Finance | **Liste de suivi** persistante ; comparer des « tickers » ; raccourcis par code | **Carnet** : épingler des objets sur n'importe quelle page, les retrouver dans Comparer et Séries |
| Santé | Compte rendu d'analyses biologiques | Chaque valeur avec sa **fourchette de référence** | Sur une fiche territoire : la valeur, la médiane et l'intervalle P25–P75 des collectivités du même niveau (calcul du site, signalé) |
| Météo | Applications météo | « Comparé à la normale » | Même idée en série : la courbe et la bande des pairs |
| Commerce | Comparateurs de produits (fiches techniques côte à côte) | 2 à 4 produits, **différences surlignées** | Face-à-face de 2 à 4 objets du même type, ligne par ligne |
| Voyage | Google Flights (grille des prix) | Grille date × date, la cellule la plus basse saute aux yeux | Grille année × objet (petits multiples / carte de chaleur) dans Séries |
| Réservation | Airbnb, Kayak | Filtres à facettes avec **le nombre de résultats** pour chaque choix | Filtres du comparateur avec compte (fait pour le total ; à étendre aux facettes) |
| Moteur de réponse | Wolfram Alpha | La question est **réécrite** (« Interprété comme : … ») avant la réponse | La recherche montre comment elle a compris la demande : objet, périmètre, année, source |
| Tableur | Excel, Airtable, Notion | Vues enregistrées, colonnes choisies, tri multi-critères | Comparateur (fait) ; vues partagées par lien (fait) |
| Archives | Gallica, Archives nationales | Cote, provenance, date de versement | Mono réservé à la cote (déjà dans la direction artistique) |

Ce qu'on **n'emprunte pas** : les tableaux de bord à jauges (jugement implicite), les flux animés décoratifs, les
couleurs « bien / mal », les classements présentés comme des palmarès.

## 3. La nouvelle structure

Trois espaces, nommés par ce qu'on y fait, pas par la source :

**Comprendre** : des questions, une réponse visible tout de suite.
- Accueil : la carte de la dépense publique (fait).
- Budget de l'État · Dépenses fiscales · Collectivités : mêmes pages qu'aujourd'hui, à terme sur le modèle de la carte.

**Analyser** : des outils de travail.
- Comparer (fait) · Séries (fait) · Face-à-face (à faire) · Carnet (à faire).

**Vérifier** : la preuve.
- Sources et méthode · Données non disponibles · Lexique · source d'un chiffre.

Et trois mécanismes communs à toutes les pages :
1. **Palette de commandes** (Ctrl+K ou « / », bouton « Rechercher » dans l'en-tête) : objets avec leur chiffre et
   leurs actions (Fiche · Comparer · Série), pages, outils.
2. **Fiche universelle** par objet : bandeau (nom, type, code, source), chiffres clés avec fourchette des pairs,
   évolution, décomposition, « Comparer avec… », pages liées.
3. **Carnet** : objets épinglés, gardés d'une page à l'autre (stockage du navigateur), injectés dans Comparer et Séries.

Les doublons disparaissent : `/explorer` (prototype) est retiré du menu ; `/depenses-publiques` devient la vue
détaillée de la carte ; `/territoires` devient le comparateur pré-réglé sur un indicateur.
