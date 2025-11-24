import pandas as pd
import numpy as np

# Leer el dataset fusionado
df = pd.read_csv('analisis_mercados_fusionado_20251124_003346.csv')

print("="*80)
print("ESTRATEGIA DE APUESTAS: CÓMO APROVECHAR ESTOS DATOS")
print("="*80)

print("\n📊 DATASET ACTUAL:")
print(f"   Total de oportunidades: {len(df)}")
print(f"   Score Final promedio: {df['Score_Final'].mean():.2f}")
print(f"   Rango de Score: {df['Score_Final'].min():.2f} - {df['Score_Final'].max():.2f}")

# ESTRATEGIA 1: EXPLOTAR MÁRGENES BAJOS EN LIGAS TOP
print("\n\n" + "="*80)
print("ESTRATEGIA 1: APOSTAR EN MÁRGENES BAJOS (Menor 'comisión')")
print("="*80)
print("""
CONCEPTO: Cuando el margen es bajo (<3-4%), la casa tiene menos protección.
Si encuentras valor, tu ventaja es mayor porque pagas menos 'comisión'.

CRITERIOS:
✓ Margen_Casa_Pct < 4%
✓ Ligas top (Champions, EPL, La Liga, Serie A)
✓ Score_Final alto (buena oportunidad según nuestro modelo)
""")

estrategia1 = df[
    (df['Margen_Casa_Pct'] < 4.0) &
    (df['Score_Final'] > df['Score_Final'].quantile(0.75))
].copy()

print(f"\n🎯 OPORTUNIDADES ENCONTRADAS: {len(estrategia1)}")
if len(estrategia1) > 0:
    print("\nTOP 15 MEJORES OPORTUNIDADES (Margen Bajo + Score Alto):")
    top15 = estrategia1.nlargest(15, 'Score_Final')[['Partido', 'Liga', 'Mercado', 'Mejor_Cuota', 'Mejor_Casa', 'Margen_Casa_Pct', 'Score_Final', 'Num_Casas']]
    for idx, row in top15.iterrows():
        print(f"   • {row['Partido'][:35]:35s} | {row['Mercado']:12s} | Cuota: {row['Mejor_Cuota']:.2f} | Margen: {row['Margen_Casa_Pct']:.2f}% | Score: {row['Score_Final']:.2f} | Casa: {row['Mejor_Casa']}")

# ESTRATEGIA 2: EXPLOTAR INEFICIENCIAS EN LIGAS SECUNDARIAS
print("\n\n" + "="*80)
print("ESTRATEGIA 2: APROVECHAR ERRORES EN LIGAS MENOS EFICIENTES")
print("="*80)
print("""
CONCEPTO: En ligas con margen alto (>6%), hay menos analistas profesionales.
Las casas usan márgenes altos porque tienen MENOS INFORMACIÓN.
Si TÚ tienes mejor análisis, puedes encontrar más errores de pricing.

CRITERIOS:
✓ Margen_Casa_Pct > 6% (liga ineficiente)
✓ Score_Final MUY alto (detectamos valor que la casa no ve)
✓ Diferencia_Cuota_Promedio alta (nuestra cuota es significativamente mejor)
""")

estrategia2 = df[
    (df['Margen_Casa_Pct'] > 6.0) &
    (df['Score_Final'] > df['Score_Final'].quantile(0.80)) &
    (df['Diferencia_Cuota_Promedio'] > 0.05)
].copy()

print(f"\n🎯 OPORTUNIDADES ENCONTRADAS: {len(estrategia2)}")
if len(estrategia2) > 0:
    print("\nTOP 15 MEJORES OPORTUNIDADES (Liga Ineficiente + Alto Valor Detectado):")
    top15 = estrategia2.nlargest(15, 'Score_Final')[['Partido', 'Liga', 'Mercado', 'Mejor_Cuota', 'Diferencia_Cuota_Promedio', 'Margen_Casa_Pct', 'Score_Final']]
    for idx, row in top15.iterrows():
        print(f"   • {row['Partido'][:35]:35s} | {row['Liga']:15s} | {row['Mercado']:12s} | Cuota: {row['Mejor_Cuota']:.2f} | Ventaja: +{row['Diferencia_Cuota_Promedio']:.3f} | Score: {row['Score_Final']:.2f}")

