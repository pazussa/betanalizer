# Combinacion entre BDI y estrategias Under

Evaluacion usando el dataset crudo deduplicado y parseo robusto de resultados (`Resultado`, `Acerto`, marcador y goles).

- Universo canonico usado: **10460** apuestas con resultado.

## Resultado resumido

| strategy | bets | profit_total | roi | hit_rate | avg_odds |
| --- | ---: | ---: | ---: | ---: | ---: |
| `Combo match-BDI top8 -> Under 2.5 + margen<=3.89` | 7 | 2.43 | 0.347 | 71.43% | 1.887 |
| `Combo match-BDI top8 -> Under 2.5 + margen<=3.89 + pinnacle` | 7 | 2.43 | 0.347 | 71.43% | 1.887 |
| `Combo match-BDI top9 -> Under 2.5 + margen<=3.89` | 7 | 2.43 | 0.347 | 71.43% | 1.887 |
| `Combo match-BDI top9 -> Under 2.5 + margen<=3.89 + pinnacle` | 7 | 2.43 | 0.347 | 71.43% | 1.887 |
| `Under 2.5 + margen<=3.89 + pinnacle` | 108 | 10.16 | 0.094 | 56.48% | 1.940 |
| `Under 2.5 + margen<=3.89` | 190 | 13.91 | 0.073 | 55.26% | 1.955 |
| `Under 3.5` | 373 | 20.84 | 0.056 | 63.54% | 1.696 |
| `Portafolio top8 BDI + Under 3.5 + Under 2.5 + margen<=3.89` | 683 | 27.13 | 0.040 | 57.39% | 1.906 |
| `Portafolio top9 BDI + Under 3.5 + Under 2.5 + margen<=3.89` | 698 | 27.51 | 0.039 | 57.16% | 1.913 |
| `Portafolio top8 BDI + Under 3.5` | 493 | 13.22 | 0.027 | 58.22% | 1.887 |
| `Portafolio top9 BDI + Under 3.5` | 508 | 13.60 | 0.027 | 57.87% | 1.897 |
| `Portafolio top9 BDI + Under 2.5 + margen<=3.89` | 325 | 6.67 | 0.021 | 49.85% | 2.161 |
| `Portafolio top8 BDI + Under 2.5 + margen<=3.89` | 310 | 6.29 | 0.020 | 50.00% | 2.158 |
| `BDI weekend top9 cuota mayor` | 135 | -7.24 | -0.054 | 42.22% | 2.450 |
| `BDI weekend top8 cuota mayor` | 120 | -7.62 | -0.064 | 41.67% | 2.478 |
| `Combo match-BDI top9 -> Under 3.5` | 2 | -0.29 | -0.145 | 50.00% | 1.595 |
| `Combo match-BDI top8 -> Under 3.5` | 1 | -1.00 | -1.000 | 0.00% | 1.480 |

## Lectura

- `Under 2.5 + margen<=3.89 + pinnacle` es la estrategia con mejor ROI estable en este dataset anual.
- `Under 3.5` tiene mas volumen y tambien funciona, pero con ROI menor.
- La estrategia BDI original (`cuota mayor`, `top 8/9` fin de semana) pierde dinero en el dataset anual completo.
- Si agregas la estrategia BDI original a un portafolio Under, el ROI del portafolio baja. Es una dilucion, no una mejora.
- La unica combinacion que sale muy bien es usar BDI solo como **selector de partido** y luego apostar `Under 2.5 + margen<=3.89`, pero el soporte es muy chico (7 apuestas).
- Para `Under 3.5` casi no hay solape util con el filtro BDI de partidos; no es una combinacion defendible por volumen.

## Conclusion

- Como regla original completa, `BDI` **no conviene mezclarlo** con las estrategias Under porque empeora el portafolio.
- La combinacion que merece seguimiento es: `partidos top BDI del fin de semana` -> si ademas cumplen `Under 2.5 + margen<=3.89`, tomar el Under. Pero hoy la muestra es demasiado chica para considerarla validada.
- Si tu objetivo es rentabilidad robusta hoy, me quedaria con las estrategias Under por separado y dejaria la variante BDI+Under2.5 como hipotesis en monitoreo, no como estrategia principal.
