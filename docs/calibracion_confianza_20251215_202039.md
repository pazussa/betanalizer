# Calibración de Confianza (20251215_202039)

Input: `data/master_dataset_deduped.csv`

Output CSV: `data/master_dataset_deduped_calibrado.csv`

Split: time-based (Fecha_Hora_Colombia), test_frac=0.2

## Métricas

- AUC (Calibrada) train=0.6424 test=0.7053
- AUC (Confianza actual) train=0.5135 test=0.5366

## ROI top 20% (seleccionando por score)

| score | split | n | winrate | ROI | avg_odds |
|---|---:|---:|---:|---:|---:|
| Calibrada(P_Win) | train | 76 | 76.3% | -2.70% | 1.273 |
| Calibrada(P_Win) | test | 19 | 89.5% | +6.63% | 1.199 |
| Confianza actual | train | 76 | 60.5% | +8.50% | 1.834 |
| Confianza actual | test | 19 | 78.9% | +26.47% | 1.666 |

## Coeficientes (logit)

| feature                             |         coef |
|:------------------------------------|-------------:|
| bias                                |  0.213305    |
| num:Num_Casas                       |  0.0327098   |
| cat:Tipo_Mercado=Doble Chance       |  0.0200331   |
| num:Score_Final                     |  0.000903642 |
| num:Margen_Casa_Pct                 | -0.000755194 |
| cat:Tipo_Mercado=Goles (Over/Under) | -0.0200331   |
| num:Volatilidad_Pct                 | -0.0326368   |
| num:Diferencia_Cuota_Promedio       | -0.0704107   |
| num:Cuota_Promedio_Mercado          | -0.0947662   |
| num:Mejor_Cuota                     | -0.0962908   |

