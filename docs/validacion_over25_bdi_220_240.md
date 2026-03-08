# Validacion de Over 2.5 en top BDI con cuota 2.2-2.4

Hipotesis validada: `Over 2.5` dentro del universo `cuota mayor entre Over 2.5 y Under 2.5`, restringido a `top 8/9` por `BDI_jsd_fair` de fin de semana y cuotas entre `2.2` y `2.4`.

## Resultado global

| segment | bets | hits | hit_rate | profit_total | roi | roi_ci95_lo | roi_ci95_hi | avg_odds | weeks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top8_over25_2p2_2p4 | 22 | 11 | 0.500 | 3.070 | 0.140 | -0.285 | 0.647 | 2.275 | 12 |
| top9_over25_2p2_2p4 | 25 | 13 | 0.520 | 4.570 | 0.183 | -0.271 | 0.640 | 2.276 | 12 |

Lectura:

- `top 8`: **11/22**, profit **3.07**, ROI **0.140**.
- `top 9`: **13/25**, profit **4.57**, ROI **0.183**.
- Ambos salen positivos en la muestra completa.
- Pero los intervalos bootstrap siguen cruzando cero; la muestra es pequena y no permite afirmar edge cerrado.

## Contra el universo comparable

| top_n | segment | bets | hits | hit_rate | profit_total | roi | avg_odds | weeks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | selected | 22 | 11 | 0.500 | 3.070 | 0.140 | 2.275 | 12 |
| 8 | rest_same_weeks | 201 | 72 | 0.358 | -38.090 | -0.190 | 2.273 | 12 |
| 8 | all_same_weeks | 223 | 83 | 0.372 | -35.020 | -0.157 | 2.274 | 12 |

| top_n | segment | bets | hits | hit_rate | profit_total | roi | avg_odds | weeks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | selected | 25 | 13 | 0.520 | 4.570 | 0.183 | 2.276 | 12 |
| 9 | rest_same_weeks | 198 | 70 | 0.354 | -39.590 | -0.200 | 2.273 | 12 |
| 9 | all_same_weeks | 223 | 83 | 0.372 | -35.020 | -0.157 | 2.274 | 12 |

Lectura:

- El universo comparable es `Over 2.5` con cuota `2.2-2.4` dentro del mismo mecanismo de eleccion `cuota mayor`.
- En ese universo, el filtro `top BDI` si agrega valor: el universo completo pierde fuerte y el subconjunto `top 8/9` pasa a positivo.

## Validacion temporal

| top_n | split | bets | hits | hit_rate | profit_total | roi | profitable_weeks | weeks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | train | 10 | 5 | 0.500 | 1.330 | 0.133 | 5 | 6 |
| 8 | valid | 8 | 4 | 0.500 | 1.130 | 0.141 | 1 | 3 |
| 8 | test | 4 | 2 | 0.500 | 0.610 | 0.152 | 1 | 3 |

| top_n | split | bets | hits | hit_rate | profit_total | roi | profitable_weeks | weeks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | train | 12 | 6 | 0.500 | 1.630 | 0.136 | 5 | 6 |
| 9 | valid | 8 | 4 | 0.500 | 1.130 | 0.141 | 1 | 3 |
| 9 | test | 5 | 3 | 0.600 | 1.810 | 0.362 | 2 | 3 |

Lectura:

- Use un corte cronologico simple `train 6 semanas`, `valid 3`, `test 3` sobre las semanas que realmente tienen apuestas para esta hipotesis.
- `top 8` y `top 9` se mantienen positivos en `train`, `valid` y `test`.
- Eso es mejor que el BDI standalone, que se caia cuando ampliabas la muestra.
- Aun asi, el numero de apuestas por tramo es chico; sigue siendo una senal prometedora, no una estrategia cerrada.

## Desglose semanal

