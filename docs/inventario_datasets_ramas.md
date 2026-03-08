# Inventario de datasets CSV por rama

Generado el 2026-03-06 comparando las ramas `main` y `origin/estrategia-confianza-calibrada` directamente desde Git, sin cambiar el checkout actual.

## Resumen general

| Rama | Commit | CSVs | Perfiles de columnas |
| --- | --- | ---: | ---: |
| `main` | `53f85cbc2392` | 15 | 9 |
| `origin/estrategia-confianza-calibrada` | `c2c08fda2f8b` | 194 | 52 |

| Comparacion | Conteo |
| --- | ---: |
| CSV compartidos por nombre entre ambas ramas | 0 |
| CSV solo en `main` | 15 |
| CSV solo en `origin/estrategia-confianza-calibrada` | 194 |

## Criterio de lectura

- `Perfil` identifica un esquema de columnas. Varios CSV pueden compartir el mismo perfil.
- `Filas` cuenta registros de datos, excluyendo el header.
- La `Descripcion inferida` se basa en el nombre del archivo y en sus columnas principales.

## Rama `main`

Commit analizado: `53f85cbc2392a6a0c35f86545f0b46639cc99abd`

CSV encontrados: **15**. Perfiles de columnas detectados: **9**.

### Inventario de archivos

| Archivo | Filas | Perfil | Descripcion inferida |
| --- | ---: | --- | --- |
| `analisis_estrategia_resultado.csv` | 88 | `M08` | Evaluacion de la estrategia con score ponderado, rating, confianza y accion sugerida. |
| `analisis_mercados_20251124_001340.csv` | 448 | `M01` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251124_002559.csv` | 282 | `M01` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251124_003036.csv` | 200 | `M01` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251124_003313.csv` | 158 | `M01` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251125_065555.csv` | 88 | `M05` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251126_105345.csv` | 66 | `M01` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251206_132125.csv` | 362 | `M01` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_fusionado_20251124_003346.csv` | 1088 | `M01` | Consolidado de multiples snapshots de analisis de mercados. |
| `analisis_mercados_fusionado_20251124_003346_con_resultados.csv` | 1088 | `M06` | Snapshot de analisis de mercados con resultado o marcador incorporado. |
| `apuestas_rentables_filtradas.csv` | 6 | `M07` | Seleccion filtrada de apuestas rentables con estrategia aplicada y resultado. |
| `mejores_oportunidades_apuestas.csv` | 433 | `M04` | Oportunidades priorizadas de apuesta con estrategia, prioridad y resultado. |
| `partidosporverificar.csv` | 15 | `M03` | Partidos pendientes o revisados manualmente con confianza, ROI y marcador. |
| `ranking_apuestas_20251126.csv` | 10 | `M09` | Ranking editorial de apuestas recomendadas con stake sugerido. |
| `top_apuestas_20251206.csv` | 15 | `M02` | Top de apuestas seleccionadas con ROI historico y nivel de confianza. |

### Perfiles de columnas

#### M01

Descripcion base: Snapshot de analisis de mercados y mejores cuotas por partido.

Archivos que usan este perfil: **7**. Total de columnas: **14**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`

#### M02

Descripcion base: Top de apuestas seleccionadas con ROI historico y nivel de confianza.

Archivos que usan este perfil: **1**. Total de columnas: **14**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Estrategia`
- `Prioridad`
- `ROI_Historico`
- `Confianza`

#### M03

Descripcion base: Partidos pendientes o revisados manualmente con confianza, ROI y marcador.

Archivos que usan este perfil: **1**. Total de columnas: **16**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Estrategia`
- `Prioridad`
- `ROI_Historico`
- `Confianza`
- `Resultado`
- `Marcador`

#### M04

Descripcion base: Oportunidades priorizadas de apuesta con estrategia, prioridad y resultado.

Archivos que usan este perfil: **1**. Total de columnas: **17**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`
- `Estrategia`
- `Prioridad`
- `Resultado`

#### M05

Descripcion base: Snapshot de analisis de mercados y mejores cuotas por partido.

Archivos que usan este perfil: **1**. Total de columnas: **15**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`
- `Resultado`

#### M06

Descripcion base: Snapshot de analisis de mercados con resultado o marcador incorporado.

Archivos que usan este perfil: **1**. Total de columnas: **15**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`
- `Resultado_Cumplido`

#### M07

Descripcion base: Seleccion filtrada de apuestas rentables con estrategia aplicada y resultado.

Archivos que usan este perfil: **1**. Total de columnas: **16**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`
- `Resultado`
- `Estrategia`

#### M08

Descripcion base: Evaluacion de la estrategia con score ponderado, rating, confianza y accion sugerida.

