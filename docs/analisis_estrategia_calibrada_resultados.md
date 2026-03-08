# Analisis de resultados de la rama estrategia calibrada

Rama analizada: `origin/estrategia-confianza-calibrada`.

## Resumen ejecutivo

- CSV con resultado util extraidos: **56**.
- Filas en la union cruda: **33,474**.
- Filas con target binario usable: **18,714**.
- Filas deduplicadas para analisis: **2,045**.
- Duplicados removidos entre backups/reconstrucciones/versiones: **16,669**.
- Hit rate global deduplicado: **54.77%**.
- ROI unitario medio deduplicado: **-0.068**.

## Hallazgos principales

- `cuota_promedio_mercado` tiende a ser menor en aciertos (diff=-0.2131, p=9.414e-35, d=-0.516).
- `mejor_cuota` tiende a ser menor en aciertos (diff=-0.2203, p=1.295e-34, d=-0.512).
- `confianza_calibrada` tiende a ser mayor en aciertos (diff=3.0721, p=4.595e-22, d=0.457).
- `p_win_calibrada` tiende a ser mayor en aciertos (diff=0.0307, p=4.595e-22, d=0.457).
- `diferencia_cuota_promedio` tiende a ser menor en aciertos (diff=-0.0072, p=3.933e-05, d=-0.208).
- Mercado destacado: `Under 3.5` con n=66, hit_rate=66.67%, ROI=0.152.
- Mercado destacado: `Under 2.5` con n=414, hit_rate=50.72%, ROI=-0.028.
- Mercado destacado: `X2` con n=482, hit_rate=56.64%, ROI=-0.055.
- Mejor regla conjunta encontrada: `diferencia_cuota_promedio >= 0.0416 AND Liga == Serie A` (n=36, hit_rate=63.89%, ROI=0.335).
- Mejor modelo fuera de muestra: `random_forest` con ROC AUC=0.629 y accuracy=0.601.

## Artefactos generados

- Carpeta de CSV con resultado: `datasets\estrategia_calibrada_con_resultado`.
- `manifest_resultados.csv`: inventario de archivos extraidos.
- `consolidado_resultados_raw.csv`: union de todas las filas con metadatos de origen.
- `consolidado_resultados_analisis.csv`: dataset deduplicado y normalizado usado para estadistica y ML.
- `metricas_numericas.csv`, `reglas_segmentos.csv`, `metricas_modelos.csv`, `importancia_features.csv`, `bandas_probabilidad.csv`.

## Inventario de archivos extraidos

| Archivo original | Filas | Filas con resultado | Columnas de resultado |
| --- | ---: | ---: | --- |
| `analisis_mercados_20251226_191537_con_resultados.csv` | 238 | 238 | Resultado, Resultado_Segunda, Marcador |
| `bdi_top_by_match_with_rendimiento.csv` | 44 | 44 | Resultado, Marcador |
| `filtro2_resultados_con_marcador_real.csv` | 80 | 80 | Resultado, Marcador |
| `filtro2_resultados_con_marcador_real_con_BDI.csv` | 80 | 80 | Resultado, Marcador |
| `historical_con_resultados/backup/historical_20250103_con_resultados.csv` | 326 | 326 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250110_con_resultados.csv` | 402 | 402 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250117_con_resultados.csv` | 650 | 650 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250124_con_resultados.csv` | 706 | 706 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250131_con_resultados.csv` | 710 | 710 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250207_con_resultados.csv` | 668 | 668 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250214_con_resultados.csv` | 858 | 858 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250221_con_resultados.csv` | 908 | 908 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250228_con_resultados.csv` | 856 | 856 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250307_con_resultados.csv` | 866 | 866 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250314_con_resultados.csv` | 906 | 906 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250321_con_resultados.csv` | 158 | 158 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup/historical_20250328_con_resultados.csv` | 902 | 902 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250103_con_resultados.csv` | 326 | 326 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250110_con_resultados.csv` | 402 | 402 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250117_con_resultados.csv` | 650 | 650 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250124_con_resultados.csv` | 706 | 706 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250131_con_resultados.csv` | 710 | 710 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250207_con_resultados.csv` | 668 | 668 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250214_con_resultados.csv` | 858 | 858 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250221_con_resultados.csv` | 908 | 908 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250228_con_resultados.csv` | 856 | 856 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250307_con_resultados.csv` | 866 | 866 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250314_con_resultados.csv` | 906 | 906 | Acerto, Score, Total_Goles |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250328_con_resultados.csv` | 902 | 902 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250103_con_resultados.csv` | 248 | 248 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250110_con_resultados.csv` | 314 | 314 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250117_con_resultados.csv` | 504 | 504 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250124_con_resultados.csv` | 534 | 534 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250131_con_resultados.csv` | 538 | 538 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250207_con_resultados.csv` | 492 | 492 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250214_con_resultados.csv` | 654 | 654 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250221_con_resultados.csv` | 694 | 694 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250228_con_resultados.csv` | 652 | 652 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250307_con_resultados.csv` | 658 | 658 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250314_con_resultados.csv` | 682 | 682 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250321_con_resultados.csv` | 140 | 140 | Acerto, Score, Total_Goles |
| `historical_con_resultados/historical_20250328_con_resultados.csv` | 722 | 722 | Acerto, Score, Total_Goles |
| `data/historico_completo.csv` | 1756 | 1756 | Resultado, Marcador, Goles_Local, Goles_Visitante |
| `resultados_definitivos/historical_20250103_con_resultados.csv` | 244 | 244 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250110_con_resultados.csv` | 308 | 308 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250117_con_resultados.csv` | 492 | 492 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250124_con_resultados.csv` | 524 | 524 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250131_con_resultados.csv` | 528 | 528 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250207_con_resultados.csv` | 488 | 488 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250214_con_resultados.csv` | 648 | 648 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250221_con_resultados.csv` | 688 | 688 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250228_con_resultados.csv` | 644 | 644 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250307_con_resultados.csv` | 646 | 646 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250314_con_resultados.csv` | 670 | 670 | Acerto, Score, Total_Goles |
| `resultados_definitivos/historical_20250328_con_resultados.csv` | 716 | 716 | Acerto, Score, Total_Goles |
| `REVISAR-analisis_mercados_20251220_214421_con_BDI_fair_con_resultados.csv` | 174 | 174 | Resultado, Marcador |

