# Autopsia de la estrategia BDI

Autopsia de la regla `sabado-domingo -> top BDI_jsd_fair -> elegir la cuota mayor entre Over 2.5 y Under 2.5` usando el dataset robusto con parseo de resultados por `Resultado`, `Acerto`, marcador y goles.

## Diagnostico

- `top 8`: **50/120** aciertos, profit **-7.62**, ROI **-0.064**.
- `top 9`: **57/135** aciertos, profit **-7.24**, ROI **-0.054**.
- Veredicto: la estrategia, tal como esta definida, **no tiene edge robusto** en el historico completo.

## Que la mata

- El `top BDI` no mejora el universo base; queda ligeramente peor que el resto de partidos elegidos por cuota mayor.
- El ranking por BDI esta demasiado pegado a cuotas altas. En la seleccion `top 8`, la correlacion Pearson `BDI -> cuota` es muy alta y la cuota media sube claramente frente al resto.
- El lado `Under 2.5` cuando es la cuota mayor es el mayor drenaje de profit.
- Las perdidas estan concentradas en pocas semanas grandes; la estrategia tiene riesgo de caida por bloques.

## Top vs resto

| top_n | selection | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | resto | 1513 | 656 | 0.434 | -73.900 | -0.049 | 2.202 |
| 8 | top8 | 120 | 50 | 0.417 | -7.620 | -0.063 | 2.478 |

| top_n | selection | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | resto | 1498 | 649 | 0.433 | -74.280 | -0.050 | 2.202 |
| 9 | top9 | 135 | 57 | 0.422 | -7.240 | -0.054 | 2.450 |

Lectura:

- `top 8` selecciona apuestas con cuota media **2.478** frente a **2.202** del resto.
- `top 9` selecciona apuestas con cuota media **2.450** frente a **2.202** del resto.
- El filtro BDI no esta comprando mas valor; esta comprando apuestas mas agresivas y no las compensa con suficiente acierto.

## Relacion BDI con cuota

| scope | bets | hit_rate | profit_total | roi | avg_odds | avg_bdi | over_share | pearson_bdi_odds | spearman_bdi_odds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_chosen | 1633 | 0.432 | -81.520 | -0.050 | 2.222 | 0.000065 | 0.558 | 0.908 | 0.053 |
| top8 | 120 | 0.417 | -7.620 | -0.064 | 2.478 | 0.000535 | 0.600 | 0.987 | 0.209 |
| top9 | 135 | 0.422 | -7.240 | -0.054 | 2.450 | 0.000486 | 0.585 | 0.986 | 0.217 |

Lectura:

- En `top 8` la correlacion Pearson entre `BDI_jsd_fair` y `Mejor_Cuota` queda en **0.987**.
- En `top 9` queda en **0.986**.
- Operativamente, el BDI termina funcionando casi como un selector de cuotas mas extremas, no como un detector limpio de valor.

## Desglose por lado

| top_n | Mercado | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | Over 2.5 | 72 | 31 | 0.431 | -1.000 | -0.014 | 2.663 |
| 8 | Under 2.5 | 48 | 19 | 0.396 | -6.620 | -0.138 | 2.202 |

| top_n | Mercado | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | Over 2.5 | 79 | 35 | 0.443 | 0.440 | 0.006 | 2.624 |
| 9 | Under 2.5 | 56 | 22 | 0.393 | -7.680 | -0.137 | 2.206 |

Lectura:

- En `top 8`, `Over 2.5` pierde poco (**-0.014**) y `Under 2.5` pierde mucho mas (**-0.138**).
- En `top 9`, `Over 2.5` queda practicamente en break-even (**0.006**) y `Under 2.5` vuelve a ser el drenaje principal (**-0.137**).

## Desglose por lado y cuota