Archivos que usan este perfil: **1**. Total de columnas: **16**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Score_Ponderado`
- `Rating`
- `Nivel_Confianza`
- `Accion_Recomendada`
- `Resultado`

#### M09

Descripcion base: Ranking editorial de apuestas recomendadas con stake sugerido.

Archivos que usan este perfil: **1**. Total de columnas: **15**.

Columnas:

- `Ranking`
- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Mercado`
- `Cuota`
- `Casa`
- `Score_Final`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Diferencia_Cuota_Promedio`
- `Pronostico_Web`
- `Recomendacion`
- `Estrellas`
- `Stake_Sugerido`

## Rama `origin/estrategia-confianza-calibrada`

Commit analizado: `c2c08fda2f8b3889461ce2af8f5ac9b6ebb9ad08`

CSV encontrados: **194**. Perfiles de columnas detectados: **52**.

### Inventario de archivos

| Archivo | Filas | Perfil | Descripcion inferida |
| --- | ---: | --- | --- |
| `analisis_completo_mercados_marzo2025.csv` | 817 | `E35` | Resumen agregado por mercado, variable y rango para evaluar rendimiento historico. |
| `analisis_mercados_20251219_100115.csv` | 312 | `E10` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251219_204227.csv` | 536 | `E10` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251220_213815.csv` | 78 | `E10` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251220_214421.csv` | 174 | `E10` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251220_214421_con_BDI.csv` | 174 | `E39` | Snapshot de analisis de mercados enriquecido con metricas BDI. |
| `analisis_mercados_20251222_135937.csv` | 22 | `E08` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251222_140054.csv` | 14 | `E08` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251222_140736.csv` | 14 | `E08` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251223_002621.csv` | 10 | `E08` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251223_002901.csv` | 10 | `E08` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251223_004207.csv` | 252 | `E08` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251226_191537.csv` | 238 | `E08` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251226_191537_con_resultados.csv` | 238 | `E45` | Snapshot de analisis de mercados con resultado o marcador incorporado. |
| `analisis_mercados_20251227_191506.csv` | 56 | `E08` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20251231_004610.csv` | 194 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260101_130333.csv` | 260 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260102_203616.csv` | 224 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260102_204756.csv` | 246 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260102_204914.csv` | 72 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260102_fusionado.csv` | 542 | `E02` | Consolidado de multiples snapshots de analisis de mercados. |
| `analisis_mercados_20260105_235345.csv` | 36 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260106_011839.csv` | 986 | `E11` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260106_012626.csv` | 64 | `E11` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260106_012813.csv` | 64 | `E11` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260106_013235.csv` | 104 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260106_013734.csv` | 64 | `E11` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260106_014031.csv` | 104 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260106_014154.csv` | 68 | `E11` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260106_020258.csv` | 64 | `E11` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260124_093601.csv` | 244 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260124_093902.csv` | 98 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260124_093939.csv` | 2 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260124_094047.csv` | 140 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260124_094235.csv` | 190 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260124_fusionado.csv` | 674 | `E02` | Consolidado de multiples snapshots de analisis de mercados. |
| `analisis_mercados_20260125_101910.csv` | 120 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260125_101948.csv` | 40 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `analisis_mercados_20260125_102237.csv` | 2 | `E02` | Snapshot de analisis de mercados y mejores cuotas por partido. |
| `api_football_h2h_20251231_004235.csv` | 230 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_h2h_20251231_004610.csv` | 230 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_h2h_20260101_130333.csv` | 222 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_h2h_20260102_195026.csv` | 352 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_h2h_20260102_203616.csv` | 352 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_h2h_20260102_204027.csv` | 352 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_h2h_20260102_204756.csv` | 352 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_h2h_20260102_204914.csv` | 352 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_h2h_20260105_195844.csv` | 351 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_h2h_20260106_013235.csv` | 236 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_h2h_20260106_014031.csv` | 236 | `E04` | Extraccion cruda o normalizada de cuotas H2H desde API-Football. |
| `api_football_odds_20251231_000943.csv` | 230 | `E04` | Extraccion de odds desde API-Football como insumo del pipeline. |
| `api_football_odds_20251231_001613.csv` | 230 | `E04` | Extraccion de odds desde API-Football como insumo del pipeline. |
| `api_football_odds_20251231_002504.csv` | 230 | `E04` | Extraccion de odds desde API-Football como insumo del pipeline. |
| `api_football_totals_20251231_004235.csv` | 4366 | `E07` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `api_football_totals_20251231_004610.csv` | 4366 | `E07` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `api_football_totals_20260101_130333.csv` | 4229 | `E07` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `api_football_totals_20260102_195026.csv` | 7286 | `E07` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `api_football_totals_20260102_203616.csv` | 7286 | `E07` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `api_football_totals_20260102_204027.csv` | 7286 | `E07` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `api_football_totals_20260102_204756.csv` | 7288 | `E07` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `api_football_totals_20260102_204914.csv` | 7288 | `E07` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `api_football_totals_20260105_195844.csv` | 6731 | `E07` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `api_football_totals_20260106_013235.csv` | 1942 | `E16` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `api_football_totals_20260106_014031.csv` | 1942 | `E16` | Extraccion cruda o normalizada de lineas de totales desde API-Football. |
| `bdi_analysis_americanfootball_nfl_20260101_210243.csv` | 90 | `E14` | Analisis BDI por deporte o liga con agrupaciones de rendimiento. |
| `bdi_analysis_americanfootball_nfl_20260101_210511.csv` | 96 | `E14` | Analisis BDI por deporte o liga con agrupaciones de rendimiento. |
| `bdi_analysis_basketball_nba_20260101_205919.csv` | 78 | `E14` | Analisis BDI por deporte o liga con agrupaciones de rendimiento. |
| `bdi_analysis_icehockey_nhl_20260101_210226.csv` | 16 | `E14` | Analisis BDI por deporte o liga con agrupaciones de rendimiento. |
| `bdi_top_by_match_with_rendimiento.csv` | 44 | `E42` | Seleccion top por partido con metricas BDI y rendimiento realizado. |
| `combined_totals_raw_20260106_000358.csv` | 5001 | `E22` | Consolidado raw de mercados de totales combinando fuentes. |
| `combined_totals_raw_20260106_000728.csv` | 9896 | `E09` | Consolidado raw de mercados de totales combinando fuentes. |
| `combined_totals_raw_20260106_001055.csv` | 9894 | `E09` | Consolidado raw de mercados de totales combinando fuentes. |
| `combined_totals_raw_20260106_001613.csv` | 3992 | `E09` | Consolidado raw de mercados de totales combinando fuentes. |
| `combined_totals_raw_20260106_002225.csv` | 3992 | `E09` | Consolidado raw de mercados de totales combinando fuentes. |
| `combined_totals_raw_20260106_002530.csv` | 3992 | `E09` | Consolidado raw de mercados de totales combinando fuentes. |
| `combined_totals_raw_20260106_002813.csv` | 3992 | `E09` | Consolidado raw de mercados de totales combinando fuentes. |
| `correlaciones_mercados_completa.csv` | 18 | `E33` | Correlaciones completas por mercado entre variables de precio, BDI y goles. |
| `correlaciones_mercados_marzo2025.csv` | 252 | `E36` | Correlaciones por mercado y variable para una ventana historica concreta. |
| `correlaciones_rendimiento_mercados.csv` | 252 | `E32` | Correlaciones entre indicadores de mercado y rendimiento o ROI. |
| `data/historico_completo.csv` | 1756 | `E38` | Historico completo consolidado como dataset maestro. |
| `docs/sweep_estrategia_test_20251215_214231.csv` | 3729 | `E47` | Barrido de parametros o estrategias usado para documentacion y pruebas. |
| `filtro1_resultados.csv` | 18 | `E10` | Resultado agregado del primer filtro experimental. |
| `filtro2_resultados.csv` | 106 | `E10` | Resultado agregado del segundo filtro experimental. |
| `filtro2_resultados_con_marcador_real.csv` | 80 | `E43` | Resultado del filtro 2 con marcador real. |
| `filtro2_resultados_con_marcador_real_con_BDI.csv` | 80 | `E44` | Resultado del filtro 2 con marcador real y metricas BDI. |
| `filtro2_results_bdi_analysis.csv` | 80 | `E19` | Analisis BDI sobre los resultados obtenidos por el filtro 2. |
| `filtro2_results_groups_of8_by_BDI.csv` | 10 | `E17` | Agrupacion por BDI en bloques de 8 sobre el filtro 2. |
| `filtro2_results_groups_of8_by_BDI_desc.csv` | 10 | `E17` | Agrupacion descendente por BDI en bloques de 8 sobre el filtro 2. |
| `historical_analysis/2025/enero/historical_20250103.csv` | 326 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/enero/historical_20250110.csv` | 402 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/enero/historical_20250117.csv` | 650 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/enero/historical_20250124.csv` | 706 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/enero/historical_20250131.csv` | 710 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/enero/raw_20250103.csv` | 1183 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/enero/raw_20250110.csv` | 1403 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/enero/raw_20250117.csv` | 2086 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/enero/raw_20250124.csv` | 2153 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/enero/raw_20250131.csv` | 2358 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/febrero/historical_20250207.csv` | 668 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/febrero/historical_20250214.csv` | 858 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/febrero/historical_20250221.csv` | 908 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/febrero/historical_20250228.csv` | 856 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/febrero/raw_20250207.csv` | 2070 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/febrero/raw_20250214.csv` | 2761 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/febrero/raw_20250221.csv` | 3021 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/febrero/raw_20250228.csv` | 2781 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/marzo/historical_20250307.csv` | 866 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/marzo/historical_20250314.csv` | 906 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/marzo/historical_20250321.csv` | 158 | `E18` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/marzo/historical_20250328.csv` | 902 | `E06` | Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas. |
| `historical_analysis/2025/marzo/raw_20250307.csv` | 2739 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/marzo/raw_20250314.csv` | 2741 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/marzo/raw_20250321.csv` | 581 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/marzo/raw_20250328.csv` | 3143 | `E05` | Extraccion historica cruda usada como insumo del analisis. |
| `historical_analysis/2025/marzo/reportes_rendimiento/reporte_20260106_105824_combinaciones.csv` | 33 | `E20` | Reporte agregado de rendimiento por combinaciones de variables. |
| `historical_analysis/2025/marzo/reportes_rendimiento/reporte_20260106_105824_estrategias.csv` | 7 | `E21` | Reporte agregado de rendimiento por estrategia. |
| `historical_analysis/2025/marzo/reportes_rendimiento/reporte_20260106_105824_por_cuota.csv` | 7 | `E46` | Reporte agregado de rendimiento segmentado por rango de cuota. |
| `historical_analysis/2025/marzo/reportes_rendimiento/reporte_20260106_105824_por_liga.csv` | 27 | `E25` | Reporte agregado de rendimiento segmentado por liga. |
| `historical_analysis/2025/marzo/reportes_rendimiento/reporte_20260106_105824_por_linea.csv` | 18 | `E31` | Reporte agregado de rendimiento segmentado por linea o mercado. |
| `historical_analysis/2025/marzo/reportes_rendimiento/reporte_20260106_105824_por_tipo.csv` | 2 | `E50` | Reporte agregado de rendimiento segmentado por tipo de mercado. |
| `historical_analysis/2025/resumen_general.csv` | 4 | `E15` | Resumen general del analisis historico por periodo. |
| `historical_con_resultados/backup/historical_20250103_con_resultados.csv` | 326 | `E03` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250110_con_resultados.csv` | 402 | `E03` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250117_con_resultados.csv` | 650 | `E03` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250124_con_resultados.csv` | 706 | `E03` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250131_con_resultados.csv` | 710 | `E03` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250207_con_resultados.csv` | 668 | `E03` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250214_con_resultados.csv` | 858 | `E12` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250221_con_resultados.csv` | 908 | `E12` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250228_con_resultados.csv` | 856 | `E12` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250307_con_resultados.csv` | 866 | `E03` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250314_con_resultados.csv` | 906 | `E03` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250321_con_resultados.csv` | 158 | `E01` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup/historical_20250328_con_resultados.csv` | 902 | `E03` | Backup del historico con resultados etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250103_con_resultados.csv` | 326 | `E03` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250110_con_resultados.csv` | 402 | `E03` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250117_con_resultados.csv` | 650 | `E03` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250124_con_resultados.csv` | 706 | `E03` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250131_con_resultados.csv` | 710 | `E03` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250207_con_resultados.csv` | 668 | `E03` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250214_con_resultados.csv` | 858 | `E12` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250221_con_resultados.csv` | 908 | `E12` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250228_con_resultados.csv` | 856 | `E12` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250307_con_resultados.csv` | 866 | `E03` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250314_con_resultados.csv` | 906 | `E03` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/backup_reconstruccion_20260107_204251/historical_20250328_con_resultados.csv` | 902 | `E03` | Backup reconstruido del historico con resultados ya etiquetados. |
| `historical_con_resultados/historical_20250103_con_resultados.csv` | 248 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250110_con_resultados.csv` | 314 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250117_con_resultados.csv` | 504 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250124_con_resultados.csv` | 534 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250131_con_resultados.csv` | 538 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250207_con_resultados.csv` | 492 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250214_con_resultados.csv` | 654 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250221_con_resultados.csv` | 694 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250228_con_resultados.csv` | 652 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250307_con_resultados.csv` | 658 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250314_con_resultados.csv` | 682 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250321_con_resultados.csv` | 140 | `E01` | Historico principal con resultados incorporados. |
| `historical_con_resultados/historical_20250328_con_resultados.csv` | 722 | `E01` | Historico principal con resultados incorporados. |
| `historical_test/2025/enero/historical_20250103.csv` | 280 | `E18` | Dataset historico de prueba para validar el pipeline. |
| `historical_test/2025/enero/raw_20250103.csv` | 1183 | `E05` | Extraccion cruda de prueba para el pipeline historico. |
| `historical_test/2025/resumen_general.csv` | 1 | `E15` | Dataset CSV del proyecto con estructura especifica del pipeline. |
| `missing_scores_template.csv` | 2644 | `E37` | Plantilla para completar manualmente marcadores faltantes. |
| `resultados_definitivos/historical_20250103_con_resultados.csv` | 244 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250110_con_resultados.csv` | 308 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250117_con_resultados.csv` | 492 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250124_con_resultados.csv` | 524 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250131_con_resultados.csv` | 528 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250207_con_resultados.csv` | 488 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250214_con_resultados.csv` | 648 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250221_con_resultados.csv` | 688 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250228_con_resultados.csv` | 644 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250307_con_resultados.csv` | 646 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250314_con_resultados.csv` | 670 | `E01` | Historico consolidado con resultados definitivos. |
| `resultados_definitivos/historical_20250328_con_resultados.csv` | 716 | `E01` | Historico consolidado con resultados definitivos. |
| `resumen_aciertos_numeric.csv` | 6 | `E23` | Comparacion estadistica de variables numericas entre aciertos y fallos. |
| `resumen_aciertos_summary.csv` | 1 | `E51` | Resumen global de aciertos, fallos y metricas agregadas. |
| `resumen_cat_Liga.csv` | 13 | `E24` | Resumen categorial por una dimension del dataset. |
| `resumen_cat_Mejor_Casa.csv` | 3 | `E28` | Resumen categorial por una dimension del dataset. |
| `resumen_cat_Mercado.csv` | 6 | `E30` | Resumen categorial por una dimension del dataset. |
| `resumen_cat_Tipo_Mercado.csv` | 1 | `E48` | Resumen categorial por una dimension del dataset. |
| `resumen_highsuccess_Liga.csv` | 9 | `E26` | Categorias con alta tasa de acierto o exito. |
| `resumen_highsuccess_Mejor_Casa.csv` | 3 | `E29` | Categorias con alta tasa de acierto o exito. |
| `resumen_highsuccess_Mercado.csv` | 2 | `E34` | Categorias con alta tasa de acierto o exito. |
| `resumen_highsuccess_Tipo_Mercado.csv` | 1 | `E49` | Categorias con alta tasa de acierto o exito. |
| `resumen_volatilidad_vs_rendimiento.csv` | 5 | `E52` | Relacion agregada entre volatilidad y rendimiento. |
| `REVISAR-analisis_mercados_20251220_214421_con_BDI_fair.csv` | 174 | `E40` | Analisis de mercados para revision manual con metricas BDI fair. |
| `REVISAR-analisis_mercados_20251220_214421_con_BDI_fair_con_resultados.csv` | 174 | `E41` | Analisis de mercados para revision manual con metricas BDI fair y resultado final. |
| `sportsgameodds_totals_20260105_234451.csv` | 166 | `E13` | Extraccion de mercados de totales desde SportsGameOdds. |
| `sportsgameodds_totals_20260105_235345.csv` | 126 | `E13` | Extraccion de mercados de totales desde SportsGameOdds. |
| `sportsgameodds_totals_20260105_235557.csv` | 108 | `E13` | Extraccion de mercados de totales desde SportsGameOdds. |
| `sportsgameodds_totals_20260105_235844.csv` | 108 | `E13` | Extraccion de mercados de totales desde SportsGameOdds. |
| `sportsgameodds_totals_20260106_000134.csv` | 108 | `E13` | Extraccion de mercados de totales desde SportsGameOdds. |
| `triple_api_analysis_20260105_234451.csv` | 50 | `E27` | Analisis combinado de tres APIs para comparar cuotas y disponibilidad. |

