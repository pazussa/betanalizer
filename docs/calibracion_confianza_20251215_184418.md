# Calibración de Confianza (20251215_184418)

Input: `data/master_dataset_deduped.csv`

Output CSV: `data/master_dataset_deduped_calibrado.csv`

Split: time-based (Fecha_Hora_Colombia), test_frac=0.2

## Métricas

- AUC (Calibrada) train=0.6602 test=0.7047
- AUC (Confianza actual) train=0.4928 test=0.5395

## ROI top 20% (seleccionando por score)

| score | split | n | winrate | ROI | avg_odds |
|---|---:|---:|---:|---:|---:|
| Calibrada(P_Win) | train | 65 | 75.4% | -4.15% | 1.277 |
| Calibrada(P_Win) | test | 16 | 93.8% | +11.38% | 1.197 |
| Confianza actual | train | 65 | 58.5% | +3.92% | 1.822 |
| Confianza actual | test | 16 | 87.5% | +43.38% | 1.672 |

## Coeficientes (logit)

| feature                             |         coef |
|:------------------------------------|-------------:|
| bias                                |  0.248086    |
| num:Num_Casas                       |  0.0453111   |
| cat:Tipo_Mercado=Doble Chance       |  0.0233468   |
| num:Margen_Casa_Pct                 | -0.000778107 |
| num:Score_Final                     | -0.00226647  |
| cat:Tipo_Mercado=Goles (Over/Under) | -0.0233468   |
| num:Volatilidad_Pct                 | -0.0379913   |
| num:Diferencia_Cuota_Promedio       | -0.0762269   |
| num:Cuota_Promedio_Mercado          | -0.105       |
| num:Mejor_Cuota                     | -0.106732    |

