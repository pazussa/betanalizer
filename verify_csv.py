import pandas as pd

df = pd.read_csv('analisis_cuotas_20251122_093214.csv')

print('Total columnas:', len(df.columns))
print('\n=== COLUMNAS ELIMINADAS (No aparecen) ===')
eliminadas = ['Equipo_Local', 'Equipo_Visitante', 'Liga', 'Timestamp']
for col in eliminadas:
    existe = col in df.columns
    print(f'{col}: {"EXISTE ❌" if existe else "NO EXISTE ✅"}')

print('\n=== COLUMNAS DE MARGEN POR BOOKMAKER ===')
margin_cols = [c for c in df.columns if c.startswith('Margen_') and c not in ['Margen_Casa_Pct', 'Margen_Mercado_Promedio_Pct', 'Ventaja_Margen_Pct']]
print(margin_cols)

print('\n=== COLUMNAS DE CUOTAS H2H ===')
h2h_cols = [c for c in df.columns if c.startswith('Cuota_')]
print(h2h_cols)

print('\n=== VERIFICAR HORA GMT-5 (Colombia) ===')
print('Fecha_Hora_COT (primeras 5):')
for fecha in df['Fecha_Hora_COT'].head(5):
    print(f'  {fecha}')

print('\n=== MUESTRA DE DATOS COMPLETOS (Primera fila) ===')
primera_fila = df.iloc[0]
print(f"Partido: {primera_fila['Partido']}")
print(f"Fecha_Hora_COT: {primera_fila['Fecha_Hora_COT']}")
print(f"Margen Pinnacle: {primera_fila['Margen_Pinnacle_Pct']}%")
print(f"Cuota 1 Pinnacle: {primera_fila['Cuota_1_Pinnacle']}")
print(f"Cuota X Pinnacle: {primera_fila['Cuota_X_Pinnacle']}")
print(f"Cuota 2 Pinnacle: {primera_fila['Cuota_2_Pinnacle']}")