### Perfiles de columnas

#### E01

Descripcion base: Historico principal con resultados incorporados.

Archivos que usan este perfil: **26**. Total de columnas: **25**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Mercado`
- `Mejor_Cuota`
- `Cuota_Promedio_Mercado`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `Mejor_Casa`
- `Num_Casas`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Liga`
- `Tipo_Mercado`
- `Snapshot_Date`
- `Todas_Las_Cuotas`
- `Score`
- `Total_Goles`
- `Acerto`

#### E02

Descripcion base: Snapshot de analisis de mercados y mejores cuotas por partido.

Archivos que usan este perfil: **18**. Total de columnas: **22**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Mercado`
- `Mejor_Cuota`
- `Cuota_Promedio_Mercado`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `Mejor_Casa`
- `Num_Casas`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Liga`
- `Tipo_Mercado`
- `Score_Final`
- `Todas_Las_Cuotas`

#### E03

Descripcion base: Backup reconstruido del historico con resultados ya etiquetados.

Archivos que usan este perfil: **18**. Total de columnas: **26**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Mercado`
- `Mejor_Cuota`
- `Cuota_Promedio_Mercado`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `Mejor_Casa`
- `Num_Casas`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Liga`
- `Tipo_Mercado`
- `Snapshot_Date`
- `Todas_Las_Cuotas`
- `Score`
- `Total_Goles`
- `Acerto`
- `Bookmaker`