| top_n | Mercado | odds_bin | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | Over 2.5 | [0.0, 2.0) | 5 | 2 | 0.400 | -1.040 | -0.208 | 1.978 |
| 8 | Over 2.5 | [2.0, 2.2) | 21 | 10 | 0.476 | -0.180 | -0.009 | 2.089 |
| 8 | Over 2.5 | [2.2, 2.4) | 22 | 11 | 0.500 | 3.070 | 0.140 | 2.275 |
| 8 | Over 2.5 | [2.4, 2.6) | 9 | 3 | 0.333 | -1.520 | -0.169 | 2.486 |
| 8 | Over 2.5 | [2.6, 10.0) | 13 | 5 | 0.385 | 0.670 | 0.052 | 2.735 |
| 8 | Over 2.5 | nan | 2 | 0 | 0.000 | -2.000 | -1.000 | 15.000 |
| 8 | Under 2.5 | [0.0, 2.0) | 1 | 1 | 1.000 | 0.980 | 0.980 | 1.980 |
| 8 | Under 2.5 | [2.0, 2.2) | 23 | 10 | 0.435 | -2.180 | -0.095 | 2.103 |
| 8 | Under 2.5 | [2.2, 2.4) | 18 | 5 | 0.278 | -6.680 | -0.371 | 2.266 |
| 8 | Under 2.5 | [2.4, 2.6) | 6 | 3 | 0.500 | 1.260 | 0.210 | 2.423 |

| top_n | Mercado | odds_bin | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | Over 2.5 | [0.0, 2.0) | 7 | 4 | 0.571 | 0.900 | 0.129 | 1.976 |
| 9 | Over 2.5 | [2.0, 2.2) | 22 | 10 | 0.455 | -1.180 | -0.054 | 2.087 |
| 9 | Over 2.5 | [2.2, 2.4) | 25 | 13 | 0.520 | 4.570 | 0.183 | 2.276 |
| 9 | Over 2.5 | [2.4, 2.6) | 9 | 3 | 0.333 | -1.520 | -0.169 | 2.486 |
| 9 | Over 2.5 | [2.6, 10.0) | 14 | 5 | 0.357 | -0.330 | -0.024 | 2.732 |
| 9 | Over 2.5 | nan | 2 | 0 | 0.000 | -2.000 | -1.000 | 15.000 |
| 9 | Under 2.5 | [0.0, 2.0) | 1 | 1 | 1.000 | 0.980 | 0.980 | 1.980 |
| 9 | Under 2.5 | [2.0, 2.2) | 28 | 12 | 0.429 | -3.090 | -0.110 | 2.099 |
| 9 | Under 2.5 | [2.2, 2.4) | 20 | 5 | 0.250 | -8.680 | -0.434 | 2.269 |
| 9 | Under 2.5 | [2.4, 2.6) | 6 | 3 | 0.500 | 1.260 | 0.210 | 2.423 |
| 9 | Under 2.5 | [2.6, 10.0) | 1 | 1 | 1.000 | 1.850 | 1.850 | 2.850 |

Lectura:

- El punto mas toxico es `Under 2.5` con cuotas entre `2.2` y `2.4`: ahi la estrategia se rompe fuerte.
- La unica zona que se ve defendible dentro de la idea original es `Over 2.5` entre `2.2` y `2.4`, pero sigue siendo una hipotesis post-hoc, no una estrategia validada.

## Riesgo semanal

| top_n | week_id | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 2025-W02 | 8 | 1 | 0.125 | -5.880 | -0.735 | 2.263 |
| 8 | 2025-W10 | 8 | 2 | 0.250 | -3.900 | -0.488 | 2.312 |
| 8 | 2025-W13 | 8 | 2 | 0.250 | -3.900 | -0.487 | 2.237 |
| 8 | 2025-W03 | 8 | 2 | 0.250 | -3.600 | -0.450 | 3.967 |
| 8 | 2025-W08 | 8 | 2 | 0.250 | -3.540 | -0.443 | 2.288 |

