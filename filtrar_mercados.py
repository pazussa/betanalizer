import pandas as pd

# Cargar el dataset
archivo = 'analisis_mercados_20251219_204227.csv'
df = pd.read_csv(archivo)

# -----------------------------
# Filtro 1: Mercado 1X, cuota 1.6-1.8, volatilidad <2.5%, casas >2
# -----------------------------
filtro1 = (
    (df['Mercado'].str.strip().str.lower() == '1x') &
    (df['Mejor_Cuota'] >= 1.6) &
    (df['Mejor_Cuota'] <= 1.8) &
    (df['Volatilidad_Pct'] < 2.5) &
    (df['Num_Casas'] > 2)
)
df_filtro1 = df[filtro1]
df_filtro1.to_csv('filtro1_resultados.csv', index=False)
print(f"Filtro 1: {len(df_filtro1)} filas guardadas en filtro1_resultados.csv")

# -----------------------------
# Filtro 2: Mercado Goles Over/Under, Volatilidad >= 1.5
# -----------------------------
filtro2 = (
    df['Tipo_Mercado'].str.contains('Goles', case=False, na=False) &
    (df['Volatilidad_Pct'] >= 1.5)
)
df_filtro2 = df[filtro2]
df_filtro2.to_csv('filtro2_resultados.csv', index=False)
print(f"Filtro 2: {len(df_filtro2)} filas guardadas en filtro2_resultados.csv")
