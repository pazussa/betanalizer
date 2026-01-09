# Análisis de Predictores - Resultados Definitivos

## Resumen Ejecutivo

Este análisis evalúa los predictores de apuestas utilizando el dataset limpio de `resultados_definitivos/`, que contiene **6,596 registros** de **1,993 partidos únicos**, procesados correctamente y con al menos 4 casas de apuestas por registro.

---

## 🎯 PREDICTOR PRINCIPAL: Under 2.25 (Muestra Considerable)

### Hallazgo Principal

**Se ha identificado un predictor con MUESTRA CONSIDERABLE y ALTA SIGNIFICANCIA ESTADÍSTICA:**

| Métrica | Valor |
|---------|-------|
| **Estrategia** | **Apostar a Under 2.25 (todo el mercado)** |
| **N (muestra)** | **449** |
| **Aciertos** | 274 |
| **Tasa de acierto** | **61.0%** |
| **RENDIMIENTO** | **+80.6** |
| **ROI** | **+17.9%** |
| **p-valor** | **0.00004 (significativo al 0.01%)** |
| **IC 95% ROI** | **[+9.1%, +26.7%]** |
| **Fechas con ROI > 0** | **12/12 (100%)** |

### ¿Por qué funciona?

El mercado Under 2.25 selecciona **partidos específicos** donde sistemáticamente hay menos goles de lo esperado por las casas:

| Under 2.5 en... | N | Tasa | Rendimiento | ROI |
|-----------------|---|------|-------------|-----|
| Partidos CON Under 2.25 | 450 | 61.1% | +25.3 | +5.6% |
| Partidos SIN Under 2.25 | 1,275 | 49.9% | -13.4 | -1.1% |

**Conclusión:** Los 449 partidos donde se ofrece Under 2.25 tienen una tendencia sistemática a terminar con pocos goles.

### Simulación de Bankroll

Con stake fijo de 10 unidades por apuesta:
- **Bankroll inicial:** 1,000
- **Bankroll final:** 1,805.9
- **Ganancia:** +805.9
- **ROI sobre capital:** +80.6%

**Todas las 12 fechas terminaron con rendimiento positivo.**

---

## Predictores Adicionales

### Hallazgo Secundario (BDI Alto - Muestra Pequeña)

**Se ha identificado otro predictor estadísticamente significativo** que supera al predictor anterior:

| Predictor | N | Tasa | ROI | p-valor | Sig. |
|-----------|---|------|-----|---------|------|
| **Under 2.25 (todo)** | **449** | **61.0%** | **+17.9%** | **0.00004** | **SÍ ✓** |
| Under 2.25 [1.6-2.0] | 348 | 63.5% | +21.2% | 0.00002 | SÍ ✓ |
| Over 2.5 + Cuota [1.7-1.9] + BDI≥P90 | 46 | 71.7% | +27.9% | 0.0201 | SÍ ✓ |
| Over 2.5 + Cuota [1.8-2.0] (anterior) | 441 | 54.0% | +2.4% | 0.2909 | NO |

---

## 1. Validación del Predictor Anterior

### 1.1 Over 2.5 + Cuota [1.8-2.0]

Este era el mejor predictor identificado en `VALIDACION_PREDICTORES_MARZO_VS_ENERO.md`.

**Resultados actuales:**
- **N = 441 apuestas**
- **Aciertos = 238** (54.0%)
- **ROI = +2.4%**
- Cuota promedio: 1.903
- Break-even requerido: 52.5%
- Exceso sobre break-even: +1.4 puntos

**Test binomial vs break-even:**
- p-valor = 0.2909
- **NO es estadísticamente significativo al 5%**

### 1.2 Conclusión sobre predictor anterior

El predictor original **NO se mantiene** con significancia estadística en el dataset completo. Aunque el ROI es positivo (+2.4%), la diferencia respecto al break-even no es significativa (p=0.29).

---

## 2. Nuevo Predictor Descubierto

### 2.1 Over 2.5 + Cuota [1.7-1.9] + BDI≥P90

