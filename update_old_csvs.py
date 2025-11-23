import pandas as pd
import os

files = [
    'analisis_cuotas_20251121_230704.csv',
    'analisis_cuotas_20251121_233731.csv'
]

for f in files:
    if os.path.exists(f):
        df = pd.read_csv(f)
        if 'Ventaja_Margen_Pct' not in df.columns:
            # Verificar si tiene las columnas de margen
            if 'Margen_Mercado_Promedio_Pct' in df.columns and 'Margen_Casa_Pct' in df.columns:
                df['Ventaja_Margen_Pct'] = (df['Margen_Mercado_Promedio_Pct'] - df['Margen_Casa_Pct']).round(2)
                df.to_csv(f, index=False)
                print(f'✅ {f} actualizado')
            else:
                print(f'⚠️ {f} no tiene columnas de margen, no se puede calcular ventaja')
        else:
            print(f'⚠️ {f} ya tiene la columna')
    else:
        print(f'❌ {f} no existe')

print('\n✅ Proceso completado')