#### E04

Descripcion base: Extraccion cruda o normalizada de cuotas H2H desde API-Football.

Archivos que usan este perfil: **14**. Total de columnas: **12**.

Columnas:

- `fixture_id`
- `league_id`
- `league_name`
- `bookmaker_id`
- `bookmaker`
- `home_odds`
- `draw_odds`
- `away_odds`
- `odds_1x`
- `odds_x2`
- `prob_1x`
- `prob_x2`

#### E05

Descripcion base: Extraccion historica cruda usada como insumo del analisis.

Archivos que usan este perfil: **14**. Total de columnas: **13**.

Columnas:

- `match_id`
- `home_team`
- `away_team`
- `commence_time`
- `sport_key`
- `league_name`
- `bookmaker`
- `line`
- `over_odds`
- `under_odds`
- `last_update`
- `snapshot_date`
- `market_key`

#### E06

Descripcion base: Snapshot historico analizado por fecha de corte, con columnas de mercado derivadas.

Archivos que usan este perfil: **12**. Total de columnas: **23**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Mercado`
- `Mejor_Cuota`
- `Cuota_Promedio_Mercado`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `Mejor_Casa`
- `Num_Casas`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Liga`
- `Tipo_Mercado`
- `Snapshot_Date`
- `Todas_Las_Cuotas`
- `Bookmaker`