| top_n | week_id | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | 2025-W02 | 9 | 1 | 0.111 | -6.880 | -0.764 | 2.241 |
| 9 | 2025-W03 | 9 | 2 | 0.222 | -4.600 | -0.511 | 3.756 |
| 9 | 2025-W10 | 9 | 3 | 0.333 | -2.930 | -0.326 | 2.274 |
| 9 | 2025-W13 | 9 | 3 | 0.333 | -2.700 | -0.300 | 2.233 |
| 9 | 2025-W05 | 9 | 3 | 0.333 | -2.530 | -0.281 | 3.563 |

- En `top 8`, las 5 peores semanas suman **-20.82** de profit frente a un total final de **-7.62**.
- En `top 9`, las 5 peores semanas suman **-19.64** frente a un total final de **-7.24**.
- Eso significa que el problema no es solo un promedio flojo: hay semanas de choque que destruyen lo ganado en las semanas buenas.

## Rango de BDI

| rank_desc | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- |
| 1.000 | 15.000 | 6.000 | 0.400 | -1.620 | -0.108 | 3.960 |
| 2.000 | 15.000 | 7.000 | 0.467 | 0.600 | 0.040 | 2.301 |
| 3.000 | 15.000 | 6.000 | 0.400 | -1.800 | -0.120 | 2.283 |
| 4.000 | 15.000 | 6.000 | 0.400 | -1.840 | -0.123 | 2.272 |
| 5.000 | 15.000 | 6.000 | 0.400 | -1.660 | -0.111 | 2.259 |
| 6.000 | 15.000 | 7.000 | 0.467 | 0.800 | 0.053 | 2.237 |
| 7.000 | 15.000 | 6.000 | 0.400 | -0.550 | -0.037 | 2.270 |
| 8.000 | 15.000 | 6.000 | 0.400 | -1.550 | -0.103 | 2.246 |
| 9.000 | 15.000 | 7.000 | 0.467 | 0.380 | 0.025 | 2.225 |
| 10.000 | 15.000 | 2.000 | 0.133 | -10.550 | -0.703 | 2.343 |
| 11.000 | 15.000 | 5.000 | 0.333 | -3.660 | -0.244 | 2.170 |
| 12.000 | 15.000 | 6.000 | 0.400 | -1.640 | -0.109 | 2.205 |

| top_n | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- |
| 1.000 | 15.000 | 6.000 | 0.400 | -1.620 | -0.108 | 3.960 |
| 2.000 | 30.000 | 13.000 | 0.433 | -1.020 | -0.034 | 3.130 |
| 3.000 | 45.000 | 19.000 | 0.422 | -2.820 | -0.063 | 2.848 |
| 4.000 | 60.000 | 25.000 | 0.417 | -4.660 | -0.078 | 2.704 |
| 5.000 | 75.000 | 31.000 | 0.413 | -6.320 | -0.084 | 2.615 |
| 6.000 | 90.000 | 38.000 | 0.422 | -5.520 | -0.061 | 2.552 |
| 7.000 | 105.000 | 44.000 | 0.419 | -6.070 | -0.058 | 2.512 |
| 8.000 | 120.000 | 50.000 | 0.417 | -7.620 | -0.064 | 2.478 |
| 9.000 | 135.000 | 57.000 | 0.422 | -7.240 | -0.054 | 2.450 |
| 10.000 | 150.000 | 59.000 | 0.393 | -17.790 | -0.119 | 2.440 |
| 11.000 | 165.000 | 64.000 | 0.388 | -21.450 | -0.130 | 2.415 |
| 12.000 | 180.000 | 70.000 | 0.389 | -23.090 | -0.128 | 2.398 |
| 13.000 | 195.000 | 74.000 | 0.379 | -29.520 | -0.151 | 2.386 |
| 14.000 | 210.000 | 79.000 | 0.376 | -33.790 | -0.161 | 2.374 |
| 15.000 | 225.000 | 83.000 | 0.369 | -39.790 | -0.177 | 2.362 |

