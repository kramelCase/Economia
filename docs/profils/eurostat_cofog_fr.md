# Profil : Dépenses des administrations publiques par fonction (COFOG) - France

- **id** : `eurostat_cofog_fr`
- **éditeur** : Eurostat, à partir des comptes nationaux transmis par l'INSEE
- **périmètre** : Toutes les administrations publiques (S13) et sous-secteurs : centrales (S1311), locales (S1313), sécurité sociale (S1314)
- **collecte** : `2026-10-26T225312Z`, sha256 `ec6fc9b58dcb6ae1…`, 2.3 Mo
- **URL** : https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/gov_10a_exp/A.MIO_EUR+PC_TOT+PC_GDP.S13+S1311+S1313+S1314..TE.FR?format=SDMX-CSV&startPeriod=1995
- **lignes** : 28680 (largeur incohérente : 0)
- **séparateur** : `,`

| colonne | type | remplies | manquantes (marqueurs) | distinctes | min / max | valeurs fréquentes |
|---|---|---|---|---|---|---|
| `DATAFLOW` | texte | 28680 | 0  | 1 |  | `ESTAT:GOV_10A_EXP(1.0)`×28680 |
| `LAST UPDATE` | texte | 28680 | 0  | 1 |  | `21/10/26 23:00:00`×28680 |
| `freq` | texte | 28680 | 0  | 1 |  | `A`×28680 |
| `unit` | texte | 28680 | 0  | 3 |  | `MIO_EUR`×9600, `PC_GDP`×9600, `PC_TOT`×9480 |
| `sector` | texte | 28680 | 0  | 4 |  | `S13`×7170, `S1311`×7170, `S1313`×7170, `S1314`×7170 |
| `cofog99` | texte | 28680 | 0  | 80 |  | `GF01`×360, `GF0101`×360, `GF0102`×360, `GF0103`×360, `GF0104`×360 |
| `na_item` | texte | 28680 | 0  | 1 |  | `TE`×28680 |
| `geo` | texte | 28680 | 0  | 1 |  | `FR`×28680 |
| `TIME_PERIOD` | numérique | 28680 | 0  | 30 | 1995 / 2024 |  |
| `OBS_VALUE` | numérique | 28680 | 0  | >5000 | -1.2 / 1.67179e+06 |  |
| `OBS_FLAG` | texte | 1450 | 27230 `(vide)`×27230 | 1 |  | `p`×1450 |
| `CONF_STATUS` | vide | 0 | 28680 `(vide)`×28680 | 0 |  |  |
