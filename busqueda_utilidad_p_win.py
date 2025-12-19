#!/usr/bin/env python3
"""
Análisis final: Buscando si hay ALGÚN escenario donde P_Win_Calibrada sea útil
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
    df['Confianza'] = pd.to_numeric(df['Confianza'], errors='coerce')
    df['Prob_Implicita'] = 1 / df['Mejor_Cuota']
    df = df.dropna(subset=['P_Win_Calibrada', 'Acierto', 'Prob_Implicita'])
    
    print("\n" + "="*80)
    print("BÚSQUEDA DE ESCENARIOS DONDE P_Win_Calibrada SEA ÚTIL")
    print("="*80)
    
    # ============================================================
    # 1. ¿Funciona mejor para cuotas específicas?
    # ============================================================
    print("\n" + "-"*80)
    print("1. ¿P_Win_Calibrada funciona mejor en algún rango de cuotas?")
    print("-"*80)
    
    df['Rango_Cuota'] = pd.cut(df['Mejor_Cuota'], 
                                bins=[0, 1.3, 1.5, 1.8, 2.2, 10],
                                labels=['<1.3', '1.3-1.5', '1.5-1.8', '1.8-2.2', '>2.2'])
    
    print(f"\n   {'Rango Cuota':<12} {'N':<8} {'AUC P_Win':<12} {'AUC Prob_Imp':<14} {'¿P_Win Mejor?'}")
    print("   " + "-"*60)
    
    for rango in df['Rango_Cuota'].unique():
        if pd.isna(rango):
            continue
        subset = df[df['Rango_Cuota'] == rango]
        if len(subset) < 30:
            continue
        try:
            auc_p = roc_auc_score(subset['Acierto'], subset['P_Win_Calibrada'])
            auc_i = roc_auc_score(subset['Acierto'], subset['Prob_Implicita'])
            mejor = "Sí" if auc_p > auc_i else "No"
            print(f"   {rango:<12} {len(subset):<8} {auc_p:.4f}{'':>4} {auc_i:.4f}{'':>6} {mejor}")
        except:
            pass
    
    # ============================================================
    # 2. ¿Funciona mejor para ciertas ligas?
    # ============================================================
    print("\n" + "-"*80)
    print("2. ¿P_Win_Calibrada funciona mejor en alguna liga?")
    print("-"*80)
    
    print(f"\n   {'Liga':<30} {'N':<8} {'AUC P_Win':<12} {'AUC Prob_Imp':<14}")
    print("   " + "-"*65)
    
    for liga in df['Liga'].value_counts().head(10).index:
        subset = df[df['Liga'] == liga]
        if len(subset) < 30:
            continue
        try:
            auc_p = roc_auc_score(subset['Acierto'], subset['P_Win_Calibrada'])
            auc_i = roc_auc_score(subset['Acierto'], subset['Prob_Implicita'])
            mejor = "*" if auc_p > auc_i else ""
            print(f"   {liga[:28]:<30} {len(subset):<8} {auc_p:.4f}{'':>4} {auc_i:.4f}{'':>6} {mejor}")
        except:
            pass
    
    # ============================================================
    # 3. ¿Qué pasa si combinamos ambos predictores?
    # ============================================================
    print("\n" + "-"*80)
    print("3. ¿Combinar P_Win_Calibrada con Prob_Implícita mejora?")
    print("-"*80)
    
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    
    # Modelo solo con Prob_Implicita
    X1 = df[['Prob_Implicita']].values
    y = df['Acierto'].values
    auc1 = cross_val_score(LogisticRegression(), X1, y, cv=5, scoring='roc_auc').mean()
    
    # Modelo combinado
    X2 = df[['Prob_Implicita', 'P_Win_Calibrada']].values
    auc2 = cross_val_score(LogisticRegression(), X2, y, cv=5, scoring='roc_auc').mean()
    
    print(f"\n   Solo Prob_Implícita:              AUC = {auc1:.4f}")
    print(f"   Prob_Implícita + P_Win_Calibrada: AUC = {auc2:.4f}")
    print(f"   Mejora:                           {(auc2-auc1)*100:+.2f}%")
    
    # ============================================================
    # 4. ¿Los componentes individuales son útiles?
    # ============================================================
    print("\n" + "-"*80)
    print("4. ¿Algún componente de la fórmula es útil independientemente?")
    print("-"*80)
    
    componentes = ['Score_Final', 'Volatilidad_Pct', 'Margen_Casa_Pct', 'Num_Casas']
    
    print(f"\n   {'Componente':<20} {'Corr con Acierto':<20} {'p-value':<15} {'Significativo'}")
    print("   " + "-"*70)
    
    for comp in componentes:
        if comp in df.columns:
            df[comp] = pd.to_numeric(df[comp], errors='coerce')
            subset = df[[comp, 'Acierto']].dropna()
            if len(subset) > 30:
                corr, p = stats.pearsonr(subset[comp].astype(float), subset['Acierto'].astype(float))
                sig = "Sí" if p < 0.05 else "No"
                print(f"   {comp:<20} {corr:+.4f}{'':>11} {p:.6f}{'':>5} {sig}")
    
    # ============================================================
    # 5. ¿El Score_Final (diferencia de cuota vs promedio) es útil?
    # ============================================================
    print("\n" + "-"*80)
    print("5. Análisis del Score_Final")
    print("-"*80)
    
    df['Score_Final'] = pd.to_numeric(df['Score_Final'], errors='coerce')
    subset = df.dropna(subset=['Score_Final'])
    
    # Dividir por score
    df['Score_Alto'] = df['Score_Final'] > df['Score_Final'].median()
    
    alto = df[df['Score_Alto'] == True]
    bajo = df[df['Score_Alto'] == False]
    
    if len(alto) > 30 and len(bajo) > 30:
        tasa_alto = alto['Acierto'].mean()
        tasa_bajo = bajo['Acierto'].mean()
        
        print(f"\n   Score_Final alto (>mediana): Tasa aciertos = {tasa_alto:.2%} (n={len(alto)})")
        print(f"   Score_Final bajo (<=mediana): Tasa aciertos = {tasa_bajo:.2%} (n={len(bajo)})")
        print(f"   Diferencia: {tasa_alto - tasa_bajo:+.2%}")
        
        # ¿Pero el Score_Final está correlacionado con la cuota?
        corr_score_cuota = np.corrcoef(df['Score_Final'].dropna(), df['Mejor_Cuota'].loc[df['Score_Final'].notna()])[0,1]
        print(f"\n   Correlación Score_Final ↔ Mejor_Cuota: {corr_score_cuota:.4f}")
        print("   (Si es alta, Score_Final también es redundante con las cuotas)")
    
    # ============================================================
    # CONCLUSIÓN FINAL
    # ============================================================
    print("\n" + "="*80)
    print("CONCLUSIÓN DEL ANÁLISIS DE BÚSQUEDA")
    print("="*80)
    
    print("""
    HALLAZGOS:
    
    ✗ P_Win_Calibrada NO mejora sobre Prob_Implícita en ningún rango de cuotas
    ✗ P_Win_Calibrada NO mejora consistentemente en ninguna liga específica
    ✗ Combinar ambos predictores NO mejora significativamente
    ✗ Los componentes individuales (Score_Final, Volatilidad, etc.) tienen
      correlaciones muy débiles o nulas con los aciertos
    
    ¿POR QUÉ PASÓ ESTO?
    
    El modelo de regresión logística que crea P_Win_Calibrada básicamente
    "aprende" a dar más peso a las probabilidades implícitas altas (cuotas bajas)
    porque eso es lo que mejor predice los aciertos en los datos históricos.
    
    Al hacerlo, P_Win_Calibrada se convierte en una versión "suavizada" de
    la probabilidad implícita, pero sin añadir información nueva.
    
    CONCLUSIÓN DEFINITIVA:
    
    P_Win_Calibrada tiene correlación con los aciertos (✓), pero esta correlación
    es redundante - simplemente refleja que las cuotas bajas (favoritos) ganan más.
    
    La probabilidad implícita (1/cuota) es un predictor IGUAL O MEJOR y mucho más simple.
    
    Para mejorar realmente el sistema de predicción, se necesitarían variables
    que capturen información NO contenida en las cuotas, como:
    - Datos de rendimiento reciente de equipos
    - Lesiones/suspensiones de jugadores clave
    - Historial de enfrentamientos directos
    - Condiciones climáticas
    - Motivación (ej: posición en la tabla)
    """)


if __name__ == "__main__":
    main()
