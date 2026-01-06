import pandas as pd
from pathlib import Path

files = [
    "analisis_mercados_20260102_203616.csv",
    "analisis_mercados_20260102_204756.csv",
    "analisis_mercados_20260102_204914.csv",
]

out = Path("analisis_mercados_20260102_fusionado.csv")

dfs = []
counts = {}
for f in files:
    p = Path(f)
    if not p.exists():
        raise FileNotFoundError(f"No existe: {f}")
    df = pd.read_csv(p)
    counts[f] = len(df)
    dfs.append(df)

# Align columns: take union of columns, reindex each df
all_cols = []
for df in dfs:
    for c in df.columns:
        if c not in all_cols:
            all_cols.append(c)

aligned = [df.reindex(columns=all_cols) for df in dfs]
merged = pd.concat(aligned, ignore_index=True)
before = len(merged)
merged = merged.drop_duplicates()
after = len(merged)

overlap = before - after

merged.to_csv(out, index=False)

print("Counts per file:")
for k, v in counts.items():
    print(f"  {k}: {v}")
print(f"Merged (rows before dedupe): {before}")
print(f"Rows after drop_duplicates: {after}")
print(f"Duplicated rows removed: {overlap}")
print(f"Saved merged CSV to: {out}")
