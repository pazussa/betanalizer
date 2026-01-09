#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from collections import Counter

def main():
    root = Path('historical_con_resultados')
    files = sorted(root.glob('*_con_resultados.csv'))
    if not files:
        print('No se encontraron archivos en historical_con_resultados')
        return 1

    lines = []
    lines.append('# Cobertura de Resultados\n')

    total_with, total_without = 0, 0
    lines.append('## Por archivo\n')
    for f in files:
        df = pd.read_csv(f)
        with_score = int(df['Score'].notna().sum())
        without_score = int(df['Score'].isna().sum())
        total_with += with_score
        total_without += without_score
        pct = (with_score / (with_score + without_score) * 100.0) if (with_score + without_score) else 0.0
        lines.append(f'- {f.name}: {with_score} con resultado, {without_score} sin resultado ({pct:.1f}%)')

    grand_pct = (total_with / (total_with + total_without) * 100.0) if (total_with + total_without) else 0.0
    lines.append(f'\n**Total**: {total_with} con resultado, {total_without} sin resultado ({grand_pct:.1f}%)\n')

    # Por liga
    lines.append('## Por liga (faltantes)\n')
    missing_by_league = Counter()
    missing_examples = {}
    for f in files:
        df = pd.read_csv(f)
        df_m = df[df['Score'].isna()]
        vc = df_m['Liga'].value_counts()
        for liga, cnt in vc.items():
            missing_by_league[liga] += int(cnt)
        # primeras 10 muestras por liga
        for liga in vc.index:
            ex = df_m[df_m['Liga']==liga]['Partido'].drop_duplicates().head(10).tolist()
            missing_examples.setdefault(liga, [])
            for p in ex:
                if p not in missing_examples[liga]:
                    missing_examples[liga].append(p)
            missing_examples[liga] = missing_examples[liga][:10]

    for liga, cnt in missing_by_league.most_common():
        lines.append(f'- {liga}: {cnt} sin resultado')

    lines.append('\n## Partidos faltantes (muestras)\n')
    for liga, ejemplos in missing_examples.items():
        lines.append(f'- {liga}:')
        for p in ejemplos:
            lines.append(f'  - {p}')

    Path('cobertura_resultados.md').write_text('\n'.join(lines), encoding='utf-8')
    print('Reporte generado en cobertura_resultados.md')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
