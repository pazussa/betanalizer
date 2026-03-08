# Validacion de estrategias solo pinnacle

Se validaron reglas en dos modos de ejecucion:
- `strict_best_pinnacle`: solo filas donde `Mejor_Casa == pinnacle`.
- `pinnacle_available`: apostar en pinnacle cuando su cuota esta disponible en el partido/mercado.

Metodologia:
- Profit por apuesta: `cuota_pinnacle - 1` si acierta, `-1` si falla.
- Corte temporal por semanas con train/valid/test (60/20/20 aprox. segun cobertura de cada regla).

## Top reglas (strict_best_pinnacle)

| strategy | all_bets | all_hits | all_roi | all_profit_total | oos_bets | oos_roi | valid_roi | test_roi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S2_sun_u35 | 7 | 6 | 0.607 | 4.250 | 3 | 0.927 | 0.950 | 0.880 |
| S_sun_u35_m65 | 4 | 3 | 0.445 | 1.780 | 3 | 0.927 | 0.950 | 0.880 |
| S_sun_u35_m55 | 4 | 3 | 0.445 | 1.780 | 3 | 0.927 | 0.950 | 0.880 |
| S1_sat_u25_m32 | 23 | 15 | 0.273 | 6.270 | 10 | 0.550 | 0.722 | -1.000 |
| S1_sat_u25_m33 | 23 | 15 | 0.273 | 6.270 | 10 | 0.550 | 0.722 | -1.000 |
| S1_sat_u25_m375 | 40 | 25 | 0.212 | 8.490 | 25 | 0.309 | 0.332 | 0.269 |
| P_user_combo | 47 | 31 | 0.271 | 12.740 | 28 | 0.307 | 0.325 | 0.269 |
| S1_sat_u25_m389 | 41 | 25 | 0.183 | 7.490 | 26 | 0.259 | 0.254 | 0.269 |

## Top reglas (pinnacle_available)

| strategy | all_bets | all_hits | all_roi | all_profit_total | oos_bets | oos_roi | valid_roi | test_roi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1_sat_u25_m32 | 23 | 15 | 0.273 | 6.270 | 10 | 0.550 | 0.722 | -1.000 |
| S1_sat_u25_m33 | 23 | 15 | 0.273 | 6.270 | 10 | 0.550 | 0.722 | -1.000 |
| S2_sun_u35 | 17 | 16 | 0.789 | 13.420 | 5 | 0.542 | 0.300 | 0.905 |
| S_sun_u35_m65 | 9 | 8 | 0.702 | 6.320 | 4 | 0.445 | 0.300 | 0.880 |
| S_sun_u35_m55 | 8 | 7 | 0.692 | 5.540 | 4 | 0.445 | -1.000 | 0.927 |
| S_wknd_u35 | 43 | 31 | 0.387 | 16.620 | 17 | 0.345 | 0.179 | 0.492 |
| S1_sat_u25_m375 | 45 | 27 | 0.166 | 7.450 | 28 | 0.312 | 0.294 | 0.344 |
| P_user_combo | 62 | 43 | 0.337 | 20.870 | 45 | 0.250 | 0.045 | 0.352 |

## Reglas recomendadas (estables)

| mode | strategy | all_bets | all_hits | all_roi | all_profit_total | oos_roi | valid_roi | test_roi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pinnacle_available | S_wknd_u35 | 43 | 31 | 0.387 | 16.620 | 0.345 | 0.179 | 0.492 |
| pinnacle_available | S1_sat_u25_m375 | 45 | 27 | 0.166 | 7.450 | 0.312 | 0.294 | 0.344 |
| pinnacle_available | P_user_combo | 62 | 43 | 0.337 | 20.870 | 0.250 | 0.045 | 0.352 |
| pinnacle_available | S_wknd_u25_m375 | 94 | 53 | 0.096 | 9.040 | 0.159 | 0.058 | 0.269 |
| pinnacle_available | S_wknd_u25_m389 | 99 | 56 | 0.098 | 9.720 | 0.145 | 0.071 | 0.230 |
| strict_best_pinnacle | S1_sat_u25_m375 | 40 | 25 | 0.212 | 8.490 | 0.309 | 0.332 | 0.269 |
| strict_best_pinnacle | P_user_combo | 47 | 31 | 0.271 | 12.740 | 0.307 | 0.325 | 0.269 |
| strict_best_pinnacle | S1_sat_u25_m389 | 41 | 25 | 0.183 | 7.490 | 0.259 | 0.254 | 0.269 |
| strict_best_pinnacle | S_wknd_u25_m375 | 87 | 51 | 0.139 | 12.080 | 0.245 | 0.235 | 0.269 |
| strict_best_pinnacle | S_wknd_u25_m389 | 91 | 53 | 0.129 | 11.740 | 0.206 | 0.181 | 0.269 |
