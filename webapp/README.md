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

Aplicación web para analizar cuotas de apuestas de fútbol usando THE_ODDS_API.

## 🚀 Despliegue en Hugging Face Spaces (GRATUITO)

### Pasos:

1. **Crear cuenta en Hugging Face** (si no tienes): https://huggingface.co/join

2. **Crear nuevo Space**:
   - Ve a https://huggingface.co/new-space
   - Nombre: `football-odds-analyzer` (o el que prefieras)
   - SDK: **Streamlit**
   - Visibilidad: Public o Private

3. **Subir archivos**:
   - Sube `app.py` y `requirements.txt` a tu Space
   - O conecta tu repositorio de GitHub

4. **¡Listo!** Tu app estará disponible en:
   ```
   https://huggingface.co/spaces/TU_USUARIO/football-odds-analyzer
   ```

## 📋 Uso

1. Obtén tu API key gratuita de [THE_ODDS_API](https://the-odds-api.com/)
2. Pega la API key en la interfaz
3. Configura:
   - **hours-from**: Horas desde ahora para comenzar búsqueda (default: 0)
   - **hours-ahead**: Horas hacia adelante para buscar partidos (default: 72)
4. Click en "Ejecutar Análisis"

## 📊 Columnas del resultado

| Columna | Descripción |
|---------|-------------|
| **Partido** | Equipos local vs visitante |
| **Fecha_Hora_Colombia** | Fecha y hora del partido (UTC-5) |
| **Mercado** | Tipo de mercado (Over/Under X.X) |
| **Mejor_Cuota** | La mejor cuota disponible |
| **BDI_jsd_fair** | Índice de desacuerdo entre bookmakers |
| **BDI_n_bookmakers_fair** | Número de bookmakers para el cálculo |

## 🔑 API Key

- Plan gratuito de THE_ODDS_API: 500 requests/mes
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