| top_n | week_id | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | 2025-W01 | 1 | 1.000 | 1.000 | 1.250 | 1.250 | 2.250 |
| 8 | 2025-W02 | 4 | 0.000 | 0.000 | -4.000 | -1.000 | 2.292 |
| 8 | 2025-W03 | 1 | 1.000 | 1.000 | 1.360 | 1.360 | 2.360 |
| 8 | 2025-W04 | 1 | 1.000 | 1.000 | 1.200 | 1.200 | 2.200 |
| 8 | 2025-W05 | 2 | 1.000 | 0.500 | 0.200 | 0.100 | 2.200 |
| 8 | 2025-W06 | 1 | 1.000 | 1.000 | 1.320 | 1.320 | 2.320 |
| 8 | 2025-W07 | 1 | 0.000 | 0.000 | -1.000 | -1.000 | 2.200 |
| 8 | 2025-W09 | 5 | 4.000 | 0.800 | 4.130 | 0.826 | 2.266 |
| 8 | 2025-W10 | 2 | 0.000 | 0.000 | -2.000 | -1.000 | 2.330 |
| 8 | 2025-W11 | 1 | 0.000 | 0.000 | -1.000 | -1.000 | 2.300 |
| 8 | 2025-W13 | 1 | 0.000 | 0.000 | -1.000 | -1.000 | 2.260 |
| 8 | 2025-W51 | 2 | 2.000 | 1.000 | 2.610 | 1.305 | 2.305 |

| top_n | week_id | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | 2025-W01 | 1 | 1.000 | 1.000 | 1.250 | 1.250 | 2.250 |
| 9 | 2025-W02 | 4 | 0.000 | 0.000 | -4.000 | -1.000 | 2.292 |
| 9 | 2025-W03 | 1 | 1.000 | 1.000 | 1.360 | 1.360 | 2.360 |
| 9 | 2025-W04 | 2 | 2.000 | 1.000 | 2.500 | 1.250 | 2.250 |
| 9 | 2025-W05 | 2 | 1.000 | 0.500 | 0.200 | 0.100 | 2.200 |
| 9 | 2025-W06 | 2 | 1.000 | 0.500 | 0.320 | 0.160 | 2.335 |
| 9 | 2025-W07 | 1 | 0.000 | 0.000 | -1.000 | -1.000 | 2.200 |
| 9 | 2025-W09 | 5 | 4.000 | 0.800 | 4.130 | 0.826 | 2.266 |
| 9 | 2025-W10 | 2 | 0.000 | 0.000 | -2.000 | -1.000 | 2.330 |
| 9 | 2025-W11 | 1 | 0.000 | 0.000 | -1.000 | -1.000 | 2.300 |
| 9 | 2025-W13 | 2 | 1.000 | 0.500 | 0.200 | 0.100 | 2.230 |
| 9 | 2025-W51 | 2 | 2.000 | 1.000 | 2.610 | 1.305 | 2.305 |

## Bookmakers

| top_n | Mejor_Casa | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | unibet | 6 | 4.000 | 0.667 | 3.060 | 0.510 | 2.263 |
| 8 | unibet_eu | 2 | 1.000 | 0.500 | 0.350 | 0.175 | 2.350 |
| 8 | matchbook | 5 | 2.000 | 0.400 | -0.360 | -0.072 | 2.300 |
| 8 | betrivers | 6 | 2.000 | 0.333 | -1.480 | -0.247 | 2.253 |

| top_n | Mejor_Casa | bets | hits | hit_rate | profit_total | roi | avg_odds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | unibet | 6 | 4.000 | 0.667 | 3.060 | 0.510 | 2.263 |
| 9 | betsson | 2 | 2.000 | 1.000 | 2.500 | 1.250 | 2.250 |
| 9 | unibet_eu | 3 | 2.000 | 0.667 | 1.650 | 0.550 | 2.333 |
| 9 | matchbook | 5 | 2.000 | 0.400 | -0.360 | -0.072 | 2.300 |
| 9 | betrivers | 7 | 2.000 | 0.286 | -2.480 | -0.354 | 2.267 |

## Conclusion

- La hipotesis **si merece seguimiento**: es una de las pocas subzonas del BDI que sale positiva y ademas se mantiene positiva en un corte temporal simple.
- La mejora parece venir de combinar tres cosas a la vez: `Over 2.5`, `BDI alto` y cuota media-larga controlada (`2.2-2.4`).
- No la daria todavia como estrategia principal por el tamano muestral: `22` apuestas en `top 8` y `25` en `top 9`.
- Si tuviera que elegir una hoy, `top 9` queda un poco mejor que `top 8` por profit y ROI.
- Recomendacion operativa: tratarla como hipotesis secundaria en monitoreo, no al mismo nivel de robustez que las estrategias `Under` ya validadas.