Lectura:

- Ni siquiera los puestos mas altos del ranking BDI salvan la regla. El `rank 1` sale negativo y con cuota media muy inflada.
- `top 1` a `top 15` se mantienen en terreno negativo; no aparece un umbral claro que rescate la estrategia completa.

## Bookmakers mas problematicos

| top_n | Mejor_Casa | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | betrivers | 24 | 8 | 0.333 | -5.890 | -0.245 | 2.257 |
| 8 | onexbet | 7 | 1 | 0.143 | -4.840 | -0.691 | 2.246 |
| 8 | unibet_eu | 21 | 8 | 0.381 | -2.400 | -0.114 | 2.314 |
| 8 | matchbook | 13 | 6 | 0.462 | 0.380 | 0.029 | 2.234 |
| 8 | unibet | 32 | 15 | 0.469 | 1.600 | 0.050 | 3.124 |

| top_n | Mejor_Casa | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | betrivers | 28 | 9 | 0.321 | -7.830 | -0.280 | 2.240 |
| 9 | onexbet | 8 | 1 | 0.125 | -5.840 | -0.730 | 2.230 |
| 9 | matchbook | 15 | 7 | 0.467 | 0.350 | 0.023 | 2.221 |
| 9 | unibet | 33 | 15 | 0.455 | 0.600 | 0.018 | 3.092 |
| 9 | unibet_eu | 23 | 10 | 0.435 | 0.750 | 0.033 | 2.337 |

Lectura:

- `betrivers` y `onexbet` destacan como los peores focos de perdida en esta regla.
- `pinnacle` no sale mal, pero la muestra es muy chica para convertirlo en regla util por si sola.

## Ligas mas problematicas

| top_n | Liga | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | Super League Switzerland | 6 | 1 | 0.167 | -3.570 | -0.595 | 2.213 |
| 8 | MLS | 5 | 1 | 0.200 | -2.600 | -0.520 | 2.226 |
| 8 | Liga MX | 6 | 2 | 0.333 | -1.900 | -0.317 | 2.153 |
| 8 | La Liga 2 | 6 | 2 | 0.333 | -1.300 | -0.217 | 2.393 |
| 8 | Serie B | 10 | 4 | 0.400 | -1.080 | -0.108 | 2.241 |

| top_n | Liga | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | Super League Switzerland | 6 | 1 | 0.167 | -3.570 | -0.595 | 2.213 |
| 9 | La Liga 2 | 7 | 2 | 0.286 | -2.300 | -0.329 | 2.437 |
| 9 | Liga MX | 6 | 2 | 0.333 | -1.900 | -0.317 | 2.153 |
| 9 | MLS | 6 | 2 | 0.333 | -1.540 | -0.257 | 2.198 |
| 9 | Premiership | 5 | 2 | 0.400 | -0.970 | -0.194 | 2.064 |

## Posibles rescates

- `Over 2.5` dentro del `top 8/9`, especialmente alrededor de cuotas `2.2` a `2.4`, es la unica veta que parece tener algo de aire.
- `Under 2.5` como cuota mayor dentro del top BDI no merece confianza; hoy lo trataria como un filtro de exclusion, no como una senal.
- Cualquier ajuste que salga de esta autopsia debe considerarse **hipotesis nueva**, porque esta construido mirando el historico perdedor.

## Conclusion

- Tu intuicion sobre usar BDI para detectar desacuerdo era razonable, pero en este historico robusto la regla final termina sesgada hacia cuotas demasiado agresivas.
- La muerte de la estrategia no viene por falta total de semanas buenas; viene porque las semanas malas y el lado `Under 2.5` de cuota mayor destruyen el edge.
- Si quieres seguir explotando BDI, yo no lo usaria mas como estrategia standalone. Solo lo dejaria como variable auxiliar para filtrar otras reglas que ya sean positivas por si mismas.