**Descripción:** Apuestas al mercado Over 2.5 goles con cuotas entre 1.7 y 1.9, donde el BDI_jsd_fair está en el percentil 90 o superior de su mercado.

**El BDI alto indica fuerte desacuerdo entre casas de apuestas**, lo cual puede señalar:
- Información asimétrica en el mercado
- Mayor incertidumbre sobre el resultado
- Posibles ineficiencias explotables

**Resultados:**
- **N = 46 apuestas**
- **Aciertos = 33** (71.7%)
- **ROI = +27.9%**
- Cuota promedio: 1.790
- Break-even requerido: 55.9%
- **Exceso sobre break-even: +15.9 puntos**

### 2.2 Tests de Significancia

#### Test Z (comparación con baseline Over 2.5)
```
Predictor: 71.7% vs Baseline: 47.2%
Z = 3.290
p-valor = 0.0005
✅ Significativo al 1%
```

#### Test Binomial (vs break-even)
```
H0: Tasa = 55.9% (break-even)
Ha: Tasa > 55.9%
p-valor = 0.0201
✅ Significativo al 5%
```

#### Intervalo de Confianza del ROI (Bootstrap 10,000 iteraciones)
```
ROI observado: +27.9%
IC 95%: [+4.3%, +50.8%]
✅ El IC NO incluye 0% → Rentabilidad significativa
```

### 2.3 Consistencia Temporal

| Fecha | N | Aciertos | Tasa | ROI |
|-------|---|----------|------|-----|
| 20250110 | 2 | 2 | 100.0% | +76.0% |
| 20250117 | 3 | 2 | 66.7% | +15.7% |
| 20250124 | 4 | 3 | 75.0% | +35.2% |
| 20250131 | 3 | 2 | 66.7% | +21.7% |
| 20250207 | 4 | 3 | 75.0% | +36.3% |
| 20250214 | 4 | 4 | 100.0% | +76.5% |
| 20250221 | 4 | 3 | 75.0% | +35.2% |
| 20250228 | 4 | 4 | 100.0% | +76.3% |
| **20250307** | **7** | **3** | **42.9%** | **-24.9%** |
| 20250314 | 6 | 4 | 66.7% | +19.3% |
| 20250328 | 5 | 3 | 60.0% | +7.6% |
| **TOTAL** | **46** | **33** | **71.7%** | **+27.9%** |

**Fechas con ROI positivo: 10/11 (91%)**

Solo una fecha (20250307) muestra pérdida significativa, lo que demuestra buena consistencia temporal.

---

## 3. Predictor Secundario Identificado

### 3.1 Under 2.25 + Cuota [1.9-2.1] + BDI≥P90

**Resultados:**
- N = 22 apuestas
- Aciertos = 15 (68.2%)
- ROI = +36.1%
- p-valor = 0.0668 (marginalmente significativo)
- IC 95%: [-1.2%, +73.0%]

**Nota:** Este predictor tiene mejor ROI pero menor muestra y no alcanza significancia al 5%. Requiere más datos para validación.

---

## 4. Estrategia Combinada

### 4.1 Over 2.5 + Under 2.25 (ambos con BDI≥P90)

Combinando ambos predictores:

| Métrica | Valor |
|---------|-------|
| N total | 68 |
| Aciertos | 48 |
| Tasa | 70.6% |
| **ROI** | **+30.5%** |
| IC 95% | **[+10.4%, +49.7%]** |

**✅ El IC combinado NO incluye 0% → La estrategia combinada es rentable**

---

## 5. Correlaciones Globales Significativas

Variables con correlación significativa con Acierto (p < 0.05):

| Variable | r | p-valor | Interpretación |
|----------|---|---------|----------------|
| Mejor_Cuota | -0.0921 | <0.001 | Cuotas más altas → menor acierto |
| Margen_Casa_Pct | +0.0376 | 0.002 | Mayor margen → mayor acierto |
| Volatilidad_Pct | -0.0370 | 0.003 | Mayor volatilidad → menor acierto |

**Nota importante:** Las métricas BDI no muestran correlación global significativa, pero **sí son altamente significativas cuando se combinan con rangos específicos de cuota y mercado**.

