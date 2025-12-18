# Calibración de Confianza (20251215_204815)

Input: `/home/user/Escritorio/bets2/betanalizer/data/master_dataset_deduped_verified.csv`

Output CSV: `/home/user/Escritorio/bets2/betanalizer/data/master_dataset_deduped_verified_calibrado.csv`

Split: time-based (Fecha_Hora_Colombia), test_frac=0.2

Filas verificadas (Acertado/Fallido): 489 (train=391 test=98)

## Métricas

- Calibrada: AUC train=0.6406 test=0.6943
- Calibrada: LogLoss train=0.6658 test=0.6409
- Calibrada: Brier train=0.2366 test=0.2251
- Confianza actual (AUC): train=0.5169 test=0.5275

## Calibración (TEST, deciles de P_Win_Calibrada)

|   bin |   n |    p_min |    p_max |   p_mean |   winrate |         gap |
|------:|----:|---------:|---------:|---------:|----------:|------------:|
|     0 |  10 | 0.114153 | 0.475954 | 0.360692 |   30      | -0.0606917  |
|     1 |  10 | 0.477235 | 0.499901 | 0.49029  |   20      | -0.29029    |
|     2 |  10 | 0.502936 | 0.518753 | 0.509659 |   50      | -0.00965891 |
|     3 |   9 | 0.518767 | 0.533051 | 0.527975 |   77.7778 |  0.249803   |
|     4 |  10 | 0.533499 | 0.564042 | 0.551092 |   50      | -0.0510916  |
|     5 |  10 | 0.564908 | 0.579536 | 0.573551 |   80      |  0.226449   |
|     6 |   9 | 0.580067 | 0.591749 | 0.585071 |   11.1111 | -0.47396    |
|     7 |  10 | 0.592704 | 0.617521 | 0.605501 |   60      | -0.00550126 |
|     8 |  10 | 0.61795  | 0.646198 | 0.632134 |   80      |  0.167866   |
|     9 |  10 | 0.647428 | 0.673426 | 0.659082 |  100      |  0.340918   |


## ROI top 20% (seleccionando por score)

| score | split | n | winrate | ROI | avg_odds |
|---|---:|---:|---:|---:|---:|
| Calibrada(P_Win) | train | 78 | 75.6% | -3.04% | 1.282 |
| Calibrada(P_Win) | test | 19 | 94.7% | +13.79% | 1.208 |
| Confianza actual | train | 78 | 60.3% | +8.10% | 1.836 |
| Confianza actual | test | 19 | 78.9% | +26.32% | 1.664 |

## Coeficientes (logit)

| feature                             |        coef |   odds_ratio |
|:------------------------------------|------------:|-------------:|
| bias                                |  0.212793   |     1.23713  |
| num:Mejor_Cuota                     | -0.0934592  |     0.910775 |
| num:Cuota_Promedio_Mercado          | -0.0916107  |     0.91246  |
| num:Diferencia_Cuota_Promedio       | -0.0749548  |     0.927785 |
| num:Volatilidad_Pct                 | -0.0388237  |     0.96192  |
| num:Num_Casas                       |  0.0320849  |     1.03261  |
| cat:Tipo_Mercado=Doble Chance       |  0.0207497  |     1.02097  |
| cat:Tipo_Mercado=Goles (Over/Under) | -0.0207497  |     0.979464 |
| num:Margen_Casa_Pct                 |  0.00391674 |     1.00392  |
| num:Score_Final                     | -0.00305653 |     0.996948 |

