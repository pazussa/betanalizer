
import pandas as pd
from pathlib import Path

# Load all csvs
files = list(Path('/home/asus/Escritorio/proyectos/betsanalizer/betanalizer/historical_con_resultados').glob('*.csv'))
dfs = []
for f in files:
    try:
        df = pd.read_csv(f)
        if 'Liga' in df.columns:
            dfs.append(df)
    except:
        pass

full_df = pd.concat(dfs, ignore_index=True)

# Inspect Leagues
unique_leagues = full_df['Liga'].unique()
print("Unique Leagues:", unique_leagues)

# Filter for Liga Profesional and missing Score
arg_missing = full_df[
    (full_df['Liga'] == 'Liga Profesional') &
    (full_df['Score'].isna() | (full_df['Score'] == ''))
]

# Create Home/Away from Partido
# Use copy to avoid warnings/errors
arg_missing = arg_missing.copy()
print(f"Arg missing rows: {len(arg_missing)}")
if len(arg_missing) > 0:
    splits = arg_missing['Partido'].str.split(' vs ', expand=True)
    # Check what splits looks like
    print("Splits columns:", splits.columns)
    if 0 in splits.columns:
        arg_missing['Home Team'] = splits[0]
    if 1 in splits.columns:
        arg_missing['Away Team'] = splits[1]
else:
    print("No missing Argentina matches found.")

unique_missing = arg_missing[['Home Team', 'Away Team', 'Fecha_Hora_Colombia']].drop_duplicates()
print(f"Found {len(unique_missing)} missing Argentina matches.")
for i, row in unique_missing.iterrows():
    print(f"{row['Home Team']} vs {row['Away Team']} ({row['Fecha_Hora_Colombia']})")
