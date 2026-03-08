# Evaluacion de la regla BDI_jsd_fair

## Como se calcula BDI_jsd_fair en el algoritmo

- El calculo esta en `src/disagreement.py` y `tools/recompute_bdi_using_both_sides.py` de la rama `origin/estrategia-confianza-calibrada`.
- Para cada bookmaker con ambas cuotas del mercado `Over/Under x`, se convierte cada cuota a probabilidad implicita `r = 1/cuota`.
- Luego se quita el vig del bookmaker normalizando solo las dos caras: `p_over = r_over / (r_over + r_under)` y `p_under = r_under / (r_over + r_under)`.
- Con eso cada casa queda representada por una distribucion fair `[p_over, p_under]`.
- Se construye un consenso como la media de esas probabilidades fair entre casas.
- `BDI_jsd_fair` es la media de la Jensen-Shannon divergence entre cada bookmaker y ese consenso.
- El valor se asigna a las dos filas del mismo partido para `Over 2.5` y `Under 2.5`, asi que por construccion debe ser igual en ambos lados.

## Verificacion del supuesto de igualdad

- Pares `Over/Under 2.5` verificados: **112**.
- Diferencia absoluta maxima entre `Over 2.5` y `Under 2.5`: **0.000000000000**.
- Conclusion: tu supuesto era correcto; el algoritmo deja el mismo `BDI_jsd_fair` para ambos lados del mismo partido.

## Dataset usado

- Fuente: `consolidado_resultados_raw.csv` generado desde la rama calibrada.
- Filtro: solo `Over 2.5` y `Under 2.5`, resultado conocido, `BDI_jsd_fair` disponible.
- Deduplicacion: prioridad a `resultados_definitivos`, luego `historical_principal`, luego datasets recientes; se eliminaron backups redundantes.

## Resultado principal

- Tu regla original mas cercana (`fin de semana sabado-domingo`, `top 8`, `elige la cuota mayor`) dio **profit total 6.09** con **ROI por apuesta 0.152**, **hit rate 52.50%** y **5 semanas ganadoras de 7**.
- La version `top 7` tambien fue positiva: profit total **3.67**, ROI **0.102**.
- La mejor variante del barrido fue `top 9` `sabado-domingo` `cuota mayor`, con profit total **7.13** y ROI **0.166**.

## Comparaciones clave

- Elegir la **cuota mayor** en `top 8` sabado-domingo: profit **6.09**, ROI **0.152**.
- Elegir la **cuota menor** en `top 8` sabado-domingo: profit **-2.44**, ROI **-0.061**.
- Conclusion: tu intuicion sobre tomar la cuota mayor fue mejor que tomar la menor.

## Top BDI vs no filtrar

- `Top 8` por `BDI_jsd_fair`: profit **6.09**, ROI **0.152**, hit rate **52.50%**.
- `Bottom 8` por `BDI_jsd_fair`: profit **4.14**, ROI **0.104**, hit rate **50.00%**.
- Conclusion: ordenar por `BDI_jsd_fair` si agrega valor frente a tomar los de BDI mas bajo.

## Ajustes sugeridos

- No veo evidencia de que exigir mas `BDI_n_bookmakers_fair` mejore la estrategia; en este historico lo empeora.
- El ajuste mas util no es cambiar de lado, sino mover el tamano del top: `top 9` sale mejor que `top 8`, aunque `top 8` ya funciona bien y esta mas cerca de tu regla original.
- Incluir viernes (`fri_sun`) empeora frente a quedarte solo con sabado-domingo.

## Conclusion

- Tu regla **no estaba equivocada**: en el dataset grande deduplicado fue rentable.
- La parte mas defendible de la idea es: `sabado-domingo`, ordenar por `BDI_jsd_fair`, tomar la **cuota mayor** entre `Over 2.5` y `Under 2.5`, y jugar un top corto por semana.
- Si la quieres dejar mas afinada, el mejor ajuste encontrado aqui es `top 9` en vez de `top 8`.
- Si la quieres dejar mas conservadora, `top 8` sabado-domingo sigue siendo una version valida y positiva.
