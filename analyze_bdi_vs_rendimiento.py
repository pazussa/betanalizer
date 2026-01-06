import pandas as pd
import numpy as np
import math

CSV = 'REVISAR-analisis_mercados_20251220_214421_con_BDI_fair_con_resultados.csv'

df = pd.read_csv(CSV)
# Keep only rows with Resultado Acertado/Fallido
df = df[df['Resultado'].astype(str).str.strip().isin(['Acertado','Fallido'])].copy()
# Convert Mejor_Cuota to numeric
df['Mejor_Cuota'] = pd.to_numeric(df['Mejor_Cuota'], errors='coerce')
# Drop rows without Mejor_Cuota
df = df.dropna(subset=['Mejor_Cuota'])

# For each Partido, pick the row with the highest Mejor_Cuota
idx = df.groupby('Partido')['Mejor_Cuota'].idxmax()
df_top = df.loc[idx].reset_index(drop=True)

# Convert BDI_jsd_fair to numeric
df_top['BDI_jsd_fair'] = pd.to_numeric(df_top['BDI_jsd_fair'], errors='coerce')
# Compute per-row rendimiento: (Mejor_Cuota - 1) if Acertado else -1
def rendimiento_from_row(r):
    cuota = float(r['Mejor_Cuota'])
    if str(r['Resultado']).strip() == 'Acertado':
        return cuota - 1.0
    else:
        return -1.0

df_top['Rendimiento'] = df_top.apply(rendimiento_from_row, axis=1)

# Drop rows with NaN BDI_jsd_fair
df_top = df_top.dropna(subset=['BDI_jsd_fair'])

n = len(df_top)
if n == 0:
    print('No hay datos válidos tras agrupar por partido y filtrar.')
    raise SystemExit(1)

x = df_top['BDI_jsd_fair'].astype(float).values
y = df_top['Rendimiento'].astype(float).values

# Pearson
pearson = np.corrcoef(x, y)[0,1]
# Spearman via ranks (avoid scipy dependency)
xr = pd.Series(x).rank().values
yr = pd.Series(y).rank().values
spearman = np.corrcoef(xr, yr)[0,1]
# Linear fit
slope, intercept = np.polyfit(x, y, 1)

print(f'N partidos (filtrados): {n}')
print(f'Pearson (BDI_jsd_fair vs Rendimiento): {pearson:.6f}')
print(f'Spearman (BDI_jsd_fair vs Rendimiento): {spearman:.6f}')
print(f'Linear slope: {slope:.6f} (intercept {intercept:.6f})')
print(f'Rendimiento medio: {np.mean(y):.4f}  std: {np.std(y):.4f}')

# Deciles summary
try:
    df_top['decile'] = pd.qcut(df_top['BDI_jsd_fair'], 10, labels=False, duplicates='drop')
except Exception:
    df_top['decile'] = pd.cut(df_top['BDI_jsd_fair'], 10, labels=False)

decile_table = df_top.groupby('decile').agg(
    n=('Rendimiento','count'),
    mean_bdi=('BDI_jsd_fair','mean'),
    mean_rend=('Rendimiento','mean'),
    pct_positive=('Rendimiento', lambda s: (s>0).mean())
).reset_index().sort_values('decile')

print('\nDecile summary (BDI_jsd_fair):')
print(decile_table.to_string(index=False, float_format='%.6f'))

# Save summary
df_top.to_csv('bdi_top_by_match_with_rendimiento.csv', index=False)
print('\nSaved filtered rows to bdi_top_by_match_with_rendimiento.csv')
