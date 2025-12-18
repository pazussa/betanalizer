# Calibración de Confianza (20251215_202957)

Input: `data/master_dataset_deduped.csv`

Output CSV: `data/master_dataset_deduped_calibrado.csv`

Split: time-based (Fecha_Hora_Colombia), test_frac=0.2

## Métricas

- AUC (Calibrada) train=0.6406 test=0.6943
- AUC (Confianza actual) train=0.5169 test=0.5275

## ROI top 20% (seleccionando por score)

| score | split | n | winrate | ROI | avg_odds |
|---|---:|---:|---:|---:|---:|
| Calibrada(P_Win) | train | 78 | 75.6% | -3.04% | 1.282 |
| Calibrada(P_Win) | test | 19 | 94.7% | +13.79% | 1.208 |
| Confianza actual | train | 78 | 60.3% | +8.10% | 1.836 |
| Confianza actual | test | 19 | 78.9% | +26.32% | 1.664 |

## Coeficientes (logit)

| feature                             |        coef |
|:------------------------------------|------------:|
| bias                                |  0.212793   |
| num:Num_Casas                       |  0.0320849  |
| cat:Tipo_Mercado=Doble Chance       |  0.0207497  |
| num:Margen_Casa_Pct                 |  0.00391674 |
| num:Score_Final                     | -0.00305653 |
| cat:Tipo_Mercado=Goles (Over/Under) | -0.0207497  |
| num:Volatilidad_Pct                 | -0.0388237  |
| num:Diferencia_Cuota_Promedio       | -0.0749548  |
| num:Cuota_Promedio_Mercado          | -0.0916107  |
| num:Mejor_Cuota                     | -0.0934592  |