#### E07

Descripcion base: Extraccion cruda o normalizada de lineas de totales desde API-Football.

Archivos que usan este perfil: **9**. Total de columnas: **9**.

Columnas:

- `fixture_id`
- `bookmaker_id`
- `bookmaker`
- `line`
- `over_odds`
- `under_odds`
- `prob_over`
- `prob_under`
- `margin`

#### E08

Descripcion base: Snapshot de analisis de mercados y mejores cuotas por partido.

Archivos que usan este perfil: **8**. Total de columnas: **22**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `Todas_Las_Cuotas`

#### E09

Descripcion base: Consolidado raw de mercados de totales combinando fuentes.

Archivos que usan este perfil: **6**. Total de columnas: **14**.

Columnas:

- `fixture_id`
- `bookmaker_id`
- `bookmaker`
- `line`
- `over_odds`
- `under_odds`
- `match`
- `league`
- `starts_at`
- `source`
- `side`
- `odds_decimal`
- `event_id`
- `odds_american`

#### E10

Descripcion base: Snapshot de analisis de mercados y mejores cuotas por partido.

Archivos que usan este perfil: **6**. Total de columnas: **14**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`

#### E11

Descripcion base: Snapshot de analisis de mercados y mejores cuotas por partido.

Archivos que usan este perfil: **6**. Total de columnas: **23**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Mercado`
- `Mejor_Cuota`
- `Cuota_Promedio_Mercado`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `Mejor_Casa`
- `Num_Casas`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Liga`
- `Tipo_Mercado`
- `Score_Final`
- `Todas_Las_Cuotas`
- `APIs_Usadas`

#### E12

Descripcion base: Backup reconstruido del historico con resultados ya etiquetados.

Archivos que usan este perfil: **6**. Total de columnas: **26**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Mercado`
- `Mejor_Cuota`
- `Cuota_Promedio_Mercado`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `Mejor_Casa`
- `Num_Casas`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Liga`
- `Tipo_Mercado`
- `Snapshot_Date`
- `Todas_Las_Cuotas`
- `Bookmaker`
- `Score`
- `Total_Goles`
- `Acerto`

#### E13

Descripcion base: Extraccion de mercados de totales desde SportsGameOdds.

Archivos que usan este perfil: **5**. Total de columnas: **11**.

Columnas:

- `event_id`
- `match`
- `league`
- `starts_at`
- `bookmaker`
- `bookmaker_id`
- `line`
- `side`
- `odds_american`
- `odds_decimal`
- `source`

#### E14

Descripcion base: Analisis BDI por deporte o liga con agrupaciones de rendimiento.

Archivos que usan este perfil: **4**. Total de columnas: **16**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Mercado`
- `Mejor_Cuota`
- `Cuota_Promedio_Mercado`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `Mejor_Casa`
- `Num_Casas`
- `Prob_Implicita_Pct`
- `Volatilidad_Pct`
- `Deporte`
- `Tipo_Mercado`
- `Todas_Las_Cuotas`

