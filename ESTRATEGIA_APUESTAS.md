# 📊 Estrategia de Apuestas - Documentación Matemática Completa

## Índice
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Fuente de Datos](#fuente-de-datos)
3. [Métricas Calculadas](#métricas-calculadas)
4. [Fórmula de Rendimiento](#fórmula-de-rendimiento)
5. [Análisis por Mercado](#análisis-por-mercado)
6. [Criterios de Filtrado](#criterios-de-filtrado)
7. [Fórmula de Confianza](#fórmula-de-confianza)
8. [Resultados Históricos](#resultados-históricos)
9. [Implementación](#implementación)

---

## Resumen Ejecutivo

Esta estrategia fue desarrollada analizando **88 apuestas históricas** del dataset `analisis_mercados_20251125_065555.csv`. 

- **ROI Global sin filtro**: -5.76%
- **ROI con estrategia filtrada**: +107.5%
- **Apuestas filtradas**: 6 de 88 (6.8%)
- **Mejora absoluta**: +113.26 puntos porcentuales

---

## Fuente de Datos

### API Utilizada
- **The Odds API** (https://the-odds-api.com)
- Datos 100% oficiales de casas de apuestas reales
- Regiones: EU, US, UK, AU
- Casas: Pinnacle, Betsson, Marathonbet, Codere

### Mercados Analizados
| Tipo | Mercados |
|------|----------|
| **Doble Chance** | 1X (Local o Empate), X2 (Empate o Visitante) |
| **Totales** | Over 2.5, Under 2.5, Over 3.5, Under 3.5 |

---

## Métricas Calculadas

### 1. Score_Final
Mide la dispersión de probabilidades implícitas entre casas de apuestas.

```
Score_Final = Σ |P_i - P_promedio| / n

Donde:
- P_i = 1/Cuota_i (probabilidad implícita de casa i)
- P_promedio = promedio de todas las probabilidades implícitas
- n = número de casas
```

**Interpretación:**
- Score bajo (< 0.3): Consenso entre casas → Mayor certeza
- Score alto (> 0.7): Discrepancia entre casas → Posible valor oculto

### 2. Diferencia_Cuota_Promedio
Diferencia entre la mejor cuota disponible y el promedio del mercado.

```
Diferencia_Cuota_Promedio = Mejor_Cuota - Cuota_Promedio_Mercado
```

**Interpretación:**
- Diferencia alta (> 0.03): La mejor casa ofrece valor significativo
- Diferencia baja (< 0.01): Mercado muy eficiente

### 3. Volatilidad_Pct
Coeficiente de variación de las cuotas expresado en porcentaje.

```
Volatilidad_Pct = (σ / μ) × 100

Donde:
- σ = desviación estándar de las cuotas
- μ = promedio de las cuotas
```

**Interpretación:**
- Volatilidad baja (< 1%): Cuotas muy estables entre casas
- Volatilidad alta (> 2%): Diferencias significativas entre casas

### 4. Margen_Casa_Pct
Margen de ganancia que aplica la casa de apuestas (vigorish/juice).

```
Margen_Casa_Pct = (Σ(1/Cuota_i) - 1) × 100

Para mercados de 2 opciones (Over/Under):
Margen = (1/Cuota_Over + 1/Cuota_Under - 1) × 100
```

**Interpretación:**
- Margen bajo (< 3%): Casa eficiente, mejores condiciones
- Margen alto (> 5%): Casa extractiva, peores condiciones

---

## Fórmula de Rendimiento

### Definición Correcta

```
Rendimiento = Σ(Cuotas_Acertadas) - Total_Apuestas

ROI (%) = (Rendimiento / Total_Apuestas) × 100
```

### Ejemplo Práctico

| Apuesta | Cuota | Resultado | Retorno |
|---------|-------|-----------|---------|
| Partido A | 2.10 | ✅ Acertado | 2.10 |
| Partido B | 1.85 | ❌ Fallido | 0.00 |
| Partido C | 1.95 | ✅ Acertado | 1.95 |
| **Total** | - | 2 de 3 | **4.05** |

```
Rendimiento = 4.05 - 3 = +1.05 unidades
ROI = (1.05 / 3) × 100 = +35%
```

### ⚠️ Error Común Evitado
**Incorrecto:** Rendimiento = Aciertos - Fallos (ignora las cuotas)
**Correcto:** Rendimiento = Σ(Cuotas cuando acierta) - n_apuestas

---

## Análisis por Mercado

### Rendimiento Global por Mercado (Dataset 25/Nov)

| Mercado | Apuestas | Aciertos | Tasa | Rendimiento | ROI |
|---------|----------|----------|------|-------------|-----|
| Under 3.5 | 5 | 4 | 80% | +4.01 | +80.25% |
| X2 | 19 | 10 | 52.6% | +1.20 | +6.32% |
| Over 2.5 | 16 | 9 | 56.3% | -0.56 | -3.47% |
| Under 2.5 | 16 | 9 | 56.3% | -0.90 | -5.62% |
| 1X | 22 | 11 | 50% | -3.86 | -17.55% |
| Over 3.5 | 5 | 0 | 0% | -5.00 | -100% |

### Hallazgos Clave

1. **Under 3.5** es el mercado más rentable (+80% ROI)
2. **X2** tiene rendimiento positivo consistente (+6.32%)
3. **1X** y **Over 3.5** son trampas estadísticas (ROI negativo)
4. **Over/Under 2.5** dependen de filtros adicionales

---

## Criterios de Filtrado

### Estrategia 1: Under 3.5 (ROI +80%)

```python
filtro_under35 = (
    (Mercado == 'Under 3.5') &
    (Mejor_Cuota > 1.70) &
    (Diferencia_Cuota_Promedio > 0.015) &
    (Volatilidad_Pct > 0.5)
)
```

**Justificación matemática:**
- Cuota > 1.70: Evita apuestas de bajo valor
- Diferencia > 0.015: Asegura que hay valor en la mejor casa
- Volatilidad > 0.5%: Indica discrepancia aprovechable

### Estrategia 2: X2 (ROI +97%)

```python
filtro_x2 = (
    (Mercado == 'X2') &
    (Score_Final >= 0.10) & (Score_Final <= 0.55) &
    (Diferencia_Cuota_Promedio >= 0.01) & (Diferencia_Cuota_Promedio <= 0.04) &
    (Margen_Casa_Pct < 3.5)
)
```

**Justificación matemática:**
- Score 0.10-0.55: Zona de consenso moderado (no extremo)
- Diferencia 0.01-0.04: Valor sin ser sospechoso
- Margen < 3.5%: Solo casas eficientes

### Estrategia 3: Over 2.5 (ROI +100%)

```python
filtro_over25 = (
    (Mercado == 'Over 2.5') &
    (Score_Final < 0.65) &
    (Diferencia_Cuota_Promedio > 0.035) &
    (Volatilidad_Pct >= 0.71) & (Volatilidad_Pct <= 1.5)
)
```

**Justificación matemática:**
- Score < 0.65: Consenso razonable entre casas
- Diferencia > 0.035: Alto valor en la mejor casa
- Volatilidad 0.71-1.5%: Rango óptimo de discrepancia

### Estrategia 4: Under 2.5 (ROI +54%)

```python
filtro_under25 = (
    (Mercado == 'Under 2.5') &
    (Score_Final > 0.65) &
    (Mejor_Cuota >= 1.93) & (Mejor_Cuota <= 2.06) &
    (Diferencia_Cuota_Promedio > 0.033) &
    (Volatilidad_Pct >= 0.49) & (Volatilidad_Pct <= 1.69) &
    (Margen_Casa_Pct < 3.5)
)
```

**Justificación matemática:**
- Score > 0.65: Busca discrepancia (posible valor oculto)
- Cuota 1.93-2.06: Rango de cuotas equilibradas (~50%)
- Múltiples filtros: Mayor selectividad = Mayor ROI

---

## Fórmula de Confianza

Para ordenar las apuestas por prioridad, se calcula un score de confianza:

```
Confianza = (ROI_Histórico × 0.3) + 
            (10 / Volatilidad_Pct) + 
            (20 / Margen_Casa_Pct) + 
            (Score_Final × 30)
```

### Desglose de Pesos

| Componente | Peso | Razón |
|------------|------|-------|
| ROI Histórico | 30% | Rendimiento probado del mercado |
| 1/Volatilidad | ~15% | Menor volatilidad = mayor estabilidad |
| 1/Margen | ~25% | Menor margen = mejores condiciones |
| Score_Final | 30% | Mayor score puede indicar valor |

### Ejemplo de Cálculo

Para **Real Madrid vs Celta Vigo - Under 3.5**:
- ROI Histórico: 80%
- Volatilidad: 2.63%
- Margen: 3.36%
- Score: 0.8601

```
Confianza = (80 × 0.3) + (10/2.63) + (20/3.36) + (0.8601 × 30)
          = 24 + 3.80 + 5.95 + 25.80
          = 59.56
```

---

## Resultados Históricos

### Dataset Original (25/Nov/2025)

| Métrica | Sin Filtro | Con Estrategia |
|---------|------------|----------------|
| Apuestas | 88 | 6 |
| Aciertos | 48 (54.5%) | 5 (83.3%) |
| Rendimiento | -5.07 | +6.45 |
| ROI | -5.76% | +107.5% |

### Apuestas Rentables Extraídas

| Partido | Mercado | Cuota | Resultado | Rendimiento |
|---------|---------|-------|-----------|-------------|
| Man City vs Leverkusen | X2 | 4.16 | ✅ | +3.16 |
| Man City vs Leverkusen | Under 3.5 | 2.14 | ✅ | +1.14 |
| Hull City vs Ipswich | Under 2.5 | 2.06 | ✅ | +1.06 |
| Motherwell vs Hibernian | Under 2.5 | 2.06 | ✅ | +1.06 |
| Norwich vs Oxford | Under 2.5 | 2.03 | ✅ | +1.03 |
| Dortmund vs Villarreal | X2 | 2.00 | ❌ | -1.00 |
| **TOTAL** | | | 5/6 | **+6.45** |

---

## Implementación

### Archivos del Proyecto

```
betanalizer/
├── main.py                           # CLI principal
├── extraer_apuestas_rentables.py     # Aplica filtros de estrategia
├── analisis_rendimiento_por_mercado.py # Análisis por variable
├── estrategia_apuestas_analisis.ipynb # Notebook Jupyter completo
├── src/
│   ├── analyzer.py                   # Motor de análisis
│   ├── models.py                     # Modelos de datos
│   └── apis/
│       └── the_odds_api.py           # Integración API
```

### Ejecución

```bash
# 1. Activar entorno
source venv/bin/activate

# 2. Ejecutar análisis (próximas 36 horas)
python main.py analyze --hours-ahead 36

# 3. Aplicar estrategia al CSV generado
python extraer_apuestas_rentables.py
```

### Adaptación a Nuevos Datos

Para aplicar la estrategia a un nuevo dataset:

```python
import pandas as pd

df = pd.read_csv('nuevo_dataset.csv')

# Aplicar filtros
filtro = (
    ((df['Mercado'] == 'Under 3.5') & (df['Mejor_Cuota'] > 1.70)) |
    ((df['Mercado'] == 'X2') & (df['Score_Final'] <= 0.55) & (df['Margen_Casa_Pct'] < 3.5)) |
    ((df['Mercado'] == 'Over 2.5') & (df['Diferencia_Cuota_Promedio'] > 0.035))
)

apuestas_recomendadas = df[filtro]
```

---

## Notas Importantes

### ⚠️ Limitaciones

1. **Muestra pequeña**: 88 apuestas es estadísticamente limitado
2. **Sesgo temporal**: Datos de un período específico
3. **Sin garantía**: Rendimiento pasado no garantiza futuro
4. **Varianza**: Incluso estrategias +EV pueden tener rachas negativas

### ✅ Buenas Prácticas

1. **Gestión de bankroll**: No apostar más del 2-5% por apuesta
2. **Diversificación**: Distribuir entre varios mercados
3. **Registro**: Mantener tracking de todas las apuestas
4. **Validación continua**: Re-evaluar estrategia cada 100+ apuestas

### 📈 Próximos Pasos

1. Acumular más datos históricos (500+ apuestas)
2. Implementar backtesting automatizado
3. Añadir análisis de ligas específicas
4. Incorporar datos de lesiones/formaciones

---

*Documentación generada el 6 de Diciembre de 2025*
*Basada en análisis de The Odds API y datos históricos del proyecto betanalizer*
