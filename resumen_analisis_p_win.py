#!/usr/bin/env python3
"""
RESUMEN EJECUTIVO: Análisis de P_Win_Calibrada como Predictor

Este documento presenta los hallazgos clave sobre la capacidad predictiva
de P_Win_Calibrada.
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score
import warnings
warnings.filterwarnings('ignore')

def main():
    df = pd.read_csv('data/historico_completo.csv')
    df = df[df['Resultado'].isin(['Acertado', 'Fallido'])].copy()
    df['Acierto'] = (df['Resultado'] == 'Acertado').astype(int)
    df['P_Win_Calibrada'] = pd.to_numeric(df['P_Win_Calibrada'], errors='coerce')
    df['Prob_Implicita'] = 1 / df['Mejor_Cuota']
    df = df.dropna(subset=['P_Win_Calibrada', 'Acierto', 'Prob_Implicita'])
    
    print("\n" + "="*80)
    print("RESUMEN EJECUTIVO: ANÁLISIS DE P_Win_Calibrada")
    print("="*80)
    
    print("\n📊 DATOS ANALIZADOS:")
    print(f"   - Registros totales: {len(df)}")
    print(f"   - Aciertos: {df['Acierto'].sum()} ({df['Acierto'].mean()*100:.1f}%)")
    print(f"   - Fallidos: {len(df) - df['Acierto'].sum()} ({(1-df['Acierto'].mean())*100:.1f}%)")
    
    # Métricas clave
    corr_pwin = stats.pearsonr(df['P_Win_Calibrada'], df['Acierto'])[0]
    corr_prob = stats.pearsonr(df['Prob_Implicita'], df['Acierto'])[0]
    auc_pwin = roc_auc_score(df['Acierto'], df['P_Win_Calibrada'])
    auc_prob = roc_auc_score(df['Acierto'], df['Prob_Implicita'])
    corr_entre = np.corrcoef(df['P_Win_Calibrada'], df['Prob_Implicita'])[0,1]
    
    print("\n" + "="*80)
    print("📈 MÉTRICAS CLAVE")
    print("="*80)
    
    print(f"""
    ┌─────────────────────────────────────────────────────────────┐
    │                  PODER PREDICTIVO                           │
    ├─────────────────────────────────────────────────────────────┤
    │  Métrica                    P_Win_Calibrada  Prob_Implícita │
    │  ─────────────────────────  ───────────────  ────────────── │
    │  Correlación con Acierto    {corr_pwin:+.4f}           {corr_prob:+.4f}         │
    │  AUC-ROC                    {auc_pwin:.4f}            {auc_prob:.4f}          │
    │  Ganador                    {'❌':^15}  {'✓':^14} │
    └─────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────┐
    │                  REDUNDANCIA                                │
    ├─────────────────────────────────────────────────────────────┤
    │  Correlación P_Win_Cal ↔ Prob_Implícita:  {corr_entre:.4f} ({corr_entre*100:.1f}%)    │
    │                                                             │
    │  Interpretación: P_Win_Calibrada está casi completamente    │
    │  determinada por la probabilidad implícita (1/cuota).       │
    │  Son esencialmente la MISMA información.                    │
    └─────────────────────────────────────────────────────────────┘
    """)
    
    print("="*80)
    print("🔍 ANÁLISIS POR TIPO DE MERCADO")
    print("="*80)
    
    print(f"""
    ┌────────────────────────────────────────────────────────────────────────┐
    │  Mercado              N     AUC P_Win_Cal   AUC Prob_Imp   Diferencia  │
    ├────────────────────────────────────────────────────────────────────────┤""")
    
    for mercado in df['Tipo_Mercado'].unique():
        subset = df[df['Tipo_Mercado'] == mercado]
        if len(subset) < 30:
            continue
        auc_p = roc_auc_score(subset['Acierto'], subset['Prob_Implicita'])
        auc_w = roc_auc_score(subset['Acierto'], subset['P_Win_Calibrada'])
        dif = auc_w - auc_p
        print(f"    │  {mercado:<18} {len(subset):<5} {auc_w:.4f}          {auc_p:.4f}         {dif:+.4f}     │")
    
    print("    └────────────────────────────────────────────────────────────────────────┘")
    
    # Análisis de efectividad real
    print("\n" + "="*80)
    print("🎯 ¿FUNCIONA LA ESTRATEGIA DE APOSTAR CON P_WIN ALTO?")
    print("="*80)
    
    # Dividir por quintiles de P_Win_Calibrada
    df['Quintil_PWin'] = pd.qcut(df['P_Win_Calibrada'], 5, labels=['Q1 (Bajo)', 'Q2', 'Q3', 'Q4', 'Q5 (Alto)'])
    
    print(f"""
    ┌───────────────────────────────────────────────────────────────────────────┐
    │  Quintil P_Win    N      % Aciertos    Cuota Media    Ganancia si 1€/ap   │
    ├───────────────────────────────────────────────────────────────────────────┤""")
    
    for quintil in ['Q1 (Bajo)', 'Q2', 'Q3', 'Q4', 'Q5 (Alto)']:
        subset = df[df['Quintil_PWin'] == quintil]
        n = len(subset)
        tasa = subset['Acierto'].mean()
        cuota_media = subset['Mejor_Cuota'].mean()
        # ROI esperado = tasa * cuota_media - 1
        roi = tasa * cuota_media - 1
        ganancia = roi * n  # Ganancia si apostamos 1€ a cada una
        print(f"    │  {quintil:<15} {n:<6} {tasa*100:.1f}%          {cuota_media:.2f}           {ganancia:+.2f}€              │")
    
    print("    └───────────────────────────────────────────────────────────────────────────┘")
    
    # Mismo análisis con Prob_Implicita
    df['Quintil_Prob'] = pd.qcut(df['Prob_Implicita'], 5, labels=['Q1 (Bajo)', 'Q2', 'Q3', 'Q4', 'Q5 (Alto)'])
    
    print(f"""
    ┌───────────────────────────────────────────────────────────────────────────┐
    │  Quintil Prob_Imp N      % Aciertos    Cuota Media    Ganancia si 1€/ap   │
    ├───────────────────────────────────────────────────────────────────────────┤""")
    
    for quintil in ['Q1 (Bajo)', 'Q2', 'Q3', 'Q4', 'Q5 (Alto)']:
        subset = df[df['Quintil_Prob'] == quintil]
        n = len(subset)
        tasa = subset['Acierto'].mean()
        cuota_media = subset['Mejor_Cuota'].mean()
        roi = tasa * cuota_media - 1
        ganancia = roi * n
        print(f"    │  {quintil:<15} {n:<6} {tasa*100:.1f}%          {cuota_media:.2f}           {ganancia:+.2f}€              │")
    
    print("    └───────────────────────────────────────────────────────────────────────────┘")
    
    # Conclusión final
    print("\n" + "="*80)
    print("📋 CONCLUSIÓN FINAL")
    print("="*80)
    
    print("""
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                                                                         │
    │  ¿P_Win_Calibrada tiene correlación con aciertos?                       │
    │  ➜ SÍ, tiene correlación positiva (r ≈ +0.23)                           │
    │                                                                         │
    │  ¿Es P_Win_Calibrada un buen predictor?                                 │
    │  ➜ MODERADO. AUC de 0.64 es mejor que azar (0.50) pero lejos de         │
    │    excelente (>0.80)                                                    │
    │                                                                         │
    │  ¿P_Win_Calibrada añade valor sobre la probabilidad implícita?          │
    │  ➜ NO SIGNIFICATIVAMENTE. La Prob_Implícita (1/cuota) tiene:            │
    │    - Mejor correlación con aciertos                                     │
    │    - Mejor AUC-ROC                                                      │
    │    - Y es más simple de calcular                                        │
    │                                                                         │
    │  ¿Por qué P_Win_Calibrada parece funcionar?                             │
    │  ➜ Porque está 89% correlacionada con la Prob_Implícita.                │
    │    Básicamente está midiendo lo mismo: las cuotas bajas (favoritos)     │
    │    tienen mayor probabilidad implícita Y mayor P_Win_Calibrada,         │
    │    y los favoritos aciertan más a menudo.                               │
    │                                                                         │
    │  RECOMENDACIÓN:                                                         │
    │  ➜ Usar directamente 1/Mejor_Cuota (Prob_Implícita) como predictor.     │
    │    Es más transparente, más simple, y tiene mejor rendimiento.          │
    │                                                                         │
    │  NOTA IMPORTANTE:                                                       │
    │  ➜ Aunque los favoritos aciertan más, sus cuotas son menores.           │
    │    Esto NO garantiza ganancias, ya que las casas de apuestas            │
    │    ajustan las cuotas para tener margen. El mercado es eficiente.       │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
    """)


if __name__ == "__main__":
    main()
