# Estrategias validadas de la rama estrategia calibrada

Este reporte toma el dataset deduplicado ya consolidado y valida reglas solo con cortes temporales.

## Esquema de validacion

- Train: primeras 9 fechas (2025-11-24 a 2025-12-07).
- Valid: siguientes 3 fechas (2025-12-13 a 2025-12-15).
- Test: ultimas 3 fechas (2025-12-20 a 2025-12-27).
- Baseline OOS (valid+test): n=722, hit_rate=52.49%, ROI=-0.071.

## Estrategias recomendadas

### Mercado == Under 3.5

- Train: n=37, hit_rate=62.16%, ROI=0.066.
- Valid: n=14, hit_rate=64.29%, ROI=0.072.
- Test: n=15, hit_rate=80.00%, ROI=0.438.
- OOS total: n=29, hit_rate=72.41%, ROI=0.261.
- Lift OOS vs baseline: hit=+19.92%, ROI=+0.332.
- Intervalo hit rate 95%: [54.28%, 85.30%].
- Intervalo ROI 95% bootstrap: [-0.034, 0.531].
- Dias OOS activos: 6, dias positivos: 4, dias no negativos: 4.

### margen_casa_pct <= 3.8900 AND Mercado == Under 2.5

- Train: n=53, hit_rate=52.83%, ROI=0.029.
- Valid: n=24, hit_rate=54.17%, ROI=0.035.
- Test: n=39, hit_rate=58.97%, ROI=0.129.
- OOS total: n=63, hit_rate=57.14%, ROI=0.093.
- Lift OOS vs baseline: hit=+4.65%, ROI=+0.164.
- Intervalo hit rate 95%: [44.86%, 68.60%].
- Intervalo ROI 95% bootstrap: [-0.132, 0.322].
- Dias OOS activos: 6, dias positivos: 4, dias no negativos: 4.

### margen_casa_pct <= 3.8900 AND Mercado == Under 2.5 AND Mejor_Casa == pinnacle

- Train: n=45, hit_rate=53.33%, ROI=0.034.
- Valid: n=23, hit_rate=52.17%, ROI=0.007.
- Test: n=32, hit_rate=62.50%, ROI=0.206.
- OOS total: n=55, hit_rate=58.18%, ROI=0.122.
- Lift OOS vs baseline: hit=+5.69%, ROI=+0.193.
- Intervalo hit rate 95%: [45.03%, 70.26%].
- Intervalo ROI 95% bootstrap: [-0.132, 0.367].
- Dias OOS activos: 5, dias positivos: 3, dias no negativos: 3.

### score_final >= 0.3618 AND margen_casa_pct <= 3.8900 AND Mercado == Under 2.5

- Train: n=46, hit_rate=52.17%, ROI=0.006.
- Valid: n=23, hit_rate=52.17%, ROI=0.007.
- Test: n=39, hit_rate=58.97%, ROI=0.129.
- OOS total: n=62, hit_rate=56.45%, ROI=0.084.
- Lift OOS vs baseline: hit=+3.96%, ROI=+0.154.
- Intervalo hit rate 95%: [44.09%, 68.06%].
- Intervalo ROI 95% bootstrap: [-0.144, 0.308].
- Dias OOS activos: 5, dias positivos: 3, dias no negativos: 3.

## Reglas que parecen buenas pero no pasan validacion estricta

- `cuota_promedio_mercado <= 1.4300 AND margen_casa_pct <= 3.8900 AND num_casas >= 4.0000` logra hit rate alto OOS (80.00%), pero falla por consistencia: ROI valid=-0.051, ROI test=0.076.

## Inventario de reglas validadas encontradas

| rule | train_n | valid_n | test_n | train_roi | valid_roi | test_roi | oos_n | oos_hit | oos_roi |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Mercado == Under 3.5` | 37 | 14 | 15 | 0.066 | 0.072 | 0.438 | 29 | 72.41% | 0.261 |
| `margen_casa_pct <= 3.8900 AND Mercado == Under 2.5` | 53 | 24 | 39 | 0.029 | 0.035 | 0.129 | 63 | 57.14% | 0.093 |
| `margen_casa_pct <= 3.8900 AND Mercado == Under 2.5 AND Mejor_Casa == pinnacle` | 45 | 23 | 32 | 0.034 | 0.007 | 0.206 | 55 | 58.18% | 0.122 |
| `score_final >= 0.3618 AND margen_casa_pct <= 3.8900 AND Mercado == Under 2.5` | 46 | 23 | 39 | 0.006 | 0.007 | 0.129 | 62 | 56.45% | 0.084 |

## Conclusion operativa

- Las estrategias que sobreviven la validacion son pocas y simples.
- La familia ganadora es `Under`, no `double chance`.
- `Under 3.5` es la mejor estrategia simple por ROI y hit rate OOS.
- `Under 2.5` mejora cuando el margen de la casa es bajo; con `pinnacle` mejora un poco mas el ROI OOS.
- No recomiendo convertir en estrategia fija reglas que solo suben hit rate pero no sostienen ROI en validacion.
