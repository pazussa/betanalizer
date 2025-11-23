# Análisis: Margen de la Casa de Apuestas (Overround)

## ¿Qué es el margen de la casa?

El **margen** (también llamado **overround** o **juice**) es el porcentaje de ganancia 
que la casa de apuestas se garantiza **independientemente del resultado del partido**.

## Cálculo matemático

```
Margen = (1/Cuota_Local + 1/Cuota_Empate + 1/Cuota_Visitante) - 1
```

### Ejemplo real del sistema

**Partido: Alavés vs Celta Vigo**

Cuotas de Pinnacle:
- Local (1): 2.61
- Empate (X): 3.53
- Visitante (2): 2.72

Cálculo:
```
Margen = (1/2.61 + 1/3.53 + 1/2.72) - 1
       = (0.383 + 0.283 + 0.368) - 1
       = 1.034 - 1
       = 0.034
       = 3.4%
```

**Esto significa que Pinnacle tiene un margen de 3.4% en este partido.**

## ¿Por qué existe el margen?

En un mercado "justo" (sin margen), las probabilidades sumarían exactamente 100%:
```
38.3% + 28.3% + 36.8% = 103.4%
```

Ese **3.4% extra** es la comisión de la casa. Sin importar quién gane, 
la casa de apuestas gana ese porcentaje en promedio.

## Interpretación del margen

| Margen | Interpretación | Calidad para apostador |
|--------|----------------|------------------------|
| 2-4%   | Excelente      | ⭐⭐⭐⭐⭐ Pinnacle/Betfair |
| 4-6%   | Bueno          | ⭐⭐⭐⭐ Casas competitivas |
| 6-8%   | Promedio       | ⭐⭐⭐ Casas mainstream |
| 8-12%  | Alto           | ⭐⭐ Casas comerciales |
| >12%   | Muy alto       | ⭐ Evitar |

## Resultados del análisis

Según nuestros datos del análisis de 70 mercados (35 partidos):

### Márgenes por casa de apuestas

**Pinnacle** (nuestra fuente principal):
- Margen mínimo: **3.2%** (Rennes vs Monaco)
- Margen máximo: **4.3%** (Volendam vs Twente, Flamengo vs Bragantino)
- Margen promedio: **~3.6%**

### Observaciones importantes

1. **Pinnacle es una casa de bajo margen**: 3-4% es excelente para apostadores
2. **Los márgenes varían según el partido**:
   - Partidos equilibrados: márgenes más bajos (3.2-3.5%)
   - Partidos muy desiguales: márgenes más altos (4.0-4.3%)
3. **Partidos europeos principales** tienden a tener márgenes menores

## ¿Afecta esto nuestras apuestas de doble chance?

**SÍ**, indirectamente. Cuando calculamos cuotas de doble chance (1X o X2), 
ya llevamos incluido el margen de la casa:

```
Cuota 1X = 1 / (1/Cuota_1 + 1/Cuota_X)
```

Si las cuotas base (1, X, 2) tienen un margen del 3.5%, las cuotas derivadas 
(1X, X2) **heredan ese margen**.

### Ejemplo concreto

**Alavés vs Celta (Margen: 3.3%)**

Cuotas originales:
- 1: 2.61
- X: 3.53
- 2: 2.72

Cuotas doble chance calculadas:
- **1X: 1.42** ← Esta incluye el 3.3% de margen
- **X2: 1.53** ← Esta incluye el 3.3% de margen

**Valor justo (sin margen):**
- 1X justo: ~1.37 (en vez de 1.42)
- X2 justo: ~1.48 (en vez de 1.53)

La diferencia es la ganancia garantizada de la casa.

## Recomendaciones estratégicas

### 1. Buscar casas con bajo margen
Pinnacle (3-4%) es excelente. Otras casas pueden tener márgenes de 6-10%, 
lo que reduce el valor esperado.

### 2. Comparar márgenes entre partidos
Si dos mercados parecen similares, elegir el que tiene menor margen.

### 3. Entender el "costo real"
Cuando apostamos a cuota 1.40:
- Probabilidad implícita: 71.4%
- Probabilidad real (ajustada por margen 3.5%): ~69.0%
- "Costo" del margen: ~2.4 puntos porcentuales

## Datos en el CSV

El sistema ahora exporta dos columnas de margen:

1. **Margen_Casa_Pct**: Margen específico del bookmaker usado
2. **Margen_Mercado_Promedio_Pct**: Promedio de márgenes de todos los bookmakers disponibles

Estos datos permiten:
- Identificar oportunidades con márgenes bajos
- Comparar la competitividad de diferentes bookmakers
- Calcular el valor real de las apuestas

## Conclusión

El margen de la casa es **información valiosa** pero NO un criterio de filtrado por sí solo. 

**Uso recomendado:**
- ✅ Mostrar en reportes para transparencia
- ✅ Usar para comparar bookmakers
- ✅ Incluir en análisis de valor esperado
- ❌ NO usarlo como criterio de filtrado principal

**El criterio principal debe seguir siendo la cuota mínima (≥ 1.30)**, 
que automáticamente favorece mercados con probabilidades implícitas favorables.
