"""
Análisis de rendimiento por mercado respecto a cada variable.
Rendimiento = Σ(Cuotas de Acertados) - Total de Apuestas
"""

import pandas as pd
import numpy as np

# Cargar datos
df = pd.read_csv('analisis_mercados_20251125_065555.csv')

# Variables a analizar
variables = ['Mejor_Cuota', 'Score_Final', 'Mejor_Casa', 'Diferencia_Cuota_Promedio', 'Volatilidad_Pct', 'Margen_Casa_Pct']

# Obtener mercados únicos
mercados = df['Mercado'].unique()

def calcular_rendimiento(subset):
    """Calcula rendimiento = Σ(cuotas acertadas) - n_apuestas"""
    n = len(subset)
    if n == 0:
        return {'n': 0, 'aciertos': 0, 'rendimiento': 0, 'roi': 0}
    
    acertados = subset[subset['Resultado'] == 'Acertado']
    suma_cuotas = acertados['Mejor_Cuota'].sum()
    rendimiento = suma_cuotas - n
    roi = (rendimiento / n) * 100 if n > 0 else 0
    
    return {
        'n': n,
        'aciertos': len(acertados),
        'tasa': len(acertados) / n * 100,
        'rendimiento': rendimiento,
        'roi': roi
    }

def analizar_variable_numerica(df_mercado, variable, n_bins=4):
    """Analiza rendimiento por rangos de una variable numérica"""
    if df_mercado[variable].isna().all() or len(df_mercado) < 4:
        return None
    
    try:
        n_bins_actual = min(n_bins, len(df_mercado))
        df_mercado = df_mercado.copy()
        df_mercado['rango'] = pd.qcut(df_mercado[variable], q=n_bins_actual, duplicates='drop')
        resultados = []
        for rango in sorted(df_mercado['rango'].unique()):
            subset = df_mercado[df_mercado['rango'] == rango]
            stats = calcular_rendimiento(subset)
            stats['rango'] = str(rango)
            resultados.append(stats)
        return resultados
    except:
        return None

def analizar_variable_categorica(df_mercado, variable):
    """Analiza rendimiento por categoría"""
    resultados = []
    for categoria in df_mercado[variable].unique():
        subset = df_mercado[df_mercado[variable] == categoria]
        stats = calcular_rendimiento(subset)
        stats['categoria'] = categoria
        resultados.append(stats)
    return sorted(resultados, key=lambda x: x['rendimiento'], reverse=True)


print("=" * 100)
print("ANÁLISIS DE RENDIMIENTO POR MERCADO Y VARIABLE")
print("Rendimiento = Σ(Cuotas de Acertados) - Total de Apuestas")
print("=" * 100)

for mercado in mercados:
    df_mercado = df[df['Mercado'] == mercado].copy()
    stats_global = calcular_rendimiento(df_mercado)
    
    print(f"\n{'#' * 100}")
    print(f"## MERCADO: {mercado}")
    print(f"   Total: {stats_global['n']} apuestas | Aciertos: {stats_global['aciertos']} ({stats_global['tasa']:.1f}%)")
    print(f"   Rendimiento: ${stats_global['rendimiento']:+.2f} | ROI: {stats_global['roi']:+.2f}%")
    print(f"{'#' * 100}")
    
    for variable in variables:
        print(f"\n{'─' * 80}")
        print(f"📊 {mercado} vs {variable}")
        print(f"{'─' * 80}")
        
        if variable == 'Mejor_Casa':
            # Variable categórica
            resultados = analizar_variable_categorica(df_mercado, variable)
            if resultados:
                print(f"{'Casa':<20} {'N':>6} {'Aciertos':>10} {'Tasa%':>8} {'Rendimiento':>12} {'ROI%':>10}")
                print("-" * 70)
                for r in resultados:
                    emoji = "🟢" if r['rendimiento'] > 0 else "🔴"
                    print(f"{emoji} {r['categoria']:<18} {r['n']:>6} {r['aciertos']:>10} {r['tasa']:>7.1f}% ${r['rendimiento']:>+10.2f} {r['roi']:>+9.2f}%")
        else:
            # Variable numérica
            resultados = analizar_variable_numerica(df_mercado, variable)
            if resultados:
                print(f"{'Rango':<25} {'N':>6} {'Aciertos':>10} {'Tasa%':>8} {'Rendimiento':>12} {'ROI%':>10}")
                print("-" * 75)
                for r in sorted(resultados, key=lambda x: x['rendimiento'], reverse=True):
                    emoji = "🟢" if r['rendimiento'] > 0 else "🔴"
                    print(f"{emoji} {r['rango']:<23} {r['n']:>6} {r['aciertos']:>10} {r['tasa']:>7.1f}% ${r['rendimiento']:>+10.2f} {r['roi']:>+9.2f}%")
            else:
                print("   ⚠️ No hay suficientes datos para crear rangos")

print("\n" + "=" * 100)
print("FIN DEL ANÁLISIS")
print("=" * 100)
