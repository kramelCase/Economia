# Critique croisée : l'économiste lit `ux.md`, `direction-artistique.md`, `dataviz.md`

2026-10-27. Renvois : §x des fichiers cités ; mes règles = `economiste.md` §3.

## (a) Ce qui trahit la rigueur ou induit en erreur, et la correction exacte

1. **UX, parcours P1 « dette vs éducation », lecture État.** Il compare la mission « Engagements financiers de
   l'État » (qui contient d'autres programmes que la charge de la dette) à « Enseignement scolaire + Recherche et
   enseignement supérieur » : c'est une **somme de deux missions**, que l'UX interdit elle-même (K9), et la recherche
   n'est pas de l'éducation. → Comparer le **programme « Charge de la dette et trésorerie de l'État »** seul à la
   mission « Enseignement scolaire » seule, chacune avec son code ; la mission recherche est proposée comme lecture
   voisine, jamais additionnée.
2. **UX §3.4, `qui=etat-apu` (S1311) libellé « État ».** S1311 = administrations publiques **centrales** (État + ODAC),
   pas l'État. → Libellé « administrations centrales (État et organismes rattachés) », distinct de `budget-etat`.
3. **UX R6 : « aides aux entreprises » → dépenses fiscales.** Faux : les dépenses fiscales profitent aussi aux
   ménages, et une bonne part des aides aux entreprises n'en sont pas (exonérations de cotisations, crédits
   budgétaires). → Réponse « pas de catégorie officielle unique » + lacune + lectures partielles nommées (dépenses
   fiscales sur l'IS, etc.). La même règle vaut pour P7.
4. **UX et DA, hero : « Combien la France dépense… », « en [France ▾] ».** « La France » n'est pas un périmètre. →
   « les administrations publiques » dans la phrase. La phrase à 2 champs de la DA (Hero 1) fait disparaître le
   périmètre et le stade : elle doit reprendre la phrase à 5 emplacements de l'UX.
5. **DA, roulement de compteur (Hero 1).** Pendant 300 ms, l'écran affiche des **montants intermédiaires faux**, et une
   capture d'écran peut les figer. → Fondu enchaîné, aucune valeur intermédiaire.
6. **DA, fac-similé « recadré sur la ligne exacte ».** Nos chiffres viennent du **CSV open data**, pas du PDF : la
   valeur imprimée peut différer (arrondi, version, rectificatif). Montrer le PDF comme « la preuve » est une fausse
   provenance. → La preuve, c'est la ligne du CSV (en mono). Le PDF sert d'illustration et porte la légende
   « document de référence ». Il n'apparaît collé au chiffre que si un contrôle a vérifié que la valeur et la page
   correspondent.
7. **Dataviz §2.3 : « % du PIB » pour une région, grisé « PIB régional non collecté ».** Cela promet une mesure peu
   pertinente : la dépense d'un conseil régional ne se rapporte pas au PIB du territoire. → Motif « mesure non
   pertinente pour une collectivité : utilisez €/hab », pas « non collecté ».
8. **Dataviz §3.2 : seuils de carte fixes sur 2012-2025 en euros courants.** L'inflation fonce toutes les cases au fil
   des ans sans que les politiques aient changé. → Seuils fixes autorisés seulement avec la mention « euros courants :
   la hausse générale des prix assombrit la carte ». Sinon, seuils annuels avec la mention « classes recalculées
   chaque année ».
9. **Dataviz §1.6 : le budget vert PLF 2025 pour le « voté vs réalisé ».** Il existe (`plf25-budget-vert`), mais
   associer sa LFI 2024 à l'exécution 2024 du budget vert 2026 croise deux millésimes dont les périmètres de mission
   bougent. → Source de référence : **PLRG 2024 / 2025** (data.economie.gouv.fr, vérifiés), qui donnent prévu et
   réalisé du **même exercice**.
10. **UX P3 / S1 : le permalien « rejouera la même phrase dans deux ans ».** Faux si les données sont révisées (2023-2024
    sont provisoires). → `v=<millésime>` dans **tout** permalien et toute citation, comme dans l'embed de la dataviz
    (§5.3), avec le bandeau « révisé depuis ».
11. **Mon propre texte, rectifié.** La dataviz a raison (§1.8) : pas de décomposition « prix/volume » par fonction,
    faute de déflateur par fonction publié. Je limite la décomposition à population + déflateur **général** nommé +
    lignes de périmètre, sans effet « volume » interprété.

## (b) Ce qui manque pour mes profils

- **Dette et déficit** : c'est la question n° 1 (plateau, réseaux, fact-check), et elle est absente des trois parcours.
  Il faut collecter `gov_10dd_edpt1` avant le lancement, et prévoir une amorce « dette » dans le hero, en M€ et en
  % du PIB côte à côte.
- **Mode « j'ai lu ce chiffre »** (fact-checkeur, utilisateur de réseau) : coller une affirmation → R5 → une grille de
  lectures (même périmètre / autre périmètre / autre année / non vérifiable), sans verdict vrai/faux. C'est une entrée
  de la même barre, pas un deuxième concept.
- **% du PIB pour le budget de l'État** et **€/hab national** : ils exigent le PIB et la population (Eurostat
  `nama_10_gdp`, `demo_pjan`). Je les classe en v1, pas « plus tard ».
