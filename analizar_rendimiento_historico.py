#!/usr/bin/env python3
"""
Script de Análisis de Rendimiento Histórico
============================================
Automatiza el análisis completo de rendimiento para archivos históricos
con resultados de apuestas Over/Under.

Uso:
    python analizar_rendimiento_historico.py <archivo_con_resultados.csv>
    
El archivo debe tener las columnas:
- Partido, Mercado, Mejor_Cuota, Liga, Score, Total_Goles, Acerto
- BDI_std_p, BDI_jsd_fair (opcionales para análisis BDI)
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
    
    # Filtrar solo los que tienen resultado
    df = df[df['Score'].notna() & (df['Score'] != '')].copy()
    
    # Calcular profit: Si acierta = cuota - 1, si falla = -1
    df['Profit'] = df.apply(
        lambda x: x['Mejor_Cuota'] - 1 if x['Acerto'] == 'Sí' else -1, 
        axis=1
    )
    
    # Extraer tipo y línea del mercado
    df['Tipo'] = df['Mercado'].apply(lambda x: x.split()[0])
    df['Linea'] = df['Mercado'].apply(lambda x: float(x.split()[1]))
    df['Acerto_Num'] = (df['Acerto'] == 'Sí').astype(int)
    
    return df


def analisis_general(df: pd.DataFrame) -> dict:
    """Análisis general del dataset."""
    total_profit = df['Profit'].sum()
    total_bets = len(df)
    roi = 100 * total_profit / total_bets
    win_rate = 100 * (df['Acerto'] == 'Sí').sum() / total_bets
    
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
                'WinRate': 100 * (sub['Acerto'] == 'Sí').sum() / len(sub),
                'Cuota_Media': sub['Mejor_Cuota'].mean()
            })
    return pd.DataFrame(stats_linea).sort_values('ROI', ascending=False)


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
    return pd.DataFrame(stats_liga).sort_values('ROI', ascending=False)


def analisis_por_cuota(df: pd.DataFrame) -> pd.DataFrame:
    """Análisis por rangos de cuota."""
    bins = [1.0, 1.5, 1.8, 2.0, 2.2, 2.5, 3.0, 10.0]
    labels = ['1.00-1.50', '1.50-1.80', '1.80-2.00', '2.00-2.20', '2.20-2.50', '2.50-3.00', '3.00+']
    df['Cuota_Rango'] = pd.cut(df['Mejor_Cuota'], bins=bins, labels=labels, include_lowest=True)
    
    stats_cuota = []
    for rango in labels:
        sub = df[df['Cuota_Rango'] == rango]
        if len(sub) > 0:
            stats_cuota.append({
                'Rango_Cuota': rango,
                'N': len(sub),
                'Profit': sub['Profit'].sum(),
                'ROI': 100 * sub['Profit'].sum() / len(sub),
                'WinRate': 100 * (sub['Acerto'] == 'Sí').sum() / len(sub),
                'Cuota_Media': sub['Mejor_Cuota'].mean()
            })
    return pd.DataFrame(stats_cuota)


def analisis_por_cuota_tipo(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    """Análisis por rangos de cuota para un tipo específico."""
    bins = [1.0, 1.5, 1.8, 2.0, 2.2, 2.5, 3.0, 10.0]
    labels = ['1.00-1.50', '1.50-1.80', '1.80-2.00', '2.00-2.20', '2.20-2.50', '2.50-3.00', '3.00+']
    df['Cuota_Rango'] = pd.cut(df['Mejor_Cuota'], bins=bins, labels=labels, include_lowest=True)
    
    df_tipo = df[df['Tipo'] == tipo]
    stats_cuota = []
    for rango in labels:
        sub = df_tipo[df_tipo['Cuota_Rango'] == rango]
        if len(sub) > 0:
            stats_cuota.append({
                'Rango_Cuota': rango,
                'N': len(sub),
                'Profit': sub['Profit'].sum(),
                'ROI': 100 * sub['Profit'].sum() / len(sub),
                'WinRate': 100 * (sub['Acerto'] == 'Sí').sum() / len(sub)
            })
    return pd.DataFrame(stats_cuota)


def analisis_por_bdi(df: pd.DataFrame) -> dict:
    """Análisis por cuartiles de BDI_std_p."""
    if 'BDI_std_p' not in df.columns:
        return None
    
    df['BDI_Q'] = pd.qcut(df['BDI_std_p'], q=4, labels=['Q1 (Bajo)', 'Q2', 'Q3', 'Q4 (Alto)'], duplicates='drop')
    
    resultados = {'general': [], 'under': [], 'over': []}
    
    for q in ['Q1 (Bajo)', 'Q2', 'Q3', 'Q4 (Alto)']:
        # General
        sub = df[df['BDI_Q'] == q]
        if len(sub) > 0:
            resultados['general'].append({
                'BDI': q,
                'N': len(sub),
                'Profit': sub['Profit'].sum(),
                'ROI': 100 * sub['Profit'].sum() / len(sub),
                'WinRate': 100 * (sub['Acerto'] == 'Sí').sum() / len(sub)
            })
        
        # Under
        sub_u = df[(df['BDI_Q'] == q) & (df['Tipo'] == 'Under')]
        if len(sub_u) > 0:
            resultados['under'].append({
                'BDI': q,
                'N': len(sub_u),
                'Profit': sub_u['Profit'].sum(),
                'ROI': 100 * sub_u['Profit'].sum() / len(sub_u)
            })
        
        # Over
        sub_o = df[(df['BDI_Q'] == q) & (df['Tipo'] == 'Over')]
        if len(sub_o) > 0:
            resultados['over'].append({
                'BDI': q,
                'N': len(sub_o),
                'Profit': sub_o['Profit'].sum(),
                'ROI': 100 * sub_o['Profit'].sum() / len(sub_o)
            })
    
    return {k: pd.DataFrame(v) for k, v in resultados.items()}


def analisis_combinaciones(df: pd.DataFrame, min_apuestas: int = 5) -> pd.DataFrame:
    """Análisis cruzado de Línea + Cuota."""
    bins = [1, 1.6, 1.9, 2.1, 2.5, 10]
    labels = ['<1.6', '1.6-1.9', '1.9-2.1', '2.1-2.5', '>2.5']
    df['Cuota_Grupo'] = pd.cut(df['Mejor_Cuota'], bins=bins, labels=labels, include_lowest=True)
    df['Combo'] = df['Mercado'] + ' | Cuota ' + df['Cuota_Grupo'].astype(str)
    
    stats_combo = []
    for combo in df['Combo'].unique():
        sub = df[df['Combo'] == combo]
        if len(sub) >= min_apuestas:
            stats_combo.append({
                'Combinacion': combo,
                'N': len(sub),
                'Profit': sub['Profit'].sum(),
                'ROI': 100 * sub['Profit'].sum() / len(sub),
                'WinRate': 100 * (sub['Acerto'] == 'Sí').sum() / len(sub)
            })
    
    return pd.DataFrame(stats_combo).sort_values('ROI', ascending=False)


def calcular_correlaciones(df: pd.DataFrame) -> dict:
    """Calcula correlaciones con Profit y Acerto."""
    num_cols = ['Mejor_Cuota', 'Linea', 'BDI_std_p', 'BDI_jsd', 'BDI_mad_p', 'BDI_n_bookmakers']
    
    correlaciones = {'profit': [], 'acerto': []}
    
    for col in num_cols:
        if col in df.columns and df[col].notna().sum() > 10:
            # Con Profit
            corr_p, pval_p = stats.pearsonr(df[col].fillna(0), df['Profit'])
            correlaciones['profit'].append({
                'Variable': col,
                'Correlacion': corr_p,
                'P_Value': pval_p,
                'Significativo': pval_p < 0.05
            })
            
            # Con Acerto
            corr_a, pval_a = stats.pearsonr(df[col].fillna(0), df['Acerto_Num'])
            correlaciones['acerto'].append({
                'Variable': col,
                'Correlacion': corr_a,
                'P_Value': pval_a,
                'Significativo': pval_a < 0.05
            })
    
    return {k: pd.DataFrame(v) for k, v in correlaciones.items()}


def test_significancia_under(df: pd.DataFrame) -> dict:
    """Test estadístico para verificar si el ROI de Under es significativo."""
    df_under = df[df['Tipo'] == 'Under']
    profits_under = df_under['Profit'].values
    
    t_stat, p_val = stats.ttest_1samp(profits_under, 0)
    
    return {
        'n': len(profits_under),
        'mean_profit': profits_under.mean(),
        't_statistic': t_stat,
        'p_value': p_val,
        'significativo': p_val < 0.05
    }


def calcular_estrategias(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula rendimiento de diferentes estrategias de filtrado."""
    estrategias = []
    
    # 1. Solo Under
    sub = df[df['Tipo'] == 'Under']
    if len(sub) > 0:
        estrategias.append({
            'Estrategia': 'Solo UNDER',
            'Filtros': 'Tipo=Under',
            'N': len(sub),
            'Profit': sub['Profit'].sum(),
            'ROI': 100 * sub['Profit'].sum() / len(sub)
        })
    
    # 2. Under 2.5
    sub = df[df['Mercado'] == 'Under 2.5']
    if len(sub) > 0:
        estrategias.append({
            'Estrategia': 'Solo Under 2.5',
            'Filtros': 'Mercado=Under 2.5',
            'N': len(sub),
            'Profit': sub['Profit'].sum(),
            'ROI': 100 * sub['Profit'].sum() / len(sub)
        })
    
    # 3. Under 2.5 + Cuota <= 2.2
    sub = df[(df['Mercado'] == 'Under 2.5') & (df['Mejor_Cuota'] <= 2.2)]
    if len(sub) > 0:
        estrategias.append({
            'Estrategia': 'Under 2.5 + Cuota≤2.2',
            'Filtros': 'Mercado=Under 2.5 & Cuota≤2.2',
            'N': len(sub),
            'Profit': sub['Profit'].sum(),
            'ROI': 100 * sub['Profit'].sum() / len(sub)
        })
    
    # 4. Under + Cuota < 2.0
    sub = df[(df['Tipo'] == 'Under') & (df['Mejor_Cuota'] < 2.0)]
    if len(sub) > 0:
        estrategias.append({
            'Estrategia': 'Under + Cuota<2.0',
            'Filtros': 'Tipo=Under & Cuota<2.0',
            'N': len(sub),
            'Profit': sub['Profit'].sum(),
            'ROI': 100 * sub['Profit'].sum() / len(sub)
        })
    
    # 5. Under 2.25/2.5/3.5
    sub = df[df['Mercado'].isin(['Under 2.25', 'Under 2.5', 'Under 3.5'])]
    if len(sub) > 0:
        estrategias.append({
            'Estrategia': 'Under 2.25/2.5/3.5',
            'Filtros': 'Mercado in [Under 2.25, 2.5, 3.5]',
            'N': len(sub),
            'Profit': sub['Profit'].sum(),
            'ROI': 100 * sub['Profit'].sum() / len(sub)
        })
    
    # 6. Under + Alto BDI (si existe)
    if 'BDI_std_p' in df.columns:
        df['BDI_Q'] = pd.qcut(df['BDI_std_p'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'], duplicates='drop')
        sub = df[(df['Tipo'] == 'Under') & (df['BDI_Q'] == 'Q4')]
        if len(sub) > 0:
            estrategias.append({
                'Estrategia': 'Under + Alto BDI (Q4)',
                'Filtros': 'Tipo=Under & BDI_std_p en Q4',
                'N': len(sub),
                'Profit': sub['Profit'].sum(),
                'ROI': 100 * sub['Profit'].sum() / len(sub)
            })
    
    # 7. Ligas TOP (si hay suficientes datos para identificarlas)
    liga_stats = df.groupby('Liga')['Profit'].agg(['sum', 'count'])
    liga_stats['ROI'] = 100 * liga_stats['sum'] / liga_stats['count']
    top_ligas = liga_stats[liga_stats['count'] >= 10].sort_values('ROI', ascending=False).head(3).index.tolist()
    
    if top_ligas:
        sub = df[(df['Tipo'] == 'Under') & (df['Liga'].isin(top_ligas))]
        if len(sub) > 0:
            estrategias.append({
                'Estrategia': f'Under en TOP 3 Ligas',
                'Filtros': f'Tipo=Under & Liga in {top_ligas[:3]}',
                'N': len(sub),
                'Profit': sub['Profit'].sum(),
                'ROI': 100 * sub['Profit'].sum() / len(sub)
            })
    
    return pd.DataFrame(estrategias).sort_values('ROI', ascending=False)


def imprimir_reporte(df: pd.DataFrame, filepath: str):
    """Imprime el reporte completo de análisis."""
    
    print('=' * 80)
    print(f'ANÁLISIS DE RENDIMIENTO HISTÓRICO')
    print(f'Archivo: {os.path.basename(filepath)}')
    print(f'Fecha de análisis: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    # General
    general = analisis_general(df)
    print(f'\n📊 RESUMEN GENERAL')
    print(f'   Partidos únicos: {general["partidos_unicos"]}')
    print(f'   Total apuestas: {general["total_bets"]}')
    print(f'   Rendimiento total: {general["total_profit"]:+.2f} unidades')
    print(f'   ROI: {general["roi"]:+.2f}%')
    print(f'   Win Rate: {general["win_rate"]:.1f}%')
    
    # Por tipo
    print(f'\n📈 POR TIPO DE MERCADO')
    print('-' * 60)
    tipo_df = analisis_por_tipo(df)
    for _, row in tipo_df.iterrows():
        emoji = '✅' if row['ROI'] > 0 else '❌'
        print(f'   {emoji} {row["Tipo"]:6s}: {row["N"]:3.0f} apuestas | Profit: {row["Profit"]:+7.2f}u | ROI: {row["ROI"]:+6.2f}% | WinRate: {row["WinRate"]:.1f}%')
    
    # Por línea
    print(f'\n📊 TOP 5 LÍNEAS MÁS RENTABLES (min 5 apuestas)')
    print('-' * 60)
    linea_df = analisis_por_linea(df).head(5)
    for _, row in linea_df.iterrows():
        print(f'   {row["Mercado"]:12s}: ROI {row["ROI"]:+6.2f}% ({row["Profit"]:+.2f}u en {row["N"]:.0f} apuestas)')
    
    print(f'\n📉 5 PEORES LÍNEAS')
    print('-' * 60)
    linea_df_worst = analisis_por_linea(df).tail(5).iloc[::-1]
    for _, row in linea_df_worst.iterrows():
        print(f'   {row["Mercado"]:12s}: ROI {row["ROI"]:+6.2f}% ({row["Profit"]:+.2f}u en {row["N"]:.0f} apuestas)')
    
    # Por cuota - UNDER
    print(f'\n💰 RENDIMIENTO UNDER POR RANGO DE CUOTA')
    print('-' * 60)
    cuota_under = analisis_por_cuota_tipo(df, 'Under')
    for _, row in cuota_under.iterrows():
        emoji = '✅' if row['ROI'] > 0 else '❌'
        print(f'   {emoji} Cuota {row["Rango_Cuota"]:10s}: {row["N"]:3.0f} apuestas | ROI: {row["ROI"]:+6.2f}% | WinRate: {row["WinRate"]:.1f}%')
    
    # Por liga
    print(f'\n🏆 TOP 5 LIGAS RENTABLES (min 10 apuestas)')
    print('-' * 60)
    liga_df = analisis_por_liga(df).head(5)
    for _, row in liga_df.iterrows():
        print(f'   {row["Liga"][:35]:35s}: ROI {row["ROI"]:+6.2f}% ({row["Profit"]:+.2f}u)')
    
    print(f'\n💀 5 PEORES LIGAS')
    print('-' * 60)
    liga_df_worst = analisis_por_liga(df).tail(5).iloc[::-1]
    for _, row in liga_df_worst.iterrows():
        print(f'   {row["Liga"][:35]:35s}: ROI {row["ROI"]:+6.2f}% ({row["Profit"]:+.2f}u)')
    
    # Por BDI
    if 'BDI_std_p' in df.columns:
        print(f'\n📐 RENDIMIENTO POR BDI (Desacuerdo entre casas)')
        print('-' * 60)
        bdi_results = analisis_por_bdi(df)
        if bdi_results and 'under' in bdi_results:
            print('   UNDER por cuartil BDI:')
            for _, row in bdi_results['under'].iterrows():
                emoji = '✅' if row['ROI'] > 0 else '❌'
                print(f'   {emoji} {row["BDI"]:12s}: {row["N"]:3.0f} apuestas | ROI: {row["ROI"]:+6.2f}%')
    
    # Mejores combinaciones
    print(f'\n🎯 TOP 5 COMBINACIONES (Línea + Cuota)')
    print('-' * 60)
    combo_df = analisis_combinaciones(df).head(5)
    for _, row in combo_df.iterrows():
        print(f'   {row["Combinacion"]:35s}: ROI {row["ROI"]:+6.2f}% ({row["N"]:.0f} apuestas)')
    
    # Correlaciones
    print(f'\n📈 CORRELACIONES SIGNIFICATIVAS')
    print('-' * 60)
    corr_results = calcular_correlaciones(df)
    for _, row in corr_results['profit'].iterrows():
        if row['Significativo']:
            print(f'   {row["Variable"]:20s} vs Profit: r={row["Correlacion"]:+.4f} (p={row["P_Value"]:.4f}) ***')
    for _, row in corr_results['acerto'].iterrows():
        if row['Significativo']:
            print(f'   {row["Variable"]:20s} vs Acerto: r={row["Correlacion"]:+.4f} (p={row["P_Value"]:.4f}) ***')
    
    # Test de significancia
    print(f'\n🧪 TEST ESTADÍSTICO (ROI Under)')
    print('-' * 60)
    test = test_significancia_under(df)
    print(f'   n={test["n"]}, mean_profit={test["mean_profit"]:.4f}')
    print(f'   T-test: t={test["t_statistic"]:.4f}, p={test["p_value"]:.4f}')
    if test['significativo']:
        print('   ✅ SIGNIFICATIVO: El ROI positivo NO es por azar (p<0.05)')
    else:
        print('   ⚠️  NO significativo: El ROI podría ser por azar')
    
    # Estrategias
    print(f'\n🎯 ESTRATEGIAS RECOMENDADAS (ordenadas por ROI)')
    print('=' * 80)
    estrategias = calcular_estrategias(df)
    print(f'{"Estrategia":<35} {"N":>6} {"Profit":>10} {"ROI":>8}')
    print('-' * 65)
    for _, row in estrategias.iterrows():
        print(f'{row["Estrategia"]:<35} {row["N"]:>6.0f} {row["Profit"]:>+10.2f}u {row["ROI"]:>+7.2f}%')
    
    print('\n' + '=' * 80)


def guardar_reporte_csv(df: pd.DataFrame, filepath: str):
    """Guarda los resultados del análisis en archivos CSV."""
    base_name = os.path.splitext(filepath)[0]
    output_dir = os.path.dirname(filepath)
    
    # Crear carpeta de reportes si no existe
    report_dir = os.path.join(output_dir, 'reportes_rendimiento')
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_report = os.path.join(report_dir, f'reporte_{timestamp}')
    
    # Guardar cada análisis
    analisis_por_tipo(df).to_csv(f'{base_report}_por_tipo.csv', index=False)
    analisis_por_linea(df).to_csv(f'{base_report}_por_linea.csv', index=False)
    analisis_por_liga(df).to_csv(f'{base_report}_por_liga.csv', index=False)
    analisis_por_cuota(df).to_csv(f'{base_report}_por_cuota.csv', index=False)
    analisis_combinaciones(df).to_csv(f'{base_report}_combinaciones.csv', index=False)
    calcular_estrategias(df).to_csv(f'{base_report}_estrategias.csv', index=False)
    
    print(f'\n📁 Reportes guardados en: {report_dir}/')
    
    return report_dir


def main():
    if len(sys.argv) < 2:
        print('Uso: python analizar_rendimiento_historico.py <archivo_con_resultados.csv>')
        print('\nEjemplo:')
        print('  python analizar_rendimiento_historico.py historical_analysis/2025/marzo/historical_20250307_con_resultados.csv')
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f'Error: No se encuentra el archivo {filepath}')
        sys.exit(1)
    
    # Cargar datos
    print(f'Cargando datos de {filepath}...')
    df = cargar_datos(filepath)
    
    # Imprimir reporte
    imprimir_reporte(df, filepath)
    
    # Guardar CSVs
    guardar_reporte_csv(df, filepath)


if __name__ == '__main__':
    main()
