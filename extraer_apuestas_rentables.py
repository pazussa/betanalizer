"""
Extrae las apuestas que cumplieron criterios de buen rendimiento
basado en el análisis realizado.
"""

import pandas as pd

# Cargar datos
df = pd.read_csv('analisis_mercados_20251125_065555.csv')

print("=" * 80)
print("EXTRACCIÓN DE APUESTAS RENTABLES")
print("=" * 80)

# Definir filtros por mercado según análisis

# 1. UNDER 3.5 - ROI +80%
filtro_under35 = (
    (df['Mercado'] == 'Under 3.5') &
    (df['Mejor_Cuota'] > 1.70) &
    (df['Diferencia_Cuota_Promedio'] > 0.015) &
    (df['Volatilidad_Pct'] > 0.5)
)

# 2. X2 - ROI +97% en su mejor rango
filtro_x2 = (
    (df['Mercado'] == 'X2') &
    (df['Score_Final'] >= 0.10) & (df['Score_Final'] <= 0.55) &
    (df['Diferencia_Cuota_Promedio'] >= 0.01) & (df['Diferencia_Cuota_Promedio'] <= 0.04) &
    (df['Margen_Casa_Pct'] < 3.5)
)

# 3. OVER 2.5 - ROI +100% en su mejor rango
filtro_over25 = (
    (df['Mercado'] == 'Over 2.5') &
    (df['Score_Final'] < 0.65) &
    (df['Diferencia_Cuota_Promedio'] > 0.035) &
    (df['Volatilidad_Pct'] >= 0.71) & (df['Volatilidad_Pct'] <= 1.5)
)

# 4. UNDER 2.5 - ROI +54% en su mejor rango
filtro_under25 = (
    (df['Mercado'] == 'Under 2.5') &
    (df['Score_Final'] > 0.65) &
    (df['Mejor_Cuota'] >= 1.93) & (df['Mejor_Cuota'] <= 2.06) &
    (df['Diferencia_Cuota_Promedio'] > 0.033) &
    (df['Volatilidad_Pct'] >= 0.49) & (df['Volatilidad_Pct'] <= 1.69) &
    (df['Margen_Casa_Pct'] < 3.5)
)

# Combinar todos los filtros
filtro_total = filtro_under35 | filtro_x2 | filtro_over25 | filtro_under25

# Extraer apuestas rentables
df_rentables = df[filtro_total].copy()

# Agregar columna de estrategia
def asignar_estrategia(row):
    if row['Mercado'] == 'Under 3.5':
        return 'Under 3.5 (Prioridad ALTA)'
    elif row['Mercado'] == 'X2':
        return 'X2 (Prioridad ALTA)'
    elif row['Mercado'] == 'Over 2.5':
        return 'Over 2.5 (Prioridad MEDIA)'
    elif row['Mercado'] == 'Under 2.5':
        return 'Under 2.5 (Prioridad BAJA)'
    return 'Otro'

df_rentables['Estrategia'] = df_rentables.apply(asignar_estrategia, axis=1)

# Calcular rendimiento
def calcular_rendimiento(subset):
    n = len(subset)
    acertados = subset[subset['Resultado'] == 'Acertado']
    suma_cuotas = acertados['Mejor_Cuota'].sum()
    rendimiento = suma_cuotas - n
    roi = (rendimiento / n) * 100 if n > 0 else 0
    return n, len(acertados), rendimiento, roi

# Mostrar resumen por estrategia
print(f"\n📊 RESUMEN DE APUESTAS EXTRAÍDAS")
print("-" * 80)

total_apuestas = 0
total_rendimiento = 0

for estrategia in df_rentables['Estrategia'].unique():
    subset = df_rentables[df_rentables['Estrategia'] == estrategia]
    n, aciertos, rend, roi = calcular_rendimiento(subset)
    total_apuestas += n
    total_rendimiento += rend
    
    emoji = "🟢" if rend > 0 else "🔴"
    print(f"{emoji} {estrategia}")
    print(f"   Apuestas: {n} | Aciertos: {aciertos} ({aciertos/n*100:.1f}%)")
    print(f"   Rendimiento: ${rend:+.2f} | ROI: {roi:+.2f}%")
    print()

print("-" * 80)
roi_total = (total_rendimiento / total_apuestas) * 100 if total_apuestas > 0 else 0
print(f"📈 TOTAL: {total_apuestas} apuestas | Rendimiento: ${total_rendimiento:+.2f} | ROI: {roi_total:+.2f}%")

# Comparar con apostar todo
n_total, aciertos_total, rend_total, roi_total_all = calcular_rendimiento(df)
print(f"\n📉 Comparación con TODAS las apuestas ({n_total}):")
print(f"   Rendimiento: ${rend_total:+.2f} | ROI: {roi_total_all:+.2f}%")

mejora = total_rendimiento - (rend_total * total_apuestas / n_total)
print(f"\n✨ MEJORA: ${mejora:+.2f} respecto a apostar sin filtro")

# Guardar CSV
output_file = 'apuestas_rentables_filtradas.csv'
df_rentables.to_csv(output_file, index=False)
print(f"\n💾 Dataset guardado en: {output_file}")

# Mostrar detalle
print("\n" + "=" * 80)
print("DETALLE DE APUESTAS RENTABLES")
print("=" * 80)

cols_mostrar = ['Partido', 'Liga', 'Mercado', 'Mejor_Cuota', 'Mejor_Casa', 
                'Score_Final', 'Diferencia_Cuota_Promedio', 'Volatilidad_Pct', 
                'Margen_Casa_Pct', 'Resultado', 'Estrategia']

for _, row in df_rentables[cols_mostrar].iterrows():
    emoji = "✅" if row['Resultado'] == 'Acertado' else "❌"
    print(f"\n{emoji} {row['Partido']}")
    print(f"   Liga: {row['Liga']} | Mercado: {row['Mercado']}")
    print(f"   Cuota: {row['Mejor_Cuota']} ({row['Mejor_Casa']})")
    print(f"   Score: {row['Score_Final']:.3f} | Diff: {row['Diferencia_Cuota_Promedio']:.4f}")
    print(f"   Vol: {row['Volatilidad_Pct']:.2f}% | Margen: {row['Margen_Casa_Pct']:.2f}%")
    print(f"   Estrategia: {row['Estrategia']}")