#### E15

Descripcion base: Dataset CSV del proyecto con estructura especifica del pipeline.

Archivos que usan este perfil: **2**. Total de columnas: **8**.

Columnas:

- `date`
- `day`
- `total_markets`
- `markets_25`
- `unique_matches`
- `avg_bookmakers`
- `avg_bdi_fair`
- `max_bdi_fair`

#### E16

Descripcion base: Extraccion cruda o normalizada de lineas de totales desde API-Football.

Archivos que usan este perfil: **2**. Total de columnas: **13**.

Columnas:

- `fixture_id`
- `home_team`
- `away_team`
- `league_name`
- `match_date`
- `bookmaker_id`
- `bookmaker`
- `line`
- `over_odds`
- `under_odds`
- `prob_over`
- `prob_under`
- `margin`

#### E17

Descripcion base: Agrupacion por BDI en bloques de 8 sobre el filtro 2.

Archivos que usan este perfil: **2**. Total de columnas: **7**.

Columnas:

- `group`
- `n`
- `bd_min`
- `bd_max`
- `sum_contribs`
- `rendimiento`
- `mean_net`

#### E18

Descripcion base: Dataset historico de prueba para validar el pipeline.

Archivos que usan este perfil: **2**. Total de columnas: **22**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Mercado`
- `Mejor_Cuota`
- `Cuota_Promedio_Mercado`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `Mejor_Casa`
- `Num_Casas`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Liga`
- `Tipo_Mercado`
- `Snapshot_Date`
- `Todas_Las_Cuotas`

#### E19

Descripcion base: Analisis BDI sobre los resultados obtenidos por el filtro 2.

Archivos que usan este perfil: **1**. Total de columnas: **2**.

Columnas:

- `BDI_jsd`
- `net_return`

#### E20

Descripcion base: Reporte agregado de rendimiento por combinaciones de variables.

Archivos que usan este perfil: **1**. Total de columnas: **5**.

Columnas:

- `Combinacion`
- `N`
- `Profit`
- `ROI`
- `WinRate`

#### E21

Descripcion base: Reporte agregado de rendimiento por estrategia.

Archivos que usan este perfil: **1**. Total de columnas: **5**.

Columnas:

- `Estrategia`
- `Filtros`
- `N`
- `Profit`
- `ROI`

#### E22

Descripcion base: Consolidado raw de mercados de totales combinando fuentes.

Archivos que usan este perfil: **1**. Total de columnas: **14**.

Columnas:

- `fixture_id`
- `bookmaker_id`
- `bookmaker`
- `line`
- `over_odds`
- `under_odds`
- `source`
- `event_id`
- `match`
- `league`
- `starts_at`
- `side`
- `odds_american`
- `odds_decimal`

#### E23

Descripcion base: Comparacion estadistica de variables numericas entre aciertos y fallos.

Archivos que usan este perfil: **1**. Total de columnas: **11**.

Columnas:

