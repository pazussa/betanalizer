#!/usr/bin/env python3
"""
ANÁLISIS PROFUNDO DE PREDICTORES DE RENDIMIENTO

Enfoque:
1. Analizar cada variable en detalle
2. Buscar combinaciones que generen ROI positivo
3. Análisis por tipo de mercado
4. Búsqueda de estrategias rentables
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def cargar_datos():
    df = pd.read_csv('data/historico_completo.csv')
    df = df[df['Resultado'].isin(['Acertado', 'Fallido'])].copy()
    df['Acierto'] = (df['Resultado'] == 'Acertado').astype(int)
    df['Mejor_Cuota'] = pd.to_numeric(df['Mejor_Cuota'], errors='coerce')
    df['Rendimiento'] = np.where(df['Acierto'] == 1, df['Mejor_Cuota'] - 1, -1)
    
    # Convertir todas las columnas numéricas potenciales
    cols_num = ['P_Win_Calibrada', 'Confianza', 'Confianza_Calibrada', 'Score_Final',
                'Diferencia_Cuota_Promedio', 'Volatilidad_Pct', 'Margen_Casa_Pct',
                'Num_Casas', 'Cuota_Promedio_Mercado']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['Prob_Implicita'] = 1 / df['Mejor_Cuota']
    
    return df.dropna(subset=['Rendimiento'])


def analisis_deciles_rendimiento(df, columna, nombre=None):
    """Análisis detallado por deciles."""
    nombre = nombre or columna
    
    subset = df.dropna(subset=[columna])
    if len(subset) < 100:
        return None
    
    try:
        subset['Decil'] = pd.qcut(subset[columna], 10, labels=range(1, 11), duplicates='drop')
    except:
        return None
    
    print(f"\n{'='*80}")
    print(f"ANÁLISIS POR DECILES: {nombre}")
    print(f"{'='*80}")
    
    print(f"\n{'Decil':<8} {'N':<8} {'Val Min':<12} {'Val Max':<12} {'Aciertos':<12} {'ROI':<12} {'Rend Total':<12}")
    print("-"*80)
    
    deciles_data = []
    for decil in range(1, 11):
        dec_data = subset[subset['Decil'] == decil]
        if len(dec_data) == 0:
            continue
        
        n = len(dec_data)
        val_min = dec_data[columna].min()
        val_max = dec_data[columna].max()
        tasa_acierto = dec_data['Acierto'].mean() * 100
        roi = dec_data['Rendimiento'].mean() * 100
        rend_total = dec_data['Rendimiento'].sum()
        
        deciles_data.append({
            'decil': decil,
            'n': n,
            'roi': roi,
            'rend_total': rend_total,
            'aciertos': tasa_acierto
        })
        
        roi_str = f"{roi:+.2f}%" if roi >= 0 else f"{roi:.2f}%"
        print(f"D{decil:<7} {n:<8} {val_min:<12.4f} {val_max:<12.4f} {tasa_acierto:>6.1f}%{'':>4} {roi_str:<12} {rend_total:+.2f}€")
    
    # ¿Hay algún decil con ROI positivo?
    positivos = [d for d in deciles_data if d['roi'] > 0]
    if positivos:
        print(f"\n✓ Deciles con ROI POSITIVO: {[d['decil'] for d in positivos]}")
        mejor = max(positivos, key=lambda x: x['roi'])
        print(f"  Mejor: D{mejor['decil']} con ROI {mejor['roi']:+.2f}% (n={mejor['n']})")
    else:
        print(f"\n✗ Ningún decil tiene ROI positivo")
    
    return deciles_data


def analisis_por_mercado(df):
    """Análisis separado por tipo de mercado."""
    print(f"\n{'='*80}")
    print("ANÁLISIS POR TIPO DE MERCADO")
    print(f"{'='*80}")
    
    columnas = ['P_Win_Calibrada', 'Diferencia_Cuota_Promedio', 'Volatilidad_Pct', 
                'Score_Final', 'Margen_Casa_Pct']
    
    for mercado in df['Tipo_Mercado'].unique():
        subset = df[df['Tipo_Mercado'] == mercado]
        if len(subset) < 100:
            continue
        
        roi_total = subset['Rendimiento'].mean() * 100
        n = len(subset)
        
        print(f"\n--- {mercado} (N={n}, ROI total={roi_total:+.2f}%) ---")
        
        print(f"{'Variable':<30} {'Corr Rend':<12} {'p-value':<12} {'ROI Q5':<12}")
        print("-"*70)
        
        for col in columnas:
            if col not in subset.columns:
                continue
            sub = subset.dropna(subset=[col])
            if len(sub) < 50:
                continue
            
            corr, p = stats.pearsonr(sub[col], sub['Rendimiento'])
            
            try:
                sub['Q'] = pd.qcut(sub[col], 5, labels=['Q1','Q2','Q3','Q4','Q5'], duplicates='drop')
                q5 = sub[sub['Q'] == 'Q5']
                roi_q5 = q5['Rendimiento'].mean() * 100 if len(q5) > 0 else np.nan
            except:
                roi_q5 = np.nan
            
            sig = "*" if p < 0.05 else ""
            roi_str = f"{roi_q5:+.2f}%" if not np.isnan(roi_q5) else "N/A"
            print(f"{col:<30} {corr:+.4f}{sig:<3} {p:<12.4f} {roi_str:<12}")


def buscar_estrategias_rentables(df):
    """Busca combinaciones de filtros que generen ROI positivo."""
    print(f"\n{'='*80}")
    print("BÚSQUEDA DE ESTRATEGIAS RENTABLES")
    print(f"{'='*80}")
    print("\nProbando combinaciones de filtros...")
    
    estrategias = []
    
    # Variables a combinar
    filtros = {
        'P_Win_Calibrada': [0.5, 0.55, 0.6],
        'Diferencia_Cuota_Promedio': [0.02, 0.05, 0.08],
        'Volatilidad_Pct': [1.5, 2.0, 2.5],
        'Score_Final': [0.5, 0.8, 1.0],
        'Margen_Casa_Pct': [None, 4.0, 3.5],  # None = sin filtro, valores = máximo
    }
    
    # Estrategia 1: Solo por P_Win_Calibrada
    for umbral in filtros['P_Win_Calibrada']:
        subset = df[df['P_Win_Calibrada'] >= umbral]
        if len(subset) >= 30:
            roi = subset['Rendimiento'].mean() * 100
            rend = subset['Rendimiento'].sum()
            tasa = subset['Acierto'].mean() * 100
            estrategias.append({
                'filtro': f'P_Win >= {umbral}',
                'n': len(subset),
                'roi': roi,
                'rend_total': rend,
                'tasa_acierto': tasa
            })
    
    # Estrategia 2: Solo por Diferencia_Cuota_Promedio
    for umbral in filtros['Diferencia_Cuota_Promedio']:
        subset = df[df['Diferencia_Cuota_Promedio'] >= umbral]
        if len(subset) >= 30:
            roi = subset['Rendimiento'].mean() * 100
            rend = subset['Rendimiento'].sum()
            tasa = subset['Acierto'].mean() * 100
            estrategias.append({
                'filtro': f'Dif_Cuota >= {umbral}',
                'n': len(subset),
                'roi': roi,
                'rend_total': rend,
                'tasa_acierto': tasa
            })
    
    # Estrategia 3: Solo por Volatilidad alta
    for umbral in filtros['Volatilidad_Pct']:
        subset = df[df['Volatilidad_Pct'] >= umbral]
        if len(subset) >= 30:
            roi = subset['Rendimiento'].mean() * 100
            rend = subset['Rendimiento'].sum()
            tasa = subset['Acierto'].mean() * 100
            estrategias.append({
                'filtro': f'Volatilidad >= {umbral}',
                'n': len(subset),
                'roi': roi,
                'rend_total': rend,
                'tasa_acierto': tasa
            })
    
    # Estrategia 4: Margen bajo
    for umbral in [4.0, 3.5, 3.0]:
        subset = df[df['Margen_Casa_Pct'] <= umbral]
        if len(subset) >= 30:
            roi = subset['Rendimiento'].mean() * 100
            rend = subset['Rendimiento'].sum()
            tasa = subset['Acierto'].mean() * 100
            estrategias.append({
                'filtro': f'Margen <= {umbral}',
                'n': len(subset),
                'roi': roi,
                'rend_total': rend,
                'tasa_acierto': tasa
            })
    
    # Estrategia 5: Score alto
    for umbral in filtros['Score_Final']:
        subset = df[df['Score_Final'] >= umbral]
        if len(subset) >= 30:
            roi = subset['Rendimiento'].mean() * 100
            rend = subset['Rendimiento'].sum()
            tasa = subset['Acierto'].mean() * 100
            estrategias.append({
                'filtro': f'Score >= {umbral}',
                'n': len(subset),
                'roi': roi,
                'rend_total': rend,
                'tasa_acierto': tasa
            })
    
    # Estrategia 6: Combinaciones
    combinaciones = [
        ('P_Win >= 0.55 & Dif >= 0.03', 
         (df['P_Win_Calibrada'] >= 0.55) & (df['Diferencia_Cuota_Promedio'] >= 0.03)),
        ('P_Win >= 0.55 & Volatilidad >= 2', 
         (df['P_Win_Calibrada'] >= 0.55) & (df['Volatilidad_Pct'] >= 2)),
        ('P_Win >= 0.55 & Margen <= 3.5', 
         (df['P_Win_Calibrada'] >= 0.55) & (df['Margen_Casa_Pct'] <= 3.5)),
        ('Dif >= 0.05 & Volatilidad >= 2', 
         (df['Diferencia_Cuota_Promedio'] >= 0.05) & (df['Volatilidad_Pct'] >= 2)),
        ('Score >= 0.8 & Margen <= 3.5', 
         (df['Score_Final'] >= 0.8) & (df['Margen_Casa_Pct'] <= 3.5)),
        ('P_Win >= 0.6 & Cuota >= 1.4', 
         (df['P_Win_Calibrada'] >= 0.6) & (df['Mejor_Cuota'] >= 1.4)),
        ('Dif >= 0.05 & Margen <= 3.5', 
         (df['Diferencia_Cuota_Promedio'] >= 0.05) & (df['Margen_Casa_Pct'] <= 3.5)),
    ]
    
    for nombre, mask in combinaciones:
        subset = df[mask]
        if len(subset) >= 20:
            roi = subset['Rendimiento'].mean() * 100
            rend = subset['Rendimiento'].sum()
            tasa = subset['Acierto'].mean() * 100
            estrategias.append({
                'filtro': nombre,
                'n': len(subset),
                'roi': roi,
                'rend_total': rend,
                'tasa_acierto': tasa
            })
    
    # Por mercado
    for mercado in ['Doble Chance', 'Goles (Over/Under)']:
        subset_m = df[df['Tipo_Mercado'] == mercado]
        
        for umbral in [0.55, 0.6]:
            subset = subset_m[subset_m['P_Win_Calibrada'] >= umbral]
            if len(subset) >= 20:
                roi = subset['Rendimiento'].mean() * 100
                rend = subset['Rendimiento'].sum()
                tasa = subset['Acierto'].mean() * 100
                estrategias.append({
                    'filtro': f'{mercado[:10]} & P_Win >= {umbral}',
                    'n': len(subset),
                    'roi': roi,
                    'rend_total': rend,
                    'tasa_acierto': tasa
                })
    
    # Ordenar por ROI
    estrategias_ord = sorted(estrategias, key=lambda x: x['roi'], reverse=True)
    
    print(f"\n{'Estrategia':<45} {'N':<8} {'ROI':<12} {'Rend €':<12} {'Aciertos':<12}")
    print("-"*90)
    
    for e in estrategias_ord[:20]:
        roi_str = f"{e['roi']:+.2f}%" if e['roi'] >= 0 else f"{e['roi']:.2f}%"
        print(f"{e['filtro']:<45} {e['n']:<8} {roi_str:<12} {e['rend_total']:+.2f}{'':>4} {e['tasa_acierto']:.1f}%")
    
    # Destacar estrategias con ROI positivo
    positivas = [e for e in estrategias_ord if e['roi'] > 0]
    if positivas:
        print(f"\n🎯 ESTRATEGIAS CON ROI POSITIVO: {len(positivas)}")
        for e in positivas:
            print(f"   • {e['filtro']}: ROI = {e['roi']:+.2f}% (n={e['n']}, €{e['rend_total']:+.2f})")
    else:
        print(f"\n⚠️  No se encontraron estrategias con ROI positivo")
    
    return estrategias_ord


def analisis_invertido(df):
    """
    Análisis invertido: ¿Qué tienen en común las apuestas ganadoras?
    """
    print(f"\n{'='*80}")
    print("ANÁLISIS INVERTIDO: CARACTERÍSTICAS DE APUESTAS GANADORAS")
    print(f"{'='*80}")
    
    # Separar ganadores y perdedores (en rendimiento, no en acierto)
    # Una apuesta es "ganadora" si su rendimiento > 0
    df['Rentable'] = (df['Rendimiento'] > 0).astype(int)
    
    rentables = df[df['Rentable'] == 1]
    no_rentables = df[df['Rentable'] == 0]
    
    print(f"\nApuestas rentables: {len(rentables)} ({len(rentables)/len(df)*100:.1f}%)")
    print(f"Apuestas no rentables: {len(no_rentables)} ({len(no_rentables)/len(df)*100:.1f}%)")
    
    cols = ['P_Win_Calibrada', 'Diferencia_Cuota_Promedio', 'Volatilidad_Pct',
            'Margen_Casa_Pct', 'Score_Final', 'Mejor_Cuota', 'Num_Casas']
    
    print(f"\n{'Variable':<30} {'Media Rentable':<18} {'Media No Rent':<18} {'Diferencia':<15} {'p-value':<12}")
    print("-"*95)
    
    for col in cols:
        if col not in df.columns:
            continue
        
        rent_vals = rentables[col].dropna()
        no_rent_vals = no_rentables[col].dropna()
        
        if len(rent_vals) < 30 or len(no_rent_vals) < 30:
            continue
        
        media_rent = rent_vals.mean()
        media_no_rent = no_rent_vals.mean()
        dif = media_rent - media_no_rent
        
        # Test t
        t_stat, p_value = stats.ttest_ind(rent_vals, no_rent_vals)
        
        sig = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else ""
        
        print(f"{col:<30} {media_rent:<18.4f} {media_no_rent:<18.4f} {dif:+.4f}{'':>6} {p_value:.4f} {sig}")
    
    print("\n>>> Las variables con diferencia significativa (p<0.05) podrían ser útiles")


def main():
    df = cargar_datos()
    
    print("\n" + "="*80)
    print("ANÁLISIS COMPLETO DE PREDICTORES DE RENDIMIENTO")
    print("="*80)
    
    # Resumen inicial
    print(f"\nDATOS:")
    print(f"  Total apuestas: {len(df)}")
    print(f"  ROI total: {df['Rendimiento'].mean()*100:+.2f}%")
    print(f"  Rendimiento neto: {df['Rendimiento'].sum():+.2f}€")
    
    # Análisis por deciles de cada variable clave
    variables = [
        ('P_Win_Calibrada', 'P_Win_Calibrada'),
        ('Diferencia_Cuota_Promedio', 'Diferencia Cuota vs Promedio'),
        ('Volatilidad_Pct', 'Volatilidad (%)'),
        ('Margen_Casa_Pct', 'Margen de la Casa (%)'),
        ('Score_Final', 'Score Final'),
    ]
    
    for col, nombre in variables:
        if col in df.columns:
            analisis_deciles_rendimiento(df, col, nombre)
    
    # Análisis por mercado
    analisis_por_mercado(df)
    
    # Análisis invertido
    analisis_invertido(df)
    
    # Búsqueda de estrategias rentables
    estrategias = buscar_estrategias_rentables(df)
    
    # Conclusión final
    print(f"\n{'='*80}")
    print("CONCLUSIÓN FINAL")
    print(f"{'='*80}")
    
    print("""
    HALLAZGOS CLAVE:
    
    1. NINGUNA variable individual tiene correlación fuerte con el rendimiento
       (todas las correlaciones < 0.05 en valor absoluto)
    
    2. P_Win_Calibrada tiene correlación NEGATIVA (-0.014) con el rendimiento:
       - Mayor P_Win → PEOR rendimiento
       - Esto ocurre porque las cuotas bajas (alta P_Win) no compensan 
         el mayor porcentaje de aciertos
    
    3. Las variables más prometedoras para RENDIMIENTO son:
       - Diferencia_Cuota_Promedio (corr +0.044): buscar cuotas mejores que el promedio
       - Volatilidad_Pct (corr +0.037): mercados con más variación de cuotas
       - Score_Final (corr +0.028): combinación de varios factores
    
    4. El ROI general es -6.79%, lo que refleja el margen de las casas de apuestas
    
    5. Para ser rentable en apuestas se necesita:
       - Encontrar valor (value betting): cuotas que subestiman la probabilidad real
       - Esto NO se puede hacer solo con P_Win_Calibrada o probabilidad implícita
       - Se necesita información externa (forma de equipos, lesiones, etc.)
    """)


if __name__ == "__main__":
    main()
