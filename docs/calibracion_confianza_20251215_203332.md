# Calibración de Confianza (20251215_203332)

Input: `/home/user/Escritorio/bets2/betanalizer/data/master_dataset_deduped.csv`

Output CSV: `/home/user/Escritorio/bets2/betanalizer/data/master_dataset_deduped_calibrado.csv`

Split: time-based (Fecha_Hora_Colombia), test_frac=0.4

Filas verificadas (Acertado/Fallido): 489 (train=293 test=196)

## Métricas

- Calibrada: AUC train=0.6335 test=0.6751
- Calibrada: LogLoss train=0.6695 test=0.6513
- Calibrada: Brier train=0.2383 test=0.2298
- Confianza actual (AUC): train=0.5305 test=0.5018

## Calibración (TEST, deciles de P_Win_Calibrada)

|   bin |   n |    p_min |    p_max |   p_mean |   winrate |        gap |
|------:|----:|---------:|---------:|---------:|----------:|-----------:|
|     0 |  20 | 0.111984 | 0.472622 | 0.393959 |   35      | -0.0439592 |
|     1 |  20 | 0.473031 | 0.495342 | 0.486893 |   40      | -0.0868925 |
|     2 |  19 | 0.495493 | 0.504821 | 0.500248 |   36.8421 | -0.131827  |
|     3 |  20 | 0.505378 | 0.523202 | 0.516162 |   55      |  0.0338376 |
|     4 |  19 | 0.523566 | 0.549659 | 0.534298 |   63.1579 |  0.0972809 |
|     5 |  20 | 0.550404 | 0.568423 | 0.560047 |   60      |  0.0399528 |
|     6 |  19 | 0.568779 | 0.580474 | 0.574684 |   47.3684 | -0.101     |
|     7 |  20 | 0.584262 | 0.610208 | 0.59897  |   65      |  0.0510304 |
|     8 |  19 | 0.611447 | 0.633953 | 0.62294  |   73.6842 |  0.113902  |
|     9 |  20 | 0.634534 | 0.657309 | 0.644138 |   90      |  0.255862  |


## Stress test: subiendo tamaño de TEST

|   test_frac |   n_train |   n_test |   auc_train |   auc_test |   logloss_test |   brier_test |
|------------:|----------:|---------:|------------:|-----------:|---------------:|-------------:|
|         0.2 |       391 |       98 |    0.640608 |   0.694292 |       0.640908 |     0.225123 |
|         0.3 |       342 |      147 |    0.625427 |   0.726568 |       0.640798 |     0.224582 |
|         0.4 |       293 |      196 |    0.633459 |   0.675146 |       0.651336 |     0.229786 |
|         0.5 |       244 |      245 |    0.605801 |   0.696835 |       0.657264 |     0.232432 |


## ROI top 20% (seleccionando por score)

| score | split | n | winrate | ROI | avg_odds |
|---|---:|---:|---:|---:|---:|
| Calibrada(P_Win) | train | 58 | 75.9% | -1.78% | 1.293 |
| Calibrada(P_Win) | test | 39 | 82.1% | +0.92% | 1.241 |
| Confianza actual | train | 58 | 58.6% | +6.52% | 1.852 |
| Confianza actual | test | 39 | 66.7% | +9.69% | 1.714 |

## Coeficientes (logit)

| feature                             |        coef |   odds_ratio |
|:------------------------------------|------------:|-------------:|
| bias                                |  0.186745   |     1.20532  |
| num:Mejor_Cuota                     | -0.08323    |     0.920139 |
| num:Cuota_Promedio_Mercado          | -0.0809352  |     0.922253 |
| num:Diferencia_Cuota_Promedio       | -0.0754273  |     0.927347 |
| num:Volatilidad_Pct                 | -0.0476076  |     0.953508 |
| cat:Tipo_Mercado=Doble Chance       |  0.0269815  |     1.02735  |
| cat:Tipo_Mercado=Goles (Over/Under) | -0.0269815  |     0.973379 |
| num:Num_Casas                       |  0.0266735  |     1.02703  |
| num:Score_Final                     |  0.00526731 |     1.00528  |
| num:Margen_Casa_Pct                 | -0.00203294 |     0.997969 |