- `H1`
- `mean_acertado`
- `mean_fallido`
- `median_acertado`
- `median_fallido`
- `tstat`
- `t_p`
- `mw_stat`
- `mw_p`
- `count_acertado`
- `count_fallido`

Notas:

- El CSV tiene al menos un encabezado vacio; PowerShell lo expone como H1 o H2.

#### E24

Descripcion base: Resumen categorial por una dimension del dataset.

Archivos que usan este perfil: **1**. Total de columnas: **5**.

Columnas:

- `Liga`
- `Acertado`
- `Fallido`
- `total`
- `rate_acierto`

#### E25

Descripcion base: Reporte agregado de rendimiento segmentado por liga.

Archivos que usan este perfil: **1**. Total de columnas: **5**.

Columnas:

- `Liga`
- `N`
- `Profit`
- `ROI`
- `WinRate`

#### E26

Descripcion base: Categorias con alta tasa de acierto o exito.

Archivos que usan este perfil: **1**. Total de columnas: **3**.

Columnas:

- `Liga`
- `total`
- `rate_acierto`

#### E27

Descripcion base: Analisis combinado de tres APIs para comparar cuotas y disponibilidad.

Archivos que usan este perfil: **1**. Total de columnas: **13**.

Columnas:

- `match`
- `league`
- `starts_at`
- `market`
- `line`
- `side`
- `num_bookmakers`
- `min_odds`
- `max_odds`
- `fair_odds`
- `BDI_jsd_fair`
- `bookmakers`
- `source`

#### E28

Descripcion base: Resumen categorial por una dimension del dataset.

Archivos que usan este perfil: **1**. Total de columnas: **5**.

Columnas:

- `Mejor_Casa`
- `Acertado`
- `Fallido`
- `total`
- `rate_acierto`

#### E29

Descripcion base: Categorias con alta tasa de acierto o exito.

Archivos que usan este perfil: **1**. Total de columnas: **3**.

Columnas:

- `Mejor_Casa`
- `total`
- `rate_acierto`

#### E30

Descripcion base: Resumen categorial por una dimension del dataset.

Archivos que usan este perfil: **1**. Total de columnas: **5**.

Columnas:

- `Mercado`
- `Acertado`
- `Fallido`
- `total`
- `rate_acierto`

#### E31

Descripcion base: Reporte agregado de rendimiento segmentado por linea o mercado.

Archivos que usan este perfil: **1**. Total de columnas: **6**.

Columnas:

- `Mercado`
- `N`
- `Profit`
- `ROI`
- `WinRate`
- `Cuota_Media`

#### E32

Descripcion base: Correlaciones entre indicadores de mercado y rendimiento o ROI.

Archivos que usan este perfil: **1**. Total de columnas: **7**.

Columnas:

- `Mercado`
- `N`
- `Rend_Total`
- `ROI`
- `Variable`
- `r`
- `p`

#### E33

Descripcion base: Correlaciones completas por mercado entre variables de precio, BDI y goles.

Archivos que usan este perfil: **1**. Total de columnas: **33**.

Columnas:

- `Mercado`
- `N`
- `Tasa_Acierto_%`
- `Mejor_Cuota_r`
- `Mejor_Cuota_p`
- `Cuota_Promedio_Mercado_r`
- `Cuota_Promedio_Mercado_p`
- `BDI_jsd_fair_r`
- `BDI_jsd_fair_p`
- `BDI_n_bookmakers_fair_r`
- `BDI_n_bookmakers_fair_p`
- `BDI_std_p_fair_r`
- `BDI_std_p_fair_p`
- `BDI_mad_p_fair_r`
- `BDI_mad_p_fair_p`
- `BDI_jsd_r`
- `BDI_jsd_p`
- `BDI_n_bookmakers_r`
- `BDI_n_bookmakers_p`
- `BDI_std_p_r`
- `BDI_std_p_p`
- `BDI_mad_p_r`
- `BDI_mad_p_p`
- `Num_Casas_r`
- `Num_Casas_p`
- `Diferencia_Cuota_Promedio_r`
- `Diferencia_Cuota_Promedio_p`
- `Volatilidad_Pct_r`
- `Volatilidad_Pct_p`
- `Margen_Casa_Pct_r`
- `Margen_Casa_Pct_p`
- `Total_Goles_r`
- `Total_Goles_p`

#### E34

Descripcion base: Categorias con alta tasa de acierto o exito.

Archivos que usan este perfil: **1**. Total de columnas: **3**.

Columnas:

- `Mercado`
- `total`
- `rate_acierto`

#### E35

Descripcion base: Resumen agregado por mercado, variable y rango para evaluar rendimiento historico.

Archivos que usan este perfil: **1**. Total de columnas: **11**.

Columnas:

- `Mercado`
- `Variable`
- `Grupo`
- `N`
- `Aciertos`
- `Pct_Acierto`
- `Rendimiento_U`
- `ROI_Pct`
- `Rango_Min`
- `Rango_Max`
- `Mediana`

#### E36

Descripcion base: Correlaciones por mercado y variable para una ventana historica concreta.

Archivos que usan este perfil: **1**. Total de columnas: **14**.

Columnas:

