# Guía de Configuración

## Requisitos del Sistema

- Python 3.7 o superior
- Conexión a internet para APIs
- API keys de proveedores oficiales

## Instalación

### 1. Clonar el Proyecto
```bash
git clone <repository-url>
cd bets2
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac  
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

## Configuración de API Keys

### The Odds API (Requerida)
1. Visita: https://the-odds-api.com/
2. Crea cuenta gratuita
3. Copia tu API key

### SportRadar (Opcional)
1. Visita: https://developer.sportradar.com/
2. Registrate para trial gratuito
3. Copia tu API key

### Configurar Variables de Entorno
```bash
# Copia el archivo de ejemplo
cp .env.example .env

# Edita .env con tus API keys
THE_ODDS_API_KEY=tu_api_key_aqui
SPORTRADAR_API_KEY=tu_api_key_aqui
```

## Verificación de Configuración

```bash
python main.py validate
```

Deberías ver:
```
🔍 Validando configuración del sistema...
🔑 The Odds API Key: ✅ Configurada
🔑 SportRadar API Key: ✅ Configurada

📡 Estado de APIs:
  ✅ The Odds Api: Conectada
  ✅ Sportradar Api: Conectada

🎉 Sistema completamente funcional
```

## Uso Básico

### Análisis Completo
```bash
python main.py analyze
```

### Personalizar Criterios
```bash
python main.py analyze --min-probability 0.8 --min-odds 1.40
```

### Solo Resultados que Cumplen
```bash
python main.py analyze --only-compliant
```

### Exportar a CSV
```bash
python main.py analyze --export-csv resultados.csv
```

## Solución de Problemas

### Error: "THE_ODDS_API_KEY es requerida"
- Verifica que el archivo `.env` existe
- Confirma que la variable está bien escrita
- Asegúrate que la API key es válida

### Error: "No se encontraron partidos"
- Verifica conexión a internet
- Confirma que las APIs están funcionando
- Intenta aumentar `--hours-ahead`

### Error 401: Unauthorized
- Verifica que tu API key es correcta
- Confirma que no ha expirado
- Revisa que tienes permisos

### Error 429: Rate Limit
- Has excedido tu quota
- Espera o actualiza tu plan
- Implementa delays entre requests

## Configuración Avanzada

### Logging Personalizado
En `main.py`, ajusta el nivel de logging:
```python
logging.basicConfig(level=logging.DEBUG)  # Para más detalle
```

### Timeout de APIs
En `.env`:
```env
API_TIMEOUT=60
API_RATE_LIMIT=30
```

### Filtros Personalizados
Modifica los valores por defecto en `src/analyzer.py`:
```python
self.min_probability = 0.75  # 75% en lugar de 70%
self.min_odds = 1.35        # 1.35 en lugar de 1.30
```