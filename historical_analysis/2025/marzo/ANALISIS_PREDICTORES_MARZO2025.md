# Análisis de Predictores - Marzo 2025

## Resumen Ejecutivo

Análisis estadístico de 1788 apuestas de mercados Over/Under de marzo 2025 (14, 21 y 28 de marzo).

## Ranking de Predictores por Confianza Estadística

| # | Predictor | N | ROI | IC 95% | Mejora | P-value | Score |
|---|-----------|---|-----|--------|--------|---------|-------|
| 1 | Over 2.5 + BDI_jsd_fair Q2 | 105 | +17.1% | [-2.5, +37.0] | +21.5% | 0.011 | 9 🟢🟢 |
| 2 | Under 2.5 + Mejor_Cuota < 1.86 | 207 | +3.3% | [-7.3, +14.7] | +5.5% | 0.0004 | 9 🟢🟢 |
| 3 | Over 2.75 + Volatilidad ≤ 2% | 45 | +31.4% | [+2.7, +56.6] | +23.6% | 0.011 | 9 🟢🟢 |
| 4 | Over 2.5 + Num_Casas ≤ 8 | 123 | +10.3% | [-8.4, +28.8] | +14.7% | 0.061 | 7 🟢 |
| 5 | Under 2.75 + Num_Casas ≥ 5 | 48 | +7.9% | [-16.6, +35.2] | +22.9% | 0.014 | 7 🟢 |
| 6 | Under 2.5 + Num_Casas > 8 | 297 | +3.4% | [-6.9, +13.5] | +5.6% | 0.061 | 7 🟢 |
| 7 | Under 2.5 + BDI_jsd_fair ≤ Q1 | 105 | +9.7% | [-8.1, +26.0] | +11.8% | 0.128 | 6 🟢 |
| 8 | Over 2.5 + Mejor_Cuota < 1.86 | 124 | -3.2% | [-18.8, +11.5] | +1.1% | 0.016 | 4 🟡 |

## Criterios de Evaluación

### Un predictor es "estadísticamente seguro" si cumple:
1. ✅ P-value < 0.05 (efecto NO es por azar con 95% confianza)
2. ✅ IC 95% del ROI **no cruza el cero** 
3. ✅ N ≥ 100 (muestra suficiente)
4. ✅ ROI > 0

## Veredicto por Predictor

| Predictor | Seguridad | P-value | IC | N | ROI |
|-----------|-----------|---------|-----|---|-----|
| Over 2.5 + BDI_jsd_fair Q2 | 55-65% | ✓ 0.011 | ✗ cruza 0 | ✓ 105 | +17.1% |
| Under 2.5 + Mejor_Cuota < 1.86 | 55-65% | ✓ 0.000 | ✗ cruza 0 | ✓ 207 | +3.3% |
| Over 2.75 + Volatilidad ≤ 2% | 55-65% | ✓ 0.011 | ✓ IC>0 | ✗ 45 | +31.4% |
| Over 2.5 + Num_Casas ≤ 8 | 45-55% | ✗ 0.061 | ✗ cruza 0 | ✓ 123 | +10.3% |
| Under 2.5 + Num_Casas > 8 | 45-55% | ✗ 0.061 | ✗ cruza 0 | ✓ 297 | +3.4% |

## Hallazgos Clave

### BDI_jsd_fair como Predictor
- **Over 2.5**: Funciona mejor en Q2 (consenso moderado) → ROI +17.1%
- **Under 2.5**: Funciona mejor en Q1 (consenso máximo) → ROI +9.7%
- El efecto es NO LINEAL, la correlación simple (Pearson/Spearman) no lo detecta

### Patrones Identificados
1. **Consenso del Mercado**: Baja dispersión entre casas (BDI_std_p, Volatilidad_Pct) mejora predicciones
2. **Profundidad de Mercado**: Num_Casas tiene efecto OPUESTO en Over vs Under
3. **Cuotas Favoritas**: Correlación significativa pero efecto práctico pequeño

## Conclusión

⚠️ **NINGÚN PREDICTOR ES "SEGURO" EN TÉRMINOS ESTADÍSTICOS ESTRICTOS**

- Casi todos los IC 95% cruzan el cero
- Necesita validación con más datos (otros meses)
- Los filtros son ORIENTATIVOS, no garantías

### Más Prometedores:
1. **Over 2.75 + Volatilidad ≤ 2%**: Único con IC>0, pero N=45 pequeño
2. **Over 2.5 + BDI_jsd_fair Q2**: ROI +17%, p<0.05, pero IC cruza 0
3. **Under 2.5 + Num_Casas > 8**: Mayor N (297), pero ROI modesto (+3.4%)

---
*Análisis generado: 6 de enero de 2026*
*Datos: Marzo 2025 (N=1788 apuestas)*
