# Live Markets Analyzer

Análisis de mercados en vivo de fútbol usando The Odds API.

## 🎯 Mercados Analizados

1. **TOTALS** (Over/Under Goles)
   - Mercado: Over/Under de goles totales
   - Líneas: 2.5, 3.5, etc.

2. **BTTS** (Both Teams To Score)
   - Mercado: Ambos equipos marcan
   - Opciones: Yes / No

3. **H2H_Q1** (Primer Tiempo 1X2)
   - Mercado: Ganador del primer tiempo
   - Opciones: Home / Draw / Away

## 📊 Metodología

Mismo análisis que el proyecto principal:
- **Score_Final**: Ventaja_Margen / Margen_Casa
- **Volatilidad**: Desviación estándar entre casas
- **Num_Casas**: Cantidad de casas ofreciendo el mercado

## 🏠 Casas de Apuestas

Exactamente las mismas 6 casas del proyecto principal:
- Betsson
- Pinnacle
- Marathonbet
- Codere IT
- Winamax FR
- Winamax DE

## 🚀 Uso

```bash
python main.py
```

## 📁 Salida

Genera 3 archivos CSV independientes:
- `totals_goles_YYYYMMDD_HHMMSS.csv`
- `btts_ambos_marcan_YYYYMMDD_HHMMSS.csv`
- `h2h_primer_tiempo_YYYYMMDD_HHMMSS.csv`

## 🔑 Configuración

Copia `.env.example` a `.env` y configura tu API key:

```
THE_ODDS_API_KEY=tu_clave_aqui
```

## 📋 Columnas del CSV

1. Partido
2. Estado (🔴 EN VIVO / ⏰ Próximo)
3. Score_Final
4. Diferencia_Cuota_Promedio
5. Mercado
6. Mejor_Cuota
7. Mejor_Casa
8. Num_Casas
9. Volatilidad_Pct
10. Margen_Casa_Pct
11. Cuota_Promedio_Mercado
12. Todas_Las_Cuotas

## ⚠️ Notas

- Solo analiza partidos en vivo o próximos a comenzar (hasta 30 min antes)
- Uso de API: ~3 requests por partido × 3 mercados = ~9 requests por partido
- Monitorea tu cuota de API (500 requests/mes en plan gratuito)
