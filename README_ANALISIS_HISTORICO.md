# Sistema de Análisis de Rendimiento Histórico

Este sistema automatiza el análisis de rendimiento de apuestas Over/Under para datos históricos.

## 📁 Archivos del Sistema

| Archivo | Descripción |
|---------|-------------|
| `analizar_rendimiento_historico.py` | Análisis completo de rendimiento (ROI, por liga, por línea, etc.) |
| `pipeline_historico.py` | Pipeline que agrega resultados + ejecuta análisis |
| `buscar_resultados_api.py` | Busca resultados usando API-FOOTBALL (requiere API key) |
| `agregar_resultados_historicos.py` | Script con resultados manuales para marzo 2025 |
| `resultados_marzo_2025.json` | Resultados de partidos 7-9 marzo 2025 en formato JSON |

## 🚀 Uso Rápido

### 1. Si ya tienes un archivo con resultados (_con_resultados.csv)

```bash
python analizar_rendimiento_historico.py archivo_con_resultados.csv
```

### 2. Si tienes un archivo histórico sin resultados + un JSON con resultados

```bash
python pipeline_historico.py historical_YYYYMMDD.csv --manual-results resultados.json
```

### 3. Estructura del JSON de resultados

```json
{
    "Real Madrid vs Barcelona": "2-1",
    "Liverpool vs Manchester United": "3-0",
    "Bayern Munich vs Dortmund": "1-1"
}
```

## 📊 Métricas Calculadas

El análisis genera las siguientes métricas:

1. **Por Tipo de Mercado** (Over vs Under)
   - ROI, Profit total, WinRate

2. **Por Línea** (Under 2.5, Over 2.5, etc.)
   - Top 5 más rentables
   - 5 peores líneas

3. **Por Liga**
   - Top 5 ligas rentables
   - 5 peores ligas

4. **Por Rango de Cuota**
   - Cuotas bajas (<1.5) vs altas (>2.5)
   - Análisis separado para Under y Over

5. **Por BDI** (Desacuerdo entre casas)
   - Cuartiles Q1-Q4
   - Análisis para Under y Over

6. **Combinaciones Línea + Cuota**
   - Mejores y peores combinaciones

7. **Correlaciones**
   - Variables vs Profit
   - Variables vs Acierto

8. **Test Estadístico**
   - T-test para verificar significancia del ROI

9. **Estrategias Recomendadas**
   - Simulación de diferentes filtros

## 📈 Ejemplo de Output

```
📊 RESUMEN GENERAL
   Partidos únicos: 193
   Total apuestas: 750
   Rendimiento total: -59.82 unidades
   ROI: -7.98%
   Win Rate: 48.1%

📈 POR TIPO DE MERCADO
   ❌ Over  : 375 apuestas | Profit:  -95.00u | ROI: -25.33%
   ✅ Under : 375 apuestas | Profit:  +35.18u | ROI:  +9.38%
```

## 🎯 Hallazgos Típicos (Marzo 2025)

| Métrica | Valor |
|---------|-------|
| UNDER ROI | +9.38% |
| OVER ROI | -25.33% |
| Mejor línea | Under 2.5 (+17.85%) |
| Peor línea | Over 3.0 (-58.17%) |
| Mejor estrategia | Under en TOP 3 Ligas (+21.22%) |

## 📂 Estructura de Salida

```
historical_analysis/
└── 2025/
    └── marzo/
        ├── historical_20250307_con_resultados.csv
        └── reportes_rendimiento/
            ├── reporte_20260106_105823_por_tipo.csv
            ├── reporte_20260106_105823_por_linea.csv
            ├── reporte_20260106_105823_por_liga.csv
            ├── reporte_20260106_105823_por_cuota.csv
            ├── reporte_20260106_105823_combinaciones.csv
            └── reporte_20260106_105823_estrategias.csv
```

## ⚠️ Notas Importantes

1. **Significancia Estadística**: Con ~400 apuestas, los resultados pueden no ser estadísticamente significativos. Se necesitan más datos.

2. **Formato del CSV de entrada**: Debe contener las columnas:
   - `Partido`, `Mercado`, `Mejor_Cuota`, `Liga`
   - `BDI_std_p`, `BDI_jsd_fair` (opcionales, para análisis BDI)

3. **Formato del CSV con resultados**: Además de lo anterior:
   - `Score`, `Total_Goles`, `Acerto`

## 🔄 Proceso para Nueva Fecha

1. Generar archivo histórico con `main6.py`:
   ```bash
   python main6.py --historical 2025-04-15
   ```

2. Buscar resultados (manual o con JSON):
   ```bash
   # Opción A: Si tienes resultados en JSON
   python pipeline_historico.py historical_20250415.csv --manual-results resultados_abril.json
   
   # Opción B: Analizar si ya tiene resultados
   python analizar_rendimiento_historico.py historical_analysis/2025/abril/historical_20250415_con_resultados.csv
   ```

3. Revisar reportes en `reportes_rendimiento/`
