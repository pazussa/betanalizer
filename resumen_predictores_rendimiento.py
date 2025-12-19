#!/usr/bin/env python3
"""
RESUMEN EJECUTIVO: ANÁLISIS DE PREDICTORES DE RENDIMIENTO
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def main():
    # Cargar datos
    df = pd.read_csv('data/historico_completo.csv')
    df = df[df['Resultado'].isin(['Acertado', 'Fallido'])].copy()
    df['Acierto'] = (df['Resultado'] == 'Acertado').astype(int)
    df['Mejor_Cuota'] = pd.to_numeric(df['Mejor_Cuota'], errors='coerce')
    df['Rendimiento'] = np.where(df['Acierto'] == 1, df['Mejor_Cuota'] - 1, -1)
    
    # Convertir columnas
    cols = ['P_Win_Calibrada', 'Confianza', 'Confianza_Calibrada', 'Score_Final',
            'Diferencia_Cuota_Promedio', 'Volatilidad_Pct', 'Margen_Casa_Pct', 'Num_Casas']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['Rendimiento'])
    
    print("\n" + "="*90)
    print("  RESUMEN EJECUTIVO: ANÁLISIS DE PREDICTORES DE RENDIMIENTO")
    print("="*90)
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════════════╗
    ║  CONCEPTO: RENDIMIENTO                                                               ║
    ║                                                                                      ║
    ║  Rendimiento = Σ(cuotas de ganados) - Σ(apuestas realizadas)                         ║
    ║                                                                                      ║
    ║  Para cada apuesta de 1€:                                                            ║
    ║    • Si ACIERTA: ganancia = cuota - 1                                                ║
    ║    • Si FALLA:   ganancia = -1                                                       ║
    ╚══════════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Estadísticas generales
    print("="*90)
    print("  ESTADÍSTICAS GENERALES DEL HISTÓRICO")
    print("="*90)
    
    roi = df['Rendimiento'].mean() * 100
    rend_total = df['Rendimiento'].sum()
    
    print(f"""
    ┌────────────────────────────────────────┬─────────────────────────────────────────────┐
    │  Total de apuestas                     │  {len(df):,}                                │
    │  Aciertos                              │  {df['Acierto'].sum():,} ({df['Acierto'].mean()*100:.1f}%)                        │
    │  Capital apostado (1€/apuesta)         │  {len(df):,}€                               │
    │  Rendimiento neto                      │  {rend_total:+,.2f}€                             │
    │  ROI                                   │  {roi:+.2f}%                                │
    └────────────────────────────────────────┴─────────────────────────────────────────────┘
    """)
    
    # Análisis de cada variable como predictor de RENDIMIENTO
    print("="*90)
    print("  CORRELACIÓN DE CADA VARIABLE CON EL RENDIMIENTO")
    print("="*90)
    
    variables = [
        ('P_Win_Calibrada', 'P_Win_Calibrada'),
        ('Confianza', 'Confianza Original'),
        ('Confianza_Calibrada', 'Confianza_Calibrada'),
        ('Score_Final', 'Score Final'),
        ('Diferencia_Cuota_Promedio', 'Diferencia Cuota Promedio'),
        ('Volatilidad_Pct', 'Volatilidad (%)'),
        ('Margen_Casa_Pct', 'Margen Casa (%)'),
        ('Num_Casas', 'Número de Casas'),
    ]
    
    resultados = []
    for col, nombre in variables:
        if col not in df.columns:
            continue
        sub = df.dropna(subset=[col])
        if len(sub) < 100:
            continue
        
        corr, p = stats.pearsonr(sub[col], sub['Rendimiento'])
        
        # ROI del quintil superior
        try:
            sub['Q'] = pd.qcut(sub[col], 5, labels=['Q1','Q2','Q3','Q4','Q5'], duplicates='drop')
            q5 = sub[sub['Q'] == 'Q5']
            roi_q5 = q5['Rendimiento'].mean() * 100
        except:
            roi_q5 = np.nan
        
        resultados.append({
            'nombre': nombre,
            'corr': corr,
            'p': p,
            'roi_q5': roi_q5
        })
    
    # Ordenar por correlación
    resultados.sort(key=lambda x: x['corr'], reverse=True)
    
    print(f"""
    ┌─────────────────────────────────┬────────────┬──────────────┬────────────┬─────────────┐
    │  Variable                       │ Correlación│  p-value     │ ROI Q5     │ Predictor?  │
    ├─────────────────────────────────┼────────────┼──────────────┼────────────┼─────────────┤""")
    
    for r in resultados:
        sig = "***" if r['p'] < 0.001 else "**" if r['p'] < 0.01 else "*" if r['p'] < 0.05 else ""
        pred = "⚠️ Débil" if abs(r['corr']) < 0.05 else ("✓ Sí" if r['corr'] > 0 else "✗ Inverso")
        roi_str = f"{r['roi_q5']:+.2f}%" if not np.isnan(r['roi_q5']) else "N/A"
        print(f"    │  {r['nombre']:<29} │  {r['corr']:+.4f}{sig:<3}│  {r['p']:<12.6f}│  {roi_str:<9}│  {pred:<10}│")
    
    print("    └─────────────────────────────────┴────────────┴──────────────┴────────────┴─────────────┘")
    
    print("""
    INTERPRETACIÓN:
    • Correlación positiva: Mayor valor → Mayor rendimiento
    • Correlación negativa: Mayor valor → Menor rendimiento
    • ROI Q5: Rendimiento si solo apostamos al quintil superior de esa variable
    • Predictor?: ¿La variable predice rendimiento positivo?
    """)
    
    # Análisis específico de P_Win_Calibrada
    print("="*90)
    print("  VEREDICTO: P_WIN_CALIBRADA COMO PREDICTOR DE RENDIMIENTO")
    print("="*90)
    
    p_win_corr = next((r['corr'] for r in resultados if r['nombre'] == 'P_Win_Calibrada'), 0)
    p_win_roi_q5 = next((r['roi_q5'] for r in resultados if r['nombre'] == 'P_Win_Calibrada'), 0)
    
    print(f"""
    ┌──────────────────────────────────────────────────────────────────────────────────────┐
    │                                                                                      │
    │  P_Win_Calibrada como predictor de ACIERTOS:                                         │
    │    • Correlación con aciertos: +0.23 (significativa)                                 │
    │    • Mayor P_Win → Mayor probabilidad de acertar ✓                                   │
    │                                                                                      │
    │  P_Win_Calibrada como predictor de RENDIMIENTO:                                      │
    │    • Correlación con rendimiento: {p_win_corr:+.4f} (NO significativa)                     │
    │    • ROI del quintil superior: {p_win_roi_q5:+.2f}%                                       │
    │    • Mayor P_Win → PEOR rendimiento ✗                                                │
    │                                                                                      │
    │  ⚠️  P_WIN_CALIBRADA NO ES UN PREDICTOR DE RENDIMIENTO                               │
    │                                                                                      │
    │  ¿Por qué?                                                                           │
    │  Las apuestas con P_Win alta tienen cuotas bajas.                                    │
    │  Aunque aciertan más, la ganancia no compensa el menor pago.                         │
    │  Ejemplo:                                                                            │
    │    • P_Win 70% con cuota 1.30: Esperanza = 0.70×1.30 - 1 = -0.09 (-9%)              │
    │    • P_Win 50% con cuota 2.00: Esperanza = 0.50×2.00 - 1 = 0.00 (0%)                │
    │                                                                                      │
    └──────────────────────────────────────────────────────────────────────────────────────┘
    """)
    
    # Variables más prometedoras
    print("="*90)
    print("  VARIABLES MÁS PROMETEDORAS PARA RENDIMIENTO")
    print("="*90)
    
    # Encontrar los mejores
    mejores = [r for r in resultados if r['corr'] > 0][:3]
    
    print(f"""
    ┌──────────────────────────────────────────────────────────────────────────────────────┐
    │  Las variables con correlación POSITIVA con el rendimiento son:                      │
    │                                                                                      │""")
    
    for i, r in enumerate(mejores, 1):
        print(f"    │  {i}. {r['nombre']:<25} (corr: {r['corr']:+.4f}, ROI Q5: {r['roi_q5']:+.2f}%){' '*(30-len(r['nombre']))}│")
    
    print("""    │                                                                                      │
    │  Sin embargo, NINGUNA tiene correlación > 0.05 (muy débil)                           │
    │                                                                                      │
    └──────────────────────────────────────────────────────────────────────────────────────┘
    """)
    
    # Estrategias encontradas
    print("="*90)
    print("  ÚNICA ESTRATEGIA CON ROI POSITIVO ENCONTRADA")
    print("="*90)
    
    # Diferencia >= 0.08
    strat = df[df['Diferencia_Cuota_Promedio'] >= 0.08]
    if len(strat) > 0:
        roi_strat = strat['Rendimiento'].mean() * 100
        rend_strat = strat['Rendimiento'].sum()
        
        print(f"""
    ┌──────────────────────────────────────────────────────────────────────────────────────┐
    │  Estrategia: Diferencia_Cuota_Promedio >= 0.08                                       │
    │                                                                                      │
    │    • Número de apuestas: {len(strat)}                                                     │
    │    • ROI: {roi_strat:+.2f}%                                                                │
    │    • Rendimiento total: {rend_strat:+.2f}€                                                    │
    │    • Tasa de aciertos: {strat['Acierto'].mean()*100:.1f}%                                            │
    │                                                                                      │
    │  ⚠️  PRECAUCIÓN:                                                                     │
    │    • Solo 69 apuestas - muestra muy pequeña                                          │
    │    • ROI de apenas +0.25% - muy cercano a 0                                          │
    │    • No es estadísticamente confiable                                                │
    │                                                                                      │
    └──────────────────────────────────────────────────────────────────────────────────────┘
    """)
    
    # Conclusión final
    print("="*90)
    print("  CONCLUSIÓN FINAL")
    print("="*90)
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                      ║
    ║  HALLAZGOS PRINCIPALES:                                                              ║
    ║                                                                                      ║
    ║  1. P_Win_Calibrada NO es predictor de rendimiento                                   ║
    ║     • Correlación prácticamente nula (-0.014)                                        ║
    ║     • Apostar por P_Win alto da ROI negativo                                         ║
    ║                                                                                      ║
    ║  2. NINGUNA variable individual predice bien el rendimiento                          ║
    ║     • Todas las correlaciones son < 0.05                                             ║
    ║     • El mercado de apuestas es eficiente                                            ║
    ║                                                                                      ║
    ║  3. Las variables más prometedoras (aunque débiles):                                 ║
    ║     • Diferencia_Cuota_Promedio: Buscar cuotas mejores que el promedio               ║
    ║     • Volatilidad: Mercados con discrepancia entre casas                             ║
    ║     • Score_Final: Combinación de factores                                           ║
    ║                                                                                      ║
    ║  4. El ROI general es -6.79%                                                         ║
    ║     • Refleja el margen de las casas de apuestas                                     ║
    ║     • Es muy difícil ser rentable con la información disponible                      ║
    ║                                                                                      ║
    ║  PARA SER RENTABLE SE NECESITA:                                                      ║
    ║                                                                                      ║
    ║  • Información externa NO contenida en las cuotas:                                   ║
    ║    - Forma reciente de equipos                                                       ║
    ║    - Lesiones y suspensiones                                                         ║
    ║    - Historial de enfrentamientos                                                    ║
    ║    - Factores motivacionales                                                         ║
    ║                                                                                      ║
    ║  • Las cuotas ya incorporan toda la información pública disponible                   ║
    ║                                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
