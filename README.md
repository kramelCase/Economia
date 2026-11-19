# Economia

Les finances publiques françaises (État, Sécurité sociale, régions, départements) expliquées à quelqu'un qui n'y
connaît rien. **Chaque chiffre affiché est relié à la ligne du fichier officiel d'où il vient.** Interface en FR et en EN.

## Pourquoi

Les chiffres des finances publiques circulent sans source, sans périmètre, et se contredisent. Economia les montre
tels que publiés (Eurostat, Insee, direction du Budget, OFGL, Assemblée nationale) et explique pourquoi deux chiffres
qui ont l'air de mesurer la même chose diffèrent.

**Ce que le site fait**
- Il répond à des questions simples : d'où vient l'argent public, à quoi il sert, quelle est la dette, que dépense mon
  département.
- Il relie chaque chiffre à sa source. Un clic mène à l'éditeur, au fichier, à la date de collecte et à la ligne.
- Il montre ce qui manque : un trou dans les données est affiché comme un trou, jamais comme un zéro.

**Ce qu'il ne fait pas** : pas de chiffre inventé, pas de méthode de calcul maison, pas de verdict politique, pas de
lien de cause suggéré entre deux courbes.

## Démarrer en 4 commandes

Il faut Python 3.12+ et [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
make install   # environnement Python et dépendances
make fetch     # télécharge les sources officielles dans raw/ (plusieurs minutes, ~550 Mo)
make build     # construit la base comptes.sqlite ; échoue si un contrôle de cohérence échoue
make serve     # ouvre le site sur http://127.0.0.1:8790
```

`make setup` enchaîne les trois premières. Le détail est dans [docs/UTILISATION.md](docs/UTILISATION.md).

## Pour aller plus loin

| Document | Contenu |
|---|---|
| [docs/UTILISATION.md](docs/UTILISATION.md) | Installer, lancer, tester, ajouter une source, mettre à jour les traductions |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Schémas : du fichier officiel à la page, la base de données, le code |
| [docs/CONTRIBUER.md](docs/CONTRIBUER.md) | Les règles du projet et comment collaborer (tickets, branches, pull requests) |
| [docs/ROADMAP.md](docs/ROADMAP.md) | La vision et les grands chantiers ; le suivi au jour le jour est dans *Issues* et *Projects* |
| [docs/INVENTAIRE.md](docs/INVENTAIRE.md) | Ce que contiennent vraiment les données, et leurs pièges |
| [docs/SCHEMA-BASE.md](docs/SCHEMA-BASE.md) | La base table par table |
| [docs/vision/](docs/vision/) | Notes de conception (interface, dataviz, économie) |

## Licence des données

Les données viennent de sources publiques sous Licence ouverte Etalab 2.0 ou sous la politique de réutilisation
d'Eurostat. La licence de chaque jeu est affichée sur sa page « source » dans le site.
