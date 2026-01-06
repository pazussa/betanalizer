---
title: Football Odds Analyzer
emoji: ⚽
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
---

# ⚽ Football Odds Analyzer

Aplicación web para analizar cuotas de apuestas de fútbol usando **THE_ODDS_API** + **API-FOOTBALL**.

## 🔑 APIs incluidas

- **THE_ODDS_API**: 58+ bookmakers (Pinnacle, Betfair, DraftKings, etc.)
- **API-FOOTBALL**: Bet365, Bwin, SBO (Sbobet) ⭐ - **Key incluida**

## 📋 Uso

1. **Selecciona una key** de THE_ODDS_API del menú desplegable (hay 10 disponibles)
2. O **pega una nueva key** si tienes más
3. Configura:
   - **Desde (horas)**: Horas desde ahora para comenzar búsqueda (default: 0)
   - **Hasta (horas)**: Horas hacia adelante para buscar partidos (default: 72)
4. Click en **"🚀 Ejecutar Análisis"**

## 📊 Columnas del resultado

| Columna | Descripción |
|---------|-------------|
| **Partido** | Equipos local vs visitante |
| **Fecha_Hora_Colombia** | Fecha y hora del partido (UTC-5) |
| **Mercado** | Tipo de mercado (Over/Under X.X) |
| **Mejor_Cuota** | La mejor cuota disponible |
| **BDI_jsd_fair** | Índice de desacuerdo entre bookmakers |
| **BDI_n_bookmakers_fair** | Número de bookmakers para el cálculo |

## 🔑 Keys

- **THE_ODDS_API**: 10 keys incluidas (seleccionar del menú)
- **API-FOOTBALL**: Key fija incluida ✅

Si necesitas más keys de THE_ODDS_API:
- Plan gratuito: 500 requests/mes
- Registrarse en: https://the-odds-api.com/

## 💻 Desarrollo local

```bash
cd webapp
pip install -r requirements.txt
streamlit run app.py
```

## ⚠️ Notas

- **Sin mercados 1X/X2**: Solo se muestran mercados Over/Under
- **Ordenado por BDI**: Mayor BDI = mayor desacuerdo entre casas (potencial valor)
- **Hora Colombia**: UTC-5
- **API-FOOTBALL**: Incluye Bet365, Bwin, SBO (marcados con ⭐)
