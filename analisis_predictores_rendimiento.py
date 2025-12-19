#!/usr/bin/env python3
"""
ANÁLISIS DE PREDICTORES DE RENDIMIENTO (ROI)

Rendimiento = Suma(cuotas de partidos ganados) - Cantidad de partidos apostados
            = Suma(ganancia/pérdida por apuesta)

Para cada apuesta de 1€:
- Si gana: +cuota - 1 = cuota - 1
- Si pierde: -1

Rendimiento total = Σ(ganancia_i) donde:
- ganancia_i = cuota_i - 1 si acierta
- ganancia_i = -1 si falla

Este script evalúa qué variables son PREDICTORES DE RENDIMIENTO,
no de aciertos. Esto elimina el problema de la redundancia con las cuotas.
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def cargar_datos():
    """Carga datos y calcula el rendimiento por apuesta."""
    df = pd.read_csv('data/historico_completo.csv')
    df = df[df['Resultado'].isin(['Acertado', 'Fallido'])].copy()
    
    # Variable binaria de acierto
    df['Acierto'] = (df['Resultado'] == 'Acertado').astype(int)
    
    # Mejor_Cuota a numérico
    df['Mejor_Cuota'] = pd.to_numeric(df['Mejor_Cuota'], errors='coerce')
    
    # RENDIMIENTO por apuesta (apostando 1€)
    # Si acierta: gana cuota - 1
    # Si falla: pierde 1
    df['Rendimiento'] = np.where(df['Acierto'] == 1, df['Mejor_Cuota'] - 1, -1)
    
    return df.dropna(subset=['Rendimiento'])


def resumen_datos(df):
    """Muestra resumen del dataset."""
    print("\n" + "="*80)
    print("DATOS Y CONCEPTO DE RENDIMIENTO")
    print("="*80)
    
    print(f"\nTotal de apuestas: {len(df)}")
    print(f"Aciertos: {df['Acierto'].sum()} ({df['Acierto'].mean()*100:.1f}%)")
    
    rend_total = df['Rendimiento'].sum()
    roi_pct = rend_total / len(df) * 100
    
    print(f"\nRendimiento total (apostando 1€ por apuesta):")
    print(f"   Capital apostado: {len(df)}€")
    print(f"   Rendimiento neto: {rend_total:+.2f}€")
    print(f"   ROI: {roi_pct:+.2f}%")
    
    print(f"\nEstadísticas del Rendimiento por apuesta:")
    print(f"   Media:     {df['Rendimiento'].mean():+.4f}")
    print(f"   Mediana:   {df['Rendimiento'].median():+.4f}")
    print(f"   Desv.Est.: {df['Rendimiento'].std():.4f}")
    print(f"   Mínimo:    {df['Rendimiento'].min():+.4f}")
    print(f"   Máximo:    {df['Rendimiento'].max():+.4f}")


def analizar_predictor_rendimiento(df, columna, nombre=None):
    """
    Analiza si una columna es predictor de RENDIMIENTO.
    
    Un buen predictor de rendimiento debería:
    1. Tener correlación con el rendimiento (no necesariamente con aciertos)
    2. Permitir seleccionar apuestas con ROI positivo
    
    Returns: dict con métricas
    """
    nombre = nombre or columna
    
    # Convertir a numérico
    df[columna] = pd.to_numeric(df[columna], errors='coerce')
    subset = df.dropna(subset=[columna, 'Rendimiento'])
    
    if len(subset) < 50:
        return None
    
    valores = subset[columna].values
    rendimiento = subset['Rendimiento'].values
    
    # 1. Correlación con rendimiento
    corr, p_value = stats.pearsonr(valores, rendimiento)
    
    # 2. Correlación de Spearman (más robusta)
    corr_spearman, p_spearman = stats.spearmanr(valores, rendimiento)
    
    # 3. Análisis por quintiles
    try:
        subset['Quintil'] = pd.qcut(subset[columna], 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'], duplicates='drop')
        quintiles = subset.groupby('Quintil', observed=True).agg({
            'Rendimiento': ['sum', 'mean', 'count'],
            'Acierto': 'mean'
        }).round(4)
        
        # ROI del quintil más alto
        q5 = subset[subset['Quintil'] == 'Q5']
        roi_q5 = q5['Rendimiento'].mean() * 100 if len(q5) > 0 else np.nan
        n_q5 = len(q5)
        
        # ROI del quintil más bajo
        q1 = subset[subset['Quintil'] == 'Q1']
        roi_q1 = q1['Rendimiento'].mean() * 100 if len(q1) > 0 else np.nan
        n_q1 = len(q1)
        
    except Exception as e:
        roi_q5 = roi_q1 = np.nan
        n_q5 = n_q1 = 0
        quintiles = None
    
    # 4. ¿Hay un umbral donde el ROI sea positivo?
    # Probar percentiles
    umbrales = [50, 60, 70, 80, 90]
    mejor_roi = -100
    mejor_umbral = None
    mejor_n = 0
    
    for p in umbrales:
        umbral = np.percentile(valores, p)
        seleccion = subset[subset[columna] >= umbral]
        if len(seleccion) >= 20:
            roi = seleccion['Rendimiento'].mean() * 100
            if roi > mejor_roi:
                mejor_roi = roi
                mejor_umbral = p
                mejor_n = len(seleccion)
    
    return {
        'columna': columna,
        'nombre': nombre,
        'n': len(subset),
        'corr_pearson': corr,
        'p_value_pearson': p_value,
        'corr_spearman': corr_spearman,
        'p_value_spearman': p_spearman,
        'roi_q5': roi_q5,
        'n_q5': n_q5,
        'roi_q1': roi_q1,
        'n_q1': n_q1,
        'mejor_roi': mejor_roi,
        'mejor_umbral_pct': mejor_umbral,
        'mejor_n': mejor_n,
        'quintiles': quintiles
    }


def main():
    df = cargar_datos()
    resumen_datos(df)
    
    # Lista de todas las columnas potenciales como predictores
    columnas_analizar = [
        ('P_Win_Calibrada', 'P_Win_Calibrada'),
        ('Confianza', 'Confianza Original'),
        ('Confianza_Calibrada', 'Confianza_Calibrada'),
        ('Score_Final', 'Score Final'),
        ('Diferencia_Cuota_Promedio', 'Dif. Cuota vs Promedio'),
        ('Volatilidad_Pct', 'Volatilidad (%)'),
        ('Margen_Casa_Pct', 'Margen Casa (%)'),
        ('Num_Casas', 'Número de Casas'),
        ('Cuota_Promedio_Mercado', 'Cuota Promedio Mercado'),
        ('Mejor_Cuota', 'Mejor Cuota'),
    ]
    
    # También la probabilidad implícita
    df['Prob_Implicita'] = 1 / df['Mejor_Cuota']
    columnas_analizar.append(('Prob_Implicita', 'Prob. Implícita (1/cuota)'))
    
    # Calcular valor esperado teórico: P_Win * Cuota - 1
    df['Valor_Esperado'] = df['P_Win_Calibrada'] * df['Mejor_Cuota'] - 1
    columnas_analizar.append(('Valor_Esperado', 'Valor Esperado (P_Win*Cuota-1)'))
    
    print("\n" + "="*80)
    print("ANÁLISIS DE PREDICTORES DE RENDIMIENTO")
    print("="*80)
    print("\nPara cada variable, evaluamos:")
    print("  - Correlación con el Rendimiento (no con aciertos)")
    print("  - ROI al seleccionar apuestas por quintiles")
    print("  - Mejor ROI alcanzable con algún umbral")
    
    resultados = []
    
    for col, nombre in columnas_analizar:
        if col in df.columns or col in ['Prob_Implicita', 'Valor_Esperado']:
            resultado = analizar_predictor_rendimiento(df, col, nombre)
            if resultado:
                resultados.append(resultado)
    
    # Mostrar tabla resumen ordenada por correlación con rendimiento
    print("\n" + "-"*100)
    print(f"{'Variable':<30} {'N':<7} {'Corr':<10} {'p-value':<12} {'ROI Q5':<10} {'ROI Q1':<10} {'Mejor ROI':<10} {'Umbral':<8}")
    print("-"*100)
    
    # Ordenar por correlación absoluta
    resultados_ordenados = sorted(resultados, key=lambda x: abs(x['corr_pearson']), reverse=True)
    
    for r in resultados_ordenados:
        sig = "***" if r['p_value_pearson'] < 0.001 else "**" if r['p_value_pearson'] < 0.01 else "*" if r['p_value_pearson'] < 0.05 else ""
        roi_q5_str = f"{r['roi_q5']:+.2f}%" if not np.isnan(r['roi_q5']) else "N/A"
        roi_q1_str = f"{r['roi_q1']:+.2f}%" if not np.isnan(r['roi_q1']) else "N/A"
        mejor_roi_str = f"{r['mejor_roi']:+.2f}%" if r['mejor_roi'] > -100 else "N/A"
        umbral_str = f"P{r['mejor_umbral_pct']}" if r['mejor_umbral_pct'] else "N/A"
        
        print(f"{r['nombre']:<30} {r['n']:<7} {r['corr_pearson']:+.4f}{sig:<3} {r['p_value_pearson']:<12.6f} {roi_q5_str:<10} {roi_q1_str:<10} {mejor_roi_str:<10} {umbral_str:<8}")
    
    # Análisis detallado de los mejores predictores
    print("\n" + "="*80)
    print("ANÁLISIS DETALLADO DE LOS MEJORES PREDICTORES")
    print("="*80)
    
    # Top 5 por correlación absoluta
    for r in resultados_ordenados[:5]:
        print(f"\n--- {r['nombre']} ---")
        print(f"Correlación con Rendimiento: {r['corr_pearson']:+.4f} (p={r['p_value_pearson']:.6f})")
        print(f"Correlación Spearman:        {r['corr_spearman']:+.4f} (p={r['p_value_spearman']:.6f})")
        
        if r['quintiles'] is not None:
            print(f"\nROI por Quintiles:")
            print(f"  Q1 (bajo): ROI = {r['roi_q1']:+.2f}% (n={r['n_q1']})")
            print(f"  Q5 (alto): ROI = {r['roi_q5']:+.2f}% (n={r['n_q5']})")
            print(f"  Diferencia Q5-Q1: {r['roi_q5'] - r['roi_q1']:+.2f}%")
        
        if r['mejor_roi'] > -100:
            print(f"\nMejor estrategia: Seleccionar >= percentil {r['mejor_umbral_pct']}")
            print(f"  ROI: {r['mejor_roi']:+.2f}% con {r['mejor_n']} apuestas")
    
    # Análisis específico de P_Win_Calibrada
    print("\n" + "="*80)
    print("ANÁLISIS ESPECÍFICO: P_WIN_CALIBRADA COMO PREDICTOR DE RENDIMIENTO")
    print("="*80)
    
    p_win_result = next((r for r in resultados if r['columna'] == 'P_Win_Calibrada'), None)
    
    if p_win_result:
        print(f"\nCorrelación P_Win_Calibrada ↔ Rendimiento: {p_win_result['corr_pearson']:+.4f}")
        
        if abs(p_win_result['corr_pearson']) < 0.05:
            print("\n⚠️  Correlación MUY DÉBIL con el rendimiento")
        elif p_win_result['corr_pearson'] < 0:
            print("\n⚠️  Correlación NEGATIVA con el rendimiento")
            print("   Mayor P_Win_Calibrada → PEOR rendimiento")
        else:
            print("\n✓  Correlación POSITIVA con el rendimiento")
        
        # Comparar con otros predictores
        print("\n>>> Comparación con otros predictores:")
        for r in resultados_ordenados[:3]:
            if r['columna'] != 'P_Win_Calibrada':
                print(f"   {r['nombre']}: corr = {r['corr_pearson']:+.4f}")
    
    # Conclusión final
    print("\n" + "="*80)
    print("CONCLUSIÓN FINAL")
    print("="*80)
    
    # Encontrar el mejor predictor de rendimiento
    mejor = resultados_ordenados[0] if resultados_ordenados else None
    
    if mejor:
        print(f"\n🏆 MEJOR PREDICTOR DE RENDIMIENTO: {mejor['nombre']}")
        print(f"   Correlación: {mejor['corr_pearson']:+.4f}")
        print(f"   ROI Q5: {mejor['roi_q5']:+.2f}%")
        
        if mejor['columna'] == 'P_Win_Calibrada':
            print("\n   ✓ P_Win_Calibrada ES el mejor predictor de rendimiento")
        else:
            p_win_rank = next((i+1 for i, r in enumerate(resultados_ordenados) if r['columna'] == 'P_Win_Calibrada'), None)
            if p_win_rank:
                print(f"\n   P_Win_Calibrada está en posición #{p_win_rank} de {len(resultados_ordenados)}")
    
    # ¿Hay algún predictor con ROI positivo consistente?
    print("\n>>> Predictores con ROI positivo en Q5:")
    for r in resultados_ordenados:
        if r['roi_q5'] > 0:
            print(f"   {r['nombre']}: ROI Q5 = {r['roi_q5']:+.2f}%")


if __name__ == "__main__":
    main()
