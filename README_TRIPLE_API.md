# Análisis Triple-API - Guía de Uso

## 🚀 Descripción

Este proyecto combina **3 APIs de odds** para obtener la cobertura más completa de bookmakers (~140+ casas de apuestas):

1. **THE_ODDS_API**: ~58 bookmakers (Pinnacle, Betfair, DraftKings, etc.)
2. **API-FOOTBALL**: ~34 bookmakers (Bet365, Bwin, SBO/Sbobet, etc.)
3. **SPORTS_GAME_ODDS**: ~80+ bookmakers (1xBet, BetMGM, Caesars, ESPN BET, etc.)

## 📋 Archivos Principales

### main5.py
Script de línea de comandos para análisis completo con las 3 APIs.

**Características:**
- Combina datos de múltiples fuentes
- Calcula BDI (Bookmaker Disagreement Index) y métricas avanzadas
- Exporta CSV con formato estándar de 22 columnas
- CLI interactiva con múltiples comandos

### webapp/app_v2.py
Interfaz web Streamlit para análisis visual e interactivo.

**Características:**
- Interfaz gráfica amigable
- Verificación de estado de APIs
- Filtros interactivos
- Descarga de resultados en CSV
- Visualización de top mercados por BDI

## 🔧 Configuración

### 1. Variables de Entorno (.env)

Crea o verifica tu archivo `.env` con las siguientes claves:

```bash
# THE ODDS API
THE_ODDS_API_KEY=71bf811f7d188e95e23785f793b94185

# API-FOOTBALL
API_FOOTBALL_KEY=beea0d8f9ab22740c465933f98a87170

# SPORTS GAME ODDS
SPORTS_GAME_ODDS_KEY=2b740f74fb858017fd41fd1808512a76
```

### 2. Dependencias

Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

Dependencias principales:
- `httpx` - Cliente HTTP asíncrono
- `pandas` - Procesamiento de datos
- `numpy` - Cálculos numéricos
- `scipy` - Estadísticas (Jensen-Shannon Divergence)
- `click` - CLI interactiva
- `streamlit` - Interfaz web
- `python-dotenv` - Gestión de variables de entorno

## 📊 Uso - main5.py (CLI)

### Comandos Disponibles

#### 1. Verificar Estado de APIs

```bash
python main5.py status
```

Muestra:
- Estado de conexión de cada API
- Requests restantes/usados
- Número de bookmakers disponibles

#### 2. Listar Bookmakers

```bash
python main5.py bookmakers
```

Lista todos los bookmakers disponibles en cada API.

#### 3. Análisis Completo

```bash
python main5.py analyze [OPTIONS]
```

**Opciones:**
- `--hours-ahead INTEGER`: Horas hacia adelante (default: 168 = 7 días)
- `--min-bookmakers INTEGER`: Mínimo de bookmakers requeridos (default: 3)
- `--export-csv`: Exportar resultados a CSV

**Ejemplo:**

```bash
# Análisis de próximas 72 horas con mínimo 3 bookmakers
python main5.py analyze --hours-ahead 72 --min-bookmakers 3 --export-csv
```

**Output:**
- CSV: `analisis_mercados_YYYYMMDD_HHMMSS.csv`
- CSV crudo: `sportsgameodds_totals_YYYYMMDD_HHMMSS.csv`

#### 4. Test de SPORTS_GAME_ODDS

```bash
python main5.py test-sgo
```

Prueba específica de la API de SportsGameOdds.

## 🌐 Uso - Webapp (Streamlit)

### Iniciar Servidor

```bash
cd webapp
streamlit run app_v2.py
```

O desde el directorio raíz:

```bash
streamlit run webapp/app_v2.py
```

La aplicación se abrirá en tu navegador (generalmente `http://localhost:8501`)

### Funcionalidades

1. **Verificar APIs**: Botón para verificar el estado de las 3 APIs
2. **Configuración**: 
   - Ajustar horas hacia adelante
   - Establecer mínimo de bookmakers
3. **Análisis**: Ejecutar análisis completo con un clic
4. **Visualización**:
   - Métricas generales
   - Top 20 mercados por BDI
   - Tabla completa con filtros
   - Exportación CSV

## 📄 Formato CSV de Salida

El CSV generado tiene **22 columnas** en formato estándar:

