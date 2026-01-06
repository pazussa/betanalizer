import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score

CSV = 'REVISAR-analisis_mercados_20251220_214421_con_BDI_fair_con_resultados.csv'
cols = ['BDI_jsd_fair', 'BDI_jsd', 'Volatilidad_Pct']

df = pd.read_csv(CSV)
# Filtrar solo verificados
df = df[df['Resultado'].astype(str).str.strip().isin(['Acertado','Fallido'])].copy()
if df.empty:
    print('No hay filas verificadas (Acertado/Fallido)')
    raise SystemExit(1)

y = (df['Resultado'].astype(str).str.strip() == 'Acertado').astype(int)

results = []
for c in cols:
    # convertir a num y manejar NaNs
    x = pd.to_numeric(df.get(c), errors='coerce')
    mask = x.notna()
    n = mask.sum()
    if n == 0:
        results.append((c, np.nan, np.nan, np.nan, 0))
        continue
    xv = x[mask]
    yv = y[mask]
    # Pearson
    pearson = np.corrcoef(xv.astype(float), yv.astype(float))[0,1]
    # Spearman
    try:
        from scipy.stats import spearmanr
        spear = spearmanr(xv, yv).correlation
    except Exception:
        spear = np.nan
    # AUC
    try:
        auc = roc_auc_score(yv, xv)
    except Exception:
        auc = np.nan
    results.append((c, pearson, spear, auc, int(n)))

# Mostrar
print('Columna, Pearson, Spearman, AUC, N')
for r in results:
    print(f'{r[0]}, {r[1]:.4f}, {r[2]:.4f}, {r[3]:.4f}, {r[4]}')

# Rankeos
by_abs_pear = sorted(results, key=lambda r: (np.nan_to_num(abs(r[1])), np.nan_to_num(r[1])), reverse=True)
by_auc = sorted(results, key=lambda r: (np.nan_to_num(r[3])), reverse=True)

print('\nRanking por |Pearson|:')
for r in by_abs_pear:
    print(f'  {r[0]} -> |Pearson|={abs(r[1]):.4f}')

print('\nRanking por AUC:')
for r in by_auc:
    print(f'  {r[0]} -> AUC={r[3]:.4f}')

# Resumen breve
best_pear = by_abs_pear[0][0]
best_auc = by_auc[0][0]
print(f"\nMejor por correlación (|Pearson|): {best_pear}")
print(f"Mejor por AUC: {best_auc}")
