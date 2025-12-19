#!/usr/bin/env python3
"""
ANÁLISIS DE PREDICTORES DE RENDIMIENTO POR TIPO DE MERCADO

Analiza cada variable como predictor de rendimiento, separado por mercado.
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
    
    # Convertir columnas numéricas
    cols = ['P_Win_Calibrada', 'Confianza', 'Confianza_Calibrada', 'Score_Final',
            'Diferencia_Cuota_Promedio', 'Volatilidad_Pct', 'Margen_Casa_Pct', 'Num_Casas']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df.dropna(subset=['Rendimiento'])


def analizar_variable_rendimiento(df, columna):
    """Analiza una variable como predictor de rendimiento."""
    sub = df.dropna(subset=[columna])
    if len(sub) < 30:
        return None
    
    # Correlación
    corr, p = stats.pearsonr(sub[columna], sub['Rendimiento'])
    
    # ROI por quintiles
    try:
        sub = sub.copy()
        sub['Q'] = pd.qcut(sub[columna], 5, labels=['Q1','Q2','Q3','Q4','Q5'], duplicates='drop')
        
        q5 = sub[sub['Q'] == 'Q5']
        q1 = sub[sub['Q'] == 'Q1']
        
        roi_q5 = q5['Rendimiento'].mean() * 100 if len(q5) > 10 else np.nan
        roi_q1 = q1['Rendimiento'].mean() * 100 if len(q1) > 10 else np.nan
        n_q5 = len(q5)
        n_q1 = len(q1)
        rend_q5 = q5['Rendimiento'].sum() if len(q5) > 0 else 0
    except:
        roi_q5 = roi_q1 = np.nan
        n_q5 = n_q1 = 0
        rend_q5 = 0
    
    return {
        'n': len(sub),
        'corr': corr,
        'p': p,
        'roi_q5': roi_q5,
        'roi_q1': roi_q1,
        'n_q5': n_q5,
        'rend_q5': rend_q5
    }


def analizar_deciles(df, columna, nombre_mercado):
    """Análisis detallado por deciles."""
    sub = df.dropna(subset=[columna]).copy()
    if len(sub) < 50:
        return None
    
    try:
        sub['Decil'] = pd.qcut(sub[columna], 10, labels=range(1,11), duplicates='drop')
    except:
        return None
    
    resultados = []
    for d in range(1, 11):
        dec = sub[sub['Decil'] == d]
        if len(dec) == 0:
            continue
        resultados.append({
            'decil': d,
            'n': len(dec),
            'val_min': dec[columna].min(),
            'val_max': dec[columna].max(),
            'aciertos': dec['Acierto'].mean() * 100,
            'roi': dec['Rendimiento'].mean() * 100,
            'rend_total': dec['Rendimiento'].sum()
        })
    
    return resultados


def buscar_estrategias_mercado(df, nombre_mercado):
    """Busca estrategias rentables para un mercado específico."""
    estrategias = []
    
    # Filtros a probar
    filtros = [
        ('P_Win >= 0.50', df['P_Win_Calibrada'] >= 0.50),
        ('P_Win >= 0.55', df['P_Win_Calibrada'] >= 0.55),
        ('P_Win >= 0.60', df['P_Win_Calibrada'] >= 0.60),
        ('Dif_Cuota >= 0.03', df['Diferencia_Cuota_Promedio'] >= 0.03),
        ('Dif_Cuota >= 0.05', df['Diferencia_Cuota_Promedio'] >= 0.05),
        ('Dif_Cuota >= 0.08', df['Diferencia_Cuota_Promedio'] >= 0.08),
        ('Volatilidad >= 1.5', df['Volatilidad_Pct'] >= 1.5),
        ('Volatilidad >= 2.0', df['Volatilidad_Pct'] >= 2.0),
        ('Volatilidad >= 2.5', df['Volatilidad_Pct'] >= 2.5),
        ('Margen <= 4.0', df['Margen_Casa_Pct'] <= 4.0),
        ('Margen <= 3.5', df['Margen_Casa_Pct'] <= 3.5),
        ('Margen <= 3.0', df['Margen_Casa_Pct'] <= 3.0),
        ('Score >= 0.5', df['Score_Final'] >= 0.5),
        ('Score >= 0.8', df['Score_Final'] >= 0.8),
        ('Cuota >= 1.5', df['Mejor_Cuota'] >= 1.5),
        ('Cuota >= 1.8', df['Mejor_Cuota'] >= 1.8),
        ('Cuota 1.4-2.0', (df['Mejor_Cuota'] >= 1.4) & (df['Mejor_Cuota'] <= 2.0)),
        ('Num_Casas >= 3', df['Num_Casas'] >= 3),
        ('Num_Casas >= 4', df['Num_Casas'] >= 4),
    ]
    
    # Combinaciones
    combinaciones = [
        ('P_Win >= 0.55 & Dif >= 0.03', 
         (df['P_Win_Calibrada'] >= 0.55) & (df['Diferencia_Cuota_Promedio'] >= 0.03)),
        ('P_Win >= 0.55 & Vol >= 1.5', 
         (df['P_Win_Calibrada'] >= 0.55) & (df['Volatilidad_Pct'] >= 1.5)),
        ('P_Win >= 0.55 & Margen <= 3.5', 
         (df['P_Win_Calibrada'] >= 0.55) & (df['Margen_Casa_Pct'] <= 3.5)),
        ('P_Win >= 0.60 & Dif >= 0.03', 
         (df['P_Win_Calibrada'] >= 0.60) & (df['Diferencia_Cuota_Promedio'] >= 0.03)),
        ('Dif >= 0.05 & Vol >= 1.5', 
         (df['Diferencia_Cuota_Promedio'] >= 0.05) & (df['Volatilidad_Pct'] >= 1.5)),
        ('Dif >= 0.05 & Margen <= 3.5', 
         (df['Diferencia_Cuota_Promedio'] >= 0.05) & (df['Margen_Casa_Pct'] <= 3.5)),
        ('Vol >= 2.0 & Margen <= 4.0', 
         (df['Volatilidad_Pct'] >= 2.0) & (df['Margen_Casa_Pct'] <= 4.0)),
        ('Score >= 0.5 & Margen <= 3.5', 
         (df['Score_Final'] >= 0.5) & (df['Margen_Casa_Pct'] <= 3.5)),
        ('Cuota 1.5-2.0 & Dif >= 0.03', 
         (df['Mejor_Cuota'] >= 1.5) & (df['Mejor_Cuota'] <= 2.0) & (df['Diferencia_Cuota_Promedio'] >= 0.03)),
        ('P_Win >= 0.55 & Cuota >= 1.5', 
         (df['P_Win_Calibrada'] >= 0.55) & (df['Mejor_Cuota'] >= 1.5)),
        ('Dif >= 0.03 & Num_Casas >= 3', 
         (df['Diferencia_Cuota_Promedio'] >= 0.03) & (df['Num_Casas'] >= 3)),
    ]
    
    for nombre, mask in filtros + combinaciones:
        try:
            subset = df[mask]
            if len(subset) >= 15:
                roi = subset['Rendimiento'].mean() * 100
                rend = subset['Rendimiento'].sum()
                tasa = subset['Acierto'].mean() * 100
                estrategias.append({
                    'filtro': nombre,
                    'n': len(subset),
                    'roi': roi,
                    'rend': rend,
                    'tasa': tasa
                })
        except:
            pass
    
    return sorted(estrategias, key=lambda x: x['roi'], reverse=True)


def main():
    df = cargar_datos()
    
    print("\n" + "="*100)
    print("  ANÁLISIS DE PREDICTORES DE RENDIMIENTO POR TIPO DE MERCADO")
    print("="*100)
    
    # Variables a analizar
    variables = [
        ('P_Win_Calibrada', 'P_Win_Calibrada'),
        ('Confianza', 'Confianza'),
        ('Score_Final', 'Score_Final'),
        ('Diferencia_Cuota_Promedio', 'Dif_Cuota_Prom'),
        ('Volatilidad_Pct', 'Volatilidad'),
        ('Margen_Casa_Pct', 'Margen_Casa'),
        ('Num_Casas', 'Num_Casas'),
        ('Mejor_Cuota', 'Mejor_Cuota'),
    ]
    
    mercados = df['Tipo_Mercado'].unique()
    
    for mercado in mercados:
        df_mercado = df[df['Tipo_Mercado'] == mercado].copy()
        
        if len(df_mercado) < 50:
            continue
        
        roi_mercado = df_mercado['Rendimiento'].mean() * 100
        rend_mercado = df_mercado['Rendimiento'].sum()
        
        print(f"\n{'='*100}")
        print(f"  MERCADO: {mercado}")
        print(f"  N={len(df_mercado)} | Aciertos={df_mercado['Acierto'].mean()*100:.1f}% | ROI={roi_mercado:+.2f}% | Rend={rend_mercado:+.2f}€")
        print(f"{'='*100}")
        
        # Tabla de correlaciones
        print(f"\n{'Variable':<20} {'N':<7} {'Corr':<10} {'p-value':<12} {'ROI Q5':<12} {'ROI Q1':<12} {'Rend Q5':<10}")
        print("-"*90)
        
        resultados_vars = []
        for col, nombre in variables:
            if col not in df_mercado.columns:
                continue
            
            res = analizar_variable_rendimiento(df_mercado, col)
            if res is None:
                continue
            
            resultados_vars.append((nombre, res))
            
            sig = "***" if res['p'] < 0.001 else "**" if res['p'] < 0.01 else "*" if res['p'] < 0.05 else ""
            roi_q5_str = f"{res['roi_q5']:+.2f}%" if not np.isnan(res['roi_q5']) else "N/A"
            roi_q1_str = f"{res['roi_q1']:+.2f}%" if not np.isnan(res['roi_q1']) else "N/A"
            
            print(f"{nombre:<20} {res['n']:<7} {res['corr']:+.4f}{sig:<3} {res['p']:<12.4f} {roi_q5_str:<12} {roi_q1_str:<12} {res['rend_q5']:+.2f}€")
        
        # Destacar la mejor variable
        if resultados_vars:
            mejor = max(resultados_vars, key=lambda x: x[1]['corr'])
            if mejor[1]['corr'] > 0.05:
                print(f"\n✓ Mejor predictor: {mejor[0]} (corr={mejor[1]['corr']:+.4f})")
            
            # Variables con ROI Q5 positivo
            positivos = [(n, r) for n, r in resultados_vars if not np.isnan(r['roi_q5']) and r['roi_q5'] > 0]
            if positivos:
                print(f"\n🎯 Variables con ROI Q5 POSITIVO:")
                for nombre, res in positivos:
                    print(f"   • {nombre}: ROI Q5 = {res['roi_q5']:+.2f}% (n={res['n_q5']}, rend={res['rend_q5']:+.2f}€)")
        
        # Análisis detallado de las mejores variables
        print(f"\n--- Análisis por Deciles ---")
        
        mejores_vars = ['Diferencia_Cuota_Promedio', 'Volatilidad_Pct', 'P_Win_Calibrada']
        for col in mejores_vars:
            if col not in df_mercado.columns:
                continue
            
            deciles = analizar_deciles(df_mercado, col, mercado)
            if deciles is None or len(deciles) < 5:
                continue
            
            # Solo mostrar si hay algún decil positivo
            positivos = [d for d in deciles if d['roi'] > 0]
            if positivos:
                print(f"\n{col}:")
                print(f"  {'Decil':<8} {'N':<6} {'Rango Valor':<20} {'Aciertos':<12} {'ROI':<12} {'Rend Total'}")
                print("  " + "-"*75)
                for d in deciles:
                    roi_mark = "✓" if d['roi'] > 0 else ""
                    print(f"  D{d['decil']:<7} {d['n']:<6} {d['val_min']:.4f}-{d['val_max']:.4f}{'':>4} {d['aciertos']:>6.1f}%{'':>4} {d['roi']:+.2f}%{'':>4} {d['rend_total']:+.2f}€ {roi_mark}")
        
        # Búsqueda de estrategias
        print(f"\n--- Estrategias Rentables ---")
        estrategias = buscar_estrategias_mercado(df_mercado, mercado)
        
        # Mostrar top 10
        print(f"\n{'Estrategia':<40} {'N':<8} {'ROI':<12} {'Rend €':<12} {'Aciertos':<10}")
        print("-"*85)
        
        for e in estrategias[:15]:
            roi_str = f"{e['roi']:+.2f}%"
            marca = "🎯" if e['roi'] > 0 else ""
            print(f"{e['filtro']:<40} {e['n']:<8} {roi_str:<12} {e['rend']:+.2f}{'':>4} {e['tasa']:.1f}% {marca}")
        
        # Destacar estrategias con ROI positivo
        positivas = [e for e in estrategias if e['roi'] > 0]
        if positivas:
            print(f"\n🏆 ESTRATEGIAS CON ROI POSITIVO EN {mercado.upper()}:")
            for e in positivas:
                print(f"   • {e['filtro']}: ROI={e['roi']:+.2f}% (n={e['n']}, €{e['rend']:+.2f})")
    
    # Resumen final
    print("\n" + "="*100)
    print("  RESUMEN FINAL: MEJORES ESTRATEGIAS POR MERCADO")
    print("="*100)
    
    for mercado in mercados:
        df_mercado = df[df['Tipo_Mercado'] == mercado].copy()
        if len(df_mercado) < 50:
            continue
        
        estrategias = buscar_estrategias_mercado(df_mercado, mercado)
        positivas = [e for e in estrategias if e['roi'] > 0]
        
        print(f"\n{mercado}:")
        if positivas:
            mejor = positivas[0]
            print(f"   ✅ MEJOR: {mejor['filtro']}")
            print(f"      ROI: {mejor['roi']:+.2f}% | N: {mejor['n']} | Rend: {mejor['rend']:+.2f}€ | Aciertos: {mejor['tasa']:.1f}%")
        else:
            print(f"   ❌ No se encontraron estrategias con ROI positivo")


if __name__ == "__main__":
    main()
