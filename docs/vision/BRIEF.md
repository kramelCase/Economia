# Brief commun : « moteur d'exploration économique » (refonte de l'interface de Comptes publics)

## La demande du porteur du projet (résumée fidèlement)
Une interface ultramoderne, immersive, interactive, avec un **hero plein écran**, capable de répondre à un
maximum de questions tout en restant **extrêmement simple**. Un vrai outil d'exploration, d'analyse et de
comparaison de données économiques, pour journalistes, économistes, chercheurs, créateurs de contenu,
utilisateurs de réseaux sociaux et simples citoyens. Elle **ne doit pas ressembler à un tableau de bord
statistique** : plutôt un moteur d'exploration nouvelle génération qui transforme une question simple en
analyse visuelle, interactive, comparative et sourcée.

Pistes données (points de départ, à challenger et dépasser) : hero plein écran, recherche intelligente
type Select2 (autocomplétion, suggestions, multicritère), tags/questions qui apparaissent pour la
découverte, onglets (thème, territoire, période, type d'analyse), comparateur universel (pays, régions,
villes, indicateurs, périodes), graphiques interactifs, cartographie type « store locator », exploration
guidée, partage/export sourcé, sources et méthodologie faciles d'accès.

Priorité absolue : maximiser exploration et analyse **sans sacrifier simplicité, lisibilité,
performances, fiabilité**. Il veut qu'on enrichisse, qu'on remette en question, qu'on propose plus
ambitieux si ça améliore vraiment le produit.

## Le projet existant (à connaître avant de proposer)
Dépôt : `~/projects/economia` (FastAPI + Jinja + SQLite, rendu serveur, JS léger sans
framework, graphiques SVG maison dans `static/charts.js`). Lire `README.md` et `docs/INVENTAIRE.md`.

Principes **non négociables** (le porteur les a imposés) :
1. **Données d'abord** : on part des données ouvertes officielles et l'interface se conçoit autour.
2. **Chaque chiffre affiché remonte à la ligne du fichier officiel** (source → fichier sha256 → ligne).
3. **Aucune méthode comptable inventée** ; on n'additionne que le long d'une nomenclature officielle, même
   source, même stade (PLF / LFI / exécution / comptes), même unité. Les calculs faits par le site
   (parts, médianes) sont signalés comme tels.
4. **Un trou n'est pas un zéro** : les lacunes (non chiffré, non publié) sont un contenu à part entière,
   avec qui devrait les publier. Objectif citoyen : « redonner le pouvoir au peuple sur ses finances ».
5. **Définitions citées** (INSEE, Légifrance, OFGL) ; tout terme technique relié au lexique + infobulle.
6. **FR / EN** ; mobile d'abord (vérifié à 320 px) ; neutralité : on répond aux questions politiques
   (« cadeaux aux milliardaires ») par des catégories officielles, sans éditorialiser.

Données **déjà en base** (≈ 530 000 montants) :
- Eurostat COFOG France 1995-2024 : dépenses de toutes les administrations publiques (et de l'État, des
  collectivités, de la Sécu séparément) par fonction et sous-fonction, en M€, % du total, % du PIB.
- Budget de l'État : budget vert PLF 2026 (exécution 2024, LFI 2025, PLF 2026, par mission/programme,
  avec cotation environnementale) ; PLF 2025 par destination (mission > programme > action, AE/CP).
- Dépenses fiscales (« niches ») : coût estimé 2024-2026 par dépense et par impôt ; 63 « non chiffrées ».
- OFGL : comptes consolidés des 17 régions et 101 départements 2012-2025 (agrégats : dépenses,
  personnel, investissement, épargne, dette… en € et €/habitant) ; dépenses des départements par fonction.
- Lexique : définitions INSEE, LOLF (Légifrance), OFGL.

**Non collecté à ce jour** (à recommander si utile, en citant la source officielle exacte) : autres pays
(Eurostat le permet), communes et intercommunalités (OFGL), Sécurité sociale détaillée (LFSS), dette et
déficit (INSEE), exécution mensuelle de l'État, recettes fiscales détaillées, inégalités, pouvoir
d'achat, prix, emploi, géométries des territoires (IGN / data.gouv) pour une carte.

## Goût du porteur (important pour le design)
Éditorial, matière, caractère, parti pris ; **déteste** les templates lisses « propres mais sans âme »,
les cartes numérotées 01/02/03, les bandes de stats de remplissage, les aplats de couleur décoratifs, les
illustrations SVG/CSS cheap à la place d'images. Test anti-générique : si on peut échanger le logo avec un
autre site sans que ça choque, c'est raté. Accessibilité (AA) non négociable. Le site actuel : serif
éditoriale (Source Serif 4) + IBM Plex Sans, papier crème / encre, mode sombre.

## Règles pour toi, spécialiste
- Écris en français, dense et concret ; pas de remplissage. Chaque idée : **pour qui, quel besoin, comment
  ça marche, ce que ça exige en données** (disponibles / à collecter, source exacte).
- Ose des idées originales, mais signale honnêtement ce qui serait gadget, trompeur ou infaisable avec
  les principes ci-dessus.
- N'invente aucun chiffre. Si tu illustres, écris « [montant réel issu de …] ».