# ESTRATEGIA 3: PINNACLE/MARATHONBET COMO REFERENCIA
print("\n\n" + "="*80)
print("ESTRATEGIA 3: USAR CASAS 'SHARP' COMO LÍNEA BASE")
print("="*80)
print("""
CONCEPTO: Pinnacle y Marathonbet tienen los márgenes más bajos (4.8% y 4.5%).
Son casas "sharp" que aceptan apuestas grandes de profesionales.
Sus cuotas reflejan el verdadero precio de mercado.

CRITERIOS:
✓ Nuestra mejor cuota es MEJOR que Pinnacle/Marathonbet
✓ Encontramos valor donde los profesionales no lo vieron
✓ Alta diferencia vs cuota promedio
""")

pinnacle_sharp = df[
    (df['Mejor_Casa'].isin(['pinnacle', 'marathonbet'])) &
    (df['Score_Final'] > df['Score_Final'].quantile(0.70))
].copy()

print(f"\n🎯 OPORTUNIDADES CON CASAS SHARP: {len(pinnacle_sharp)}")
if len(pinnacle_sharp) > 0:
    print("\nTOP 15 MEJORES (Pinnacle/Marathonbet tiene la mejor cuota Y nuestro modelo lo confirma):")
    top15 = pinnacle_sharp.nlargest(15, 'Score_Final')[['Partido', 'Liga', 'Mercado', 'Mejor_Cuota', 'Mejor_Casa', 'Score_Final', 'Margen_Casa_Pct']]
    for idx, row in top15.iterrows():
        print(f"   • {row['Partido'][:35]:35s} | {row['Mercado']:12s} | Cuota: {row['Mejor_Cuota']:.2f} | Score: {row['Score_Final']:.2f} | Casa: {row['Mejor_Casa']}")

# ESTRATEGIA 4: ALTA VOLATILIDAD = EVITAR (menos consenso = más riesgo)
print("\n\n" + "="*80)
print("ESTRATEGIA 4: EVITAR ALTA VOLATILIDAD (Desacuerdo del Mercado)")
print("="*80)
print("""
CONCEPTO: Volatilidad alta = Las casas no están de acuerdo en el precio.
Esto indica incertidumbre. Es más difícil encontrar valor real.

CRITERIOS PARA EVITAR:
✗ Volatilidad_Pct > 3%
✗ Alta dispersión indica evento impredecible
""")

alta_volatilidad = df[df['Volatilidad_Pct'] > 3.0]
print(f"\n⚠️  PARTIDOS CON ALTA VOLATILIDAD (>3%): {len(alta_volatilidad)} - EVITAR")
print(f"    Estos representan el {len(alta_volatilidad)/len(df)*100:.1f}% del dataset")

# ESTRATEGIA 5: MÚLTIPLES CASAS = MAYOR CONFIANZA
print("\n\n" + "="*80)
print("ESTRATEGIA 5: PREFERIR OPORTUNIDADES CON MÚLTIPLE VALIDACIÓN")
print("="*80)
print("""
CONCEPTO: Si 4-5 casas ofrecen cuotas y nuestra mejor es significativamente
mejor que el promedio, hay más confianza en que encontramos valor real.

CRITERIOS:
✓ Num_Casas >= 4
✓ Diferencia_Cuota_Promedio > 0.05 (nuestra cuota es 5%+ mejor)
✓ Score_Final alto
""")

alta_confianza = df[
    (df['Num_Casas'] >= 4) &
    (df['Diferencia_Cuota_Promedio'] > 0.05) &
    (df['Score_Final'] > df['Score_Final'].quantile(0.75))
].copy()

print(f"\n🎯 OPORTUNIDADES DE ALTA CONFIANZA: {len(alta_confianza)}")
if len(alta_confianza) > 0:
    print("\nTOP 15 MEJORES (Múltiple Validación + Alto Score):")
    top15 = alta_confianza.nlargest(15, 'Score_Final')[['Partido', 'Liga', 'Mercado', 'Mejor_Cuota', 'Num_Casas', 'Diferencia_Cuota_Promedio', 'Score_Final', 'Volatilidad_Pct']]
    for idx, row in top15.iterrows():
        print(f"   • {row['Partido'][:35]:35s} | {row['Mercado']:12s} | Cuota: {row['Mejor_Cuota']:.2f} | Casas: {row['Num_Casas']} | Ventaja: +{row['Diferencia_Cuota_Promedio']:.3f} | Score: {row['Score_Final']:.2f}")

