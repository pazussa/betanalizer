#!/usr/bin/env python3
import pandas as pd
from pathlib import Path


def calcular_total_goles(score: str):
    try:
        a, b = str(score).split('-', 1)
        return int(a), int(b), int(a) + int(b)
    except Exception:
        return None, None, None


def calcular_acierto(mercado: str, tipo_mercado: str, total_goles: int) -> str:
    if tipo_mercado == 'Goles (Over/Under)':
        try:
            parts = str(mercado).split()
            tipo = parts[0]
            punto = float(parts[1])
            if tipo == 'Over':
                return 'Sí' if total_goles > punto else 'No'
            if tipo == 'Under':
                return 'Sí' if total_goles < punto else 'No'
        except Exception:
            return None
    # Otros mercados no evaluados aquí
    return None


def main():
    tpl_path = Path('missing_scores_template.csv')
    if not tpl_path.exists():
        print('missing_scores_template.csv no existe. Genera la plantilla primero.')
        return 1

    tpl = pd.read_csv(tpl_path)
    # Filtrar solo filas con Verified_Score relleno
    tpl = tpl[(tpl['Verified_Score'].astype(str).str.strip() != '') & (tpl['Source'].astype(str).str.strip() != '')]
    if tpl.empty:
        print('La plantilla no tiene Verified_Score rellenados.')
        return 1

    # Agrupar por archivo de origen para aplicar en lote
    for archivo, grp in tpl.groupby('Archivo_Origen'):
        fpath = Path('historical_con_resultados')/archivo
        if not fpath.exists():
            print(f'Archivo no encontrado: {archivo}')
            continue
        df = pd.read_csv(fpath)
        updated = 0
        for _, r in grp.iterrows():
            partido = str(r['Partido'])
            score = str(r['Verified_Score']).strip()
            # localizar filas por partido exacto (match directo)
            mask = df['Partido'].astype(str).str.strip() == partido.strip()
            if not mask.any():
                # intento: contener ambos equipos
                parts = partido.split(' vs ')
                if len(parts) == 2:
                    home, away = parts
                    m2 = df['Partido'].astype(str).str.contains(home, na=False) & df['Partido'].astype(str).str.contains(away, na=False)
                    mask = m2
            if not mask.any():
                print(f'No se encontró partido en {archivo}: {partido}')
                continue
            gl, gv, total = calcular_total_goles(score)
            if total is None:
                print(f'Score inválido para {partido}: {score}')
                continue
            # Añadir columna de fuente si no existe
            if 'Fuente_Web' not in df.columns:
                df['Fuente_Web'] = ''
            df.loc[mask, 'Score'] = score
            df.loc[mask, 'Total_Goles'] = total
            df.loc[mask, 'Fuente_Web'] = str(r['Source']).strip()
            # calcular acierto sólo si es Over/Under
            tipo = (df.loc[mask, 'Tipo_Mercado'].astype(str).unique()[0])
            mercado = (df.loc[mask, 'Mercado'].astype(str).unique()[0])
            ac = calcular_acierto(mercado, tipo, total)
            if ac is not None:
                df.loc[mask, 'Acerto'] = ac
            updated += int(mask.sum())
        df.to_csv(fpath, index=False)
        print(f'{archivo}: {updated} filas actualizadas')

    print('Aplicación completada.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
