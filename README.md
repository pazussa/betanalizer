# ⚽ Football Betting Odds Analyzer

**Análisis verídico y automático de cuotas de fútbol usando APIs oficiales**

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

## 🎯 ¿Qué es esto?

Un sistema profesional que analiza cuotas de apuestas deportivas usando **solo fuentes oficiales y APIs autorizadas**. Sin scraping, sin violaciones de términos de servicio, solo datos auténticos y verificables.

### ✅ **Garantías de Veracidad**
- 📊 **APIs Oficiales**: The Odds API, SportRadar, y otros proveedores autorizados
- 🚫 **Sin Scraping**: Cero manipulación de sitios web o datos no autorizados  
- ✅ **Datos Verificables**: Cada cuota incluye timestamp y fuente oficial
- 🔒 **Cumplimiento Legal**: Respeta términos de servicio y rate limits
- 📈 **Cálculos Transparentes**: Probabilidades implícitas usando fórmulas matemáticas estándar

## 🚀 Características Principales

### 🎯 **Análisis Especializado**
- **Mercados Doble Oportunidad**: 1X (Local/Empate) y X2 (Empate/Visitante)
- **Probabilidades Implícitas**: Cálculo automático usando 1/cuota
- **Filtrado Inteligente**: Criterios personalizables de probabilidad y cuotas mínimas
- **Múltiples Bookmakers**: Comparación automática para encontrar mejores cuotas

### 📊 **Reportes Detallados**
- **Tabla Completa**: Análisis de todos los partidos disponibles
- **Reporte de Cumplimiento**: Solo mercados que cumplen tus criterios
- **Estadísticas**: Distribución por ligas, bookmakers, y métricas de rendimiento
- **Exportación**: CSV para análisis adicional en Excel/Python

### 🔧 **APIs Soportadas**

| Proveedor | Tipo | Datos Disponibles | Status |
|-----------|------|-------------------|--------|
| **The Odds API** | Oficial | Cuotas en tiempo real | ✅ Activo |
| **SportRadar** | Oficial | Calendarios de ligas | ✅ Activo |
| **BetConstruct** | Oficial | Cuotas pre-partido | 🔄 Próximamente |
| **LSports** | Oficial | Feed deportivo | 🔄 Próximamente |

## 🛠️ Instalación y Configuración

### Requisitos del Sistema
- Python 3.7 o superior
- Conexión a internet
- API keys de proveedores oficiales

### 1. Clonar y Configurar Entorno
```bash
git clone <repository-url>
cd bets2
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configurar API Keys

#### The Odds API (Requerida)
1. Visita: https://the-odds-api.com/
2. Crea cuenta gratuita (500 requests/mes)
3. Copia tu API key

#### SportRadar (Opcional)
1. Visita: https://developer.sportradar.com/
2. Trial gratuito (1000 requests/mes)
3. Copia tu API key

### 3. Variables de Entorno
```bash
# Copia el archivo de ejemplo
cp .env.example .env

# Edita .env con tus API keys
THE_ODDS_API_KEY=tu_api_key_aqui
SPORTRADAR_API_KEY=tu_api_key_aqui  # Opcional
```

### 4. Verificar Configuración
```bash
python main.py validate
```

Deberías ver:
```
🔍 Validando configuración del sistema...
🔑 The Odds API Key: ✅ Configurada
📡 Estado de APIs:
  ✅ The Odds Api: Conectada
🎉 Sistema completamente funcional
```

## 📖 Uso del Sistema

### Análisis Básico
```bash
# Ejecutar análisis completo con configuración por defecto
python main.py analyze

# Solo mostrar mercados que cumplen criterios
python main.py analyze --only-compliant

# Exportar resultados a CSV
python main.py analyze --export-csv resultados.csv
```

### Personalizar Criterios
```bash
# Probabilidad mínima 80% y cuota mínima 1.40
python main.py analyze --min-probability 0.8 --min-odds 1.40

# Buscar partidos en las próximas 24 horas
python main.py analyze --hours-ahead 24

# Reporte de solo cumplimiento de criterios
python main.py compliance --min-probability 0.75
```

### Uso Programático
```python
from src.analyzer import FootballOddsAnalyzer
from src.reporter import ReportGenerator

# Inicializar analizador
analyzer = FootballOddsAnalyzer()

# Ejecutar análisis
results = await analyzer.analyze_all_matches(
    min_probability=0.7,
    min_odds=1.30,
    hours_ahead=48
)

# Generar reporte
reporter = ReportGenerator()
table = reporter.generate_analysis_table(results)
print(table)

# Limpiar recursos
await analyzer.cleanup()
```

## 📊 Ejemplo de Salida

```
📊 **ANÁLISIS VERÍDICO DE CUOTAS DE FÚTBOL**
🔗 **Fuentes**: APIs oficiales (The Odds API, SportRadar)
⚡ **Sin Scraping**: Solo datos autorizados y verificados