# RESUMEN FINAL Y RECOMENDACIONES
print("\n\n" + "="*80)
print("RESUMEN: ESTRATEGIA ÓPTIMA DE APUESTAS")
print("="*80)
print("""
🎯 ORDEN DE PRIORIDAD (de mejor a peor):

1. ESTRATEGIA 5 - MÁXIMA CONFIANZA ⭐⭐⭐⭐⭐
   • 4+ casas compitiendo
   • Ventaja de cuota >5%
   • Score Final alto
   • Volatilidad baja
   → APOSTAR CON CONFIANZA

2. ESTRATEGIA 1 - LIGAS TOP CON MARGEN BAJO ⭐⭐⭐⭐
   • Champions, EPL, La Liga
   • Margen <4%
   • Score alto
   → BUENA EFICIENCIA DE MERCADO, SI HAY VALOR ES REAL

3. ESTRATEGIA 3 - VALIDACIÓN SHARP ⭐⭐⭐⭐
   • Pinnacle/Marathonbet tienen mejor cuota
   • Nuestro modelo lo confirma
   → PROFESIONALES TAMBIÉN LO VIERON

4. ESTRATEGIA 2 - LIGAS SECUNDARIAS ⭐⭐⭐
   • Margen >6%
   • Score MUY alto (>percentil 80)
   • Ventaja de cuota significativa
   → MÁS RIESGO, PERO MAYOR POTENCIAL SI ACIERTAS

🚫 EVITAR:
   • Volatilidad >3% (desacuerdo del mercado)
   • Score Final bajo (<0.5)
   • Solo 2 casas ofreciendo (poca validación)
   • Margen >7% sin análisis adicional

💰 GESTIÓN DE BANKROLL:
   • Estrategia 5: Apostar 2-3% del bankroll
   • Estrategia 1/3: Apostar 1-2% del bankroll
   • Estrategia 2: Apostar 0.5-1% del bankroll (mayor riesgo)

📊 TRACKING:
   • Registra todas las apuestas con su Score_Final
   • Analiza qué rangos de Score son más rentables
   • Ajusta umbrales según resultados reales
""")

# CREAR CSV CON LAS MEJORES OPORTUNIDADES
print("\n\n💾 Generando CSV con las mejores oportunidades...")

# Combinar todas las estrategias y marcar con prioridad
estrategia1['Estrategia'] = 'E1_Margen_Bajo'
estrategia1['Prioridad'] = 4

estrategia2['Estrategia'] = 'E2_Liga_Ineficiente'
estrategia2['Prioridad'] = 3

pinnacle_sharp['Estrategia'] = 'E3_Sharp_Validation'
pinnacle_sharp['Prioridad'] = 4

alta_confianza['Estrategia'] = 'E5_Alta_Confianza'
alta_confianza['Prioridad'] = 5

mejores_ops = pd.concat([estrategia1, estrategia2, pinnacle_sharp, alta_confianza]).drop_duplicates()
mejores_ops = mejores_ops.sort_values(['Prioridad', 'Score_Final'], ascending=[False, False])

output_file = 'mejores_oportunidades_apuestas.csv'
mejores_ops.to_csv(output_file, index=False, encoding='utf-8')

print(f"✅ Archivo creado: {output_file}")
print(f"   Total de oportunidades priorizadas: {len(mejores_ops)}")
print(f"   Prioridad 5 (Máxima confianza): {len(mejores_ops[mejores_ops['Prioridad']==5])}")
print(f"   Prioridad 4 (Alta confianza): {len(mejores_ops[mejores_ops['Prioridad']==4])}")
print(f"   Prioridad 3 (Media confianza): {len(mejores_ops[mejores_ops['Prioridad']==3])}")

print("\n✅ Análisis de estrategias completado")