| # | Columna | Descripción |
|---|---------|-------------|
| 1 | Partido | Equipos (e.g., "Manchester City vs Chelsea") |
| 2 | Fecha_Hora_Colombia | Timestamp en hora de Colombia (UTC-5) |
| 3 | Mercado | Tipo de mercado (e.g., "Over 2.5", "1X", "X2") |
| 4 | Mejor_Cuota | Mejor cuota encontrada |
| 5 | Cuota_Promedio_Mercado | Promedio de cuotas |
| 6 | BDI_jsd_fair | BDI calculado con Jensen-Shannon Divergence |
| 7 | BDI_n_bookmakers_fair | Número de bookmakers (fair) |
| 8 | BDI_std_p_fair | Desviación estándar de probabilidades (fair) |
| 9 | BDI_mad_p_fair | Median Absolute Deviation (fair) |
| 10 | BDI_jsd | BDI JSD (sin fair) |
| 11 | BDI_n_bookmakers | Número de bookmakers |
| 12 | BDI_std_p | Desviación estándar de probabilidades |
| 13 | BDI_mad_p | Median Absolute Deviation |
| 14 | Mejor_Casa | Bookmaker con mejor cuota |
| 15 | Num_Casas | Número total de casas que ofrecen el mercado |
| 16 | Diferencia_Cuota_Promedio | Diferencia entre mejor cuota y promedio |
| 17 | Volatilidad_Pct | Volatilidad porcentual |
| 18 | Margen_Casa_Pct | Margen de la casa (overround) |
| 19 | Liga | Liga del partido |
| 20 | Tipo_Mercado | Tipo general (e.g., "Over/Under", "Doble Chance") |
| 21 | Score_Final | Resultado final (null si no ha terminado) |
| 22 | Todas_Las_Cuotas | Todas las cuotas con formato "bookmaker:odds; ..." |

### Ejemplo de Fila CSV

```csv
Manchester City vs Chelsea,2026-01-08 15:00:00,Over 2.5,1.9500,1.8750,0.0125,,0.0095,0.0072,,5,0.0095,0.0072,BetPARX,5,0.0750,4.12,102.50,Premier League,Over/Under,,Bet365:1.8500; Betfair:1.8900; BetPARX:1.9500; Pinnacle:1.8600; DraftKings:1.8750
```

## 🔍 Interpretación de Resultados

### BDI (Bookmaker Disagreement Index)

El BDI mide el **desacuerdo entre bookmakers**:

- **BDI Alto (>0.01)**: Gran desacuerdo → Posible valor de apuesta
- **BDI Medio (0.005-0.01)**: Desacuerdo moderado
- **BDI Bajo (<0.005)**: Consenso entre bookmakers

**Interpretación:**
- Mayor BDI = Mayor incertidumbre en el mercado
- Puede indicar información asimétrica
- Oportunidad para encontrar valor si tienes mejor información

### Volatilidad

Mide la dispersión de probabilidades:
- **Alta (>5%)**: Mercado muy dividido
- **Media (2-5%)**: Dispersión normal
- **Baja (<2%)**: Consenso fuerte

### Margen de la Casa

Indica el overround promedio:
- **Normal**: 100-110%
- **Alto (>110%)**: Casa toma más margen
- **Bajo (<100%)**: Posible arbitraje (raro)

## 🎯 Estrategias de Uso

### 1. Búsqueda de Valor
1. Ordenar por BDI descendente
2. Buscar mercados con BDI > 0.01
3. Comparar con tu propio análisis
4. Aprovechar mejor cuota si tienes convicción

### 2. Arbitraje
1. Filtrar por margen < 100%
2. Verificar liquidez de bookmakers
3. Calcular stake óptimo

### 3. Análisis de Consenso
1. Filtrar por BDI < 0.005 (bajo desacuerdo)
2. Identificar favoritos claros
3. Usar como línea base

## 🐛 Troubleshooting

### Error 401 en THE_ODDS_API
- **Causa**: API key expirada o sin requests
- **Solución**: El script continúa con las otras 2 APIs automáticamente

### No se generan datos
- **Verificar**: `python main5.py status`
- **Revisar**: Que al menos 1 API esté funcionando
- **Ajustar**: `--min-bookmakers` a un valor más bajo (e.g., 2)

### Webapp no inicia
- **Verificar instalación**: `pip install streamlit`
- **Puerto ocupado**: Cambiar con `streamlit run app_v2.py --server.port 8502`

## 📚 Recursos Adicionales

### Documentación de APIs

- [THE ODDS API](https://the-odds-api.com/liveapi/guides/v4/)
- [API-FOOTBALL](https://www.api-football.com/documentation-v3)
- [SPORTS GAME ODDS](https://sportsgameodds.com/api)

### Archivos Relacionados

- `ANALISIS_MARGEN_CASA.md` - Análisis de márgenes
- `ANALISIS_PROBABILIDAD_IMPLICITA.md` - Probabilidades implícitas
- Scripts de análisis adicionales en el directorio raíz

## 📞 Soporte

Para problemas o preguntas:
1. Revisar los logs de ejecución
2. Verificar estado de APIs con `python main5.py status`
3. Consultar documentación de cada API

---

**Versión**: 2.0  
**Última actualización**: Enero 2026  
**Autor**: Sistema de Análisis de Apuestas
