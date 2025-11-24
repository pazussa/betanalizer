import pandas as pd
import numpy as np

# Leer el dataset fusionado
df = pd.read_csv('analisis_mercados_fusionado_20251124_003346.csv')

print("="*80)
print("ANÁLISIS: ¿POR QUÉ LAS CASAS TIENEN MAYOR MARGEN EN UNOS PARTIDOS?")
print("="*80)

# 1. ANÁLISIS POR LIGA
print("\n1. MARGEN PROMEDIO POR LIGA (ordenado de mayor a menor margen)")
print("-"*80)
margen_liga = df.groupby('Liga')['Margen_Casa_Pct'].agg(['mean', 'std', 'count']).round(2)
margen_liga = margen_liga.sort_values('mean', ascending=False)
margen_liga.columns = ['Margen_Promedio_%', 'Desv_Std', 'Num_Mercados']
print(margen_liga.head(15))

print("\n📊 INTERPRETACIÓN:")
print("   • Ligas menos conocidas/populares → Mayor margen (menor liquidez, más riesgo)")
print("   • Ligas top europeas → Menor margen (alta liquidez, competencia entre casas)")

# 2. ANÁLISIS POR TIPO DE MERCADO
print("\n\n2. MARGEN PROMEDIO POR TIPO DE MERCADO")
print("-"*80)
margen_mercado = df.groupby('Tipo_Mercado')['Margen_Casa_Pct'].agg(['mean', 'std', 'count']).round(2)
margen_mercado = margen_mercado.sort_values('mean', ascending=False)
margen_mercado.columns = ['Margen_Promedio_%', 'Desv_Std', 'Num_Mercados']
print(margen_mercado)

print("\n📊 INTERPRETACIÓN:")
print("   • Doble Chance suele tener mayor margen (menos información pública, más difícil modelar)")
print("   • Over/Under puede tener menor margen (estadísticas más claras, más predecible)")

# 3. ANÁLISIS POR CASA DE APUESTAS
print("\n\n3. MARGEN PROMEDIO POR CASA DE APUESTAS")
print("-"*80)
margen_casa = df.groupby('Mejor_Casa')['Margen_Casa_Pct'].agg(['mean', 'std', 'count']).round(2)
margen_casa = margen_casa.sort_values('mean', ascending=False)
margen_casa.columns = ['Margen_Promedio_%', 'Desv_Std', 'Num_Veces_Mejor']
print(margen_casa)

print("\n📊 INTERPRETACIÓN:")
print("   • Pinnacle históricamente tiene márgenes más bajos (modelo sharp, alta liquidez)")
print("   • Casas retail suelen tener márgenes más altos (costos operativos, perfil recreativo)")

# 4. ANÁLISIS POR NÚMERO DE CASAS DISPONIBLES
print("\n\n4. RELACIÓN ENTRE COMPETENCIA (Num_Casas) Y MARGEN")
print("-"*80)
margen_competencia = df.groupby('Num_Casas')['Margen_Casa_Pct'].agg(['mean', 'std', 'count']).round(2)
margen_competencia = margen_competencia.sort_values('mean', ascending=False)
margen_competencia.columns = ['Margen_Promedio_%', 'Desv_Std', 'Num_Mercados']
print(margen_competencia)

print("\n📊 INTERPRETACIÓN:")
print("   • Más casas = Mayor competencia = Menor margen (presión para ofrecer mejores cuotas)")
print("   • Pocas casas = Menos competencia = Mayor margen (menos presión de mercado)")

# 5. ANÁLISIS POR VOLATILIDAD
print("\n\n5. RELACIÓN ENTRE VOLATILIDAD Y MARGEN")
print("-"*80)
# Crear bins de volatilidad
df['Volatilidad_Bin'] = pd.cut(df['Volatilidad_Pct'], bins=[0, 1, 2, 3, 100], labels=['Baja (0-1%)', 'Media (1-2%)', 'Alta (2-3%)', 'Muy Alta (>3%)'])
margen_volatilidad = df.groupby('Volatilidad_Bin')['Margen_Casa_Pct'].agg(['mean', 'std', 'count']).round(2)
margen_volatilidad.columns = ['Margen_Promedio_%', 'Desv_Std', 'Num_Mercados']
print(margen_volatilidad)

print("\n📊 INTERPRETACIÓN:")
print("   • Alta volatilidad = Mayor incertidumbre = Mayor margen (protección contra riesgo)")
print("   • Baja volatilidad = Consenso del mercado = Menor margen (menos riesgo)")

# 6. CASOS EXTREMOS: MAYOR Y MENOR MARGEN
print("\n\n6. PARTIDOS CON MAYOR Y MENOR MARGEN")
print("-"*80)
print("\n🔴 TOP 10 PARTIDOS CON MAYOR MARGEN (Mayor protección de las casas):")
top_margen = df.nlargest(10, 'Margen_Casa_Pct')[['Partido', 'Liga', 'Tipo_Mercado', 'Margen_Casa_Pct', 'Num_Casas', 'Volatilidad_Pct']]
for idx, row in top_margen.iterrows():
    print(f"   • {row['Partido'][:40]:40s} | Liga: {row['Liga']:20s} | Margen: {row['Margen_Casa_Pct']:.2f}% | Casas: {row['Num_Casas']} | Vol: {row['Volatilidad_Pct']:.2f}%")

print("\n🟢 TOP 10 PARTIDOS CON MENOR MARGEN (Mayor confianza/competencia):")
bottom_margen = df.nsmallest(10, 'Margen_Casa_Pct')[['Partido', 'Liga', 'Tipo_Mercado', 'Margen_Casa_Pct', 'Num_Casas', 'Volatilidad_Pct']]
for idx, row in bottom_margen.iterrows():
    print(f"   • {row['Partido'][:40]:40s} | Liga: {row['Liga']:20s} | Margen: {row['Margen_Casa_Pct']:.2f}% | Casas: {row['Num_Casas']} | Vol: {row['Volatilidad_Pct']:.2f}%")

# 7. RESUMEN DE FACTORES
print("\n\n" + "="*80)
print("RESUMEN: FACTORES QUE AUMENTAN EL MARGEN DE LAS CASAS")
print("="*80)
print("""
1. 🌍 POPULARIDAD DE LA LIGA:
   - Ligas menos conocidas → Mayor margen (menos información, menor liquidez)
   - Ligas secundarias → Mayor riesgo de información asimétrica

2. 📊 TIPO DE MERCADO:
   - Mercados complejos (Doble Chance) → Mayor margen
   - Mercados estadísticos (Totales) → Potencialmente menor margen

3. 🏢 COMPETENCIA:
   - Pocas casas ofreciendo cuotas → Mayor margen
   - Muchas casas compitiendo → Menor margen (presión de mercado)

4. 📈 VOLATILIDAD/INCERTIDUMBRE:
   - Alta dispersión de cuotas → Mayor margen (desacuerdo del mercado)
   - Consenso de cuotas → Menor margen (confianza en predicción)

5. ⚽ CARACTERÍSTICAS DEL PARTIDO:
   - Partidos impredecibles → Mayor margen
   - Partidos con favoritos claros → Potencialmente menor margen

6. 💼 MODELO DE NEGOCIO:
   - Casas "sharp" (Pinnacle) → Margen bajo, alto volumen
   - Casas "retail" → Margen alto, clientes recreativos

CONCLUSIÓN: Las casas aumentan el margen cuando perciben MAYOR RIESGO o tienen
MENOS COMPETENCIA. El margen es su "seguro" contra la incertidumbre.
""")

print("\n✅ Análisis completado")