## Variables numericas con mas senal

| feature | n | hit_mean | miss_mean | mean_diff | cohens_d | mannwhitney_p |
| --- | --- | --- | --- | --- | --- | --- |
| cuota_promedio_mercado | 2045 | 1.6719 | 1.8851 | -0.2131 | -0.5157 | 0.0000 |
| mejor_cuota | 2045 | 1.7020 | 1.9223 | -0.2203 | -0.5124 | 0.0000 |
| confianza_calibrada | 1621 | 56.2982 | 53.2261 | 3.0721 | 0.4569 | 0.0000 |
| p_win_calibrada | 1621 | 0.5630 | 0.5323 | 0.0307 | 0.4569 | 0.0000 |
| diferencia_cuota_promedio | 2045 | 0.0301 | 0.0373 | -0.0072 | -0.2076 | 0.0000 |
| num_casas | 2045 | 5.0312 | 4.7114 | 0.3199 | 0.0500 | 0.0051 |
| bdi_n_bookmakers | 344 | 15.7011 | 12.6353 | 3.0659 | 0.2645 | 0.0475 |
| volatilidad_pct | 2045 | 1.3641 | 1.4724 | -0.1083 | -0.1213 | 0.0620 |
| confianza | 1621 | 39.8199 | 40.9578 | -1.1378 | -0.0720 | 0.1591 |
| edge_pct | 2045 | 1.7407 | 1.8887 | -0.1480 | -0.0987 | 0.1879 |

## Segmentacion por market_family

| market_family | n | hit_rate | roi |
| --- | --- | --- | --- |
| totals | 1080 | 0.4926 | -0.0640 |
| double_chance | 965 | 0.6093 | -0.0721 |

## Segmentacion por Mercado

| Mercado | n | hit_rate | roi |
| --- | --- | --- | --- |
| Under 3.5 | 66 | 0.6667 | 0.1517 |
| Under 2.5 | 414 | 0.5072 | -0.0282 |
| X2 | 482 | 0.5664 | -0.0547 |
| Over 2.5 | 406 | 0.4901 | -0.0760 |
| 1X | 483 | 0.6522 | -0.0895 |
| Over 3.5 | 66 | 0.3333 | -0.2980 |

## Segmentacion por Tipo_Mercado

| Tipo_Mercado | n | hit_rate | roi |
| --- | --- | --- | --- |
| Goles (Over/Under) | 1080 | 0.4926 | -0.0640 |
| Doble Chance | 965 | 0.6093 | -0.0721 |

## Segmentacion por Liga

