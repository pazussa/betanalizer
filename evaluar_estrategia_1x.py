#!/usr/bin/env python3
"""
Evaluación de estrategia específica para apuestas 1X
"""

import pandas as pd
import numpy as np

# Cargar datos
df = pd.read_csv('data/historico_completo.csv')

# Filtrar solo resultados verificados
df = df[df['Resultado'].isin(['Acertado', 'Fallido'])].copy()
df['Acierto'] = (df['Resultado'] == 'Acertado').astype(int)
df['Rendimiento'] = np.where(df['Acierto'] == 1, df['Mejor_Cuota'] - 1, -1)

print("=" * 70)
print("   EVALUACIÓN DE ESTRATEGIA: APUESTAS 1X")
print("=" * 70)

# Ver distribución de mercados
print("\n--- Mercados disponibles en Doble Chance ---")
df_dc = df[df['Tipo_Mercado'] == 'Doble Chance']
print(df_dc['Mercado'].value_counts())

# ================================================================
# FILTROS OBLIGATORIOS
# ================================================================
print("\n" + "=" * 70)
print("   APLICANDO FILTROS OBLIGATORIOS")
print("=" * 70)

# Dataset inicial
print(f"\nTotal registros verificados: {len(df)}")

# 1. Solo apuestas 1X
df_1x = df[df['Mercado'] == '1X'].copy()
print(f"1. Apuestas 1X: {len(df_1x)} registros")

# 2. Cuota entre 1.6 y 1.8
df_cuota = df_1x[(df_1x['Mejor_Cuota'] >= 1.6) & (df_1x['Mejor_Cuota'] <= 1.8)].copy()
print(f"2. Cuota 1.6-1.8: {len(df_cuota)} registros")

# 3. Volatilidad menor a 2.5%
df_vol = df_cuota[df_cuota['Volatilidad_Pct'] < 2.5].copy()
print(f"3. Volatilidad < 2.5%: {len(df_vol)} registros")

# 4. Número de casas > 2
df_casas = df_vol[df_vol['Num_Casas'] > 2].copy()
print(f"4. Num_Casas > 2: {len(df_casas)} registros")

df_obligatorio = df_casas.copy()

# ================================================================
# RESULTADOS CON FILTROS OBLIGATORIOS
# ================================================================
print("\n" + "=" * 70)
print("   RESULTADOS: SOLO FILTROS OBLIGATORIOS")
print("=" * 70)

if len(df_obligatorio) > 0:
    n = len(df_obligatorio)
    aciertos = df_obligatorio['Acierto'].sum()
    pct_aciertos = aciertos / n * 100
    rend_total = df_obligatorio['Rendimiento'].sum()
    roi = rend_total / n * 100
    
    print(f"\n📊 N apuestas: {n}")
    print(f"✅ Aciertos: {aciertos} ({pct_aciertos:.1f}%)")
    print(f"💰 Rendimiento total: {rend_total:.2f}€")
    print(f"📈 ROI: {roi:.2f}%")
    
    # Detalle de apuestas
    print("\n--- Detalle de apuestas (filtros obligatorios) ---")
    cols_mostrar = ['Partido', 'Liga', 'Mercado', 'Mejor_Cuota', 'Volatilidad_Pct', 
                    'Num_Casas', 'Margen_Casa_Pct', 'Resultado', 'Rendimiento']
    print(df_obligatorio[cols_mostrar].to_string())
else:
    print("\n⚠️ No hay apuestas que cumplan todos los filtros obligatorios")

# ================================================================
# BONUS: APLICAR PUNTUACIÓN
# ================================================================
print("\n" + "=" * 70)
print("   ANÁLISIS CON SISTEMA DE PUNTOS BONUS")
print("=" * 70)

# Ligas preferidas
ligas_bonus = ['Brasileirão', 'Brasileirao', 'Bundesliga 2', 'Swiss Superleague', 
               'Eredivisie', 'Superliga', 'Primeira Liga']

if len(df_obligatorio) > 0:
    df_bonus = df_obligatorio.copy()
    df_bonus['Puntos_Bonus'] = 0
    
    # +1 punto por liga preferida
    for liga in ligas_bonus:
        mask = df_bonus['Liga'].str.contains(liga, case=False, na=False)
        df_bonus.loc[mask, 'Puntos_Bonus'] += 1
    
    # +1 punto por margen casa 3-4%
    mask_margen = (df_bonus['Margen_Casa_Pct'] >= 3) & (df_bonus['Margen_Casa_Pct'] <= 4)
    df_bonus.loc[mask_margen, 'Puntos_Bonus'] += 1
    
    # +1 punto por volatilidad < 1%
    mask_vol = df_bonus['Volatilidad_Pct'] < 1
    df_bonus.loc[mask_vol, 'Puntos_Bonus'] += 1
    
    print("\n--- Distribución de puntos bonus ---")
    print(df_bonus['Puntos_Bonus'].value_counts().sort_index())
    
    print("\n--- Ligas en el subset ---")
    print(df_bonus['Liga'].value_counts())
    
    # Análisis por puntos
    print("\n--- Rendimiento por puntos bonus ---")
    for pts in sorted(df_bonus['Puntos_Bonus'].unique()):
        subset = df_bonus[df_bonus['Puntos_Bonus'] >= pts]
        if len(subset) > 0:
            n = len(subset)
            aciertos = subset['Acierto'].sum()
            pct = aciertos / n * 100
            rend = subset['Rendimiento'].sum()
            roi = rend / n * 100
            print(f"Puntos >= {pts}: N={n}, Aciertos={pct:.1f}%, ROI={roi:.2f}%, Rend={rend:.2f}€")
    
    # Mostrar las mejores apuestas (con más puntos)
    print("\n--- Apuestas ordenadas por puntos bonus ---")
    df_top = df_bonus.sort_values('Puntos_Bonus', ascending=False)
    cols_mostrar = ['Partido', 'Liga', 'Mejor_Cuota', 'Volatilidad_Pct', 
                    'Margen_Casa_Pct', 'Puntos_Bonus', 'Resultado', 'Rendimiento']
    print(df_top[cols_mostrar].to_string())
