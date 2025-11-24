# 🎯 Corners Live Analyzer

Análisis en tiempo real de cuotas de **tiros de esquina (corners)** para partidos de fútbol en vivo.

## ✨ Características

- 🔴 **Detección automática** de partidos en vivo
- ⚽ **Mercados de corners**: Over/Under de tiros de esquina
- 📊 **Score_Final**: Métrica calculada como `Ventaja_Margen / Margen_Casa`
- 📈 **Volatilidad**: Desviación estándar de cuotas entre casas
- 💾 **Exportación CSV**: Todas las métricas en formato estructurado
- 🌍 **Ligas incluidas**: 13+ ligas principales (EPL, La Liga, Bundesliga, Serie A, etc.)

## 🚀 Instalación Rápida

```bash
# 1. Navegar a la carpeta
cd corners_live

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar API key (ya está copiada del proyecto principal)
# Si no: cp .env.example .env y editar
```

## 💻 Uso

```bash
python main.py
```

El script:
1. Detecta partidos en vivo
2. Consulta cuotas de corners
3. Calcula métricas de análisis
4. Exporta CSV con resultados
5. Muestra top 10 en consola

## 📊 Estructura del CSV

| Columna | Descripción |
|---------|-------------|
| **Partido** | Equipos jugando (ej: "Real Madrid vs Barcelona") |
| **Estado** | 🔴 EN VIVO / ⏰ Próximo |
| **Score_Final** | Ventaja_Margen ÷ Margen_Casa (mayor = mejor oportunidad) |
| **Diferencia_Cuota_Promedio** | Mejor cuota - Promedio del mercado |
| **Mercado** | Tipo de mercado (ej: "Over 9.5", "Under 10.5") |
| **Cuota** | Mejor cuota encontrada |
| **Casa_Apuestas** | Bookmaker con mejor cuota |
| **Volatilidad_Pct** | Desviación estándar de cuotas (%) |
| **Margen_Casa_Pct** | Margen del bookmaker (%) |
| **Cuota_Promedio_Mercado** | Promedio de todas las cuotas del mercado |

## 📈 Interpretación de Métricas

### Score_Final
```
Score_Final = Ventaja_Margen / Margen_Casa
```
- **> 1.0**: Excelente oportunidad 🟢
- **0.5 - 1.0**: Buena oportunidad 🟡
- **< 0.5**: Oportunidad moderada ⚪

### Volatilidad
- **< 3%**: Mercado estable 🟢 (todas las casas de acuerdo)
- **3-8%**: Normal 🟡 (variación típica)
- **> 8%**: Alta 🔴 (requiere investigación)

## 🏟️ Mercados de Corners

### Total Corners (Totals)
Apuestas sobre el total de tiros de esquina en el partido:
- **Over X.5**: Más de X corners en el partido
- **Under X.5**: Menos de X corners en el partido

Líneas comunes: 8.5, 9.5, 10.5, 11.5, 12.5

## 📁 Estructura del Proyecto

```
corners_live/
├── main.py              # Script principal
├── api_client.py        # Cliente de The Odds API
├── analyzer.py          # Lógica de análisis
├── reporter.py          # Generación de reportes
├── models.py            # Modelos de datos
├── requirements.txt     # Dependencias
├── .env                 # API keys (copiada del proyecto principal)
├── .env.example         # Plantilla de configuración
└── README.md            # Esta documentación
```

## 🎯 Ejemplo de Salida

```
🏟️  ANÁLISIS DE CORNERS EN VIVO
🔗 Fuente: The Odds API (datos 100% reales)
================================================================================

📊 RESUMEN:
  • Partidos en vivo analizados: 5
  • Mercados de corners encontrados: 23

🏆 TOP 10 OPORTUNIDADES (por Score_Final):

#1 - Liverpool vs Manchester City 🔴 VIVO
    Mercado: Over 10.5
    Cuota: 2.15 (pinnacle)
    Score_Final: 1.2456
    Volatilidad: 3.2%
```

## 🤝 Comparación con Proyecto Principal

| Característica | Proyecto Principal | Corners Live |
|---------------|-------------------|--------------|
| Mercados | Double Chance (1X, X2) | Corners (Over/Under) |
| Timing | Partidos próximos | **Solo en vivo** |
| Cuotas Bwin | ✅ Incluidas | ❌ No incluidas |
| Score_Final | ✅ Mismo cálculo | ✅ Mismo cálculo |
| Volatilidad | ✅ Incluida | ✅ Incluida |

## ⚠️ Notas Importantes

1. **Partidos en Vivo**: Solo analiza partidos que YA comenzaron
2. **Disponibilidad de Datos**: No todos los partidos tienen mercados de corners
3. **Quota API**: Plan gratuito = 500 requests/mes (compartida con proyecto principal)
4. **Sin Web Scraping**: Solo datos oficiales de The Odds API
