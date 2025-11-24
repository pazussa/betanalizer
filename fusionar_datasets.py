import pandas as pd
from datetime import datetime

# Lista de archivos a fusionar
files = [
    'analisis_mercados_20251124_001340.csv',
    'analisis_mercados_20251124_002559.csv',
    'analisis_mercados_20251124_003036.csv',
    'analisis_mercados_20251124_003313.csv',
]

# Leer y concatenar los archivos
frames = []
for f in files:
    try:
        df = pd.read_csv(f)
        frames.append(df)
        print(f'✅ {f} leído ({len(df)} filas)')
    except Exception as e:
        print(f'❌ Error leyendo {f}: {e}')

fusionado = pd.concat(frames, ignore_index=True)
print(f'🔗 Total filas fusionadas: {len(fusionado)}')

# Guardar el archivo fusionado
fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
output = f'analisis_mercados_fusionado_{fecha}.csv'
fusionado.to_csv(output, index=False, encoding='utf-8')
print(f'✅ Archivo fusionado guardado como: {output}')
