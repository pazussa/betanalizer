# Calibración de Confianza (20251215_160129)

Input: `data/master_dataset_deduped.csv`

Output CSV: `data/master_dataset_deduped_calibrado.csv`

Split: time-based (Fecha_Hora_Colombia), test_frac=0.2

## Métricas

- AUC (Calibrada) train=0.6507 test=0.6690
- AUC (Confianza actual) train=0.5082 test=0.5895

## ROI top 20% (seleccionando por score)

| score | split | n | winrate | ROI | avg_odds |
|---|---:|---:|---:|---:|---:|
| Calibrada(P_Win) | train | 58 | 74.1% | -5.33% | 1.278 |
| Calibrada(P_Win) | test | 14 | 85.7% | +2.43% | 1.205 |
| Confianza actual | train | 58 | 58.6% | +5.17% | 1.846 |
| Confianza actual | test | 14 | 85.7% | +33.43% | 1.614 |

## Coeficientes (logit)

| feature                             |         coef |
|:------------------------------------|-------------:|
| bias                                |  0.188438    |
| num:Num_Casas                       |  0.041155    |
| cat:Tipo_Mercado=Doble Chance       |  0.0209578   |
| num:Margen_Casa_Pct                 |  0.000757174 |
| num:Score_Final                     | -0.00745056  |
| cat:Tipo_Mercado=Goles (Over/Under) | -0.0209578   |
| num:Volatilidad_Pct                 | -0.037264    |
| num:Diferencia_Cuota_Promedio       | -0.0706175   |
| num:Cuota_Promedio_Mercado          | -0.0984717   |
| num:Mejor_Cuota                     | -0.100075    |