📈 **RESUMEN EJECUTIVO**
• Total de mercados analizados: 15
• Mercados que cumplen criterios: 4
• Tasa de cumplimiento: 26.7%
• Criterios aplicados: Prob. ≥ 70%, Cuota ≥ 1.30

+--------------------------------+-----------------------+------------------+-------------------+
| Partido                        | Mercado Analizado     |  Cuota Más Alta  | Prob. Implícita   |
+================================+=======================+==================+===================+
| Manchester United vs Liverpool | X2 (Empate/Visitante) |       1.35       | 74.1%             |
| Barcelona vs Real Madrid       | 1X (Local/Empate)     |       1.38       | 72.5%             |
| Bayern Munich vs Dortmund      | X2 (Empate/Visitante) |       1.42       | 70.4%             |
+--------------------------------+-----------------------+------------------+-------------------+

✅ Cuotas obtenidas de fuentes oficiales
✅ Probabilidades calculadas matemáticamente (1/cuota)  
✅ Filtrado automático por criterios establecidos
✅ Sin manipulación o scraping de sitios web
```

## 🧪 Testing y Demo

### Ejecutar Demo (Sin API Keys)
```bash
python demo.py
```

### Ejecutar Tests
```bash
python -m pytest tests/ -v
```

### Validar Sistema Completo
```bash
python main.py validate
```

## 📁 Estructura del Proyecto

```
bets2/
├── src/                    # Código fuente principal
│   ├── models.py          # Modelos de datos (Match, OddsData, etc.)
│   ├── analyzer.py        # Motor principal de análisis  
│   ├── reporter.py        # Generación de reportes y tablas
│   └── apis/              # Integraciones con APIs oficiales
│       ├── the_odds_api.py     # Cliente de The Odds API
│       └── sportradar_api.py   # Cliente de SportRadar
├── tests/                 # Tests automatizados
├── docs/                  # Documentación técnica
├── main.py               # CLI principal
├── demo.py               # Demo con datos simulados
├── requirements.txt      # Dependencias Python
├── .env.example         # Template de variables de entorno
└── README.md            # Esta documentación
```

## 🔧 Configuración Avanzada

### Ajustar Rate Limits
```env
# .env
API_RATE_LIMIT=30    # Requests per minute
API_TIMEOUT=60       # Timeout en segundos
```

### Personalizar Filtros por Defecto
```python
# src/analyzer.py
self.min_probability = 0.75  # 75% en lugar de 70%
self.min_odds = 1.35        # 1.35 en lugar de 1.30
```

### Logging Detallado
```python
import logging
logging.basicConfig(level=logging.DEBUG)  # Para debugging
```

## 🚨 Limitaciones y Consideraciones

### Quotas de APIs Gratuitas
- **The Odds API**: 500 requests/mes
- **SportRadar**: 1000 requests/mes  
- **Recomendación**: Monitorear uso con `python main.py validate`

### Rate Limiting
- Pausas automáticas entre requests
- Manejo de errores 429 (quota excedida)
- Reintentos automáticos en caso de fallas temporales

### Actualizaciones de Cuotas
- Las cuotas cambian constantemente
- Datos válidos al momento de la consulta
- Re-ejecutar análisis para datos actualizados

## 🤝 Cumplimiento y Ética

### ✅ **Lo que SÍ hacemos**
- Usar APIs oficiales con autenticación apropiada
- Respetar rate limits y términos de servicio
- Validar autenticidad de todos los datos
- Proporcionar trazabilidad completa de fuentes

### ❌ **Lo que NO hacemos**
- Web scraping de sitios de apuestas
- Violación de términos de servicio
- Manipulación o alteración de datos
- Acceso no autorizado a sistemas

### 📜 **Disclaimer Legal**
Este software es únicamente para análisis informativo. Las cuotas son datos públicos obtenidos de fuentes oficiales. Los usuarios son responsables del cumplimiento de las leyes locales sobre apuestas deportivas.

## 📞 Soporte y Contribuciones

### Problemas Comunes
1. **Error de API Key**: Verifica `.env` y validez de keys
2. **Sin partidos**: Ajusta `--hours-ahead` o verifica fechas
3. **Rate limit**: Espera o actualiza tu plan de API
4. **Timeout**: Aumenta `API_TIMEOUT` en `.env`

### Reportar Issues
- Incluye logs completos (`betting_analysis.log`)
- Especifica versión de Python y sistema operativo
- Adjunta archivo `.env.example` con configuración

### Desarrollo
```bash
# Instalar dependencias de desarrollo
pip install -r requirements.txt pytest pytest-asyncio

# Ejecutar tests
pytest tests/ -v

# Linting
flake8 src/ tests/
```

## 📄 Licencia

MIT License - Consulta el archivo `LICENSE` para más detalles.

---

**⚡ Desarrollado para análisis serio con datos verídicos ⚡**