- **Population** (demande de la dataviz) : utiliser la population publiée **dans le jeu OFGL lui-même** pour tout
  €/hab local, sans recalcul. Pour le national, la population Eurostat au 1er janvier, avec son millésime affiché.
  Ne jamais mélanger population municipale, totale et DGF.
- **API JSON** (UX S6, « plus tard ») : à monter en v1. Elle ne coûte presque rien et sert les agents IA, qui
  porteront le plus de volume et la promesse « chaque chiffre a sa ligne ».
- **Qui fait quoi** (compétences commune / département / région / État) dans « Pour bien lire » : sans elle, la
  comparaison Paris / Lyon / CeA / collectivités uniques reste trompeuse.
- **Formulations du stade (demande de la DA)** : « Projet (PLF) », « Voté (LFI) », « Réalisé (exécution) »,
  « Comptes nationaux ». En anglais, je ne connais pas de traduction officielle pour la LOLF : marquer la version
  anglaise « traduction non officielle ».

## (c) J'approuve sans réserve

La phrase-requête qui porte le périmètre et le stade **dans la question** ; le sélecteur de lecture R7 ; les options
impossibles affichées comme lacunes (R8) ; la garde de comparabilité K2 et le refus des sommes libres (K9) ; le refus
du chatbot, du « où vont mes impôts » personnalisé et du constructeur libre. Côté dataviz : un graphique = une source
× un stade × une unité ; pas de segment entre stades ; le pointillé réservé à la prévision et le « provisoire » distinct ;
la cascade avec une marche à part pour les MP/MT ; la marche des niches avec sa queue `nc` « coût inconnu, pas nul » ;
le mur des absences ; le refus du Sankey et du jour de libération fiscale ; une divergente bleu ↔ orange.
Côté DA : la cote mono, la lacune achromatique en hachure, Marianne exclue, aucune couleur qui juge.

## (d) Arbitrages à trancher

1. **Euros courants ou constants par défaut : je me range à la dataviz, avec deux conditions.** Le chiffre de la
   première couche doit être une ligne source ; or un euro constant est un calcul. Défaut = **courants**. Mais
   (i) pour une évolution de plus de 10 ans au niveau national, le défaut est **% du PIB** (publié par Eurostat) ;
   (ii) toute série de plus de 5 ans en euros courants porte, **à côté de la courbe** (pas dans une note),
   « euros courants : inflation non déduite » et la bascule « constants » à un geste. Déflateur : **prix du PIB**
   (Eurostat `nama_10_gdp`) pour les agrégats publics ; l'IPC INSEE (`001759970`) seulement pour une question de
   pouvoir d'achat.
2. **Phrase-requête à 5 emplacements : oui, à trois corrections près.** (i) Le stade ne doit pas se fondre dans
   « temps » : la phrase l'écrit en clair (« en 2024, **réalisé** »), car c'est la confusion la plus fréquente.
   (ii) Le sélecteur « mesure » refuse les mesures non pertinentes (€ total sur une carte, % du PIB pour une
   collectivité) en disant pourquoi. (iii) À 320 px, les valeurs par défaut restent écrites : un emplacement replié
   ne doit jamais cacher le périmètre.
3. **« 1 visuel par réponse » : oui comme défaut, non comme dogme.** Je demande la règle « un visuel principal +
   **un témoin obligatoire** quand une règle de rigueur l'exige ». Trois cas : deux lectures de périmètre (deux
   panneaux empilés, jamais un seul axe) ; un ratio % du PIB qui bouge avec le PIB (numérateur en M€ en vignette) ;
   un total incomplet (la queue `nc`). Ce qui compte, c'est de ne jamais induire en erreur, et un seul visuel peut
   le faire.
4. **Chiffre vedette par défaut (demande de la DA)** : COFOG S13, dernière année, une fonction tirée d'un vivier relu,
   en **% du total publié** puis en M€, avec la mention « provisoire ». Pas de dette par défaut tant qu'elle n'est pas
   collectée et montrée en M€ et en % du PIB.
5. **M€ → Md€** : acceptable. C'est un changement d'échelle, pas de méthode. La valeur exacte reste dans la cote, et
   l'arrondi ne dépasse jamais la précision de la source.
6. **Carte ou tuiles sur mobile** : les tuiles (dataviz), toujours en €/hab ou en ratio, avec Paris, Lyon, la CeA, les
   collectivités uniques et l'Outre-mer annotés, pas retirés.
7. **Orthophoto (DA, Hero 3)** : seulement sur les fiches territoire, jamais comme fond d'un chiffre comparé (une photo
   rurale ou urbaine oriente la lecture d'un €/hab).
