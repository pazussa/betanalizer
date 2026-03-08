# Correlacion de la regla BDI_jsd_fair

Evaluacion de la idea `elegir la cuota mayor entre Over 2.5 y Under 2.5` y usar `BDI_jsd_fair` como orden de prioridad.

## Supuesto del algoritmo

- Pares verificados con ambos lados: **112**.
- Diferencia maxima entre `Over 2.5` y `Under 2.5` para `BDI_jsd_fair`: **0.000000000000**.
- Esto confirma que la metrica es compartida por ambos lados del mismo partido.

## Correlacion simple

| scope | bets | profit_total | roi_per_bet | hit_rate | pearson_bdi_profit | spearman_bdi_profit | pearson_rank_profit | spearman_rank_profit | pearson_selected_top8_profit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | 112 | -0.9100 | -0.0081 | 0.4554 | 0.0817 | -0.0328 | 0.0017 | 0.0118 | 0.0773 |
| weekend | 102 | 0.8400 | 0.0082 | 0.4608 | 0.0818 | -0.0354 | -0.0195 | -0.0200 | 0.1053 |

Lectura:

- La correlacion lineal directa entre `BDI_jsd_fair` y `profit` es debil en ambos cortes.
- Eso significa que la senal no es una recta simple del tipo `mas BDI => mas profit` para todos los partidos.
- La correlacion mejora un poco cuando usas la variable operativa `selected_top8`, porque se parece mas a tu regla real.

## Deciles de BDI en todo el dataset

| bdi_decile | bets | mean_bdi | roi | hit_rate | avg_odds |
| --- | --- | --- | --- | --- | --- |
| (-0.000998, 8.02e-06] | 12 | 0.0000 | -0.2833 | 0.3333 | 2.2833 |
| (8.02e-06, 1.44e-05] | 11 | 0.0000 | 0.0382 | 0.4545 | 2.1927 |
| (1.44e-05, 2.02e-05] | 11 | 0.0000 | 0.1655 | 0.5455 | 2.1555 |
| (2.02e-05, 2.61e-05] | 11 | 0.0000 | 0.3891 | 0.6364 | 2.2009 |
| (2.61e-05, 3.76e-05] | 11 | 0.0000 | -0.1709 | 0.3636 | 2.2336 |
| (3.76e-05, 4.74e-05] | 11 | 0.0000 | 0.2009 | 0.5455 | 2.1936 |
| (4.74e-05, 6.86e-05] | 11 | 0.0001 | -0.2645 | 0.3636 | 2.2255 |
| (6.86e-05, 8.44e-05] | 11 | 0.0001 | -0.4218 | 0.2727 | 2.1727 |
| (8.44e-05, 0.000113] | 11 | 0.0001 | 0.0227 | 0.4545 | 2.2209 |
| (0.000113, 0.00042] | 12 | 0.0002 | 0.2450 | 0.5833 | 2.2075 |

## Deciles de BDI solo sabado-domingo

| bdi_decile | bets | mean_bdi | roi | hit_rate | avg_odds |
| --- | --- | --- | --- | --- | --- |
| (-0.000998, 8.2e-06] | 11 | 0.0000 | -0.2182 | 0.3636 | 2.2864 |
| (8.2e-06, 1.44e-05] | 10 | 0.0000 | 0.1420 | 0.5000 | 2.2100 |
| (1.44e-05, 2.02e-05] | 10 | 0.0000 | 0.0720 | 0.5000 | 2.1610 |
| (2.02e-05, 2.59e-05] | 10 | 0.0000 | 0.5280 | 0.7000 | 2.2090 |
| (2.59e-05, 3.76e-05] | 10 | 0.0000 | -0.2920 | 0.3000 | 2.2630 |
| (3.76e-05, 5.01e-05] | 10 | 0.0000 | 0.1150 | 0.5000 | 2.2070 |
| (5.01e-05, 7.29e-05] | 10 | 0.0001 | -0.1860 | 0.4000 | 2.2170 |
| (7.29e-05, 8.49e-05] | 10 | 0.0001 | -0.3540 | 0.3000 | 2.0900 |
| (8.49e-05, 0.000127] | 10 | 0.0001 | -0.0950 | 0.4000 | 2.2180 |
| (0.000127, 0.00042] | 11 | 0.0002 | 0.3582 | 0.6364 | 2.2127 |

## Top 8 vs resto

### Todo el dataset

| selected_top8 | bets | profit_total | roi | hit_rate | avg_bdi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- |
| False | 64 | -5.2000 | -0.0813 | 0.4219 | 0.0000 | 2.2089 |
| True | 48 | 4.2900 | 0.0894 | 0.5000 | 0.0001 | 2.2098 |

### Solo sabado-domingo

| selected_top8 | bets | profit_total | roi | hit_rate | avg_bdi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- |
| False | 62 | -5.2500 | -0.0847 | 0.4194 | 0.0000 | 2.2145 |
| True | 40 | 6.0900 | 0.1522 | 0.5250 | 0.0001 | 2.1985 |

## Conclusiones

- Si usas **todo el dataset**, la regla completa pierde ligeramente dinero en promedio (`ROI` cerca de cero/negativo), y la correlacion simple con BDI es muy debil.
- Si usas **solo sabados y domingos**, la rentabilidad mejora y el `top 8` supera claramente al resto.
- La senal parece ser **de cola alta**: no funciona tan bien como relacion monotona general, pero si cuando te concentras en los partidos con `BDI_jsd_fair` mas alto.
- Eso encaja con tu intuicion original: el valor no estaba en todo el rango de BDI, sino en usarlo para priorizar pocos partidos.
