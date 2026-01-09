# 🔍 Buscador de Resultados

Carpeta con herramientas para buscar resultados de partidos y analizar rendimiento.

## 📁 Archivos

| Archivo | Descripción |
|---------|-------------|
| `buscar_resultados.py` | Busca resultados y los agrega al CSV |
| `analizar_rendimiento.py` | Analiza ROI, profit por mercado/liga |
| `procesar_multiples.py` | Procesa varios archivos a la vez |
| `resultados_marzo_2025.json` | Base de 405 resultados de marzo 2025 |

## 🚀 Uso Rápido

### Procesar un archivo
```bash
python buscar_resultados.py ../historical_analysis/2025/marzo/historical_20250314.csv
```

### Procesar múltiples archivos
```bash
python procesar_multiples.py ../historical_analysis/2025/marzo/historical_2025031*.csv
```

### Solo analizar (si ya tiene resultados)
```bash
python analizar_rendimiento.py archivo_con_resultados.csv
```

## 📄 Formato JSON de Resultados

```json
{
    "Real Madrid vs Barcelona": "2-1",
    "Liverpool vs Manchester United": "3-0"
}
```

## 🔄 Flujo de Trabajo

1. **Ejecutar búsqueda** → Genera `_resultados.json` y `_no_encontrados.txt`
2. **Buscar manualmente** los partidos faltantes (Google, Flashscore, ESPN)
3. **Agregar al JSON** los resultados encontrados
4. **Re-ejecutar** para completar el procesamiento
5. **Analizar rendimiento** con el archivo `_con_resultados.csv`

## 📊 Salida

- `archivo_resultados.json` - Resultados encontrados
- `archivo_no_encontrados.txt` - Partidos sin resultado
- `archivo_con_resultados.csv` - CSV con Score, Total_Goles, Acerto
