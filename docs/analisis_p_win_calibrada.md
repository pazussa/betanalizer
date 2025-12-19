# Análisis de P_Win_Calibrada como Predictor de Aciertos

**Fecha:** 18 de diciembre de 2025  
**Objetivo:** Verificar si P_Win_Calibrada es realmente un predictor útil de aciertos

## Resumen Ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿P_Win_Calibrada tiene correlación con aciertos? | ✅ Sí (r = +0.23, p < 0.001) |
| ¿Es estadísticamente significativa? | ✅ Sí |
| ¿Es un predictor ÚTIL? | ⚠️ **No independientemente** |
| ¿Por qué? | Está 89% correlacionada con la probabilidad implícita (1/cuota) |

## Metodología

Se realizaron 8 tests estadísticos exhaustivos sobre 1,756 registros históricos con resultados verificados:

1. **Correlación estadística** (Pearson, Spearman, Point-Biserial)
2. **AUC-ROC** con intervalos de confianza bootstrap
3. **Calibración de probabilidades** (Brier Score)
4. **Comparación de grupos extremos** (Chi-cuadrado)
5. **Regresión logística** con cross-validation
6. **Comparación con predictor aleatorio** (Log Loss)
7. **Análisis por tipo de mercado**
8. **Consistencia temporal**

## Resultados Principales

### Test 1: Correlación Estadística

| Métrica | Valor | p-value |
|---------|-------|---------|
| Correlación de Pearson | +0.2310 | < 0.0001 |
| Correlación de Spearman | +0.2485 | < 0.0001 |
| Correlación Point-Biserial | +0.2310 | < 0.0001 |

**Interpretación:** Correlación DÉBIL pero estadísticamente significativa.

### Test 2: Capacidad Discriminativa (AUC-ROC)

- **AUC-ROC:** 0.6445
- **Intervalo de confianza 95%:** [0.6182, 0.6694]

**Interpretación:** 
- El IC no incluye 0.5, hay evidencia de poder predictivo
- Pero AUC < 0.7 indica capacidad discriminativa POBRE

### Test 3: Calibración

| Rango P_Win | N | Tasa Real | P_Win Media | Diferencia |
|-------------|---|-----------|-------------|------------|
| <35% | 26 | 30.77% | 25.84% | +4.93% |
| 35-45% | 73 | 36.99% | 41.77% | -4.79% |
| 45-50% | 227 | 44.93% | 48.20% | -3.26% |
| 50-55% | 511 | 46.97% | 52.45% | -5.48% |
| 55-65% | 880 | 65.00% | 59.66% | +5.34% |
| >65% | 39 | 84.62% | 65.56% | +19.05% |

**Brier Skill Score:** 0.0442 (> 0 indica mejora sobre baseline)

### Test 4: Grupos Extremos

| Grupo | N | Tasa de Aciertos |
|-------|---|------------------|
| Cuartil Inferior (P_Win ≤ 51.14%) | 439 | 40.77% |
| Cuartil Superior (P_Win ≥ 59.98%) | 439 | 73.12% |

**Chi-cuadrado:** χ² = 92.36, p < 0.0001  
**Diferencia:** +32.35% (significativa)

### Test 5: Regresión Logística

- **Coeficiente:** +4.67 (positivo = dirección correcta)
- **Accuracy CV:** 58.83% vs baseline 55.92%
- **AUC CV:** 0.6451

## El Problema: Redundancia

### Hallazgo Crítico

| Comparación | P_Win_Calibrada | Prob. Implícita (1/cuota) |
|-------------|-----------------|---------------------------|
| Correlación con Acierto | +0.2310 | **+0.2770** |
| AUC-ROC | 0.6445 | **0.6615** |

**Correlación entre P_Win_Calibrada y Prob_Implícita: 0.8870 (89%)**

### Análisis de Residuos

Si descomponemos P_Win_Calibrada en:
```
P_Win_Calibrada = f(Prob_Implícita) + Residuo
```

El **Residuo** (información "adicional" de P_Win_Calibrada) tiene:
- Correlación con Acierto: -0.0318
- p-value: 0.1833 (NO significativo)

**Conclusión:** El residuo NO tiene correlación significativa con los aciertos. P_Win_Calibrada no añade información útil más allá de la probabilidad implícita.

### Análisis por Tipo de Mercado

| Mercado | N | AUC P_Win | AUC Prob_Imp | Mejor |
|---------|---|-----------|--------------|-------|
| Goles (Over/Under) | 778 | 0.5525 | **0.6048** | Prob_Imp |
| Doble Chance | 978 | 0.6748 | **0.6859** | Prob_Imp |

En **todos** los mercados, la probabilidad implícita predice igual o mejor.

### Test de Valor Incremental

| Modelo | AUC-ROC (CV) |
|--------|--------------|
| Solo Prob_Implícita | 0.6615 |
| Solo P_Win_Calibrada | 0.6451 |
| Prob_Imp + P_Win | 0.6603 |

**Combinar ambos NO mejora** el rendimiento.

## Conclusiones

### ¿P_Win_Calibrada funciona?

✅ **Sí**, tiene correlación positiva con los aciertos.  
✅ **Sí**, la correlación es estadísticamente significativa.  
✅ **Sí**, cumple 6/6 criterios de validación básicos.

### ¿Es un predictor ÚTIL?

⚠️ **No como predictor independiente.**

P_Win_Calibrada es esencialmente una transformación de la probabilidad implícita (1/cuota). Captura la misma información que las cuotas ya contienen: que los favoritos (cuotas bajas) aciertan más frecuentemente.

### ¿Por qué parece funcionar?

El modelo de regresión logística que genera P_Win_Calibrada "aprende" a dar más peso a la probabilidad implícita porque ese es el mejor predictor disponible en los datos. Al hacerlo, P_Win_Calibrada se convierte en una versión suavizada de 1/cuota, sin añadir información nueva.

### Recomendación

**Usar directamente 1/Mejor_Cuota (probabilidad implícita) como predictor:**
- Es más simple
- Es más transparente
- Tiene **mejor** poder predictivo
- No requiere modelo de calibración

### Para mejorar realmente

Se necesitarían variables que capturen información **no contenida** en las cuotas:
- Rendimiento reciente de equipos (forma)
- Lesiones/suspensiones de jugadores clave
- Historial de enfrentamientos directos
- Condiciones del partido (clima, local/visitante)
- Factores motivacionales (posición en tabla, importancia del partido)

## Archivos de Análisis Generados

- `analisis_p_win_calibrada.py` - Análisis exhaustivo inicial
- `analisis_p_win_profundo.py` - Análisis de componentes y redundancia
- `verificacion_final_p_win.py` - Verificación de redundancia con residuos
- `resumen_analisis_p_win.py` - Resumen ejecutivo con tablas
- `busqueda_utilidad_p_win.py` - Búsqueda de escenarios específicos