| Liga | n | hit_rate | roi |
| --- | --- | --- | --- |
| Europa League | 72 | 0.5972 | 0.0889 |
| Belgium First Div | 78 | 0.6026 | 0.0538 |
| Bundesliga | 65 | 0.5846 | 0.0109 |
| Eredivisie | 93 | 0.5699 | 0.0092 |
| League 2 | 57 | 0.5614 | -0.0211 |
| Premiership | 92 | 0.5543 | -0.0256 |
| A-League | 38 | 0.5526 | -0.0435 |
| La Liga 2 | 92 | 0.5435 | -0.0483 |
| Serie A | 129 | 0.5271 | -0.0488 |
| Austrian Bundesliga | 46 | 0.5652 | -0.0509 |

## Segmentacion por Mejor_Casa

| Mejor_Casa | n | hit_rate | roi |
| --- | --- | --- | --- |
| codere_it | 294 | 0.5510 | -0.0437 |
| betsson | 409 | 0.5257 | -0.0630 |
| pinnacle | 972 | 0.5525 | -0.0716 |
| marathonbet | 150 | 0.6067 | -0.0810 |
| coolbet | 25 | 0.4400 | -0.1556 |

## Segmentacion por source_group

| source_group | n | hit_rate | roi |
| --- | --- | --- | --- |
| analisis_mercados | 184 | 0.5435 | -0.0538 |
| historico_maestro | 1621 | 0.5595 | -0.0647 |
| filtro2 | 80 | 0.4875 | -0.0786 |
| revision_manual | 160 | 0.4625 | -0.1106 |

## Reglas conjuntas candidatas

| rule | n | hit_rate | roi | hit_lift | roi_lift |
| --- | --- | --- | --- | --- | --- |
| diferencia_cuota_promedio >= 0.0416 AND Liga == Serie A | 36 | 0.6389 | 0.3354 | 0.0912 | 0.4032 |
| volatilidad_pct >= 1.8700 AND num_casas <= 2.0000 AND Mercado == Over 2.5 | 36 | 0.6389 | 0.2636 | 0.0912 | 0.3315 |
| volatilidad_pct >= 1.8700 AND Mejor_Casa == betsson AND source_group == historico_maestro | 62 | 0.5323 | 0.2324 | -0.0154 | 0.3003 |
| volatilidad_pct >= 1.8700 AND confianza_calibrada <= 51.1500 AND Mejor_Casa == betsson | 51 | 0.4902 | 0.2314 | -0.0575 | 0.2992 |
| volatilidad_pct >= 1.8700 AND p_win_calibrada <= 0.5115 AND Mejor_Casa == betsson | 51 | 0.4902 | 0.2314 | -0.0575 | 0.2992 |
| mejor_cuota >= 2.0200 AND edge_pct >= 2.3121 AND Mejor_Casa == betsson | 32 | 0.4375 | 0.2263 | -0.1102 | 0.2941 |
| volatilidad_pct >= 1.8700 AND edge_pct >= 2.3121 AND Mejor_Casa == betsson | 33 | 0.4545 | 0.2130 | -0.0931 | 0.2809 |
| diferencia_cuota_promedio >= 0.0416 AND confianza_calibrada <= 51.1500 AND Mejor_Casa == betsson | 49 | 0.4694 | 0.2090 | -0.0783 | 0.2768 |
| diferencia_cuota_promedio >= 0.0416 AND p_win_calibrada <= 0.5115 AND Mejor_Casa == betsson | 49 | 0.4694 | 0.2090 | -0.0783 | 0.2768 |
| diferencia_cuota_promedio >= 0.0416 AND Mejor_Casa == betsson AND source_group == historico_maestro | 49 | 0.4694 | 0.2090 | -0.0783 | 0.2768 |
| volatilidad_pct >= 1.8700 AND num_casas <= 2.0000 AND Mejor_Casa == betsson | 50 | 0.5800 | 0.2044 | 0.0323 | 0.2722 |
| diferencia_cuota_promedio >= 0.0416 AND edge_pct >= 2.3121 AND Mejor_Casa == betsson | 34 | 0.4412 | 0.2041 | -0.1065 | 0.2720 |
| diferencia_cuota_promedio >= 0.0416 AND num_casas <= 2.0000 AND Mejor_Casa == betsson | 33 | 0.5455 | 0.1973 | -0.0022 | 0.2651 |
| margen_casa_pct >= 6.0800 AND Mercado == Under 3.5 | 34 | 0.7059 | 0.1915 | 0.1582 | 0.2593 |
| margen_casa_pct >= 6.0800 AND market_family == totals AND Mercado == Under 3.5 | 34 | 0.7059 | 0.1915 | 0.1582 | 0.2593 |
| margen_casa_pct >= 6.0800 AND Mercado == Under 3.5 AND Tipo_Mercado == Goles (Over/Under) | 34 | 0.7059 | 0.1915 | 0.1582 | 0.2593 |
| edge_pct >= 2.3121 AND Mejor_Casa == betsson | 36 | 0.4444 | 0.1844 | -0.1032 | 0.2523 |
| volatilidad_pct >= 1.8700 AND margen_casa_pct >= 6.0800 AND num_casas <= 2.0000 | 30 | 0.5667 | 0.1813 | 0.0190 | 0.2492 |
| mejor_cuota <= 1.5100 AND volatilidad_pct >= 1.8700 AND Mercado == 1X | 32 | 0.8750 | 0.1707 | 0.3273 | 0.2385 |
| volatilidad_pct >= 1.8700 AND market_family == totals AND Mejor_Casa == betsson | 55 | 0.5636 | 0.1691 | 0.0160 | 0.2369 |