else:
    print("\n⚠️ No hay datos para analizar con sistema de puntos")

# ================================================================
# COMPARACIÓN: Esta estrategia vs mercado general
# ================================================================
print("\n" + "=" * 70)
print("   COMPARACIÓN CON MERCADO GENERAL")
print("=" * 70)

# Todas las apuestas 1X
df_all_1x = df[df['Mercado'] == '1X'].copy()
if len(df_all_1x) > 0:
    n_all = len(df_all_1x)
    roi_all = df_all_1x['Rendimiento'].sum() / n_all * 100
    aciertos_all = df_all_1x['Acierto'].mean() * 100
    print(f"\nTodas las apuestas 1X: N={n_all}, Aciertos={aciertos_all:.1f}%, ROI={roi_all:.2f}%")

# Todo Doble Chance
df_dc = df[df['Tipo_Mercado'] == 'Doble Chance'].copy()
if len(df_dc) > 0:
    n_dc = len(df_dc)
    roi_dc = df_dc['Rendimiento'].sum() / n_dc * 100
    aciertos_dc = df_dc['Acierto'].mean() * 100
    print(f"Todo Doble Chance: N={n_dc}, Aciertos={aciertos_dc:.1f}%, ROI={roi_dc:.2f}%")

# Todo el dataset
n_total = len(df)
roi_total = df['Rendimiento'].sum() / n_total * 100
aciertos_total = df['Acierto'].mean() * 100
print(f"Todo el dataset: N={n_total}, Aciertos={aciertos_total:.1f}%, ROI={roi_total:.2f}%")

# Estrategia específica
if len(df_obligatorio) > 0:
    n_est = len(df_obligatorio)
    roi_est = df_obligatorio['Rendimiento'].sum() / n_est * 100
    aciertos_est = df_obligatorio['Acierto'].mean() * 100
    print(f"\n🎯 Estrategia 1X específica: N={n_est}, Aciertos={aciertos_est:.1f}%, ROI={roi_est:.2f}%")
    
    mejora_vs_1x = roi_est - roi_all if len(df_all_1x) > 0 else 0
    mejora_vs_dc = roi_est - roi_dc if len(df_dc) > 0 else 0
    mejora_vs_total = roi_est - roi_total
    
    print(f"\n--- Comparación ---")
    print(f"vs Todas 1X: {'✅ MEJORA' if mejora_vs_1x > 0 else '❌ EMPEORA'} {mejora_vs_1x:+.2f}%")
    print(f"vs Doble Chance: {'✅ MEJORA' if mejora_vs_dc > 0 else '❌ EMPEORA'} {mejora_vs_dc:+.2f}%")
    print(f"vs Todo dataset: {'✅ MEJORA' if mejora_vs_total > 0 else '❌ EMPEORA'} {mejora_vs_total:+.2f}%")

# ================================================================
# ANÁLISIS DE SENSIBILIDAD: ¿Qué pasa si relajamos filtros?
# ================================================================
print("\n" + "=" * 70)
print("   ANÁLISIS DE SENSIBILIDAD")
print("=" * 70)

print("\n--- Variando rango de cuota ---")
for cuota_min, cuota_max in [(1.5, 1.7), (1.6, 1.8), (1.7, 1.9), (1.5, 1.9), (1.4, 2.0)]:
    subset = df_1x[(df_1x['Mejor_Cuota'] >= cuota_min) & 
                   (df_1x['Mejor_Cuota'] <= cuota_max) &
                   (df_1x['Volatilidad_Pct'] < 2.5) &
                   (df_1x['Num_Casas'] > 2)]
    if len(subset) > 0:
        n = len(subset)
        roi = subset['Rendimiento'].sum() / n * 100
        aciertos = subset['Acierto'].mean() * 100
        print(f"Cuota {cuota_min}-{cuota_max}: N={n}, Aciertos={aciertos:.1f}%, ROI={roi:.2f}%")

print("\n--- Variando volatilidad máxima ---")
for vol_max in [1.0, 1.5, 2.0, 2.5, 3.0]:
    subset = df_1x[(df_1x['Mejor_Cuota'] >= 1.6) & 
                   (df_1x['Mejor_Cuota'] <= 1.8) &
                   (df_1x['Volatilidad_Pct'] < vol_max) &
                   (df_1x['Num_Casas'] > 2)]
    if len(subset) > 0:
        n = len(subset)
        roi = subset['Rendimiento'].sum() / n * 100
        aciertos = subset['Acierto'].mean() * 100
        print(f"Volatilidad < {vol_max}%: N={n}, Aciertos={aciertos:.1f}%, ROI={roi:.2f}%")

print("\n--- Variando número mínimo de casas ---")
for casas_min in [1, 2, 3, 4, 5]:
    subset = df_1x[(df_1x['Mejor_Cuota'] >= 1.6) & 
                   (df_1x['Mejor_Cuota'] <= 1.8) &
                   (df_1x['Volatilidad_Pct'] < 2.5) &
                   (df_1x['Num_Casas'] > casas_min)]
    if len(subset) > 0:
        n = len(subset)
        roi = subset['Rendimiento'].sum() / n * 100
        aciertos = subset['Acierto'].mean() * 100
        print(f"Num_Casas > {casas_min}: N={n}, Aciertos={aciertos:.1f}%, ROI={roi:.2f}%")
