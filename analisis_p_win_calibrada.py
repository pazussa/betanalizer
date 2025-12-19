#!/usr/bin/env python3
"""
Análisis exhaustivo de P_Win_Calibrada como predictor de aciertos.

Este script verifica si P_Win_Calibrada tiene correlación real con los resultados
y es un predictor útil para las apuestas.
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
from sklearn.calibration import calibration_curve
import warnings
warnings.filterwarnings('ignore')

def cargar_datos():
    """Carga y prepara los datos del histórico."""
    df = pd.read_csv('data/historico_completo.csv')
    
    # Filtrar solo registros con resultado definido
    df_analisis = df[df['Resultado'].isin(['Acertado', 'Fallido'])].copy()
    
    # Crear variable binaria de acierto
    df_analisis['Acierto'] = (df_analisis['Resultado'] == 'Acertado').astype(int)
    
    # Asegurar que P_Win_Calibrada sea numérica
    df_analisis['P_Win_Calibrada'] = pd.to_numeric(df_analisis['P_Win_Calibrada'], errors='coerce')
    
    # Eliminar valores nulos
    df_analisis = df_analisis.dropna(subset=['P_Win_Calibrada', 'Acierto'])
    
    return df_analisis


def test_correlacion(df):
    """
    Test 1: Correlación estadística entre P_Win_Calibrada y Aciertos
    """
    print("\n" + "="*80)
    print("TEST 1: CORRELACIÓN ESTADÍSTICA")
    print("="*80)
    
    # Correlación de Pearson
    corr_pearson, p_value_pearson = stats.pearsonr(df['P_Win_Calibrada'], df['Acierto'])
    
    # Correlación de Spearman (más robusta para datos no normales)
    corr_spearman, p_value_spearman = stats.spearmanr(df['P_Win_Calibrada'], df['Acierto'])
    
    # Correlación Point-Biserial (específica para variable binaria)
    corr_pb, p_value_pb = stats.pointbiserialr(df['Acierto'], df['P_Win_Calibrada'])
    
    print(f"\nCorrelación de Pearson:           r = {corr_pearson:.4f}, p-value = {p_value_pearson:.6f}")
    print(f"Correlación de Spearman:          ρ = {corr_spearman:.4f}, p-value = {p_value_spearman:.6f}")
    print(f"Correlación Point-Biserial:       r = {corr_pb:.4f}, p-value = {p_value_pb:.6f}")
    
    # Interpretación
    print("\n>>> INTERPRETACIÓN:")
    if abs(corr_pearson) < 0.1:
        print("   - Correlación MUY DÉBIL o inexistente")
    elif abs(corr_pearson) < 0.3:
        print("   - Correlación DÉBIL")
    elif abs(corr_pearson) < 0.5:
        print("   - Correlación MODERADA")
    else:
        print("   - Correlación FUERTE")
    
    if p_value_pearson < 0.05:
        print("   - La correlación ES estadísticamente significativa (p < 0.05)")
    else:
        print("   - La correlación NO es estadísticamente significativa (p >= 0.05)")
    
    return corr_pearson, p_value_pearson


def test_auc_roc(df):
    """
    Test 2: AUC-ROC - Capacidad discriminativa
    """
    print("\n" + "="*80)
    print("TEST 2: AUC-ROC (Capacidad Discriminativa)")
    print("="*80)
    
    auc = roc_auc_score(df['Acierto'], df['P_Win_Calibrada'])
    
    print(f"\nAUC-ROC: {auc:.4f}")
    
    print("\n>>> INTERPRETACIÓN:")
    if auc < 0.5:
        print("   - PEOR que aleatorio (predicción inversa)")
    elif auc == 0.5:
        print("   - IGUAL a aleatorio (sin poder predictivo)")
    elif auc < 0.6:
        print("   - Capacidad discriminativa MUY POBRE")
    elif auc < 0.7:
        print("   - Capacidad discriminativa POBRE")
    elif auc < 0.8:
        print("   - Capacidad discriminativa ACEPTABLE")
    elif auc < 0.9:
        print("   - Capacidad discriminativa BUENA")
    else:
        print("   - Capacidad discriminativa EXCELENTE")
    
    # Test de significancia del AUC
    # Bootstrap para intervalo de confianza
    n_bootstraps = 1000
    rng = np.random.RandomState(42)
    bootstrapped_aucs = []
    
    for i in range(n_bootstraps):
        indices = rng.randint(0, len(df), len(df))
        if len(np.unique(df['Acierto'].iloc[indices])) < 2:
            continue
        score = roc_auc_score(df['Acierto'].iloc[indices], 
                             df['P_Win_Calibrada'].iloc[indices])
        bootstrapped_aucs.append(score)
    
    ci_lower = np.percentile(bootstrapped_aucs, 2.5)
    ci_upper = np.percentile(bootstrapped_aucs, 97.5)
    
    print(f"\n   Intervalo de confianza 95%: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    if ci_lower > 0.5:
        print("   - El IC NO incluye 0.5, hay evidencia de poder predictivo")
    else:
        print("   - El IC incluye 0.5, NO hay evidencia clara de poder predictivo")
    
    return auc, ci_lower, ci_upper


def test_calibracion(df):
    """
    Test 3: Calibración - ¿Las probabilidades predichas reflejan frecuencias reales?
    """
    print("\n" + "="*80)
    print("TEST 3: CALIBRACIÓN DE PROBABILIDADES")
    print("="*80)
    
    # Brier Score
    brier = brier_score_loss(df['Acierto'], df['P_Win_Calibrada'])
    
    # Brier Score de un modelo baseline (siempre predice la media)
    baseline_prob = df['Acierto'].mean()
    brier_baseline = brier_score_loss(df['Acierto'], [baseline_prob] * len(df))
    
    # Brier Skill Score
    bss = 1 - (brier / brier_baseline)
    
    print(f"\nBrier Score:           {brier:.4f} (menor es mejor, 0 = perfecto)")
    print(f"Brier Score Baseline:  {brier_baseline:.4f}")
    print(f"Brier Skill Score:     {bss:.4f} (> 0 indica mejora sobre baseline)")
    
    # Curva de calibración por bins
    print("\n>>> ANÁLISIS POR RANGOS DE P_Win_Calibrada:")
    print("-" * 70)
    
    bins = [0, 0.35, 0.45, 0.50, 0.55, 0.65, 1.0]
    labels = ['<35%', '35-45%', '45-50%', '50-55%', '55-65%', '>65%']
    
    df['Bin_P'] = pd.cut(df['P_Win_Calibrada'], bins=bins, labels=labels)
    
    print(f"{'Rango P_Win':<12} {'N':<8} {'Aciertos':<10} {'Tasa Real':<12} {'P_Win Media':<12} {'Diferencia':<12}")
    print("-" * 70)
    
    calibracion_ok = True
    for label in labels:
        subset = df[df['Bin_P'] == label]
        if len(subset) > 0:
            n = len(subset)
            aciertos = subset['Acierto'].sum()
            tasa_real = subset['Acierto'].mean()
            p_win_media = subset['P_Win_Calibrada'].mean()
            diferencia = tasa_real - p_win_media
            
            print(f"{label:<12} {n:<8} {aciertos:<10} {tasa_real:.2%}{'':>4} {p_win_media:.2%}{'':>4} {diferencia:+.2%}")
            
            # Si la diferencia es muy grande, la calibración es mala
            if abs(diferencia) > 0.15:
                calibracion_ok = False
    
    print("\n>>> INTERPRETACIÓN:")
    if bss > 0:
        print(f"   - BSS > 0: P_Win_Calibrada ES MEJOR que predecir siempre la media")
    else:
        print(f"   - BSS <= 0: P_Win_Calibrada NO MEJORA sobre predecir siempre la media")
    
    if calibracion_ok:
        print("   - Las probabilidades están razonablemente calibradas")
    else:
        print("   - Las probabilidades NO están bien calibradas (grandes desviaciones)")
    
    return brier, bss


def test_grupos_extremos(df):
    """
    Test 4: ¿Los grupos con P_Win alta tienen más aciertos que los de P_Win baja?
    """
    print("\n" + "="*80)
    print("TEST 4: COMPARACIÓN DE GRUPOS EXTREMOS")
    print("="*80)
    
    # Dividir en cuartiles
    q25 = df['P_Win_Calibrada'].quantile(0.25)
    q75 = df['P_Win_Calibrada'].quantile(0.75)
    
    grupo_bajo = df[df['P_Win_Calibrada'] <= q25]
    grupo_alto = df[df['P_Win_Calibrada'] >= q75]
    grupo_medio = df[(df['P_Win_Calibrada'] > q25) & (df['P_Win_Calibrada'] < q75)]
    
    tasa_bajo = grupo_bajo['Acierto'].mean()
    tasa_medio = grupo_medio['Acierto'].mean()
    tasa_alto = grupo_alto['Acierto'].mean()
    
    print(f"\nCuartil Inferior (P_Win <= {q25:.2%}):")
    print(f"   N = {len(grupo_bajo)}, Tasa de aciertos = {tasa_bajo:.2%}")
    
    print(f"\nCuartiles Medios ({q25:.2%} < P_Win < {q75:.2%}):")
    print(f"   N = {len(grupo_medio)}, Tasa de aciertos = {tasa_medio:.2%}")
    
    print(f"\nCuartil Superior (P_Win >= {q75:.2%}):")
    print(f"   N = {len(grupo_alto)}, Tasa de aciertos = {tasa_alto:.2%}")
    
    # Test estadístico: ¿Hay diferencia significativa entre grupos?
    from scipy.stats import chi2_contingency
    
    contingency = np.array([
        [grupo_bajo['Acierto'].sum(), len(grupo_bajo) - grupo_bajo['Acierto'].sum()],
        [grupo_alto['Acierto'].sum(), len(grupo_alto) - grupo_alto['Acierto'].sum()]
    ])
    
    chi2, p_value, dof, expected = chi2_contingency(contingency)
    
    print(f"\nTest Chi-cuadrado (grupo bajo vs alto):")
    print(f"   χ² = {chi2:.4f}, p-value = {p_value:.6f}")
    
    print("\n>>> INTERPRETACIÓN:")
    if tasa_alto > tasa_bajo:
        print("   - El grupo con P_Win alta tiene MÁS aciertos (dirección correcta)")
    else:
        print("   - ⚠️ El grupo con P_Win alta tiene MENOS aciertos (dirección incorrecta)")
    
    diferencia = tasa_alto - tasa_bajo
    print(f"   - Diferencia en tasa de aciertos: {diferencia:+.2%}")
    
    if p_value < 0.05:
        print("   - La diferencia ES estadísticamente significativa")
    else:
        print("   - La diferencia NO es estadísticamente significativa")
    
    return tasa_bajo, tasa_alto, p_value


def test_regresion_logistica(df):
    """
    Test 5: Regresión logística - ¿P_Win_Calibrada predice significativamente los aciertos?
    """
    print("\n" + "="*80)
    print("TEST 5: REGRESIÓN LOGÍSTICA")
    print("="*80)
    
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    
    X = df[['P_Win_Calibrada']].values
    y = df['Acierto'].values
    
    # Modelo
    model = LogisticRegression(random_state=42)
    model.fit(X, y)
    
    coef = model.coef_[0][0]
    intercept = model.intercept_[0]
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    cv_auc = cross_val_score(model, X, y, cv=5, scoring='roc_auc')
    
    print(f"\nCoeficiente: {coef:.4f}")
    print(f"Intercepto:  {intercept:.4f}")
    print(f"\nAccuracy (CV 5-fold): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"AUC-ROC (CV 5-fold):  {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")
    
    # Comparar con modelo baseline (predecir siempre la clase mayoritaria)
    baseline_acc = max(df['Acierto'].mean(), 1 - df['Acierto'].mean())
    
    print(f"\nBaseline accuracy:    {baseline_acc:.4f}")
    
    print("\n>>> INTERPRETACIÓN:")
    if coef > 0:
        print("   - Coeficiente positivo: Mayor P_Win → Mayor probabilidad de acierto ✓")
    else:
        print("   - ⚠️ Coeficiente negativo: Mayor P_Win → MENOR probabilidad de acierto")
    
    if cv_scores.mean() > baseline_acc:
        print(f"   - El modelo MEJORA sobre el baseline ({cv_scores.mean():.4f} vs {baseline_acc:.4f})")
    else:
        print(f"   - El modelo NO mejora sobre el baseline")
    
    return coef, cv_scores.mean(), cv_auc.mean()


def test_comparacion_predictor_aleatorio(df):
    """
    Test 6: Comparación con un predictor aleatorio
    """
    print("\n" + "="*80)
    print("TEST 6: COMPARACIÓN CON PREDICTOR ALEATORIO")
    print("="*80)
    
    # Log loss de P_Win_Calibrada
    ll_model = log_loss(df['Acierto'], df['P_Win_Calibrada'])
    
    # Log loss de predictor aleatorio (probabilidad uniforme 0.5)
    ll_random = log_loss(df['Acierto'], [0.5] * len(df))
    
    # Log loss de baseline (siempre la media)
    baseline_prob = df['Acierto'].mean()
    ll_baseline = log_loss(df['Acierto'], [baseline_prob] * len(df))
    
    print(f"\nLog Loss P_Win_Calibrada: {ll_model:.4f}")
    print(f"Log Loss aleatorio (0.5): {ll_random:.4f}")
    print(f"Log Loss baseline (media): {ll_baseline:.4f}")
    
    print("\n>>> INTERPRETACIÓN:")
    if ll_model < ll_random:
        print("   - P_Win_Calibrada es MEJOR que predicción aleatoria")
    else:
        print("   - ⚠️ P_Win_Calibrada es IGUAL o PEOR que predicción aleatoria")
    
    if ll_model < ll_baseline:
        print("   - P_Win_Calibrada es MEJOR que siempre predecir la media")
    else:
        print("   - ⚠️ P_Win_Calibrada NO mejora sobre predecir siempre la media")
    
    return ll_model, ll_random, ll_baseline


def analisis_por_mercado(df):
    """
    Test 7: Análisis separado por tipo de mercado
    """
    print("\n" + "="*80)
    print("TEST 7: ANÁLISIS POR TIPO DE MERCADO")
    print("="*80)
    
    mercados = df['Tipo_Mercado'].unique()
    
    print(f"\n{'Mercado':<30} {'N':<8} {'Corr':<10} {'AUC':<10} {'Tasa Acierto':<15}")
    print("-" * 75)
    
    for mercado in mercados:
        subset = df[df['Tipo_Mercado'] == mercado]
        if len(subset) < 30:  # Mínimo para análisis
            continue
        
        corr, _ = stats.pearsonr(subset['P_Win_Calibrada'], subset['Acierto'])
        
        try:
            auc = roc_auc_score(subset['Acierto'], subset['P_Win_Calibrada'])
        except:
            auc = 0.5
        
        tasa = subset['Acierto'].mean()
        
        print(f"{mercado:<30} {len(subset):<8} {corr:+.4f}{'':>2} {auc:.4f}{'':>2} {tasa:.2%}")


def test_consistencia_temporal(df):
    """
    Test 8: ¿La relación es consistente en el tiempo?
    """
    print("\n" + "="*80)
    print("TEST 8: CONSISTENCIA TEMPORAL")
    print("="*80)
    
    # Convertir fecha
    df['Fecha'] = pd.to_datetime(df['Fecha_Hora_Colombia'], errors='coerce')
    df = df.dropna(subset=['Fecha'])
    
    # Dividir en mitades temporales
    fecha_mediana = df['Fecha'].median()
    
    primera_mitad = df[df['Fecha'] < fecha_mediana]
    segunda_mitad = df[df['Fecha'] >= fecha_mediana]
    
    if len(primera_mitad) > 30 and len(segunda_mitad) > 30:
        corr1, _ = stats.pearsonr(primera_mitad['P_Win_Calibrada'], primera_mitad['Acierto'])
        corr2, _ = stats.pearsonr(segunda_mitad['P_Win_Calibrada'], segunda_mitad['Acierto'])
        
        try:
            auc1 = roc_auc_score(primera_mitad['Acierto'], primera_mitad['P_Win_Calibrada'])
            auc2 = roc_auc_score(segunda_mitad['Acierto'], segunda_mitad['P_Win_Calibrada'])
        except:
            auc1 = auc2 = 0.5
        
        print(f"\nPrimera mitad (antes de {fecha_mediana.strftime('%Y-%m-%d')}):")
        print(f"   N = {len(primera_mitad)}, Correlación = {corr1:+.4f}, AUC = {auc1:.4f}")
        
        print(f"\nSegunda mitad (desde {fecha_mediana.strftime('%Y-%m-%d')}):")
        print(f"   N = {len(segunda_mitad)}, Correlación = {corr2:+.4f}, AUC = {auc2:.4f}")
        
        print("\n>>> INTERPRETACIÓN:")
        if (corr1 > 0 and corr2 > 0) or (auc1 > 0.5 and auc2 > 0.5):
            print("   - La relación es CONSISTENTE en el tiempo")
        else:
            print("   - ⚠️ La relación NO es consistente en el tiempo")
    else:
        print("   Datos insuficientes para análisis temporal")


def resumen_final(resultados):
    """
    Genera un resumen con la conclusión final
    """
    print("\n" + "="*80)
    print("RESUMEN FINAL Y CONCLUSIÓN")
    print("="*80)
    
    # Criterios de evaluación
    criterios = {
        'Correlación significativa': resultados['p_value'] < 0.05 and resultados['correlacion'] > 0,
        'AUC > 0.5 con IC': resultados['auc_lower'] > 0.5,
        'Mejor que baseline': resultados['bss'] > 0,
        'Grupos extremos diferentes': resultados['p_value_grupos'] < 0.05 and resultados['tasa_alta'] > resultados['tasa_baja'],
        'Coeficiente positivo': resultados['coef_logit'] > 0,
        'Mejor que aleatorio': resultados['ll_model'] < resultados['ll_random']
    }
    
    print("\n>>> CHECKLIST DE VALIDACIÓN:")
    cumplidos = 0
    for criterio, cumple in criterios.items():
        emoji = "✓" if cumple else "✗"
        print(f"   [{emoji}] {criterio}")
        if cumple:
            cumplidos += 1
    
    print(f"\n>>> RESULTADO: {cumplidos}/{len(criterios)} criterios cumplidos")
    
    print("\n>>> CONCLUSIÓN:")
    if cumplidos >= 5:
        print("   P_Win_Calibrada ES un predictor EFECTIVO de aciertos.")
        print("   Hay evidencia estadística de correlación significativa.")
    elif cumplidos >= 3:
        print("   P_Win_Calibrada tiene capacidad predictiva DÉBIL.")
        print("   Puede ser útil como factor, pero no como predictor único.")
    else:
        print("   ⚠️ P_Win_Calibrada NO es un predictor efectivo de aciertos.")
        print("   No hay evidencia suficiente de correlación con los resultados.")


def main():
    print("\n" + "="*80)
    print("ANÁLISIS EXHAUSTIVO: P_Win_Calibrada COMO PREDICTOR DE ACIERTOS")
    print("="*80)
    
    # Cargar datos
    df = cargar_datos()
    
    print(f"\nDatos cargados:")
    print(f"   - Total de registros con resultado: {len(df)}")
    print(f"   - Aciertos: {df['Acierto'].sum()} ({df['Acierto'].mean():.2%})")
    print(f"   - Fallidos: {len(df) - df['Acierto'].sum()} ({1 - df['Acierto'].mean():.2%})")
    print(f"   - P_Win_Calibrada: min={df['P_Win_Calibrada'].min():.4f}, max={df['P_Win_Calibrada'].max():.4f}, mean={df['P_Win_Calibrada'].mean():.4f}")
    
    # Ejecutar todos los tests
    resultados = {}
    
    corr, p_value = test_correlacion(df)
    resultados['correlacion'] = corr
    resultados['p_value'] = p_value
    
    auc, auc_lower, auc_upper = test_auc_roc(df)
    resultados['auc'] = auc
    resultados['auc_lower'] = auc_lower
    resultados['auc_upper'] = auc_upper
    
    brier, bss = test_calibracion(df)
    resultados['brier'] = brier
    resultados['bss'] = bss
    
    tasa_baja, tasa_alta, p_value_grupos = test_grupos_extremos(df)
    resultados['tasa_baja'] = tasa_baja
    resultados['tasa_alta'] = tasa_alta
    resultados['p_value_grupos'] = p_value_grupos
    
    coef, acc, auc_cv = test_regresion_logistica(df)
    resultados['coef_logit'] = coef
    resultados['acc_cv'] = acc
    resultados['auc_cv'] = auc_cv
    
    ll_model, ll_random, ll_baseline = test_comparacion_predictor_aleatorio(df)
    resultados['ll_model'] = ll_model
    resultados['ll_random'] = ll_random
    resultados['ll_baseline'] = ll_baseline
    
    analisis_por_mercado(df)
    test_consistencia_temporal(df)
    
    # Resumen final
    resumen_final(resultados)


if __name__ == "__main__":
    main()