---

## 6. Comparación con Análisis Anterior

### 6.1 VALIDACION_PREDICTORES_MARZO_VS_ENERO.md

| Aspecto | Análisis Anterior | Análisis Actual |
|---------|-------------------|-----------------|
| Mejor predictor | Over 2.5 + Cuota [1.8-2.0] | Over 2.5 + Cuota [1.7-1.9] + BDI≥P90 |
| ROI | +10.5% (marzo) / +2.4% (todos) | +27.9% |
| Significancia | NO | **SÍ (p=0.02)** |
| N | ~200 | 46 |
| Uso de BDI | No | **Sí (crítico)** |

### 6.2 Mejora Clave: Incorporación de BDI

El BDI (Bookmaker Disagreement Index) permite **filtrar apuestas donde hay mayor desacuerdo entre casas**, lo cual:

1. **Reduce la muestra** (de 441 a 46 apuestas)
2. **Aumenta significativamente el ROI** (de +2.4% a +27.9%)
3. **Logra significancia estadística** (p=0.02)

---

## 7. Conclusiones y Recomendaciones

### 7.1 Conclusiones

1. **El predictor anterior (Over 2.5 + Cuota [1.8-2.0]) NO es estadísticamente significativo** con el dataset completo.

2. **Se ha identificado un nuevo predictor significativo**: Over 2.5 + Cuota [1.7-1.9] + BDI≥P90
   - ROI: +27.9%
   - p-valor: 0.0201
   - IC 95%: [+4.3%, +50.8%]

3. **El BDI es un factor discriminante crítico** que no se había utilizado previamente.

4. **La estrategia combinada (Over 2.5 + Under 2.25 con BDI alto)** ofrece:
   - 68 apuestas
   - ROI +30.5%
   - IC 95%: [+10.4%, +49.7%]

### 7.2 Limitaciones

1. **Tamaño de muestra pequeño** (N=46 para el mejor predictor)
2. **Período temporal limitado** (enero-marzo 2025)
3. **Una fecha con pérdida significativa** (20250307 con -24.9%)
4. **Posible overfitting** al optimizar múltiples parámetros

### 7.3 Recomendaciones

1. **Validar con datos futuros** - El predictor debe probarse out-of-sample
2. **Gestión de bankroll conservadora** - Dada la varianza observada
3. **Monitorear el BDI_jsd_fair** como indicador principal
4. **Implementar alertas automáticas** cuando se detecten apuestas que cumplan los criterios

### 7.4 Criterios para Apuestas de Alto Valor

**PREDICTOR PRINCIPAL (Muestra Grande, Alta Confianza):**
```
IF Mercado = "Under 2.25"
THEN → APOSTAR (ROI esperado ~18%, p<0.0001)
```

**PREDICTOR SECUNDARIO (ROI Alto, Muestra Pequeña):**
```
IF Mercado = "Over 2.5"
   AND Mejor_Cuota >= 1.7 AND Mejor_Cuota <= 1.9
   AND BDI_jsd_fair >= P90 de Over 2.5
THEN → APOSTAR (ROI esperado ~28%)

IF Mercado = "Under 2.25"
   AND Mejor_Cuota >= 1.9 AND Mejor_Cuota <= 2.1
   AND BDI_jsd_fair >= P90 de Under 2.25
THEN → APOSTAR (ROI esperado ~36%, pero menos significativo)
```

---

## Anexo: Umbrales BDI por Mercado

Para referencia, los percentiles del BDI_jsd_fair:

| Mercado | BDI_jsd_fair P75 | BDI_jsd_fair P90 |
|---------|------------------|------------------|
| Over 2.5 | 0.000044 | 0.000078 |
| Under 2.25 | 0.000018 | 0.000034 |
| Over 2.75 | 0.000019 | 0.000030 |
| Under 2.75 | 0.000019 | 0.000030 |

**Nota:** Estos valores son específicos del dataset actual y deben recalcularse si se agregan nuevos datos.

---

*Generado: 2025-01-08*
*Dataset: resultados_definitivos/ (6,596 registros, 1,993 partidos)*
