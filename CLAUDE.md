# Règles pour un agent de code

Lire `docs/CONTRIBUER.md` (principes et règles) et `docs/INVENTAIRE.md` (pièges des données) avant toute modification.
Le plus important : aucun chiffre, libellé officiel ou définition écrit à la main ; aucune affirmation non sourcée dans
l'interface ; ne jamais additionner des agrégats emboîtés (OFGL, COFOG).

Après un changement : `make build && make test`.
