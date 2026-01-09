#!/usr/bin/env python3
"""
📊 ANALIZADOR DE RENDIMIENTO
============================

Analiza el rendimiento (ROI, profit) de un archivo histórico con resultados.

Uso:
    python analizar_rendimiento.py <archivo_con_resultados.csv>
"""

import pandas as pd
import numpy as np
from scipy import stats
import sys
import os
from datetime import datetime


def cargar_datos(filepath: str) -> pd.DataFrame:
    """Carga y prepara el DataFrame con los datos históricos."""
    df = pd.read_csv(filepath)
    df = df[df['Score'].notna() & (df['Score'] != '')].copy()
    df['Profit'] = df.apply(
        lambda x: x['Mejor_Cuota'] - 1 if x['Acerto'] == 'Sí' else -1, 
        axis=1
    )
    df['Tipo'] = df['Mercado'].apply(lambda x: x.split()[0])
    df['Linea'] = df['Mercado'].apply(lambda x: float(x.split()[1]))
    df['Acerto_Num'] = (df['Acerto'] == 'Sí').astype(int)
    return df


def analisis_general(df: pd.DataFrame) -> dict:
    """Análisis general del dataset."""
    total_profit = df['Profit'].sum()
    total_bets = len(df)
    roi = 100 * total_profit / total_bets if total_bets > 0 else 0
    win_rate = 100 * (df['Acerto'] == 'Sí').sum() / total_bets if total_bets > 0 else 0
    return {
        'total_bets': total_bets,
        'total_profit': total_profit,
        'roi': roi,
        'win_rate': win_rate,
        'partidos_unicos': df['Partido'].nunique()
    }


def analisis_por_tipo(df: pd.DataFrame) -> pd.DataFrame:
    """Análisis por tipo de mercado (Over/Under)."""
    stats_tipo = []
    for tipo in ['Over', 'Under']:
        sub = df[df['Tipo'] == tipo]
        if len(sub) > 0:
            stats_tipo.append({
                'Tipo': tipo,
                'N': len(sub),
                'Profit': sub['Profit'].sum(),
                'ROI': 100 * sub['Profit'].sum() / len(sub),
                'WinRate': 100 * (sub['Acerto'] == 'Sí').sum() / len(sub),
                'Cuota_Media': sub['Mejor_Cuota'].mean()
            })
    return pd.DataFrame(stats_tipo)


def analisis_por_linea(df: pd.DataFrame, min_apuestas: int = 5) -> pd.DataFrame:
    """Análisis por línea de mercado."""
    stats_linea = []
    for mercado in df['Mercado'].unique():
        sub = df[df['Mercado'] == mercado]
        if len(sub) >= min_apuestas:
            stats_linea.append({
                'Mercado': mercado,
                'N': len(sub),
                'Profit': sub['Profit'].sum(),
                'ROI': 100 * sub['Profit'].sum() / len(sub),
                'WinRate': 100 * (sub['Acerto'] == 'Sí').sum() / len(sub)
            })
    return pd.DataFrame(stats_linea).sort_values('ROI', ascending=False) if stats_linea else pd.DataFrame()


def analisis_por_liga(df: pd.DataFrame, min_apuestas: int = 10) -> pd.DataFrame:
    """Análisis por liga."""
    stats_liga = []
    for liga in df['Liga'].unique():
        sub = df[df['Liga'] == liga]
        if len(sub) >= min_apuestas:
            stats_liga.append({
                'Liga': liga,
                'N': len(sub),
                'Profit': sub['Profit'].sum(),
                'ROI': 100 * sub['Profit'].sum() / len(sub),
                'WinRate': 100 * (sub['Acerto'] == 'Sí').sum() / len(sub)
            })
    return pd.DataFrame(stats_liga).sort_values('ROI', ascending=False) if stats_liga else pd.DataFrame()