## Metricas de modelos

| model | train_rows | test_rows | accuracy | roc_auc | brier | log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| random_forest | 1636 | 409 | 0.6015 | 0.6285 | 0.2407 | 0.6744 |
| logistic | 1636 | 409 | 0.4914 | 0.4741 | 0.2828 | 0.8462 |

## Features mas importantes

| model | feature | importance |
| --- | --- | --- |
| logistic | cat__Mejor_Casa_bwin | 0.7089 |
| logistic | num__diferencia_cuota_promedio | 0.5941 |
| logistic | num__cuota_promedio_mercado | 0.3652 |
| logistic | cat__Liga_Bundesliga | 0.3493 |
| logistic | cat__Liga_Primera División | 0.3447 |
| logistic | cat__Liga_Europa League | 0.3223 |
| logistic | num__edge_pct | 0.3196 |
| logistic | num__mejor_cuota | 0.3183 |
| logistic | cat__Mercado_Over 3.5 | 0.3176 |
| logistic | cat__Liga_Ligue 2 | 0.2764 |
| logistic | cat__Liga_Swiss Superleague | 0.2656 |
| logistic | cat__Liga_Belgium First Div | 0.2603 |
| logistic | cat__Mejor_Casa_betsson | 0.2298 |
| logistic | cat__Liga_Serie B | 0.2130 |
| logistic | cat__Liga_Eliteserien | 0.2024 |
| logistic | cat__Mercado_Under 1.5 | 0.1892 |
| logistic | cat__Liga_League 1 | 0.1869 |
| logistic | cat__Mercado_Under 3.5 | 0.1636 |
| logistic | cat__Mejor_Casa_marathonbet | 0.1624 |
| logistic | cat__Mejor_Casa_pinnacle | 0.1615 |
| random_forest | num__cuota_promedio_mercado | 0.1734 |
| random_forest | num__mejor_cuota | 0.1627 |
| random_forest | num__p_win_calibrada | 0.1177 |
| random_forest | num__confianza_calibrada | 0.1177 |
| random_forest | num__volatilidad_pct | 0.0543 |

## Bandas de probabilidad del test

| model | prob_bin | n | hit_rate | roi | prob_min | prob_max |
| --- | --- | --- | --- | --- | --- | --- |
| logistic | (-0.000999999849, 0.339] | 82 | 0.5732 | -0.0012 | 0.0000 | 0.3387 |
| logistic | (0.339, 0.419] | 82 | 0.4390 | -0.1441 | 0.3399 | 0.4194 |
| logistic | (0.419, 0.462] | 81 | 0.5185 | -0.0289 | 0.4195 | 0.4615 |
| logistic | (0.462, 0.514] | 82 | 0.5000 | -0.0964 | 0.4620 | 0.5140 |
| logistic | (0.514, 0.805] | 82 | 0.4756 | -0.1503 | 0.5145 | 0.8051 |
| random_forest | (0.307, 0.405] | 82 | 0.3537 | -0.2405 | 0.3078 | 0.4046 |
| random_forest | (0.405, 0.435] | 82 | 0.4268 | -0.0970 | 0.4053 | 0.4351 |
| random_forest | (0.435, 0.485] | 81 | 0.4691 | -0.0884 | 0.4351 | 0.4827 |
| random_forest | (0.485, 0.527] | 82 | 0.5854 | -0.0009 | 0.4860 | 0.5270 |
| random_forest | (0.527, 0.61] | 82 | 0.6707 | 0.0051 | 0.5271 | 0.6096 |

## Notas metodologicas

- La union cruda conserva todos los archivos con resultado disponible por fila; esto incluye backups y reconstrucciones.
- El analisis usa la version deduplicada para evitar que un mismo evento repetido en backups sesgue tendencias y modelos.
- El target binario se toma solo de columnas explicitamente observadas (`Resultado`, `Acerto`, etc.).
- Los modelos usan solo variables prepartido o de mercado, no columnas de resultado real.
