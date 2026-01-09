#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

TEMPLATE_COLUMNS = [
    'Partido','Fecha_Hora_Colombia','Liga','Mercado','Tipo_Mercado',
    'Archivo_Origen','Verified_Score','Source'
]

def main():
    root = Path('historical_con_resultados')
    files = sorted(root.glob('*_con_resultados.csv'))
    if not files:
        print('No se encontraron archivos en historical_con_resultados')
        return 1

    rows = []
    for f in files:
        df = pd.read_csv(f)
        miss = df[df['Score'].isna()].copy()
        if miss.empty:
            continue
        miss['Archivo_Origen'] = f.name
        miss['Verified_Score'] = ''
        miss['Source'] = ''
        rows.append(miss[['Partido','Fecha_Hora_Colombia','Liga','Mercado','Tipo_Mercado','Archivo_Origen','Verified_Score','Source']])

    if not rows:
        print('No hay partidos faltantes de marcador en los archivos.')
        return 0

    out = pd.concat(rows, ignore_index=True)
    # Ordenar por liga y archivo
    out.sort_values(['Liga','Archivo_Origen','Fecha_Hora_Colombia','Partido'], inplace=True)
    out.to_csv('missing_scores_template.csv', index=False)
    print('Plantilla generada: missing_scores_template.csv')
    print('Columnas: ', ', '.join(TEMPLATE_COLUMNS))
    print('Rellena Verified_Score (ej. 2-1) y Source (ej. ESPN) con datos verificados.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