def calcular_estrategias(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula rendimiento de diferentes estrategias de filtrado."""
    estrategias = []
    
    # Solo Under
    sub = df[df['Tipo'] == 'Under']
    if len(sub) > 0:
        estrategias.append({
            'Estrategia': 'Solo UNDER',
            'N': len(sub),
            'Profit': sub['Profit'].sum(),
            'ROI': 100 * sub['Profit'].sum() / len(sub)
        })
    
    # Under 2.5
    sub = df[df['Mercado'] == 'Under 2.5']
    if len(sub) > 0:
        estrategias.append({
            'Estrategia': 'Solo Under 2.5',
            'N': len(sub),
            'Profit': sub['Profit'].sum(),
            'ROI': 100 * sub['Profit'].sum() / len(sub)
        })
    
    # Under 2.5 + Cuota <= 2.2
    sub = df[(df['Mercado'] == 'Under 2.5') & (df['Mejor_Cuota'] <= 2.2)]
    if len(sub) > 0:
        estrategias.append({
            'Estrategia': 'Under 2.5 + Cuota≤2.2',
            'N': len(sub),
            'Profit': sub['Profit'].sum(),
            'ROI': 100 * sub['Profit'].sum() / len(sub)
        })
    
    # Under + Cuota < 2.0
    sub = df[(df['Tipo'] == 'Under') & (df['Mejor_Cuota'] < 2.0)]
    if len(sub) > 0:
        estrategias.append({
            'Estrategia': 'Under + Cuota<2.0',
            'N': len(sub),
            'Profit': sub['Profit'].sum(),
            'ROI': 100 * sub['Profit'].sum() / len(sub)
        })
    
    # Under 2.25/2.5/3.5
    sub = df[df['Mercado'].isin(['Under 2.25', 'Under 2.5', 'Under 3.5'])]
    if len(sub) > 0:
        estrategias.append({
            'Estrategia': 'Under 2.25/2.5/3.5',
            'N': len(sub),
            'Profit': sub['Profit'].sum(),
            'ROI': 100 * sub['Profit'].sum() / len(sub)
        })
    
    return pd.DataFrame(estrategias).sort_values('ROI', ascending=False) if estrategias else pd.DataFrame()


def imprimir_reporte(df: pd.DataFrame, filepath: str):
    """Imprime el reporte completo de análisis."""
    
    print('=' * 70)
    print(f'ANÁLISIS DE RENDIMIENTO HISTÓRICO')
    print(f'Archivo: {os.path.basename(filepath)}')
    print(f'Fecha análisis: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)
    
    # General
    general = analisis_general(df)
    print(f'\n📊 RESUMEN GENERAL')
    print(f'   Partidos únicos: {general["partidos_unicos"]}')
    print(f'   Total apuestas: {general["total_bets"]}')
    print(f'   Rendimiento: {general["total_profit"]:+.2f} unidades')
    print(f'   ROI: {general["roi"]:+.2f}%')
    print(f'   Win Rate: {general["win_rate"]:.1f}%')
    
    # Por tipo
    print(f'\n📈 POR TIPO DE MERCADO')
    print('-' * 60)
    tipo_df = analisis_por_tipo(df)
    for _, row in tipo_df.iterrows():
        emoji = '✅' if row['ROI'] > 0 else '❌'
        print(f'   {emoji} {row["Tipo"]:6s}: {row["N"]:3.0f} apuestas | Profit: {row["Profit"]:+7.2f}u | ROI: {row["ROI"]:+6.2f}%')
    
    # Por línea
    linea_df = analisis_por_linea(df)
    if not linea_df.empty:
        print(f'\n📊 TOP 5 LÍNEAS RENTABLES (min 5 apuestas)')
        print('-' * 60)
        for _, row in linea_df.head(5).iterrows():
            print(f'   {row["Mercado"]:12s}: ROI {row["ROI"]:+6.2f}% ({row["Profit"]:+.2f}u en {row["N"]:.0f})')
        
        print(f'\n📉 5 PEORES LÍNEAS')
        print('-' * 60)
        for _, row in linea_df.tail(5).iloc[::-1].iterrows():
            print(f'   {row["Mercado"]:12s}: ROI {row["ROI"]:+6.2f}% ({row["Profit"]:+.2f}u en {row["N"]:.0f})')
    
    # Por liga
    liga_df = analisis_por_liga(df)
    if not liga_df.empty:
        print(f'\n🏆 TOP 5 LIGAS (min 10 apuestas)')
        print('-' * 60)
        for _, row in liga_df.head(5).iterrows():
            print(f'   {row["Liga"][:30]:30s}: ROI {row["ROI"]:+6.2f}%')
    
    # Estrategias
    estrategias = calcular_estrategias(df)
    if not estrategias.empty:
        print(f'\n🎯 ESTRATEGIAS RECOMENDADAS')
        print('=' * 70)
        print(f'{"Estrategia":<30} {"N":>6} {"Profit":>10} {"ROI":>8}')
        print('-' * 58)
        for _, row in estrategias.iterrows():
            print(f'{row["Estrategia"]:<30} {row["N"]:>6.0f} {row["Profit"]:>+10.2f}u {row["ROI"]:>+7.2f}%')
    
    print('\n' + '=' * 70)


def main():
    if len(sys.argv) < 2:
        print('Uso: python analizar_rendimiento.py <archivo_con_resultados.csv>')
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f'Error: No se encuentra el archivo {filepath}')
        sys.exit(1)
    
    df = cargar_datos(filepath)
    
    if len(df) == 0:
        print('Error: No hay datos con resultados para analizar')
        sys.exit(1)
    
    imprimir_reporte(df, filepath)


if __name__ == '__main__':
    main()
