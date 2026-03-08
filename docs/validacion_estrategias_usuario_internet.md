# Validacion de estrategias de usuario e internet

Comparacion en dataset canonico robusto con dos modos de ejecucion:
- `best`: usando `Mejor_Cuota` del mercado.
- `pin`: apostando en `pinnacle` cuando hay cuota pinnacle disponible.

## Ranking por ROI en modo pinnacle

```text
                           strategy   source  pin_bets  pin_hits  pin_profit  pin_roi  best_bets  best_profit  best_roi  pin_coverage_vs_best
                       USER_sun_u35     user        17        16     13.4200   0.7894        116      20.6600    0.1781                0.1466
USER_portfolio_sat_u25m375__sun_u35     user        62        43     20.8700   0.3366        182      36.2200    0.1990                0.3407
             USER_sat_u25_margin375     user        45        27      7.4500   0.1656         66      15.5600    0.2358                0.6818
         INT_favorites_odds_le_1_80 internet       590       384    -40.6092  -0.0688       2917    -121.8720   -0.0418                0.2023
         INT_low_vig_margin_le_3_50 internet       554       279    -50.9598  -0.0920        756     -49.1383   -0.0650                0.7328
             INT_value_edge_ge_5pct internet        78        29    -12.1900  -0.1563        328     -81.2200   -0.2476                0.2378
             INT_value_edge_ge_2pct internet       152        60    -24.8700  -0.1636        442     -92.4000   -0.2090                0.3439
         INT_longshots_odds_ge_2_40 internet        58        15    -16.4593  -0.2838        765      28.9056    0.0378                0.0758
```

## Cobertura pinnacle global

- Filas totales canonicas: **10460**
- Filas con cuota pinnacle disponible: **5241** (50.11%)