- `Mercado`
- `Variable`
- `N`
- `Media`
- `Std`
- `Mediana`
- `Corr_Pearson`
- `P_Pearson`
- `Corr_Spearman`
- `P_Spearman`
- `Corr_PointBiserial`
- `P_PointBiserial`
- `Sig_005`
- `Sig_010`

#### E37

Descripcion base: Plantilla para completar manualmente marcadores faltantes.

Archivos que usan este perfil: **1**. Total de columnas: **8**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Mercado`
- `Tipo_Mercado`
- `Archivo_Origen`
- `Verified_Score`
- `Source`

#### E38

Descripcion base: Historico completo consolidado como dataset maestro.

Archivos que usan este perfil: **1**. Total de columnas: **20**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Casa`
- `Mejor_Cuota`
- `Num_Casas`
- `Cuota_Promedio_Mercado`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Resultado`
- `Marcador`
- `Confianza`
- `P_Win_Calibrada`
- `Confianza_Calibrada`
- `Goles_Local`
- `Goles_Visitante`

#### E39

Descripcion base: Snapshot de analisis de mercados enriquecido con metricas BDI.

Archivos que usan este perfil: **1**. Total de columnas: **18**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`

#### E40

Descripcion base: Analisis de mercados para revision manual con metricas BDI fair.

Archivos que usan este perfil: **1**. Total de columnas: **22**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`

#### E41

Descripcion base: Analisis de mercados para revision manual con metricas BDI fair y resultado final.

Archivos que usan este perfil: **1**. Total de columnas: **24**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `Marcador`
- `Resultado`

#### E42

Descripcion base: Seleccion top por partido con metricas BDI y rendimiento realizado.

Archivos que usan este perfil: **1**. Total de columnas: **26**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `Marcador`
- `Resultado`
- `Rendimiento`
- `decile`

#### E43

Descripcion base: Resultado del filtro 2 con marcador real.

Archivos que usan este perfil: **1**. Total de columnas: **16**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`
- `Marcador`
- `Resultado`

#### E44

Descripcion base: Resultado del filtro 2 con marcador real y metricas BDI.

Archivos que usan este perfil: **1**. Total de columnas: **20**.

Columnas:

- `Partido`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `Todas_Las_Cuotas`
- `Marcador`
- `Resultado`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`

#### E45

Descripcion base: Snapshot de analisis de mercados con resultado o marcador incorporado.

Archivos que usan este perfil: **1**. Total de columnas: **25**.

Columnas:

- `Partido`
- `Resultado`
- `Fecha_Hora_Colombia`
- `Liga`
- `Tipo_Mercado`
- `Mercado`
- `Mejor_Cuota`
- `Mejor_Casa`
- `Num_Casas`
- `Score_Final`
- `Diferencia_Cuota_Promedio`
- `Volatilidad_Pct`
- `Margen_Casa_Pct`
- `Cuota_Promedio_Mercado`
- `BDI_jsd`
- `BDI_n_bookmakers`
- `BDI_std_p`
- `BDI_mad_p`
- `BDI_jsd_fair`
- `BDI_n_bookmakers_fair`
- `BDI_std_p_fair`
- `BDI_mad_p_fair`
- `Todas_Las_Cuotas`
- `Marcador`
- `Resultado_Segunda`

#### E46

Descripcion base: Reporte agregado de rendimiento segmentado por rango de cuota.

Archivos que usan este perfil: **1**. Total de columnas: **6**.

Columnas:

- `Rango_Cuota`
- `N`
- `Profit`
- `ROI`
- `WinRate`
- `Cuota_Media`

#### E47

Descripcion base: Barrido de parametros o estrategias usado para documentacion y pruebas.

Archivos que usan este perfil: **1**. Total de columnas: **11**.

Columnas:

- `thr_pwin`
- `vol_max`
- `margen_max`
- `num_casas_min`
- `diff_min`
- `min_odds`
- `max_odds`
- `n`
- `winrate_pct`
- `roi_pct`
- `avg_odds`

#### E48

Descripcion base: Resumen categorial por una dimension del dataset.

Archivos que usan este perfil: **1**. Total de columnas: **5**.

Columnas:

- `Tipo_Mercado`
- `Acertado`
- `Fallido`
- `total`
- `rate_acierto`

#### E49

Descripcion base: Categorias con alta tasa de acierto o exito.

Archivos que usan este perfil: **1**. Total de columnas: **3**.

Columnas:

- `Tipo_Mercado`
- `total`
- `rate_acierto`

#### E50

Descripcion base: Reporte agregado de rendimiento segmentado por tipo de mercado.

Archivos que usan este perfil: **1**. Total de columnas: **6**.

Columnas:

- `Tipo`
- `N`
- `Profit`
- `ROI`
- `WinRate`
- `Cuota_Media`

#### E51

Descripcion base: Resumen global de aciertos, fallos y metricas agregadas.

Archivos que usan este perfil: **1**. Total de columnas: **4**.

Columnas:

- `total`
- `acertados`
- `fallidos`
- `acierto_rate`

#### E52

Descripcion base: Relacion agregada entre volatilidad y rendimiento.

Archivos que usan este perfil: **1**. Total de columnas: **5**.

Columnas:

- `vol_bin`
- `count`
- `mean_net`
- `std_net`
- `mean_vol`

