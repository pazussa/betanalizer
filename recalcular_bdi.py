#!/usr/bin/env python3
"""
Script para recalcular correctamente los BDI de registros que fueron mal calculados.

El problema: BDI_jsd_fair fue calculado igual que BDI_jsd, cuando deberían ser diferentes.

- BDI_jsd_fair: Se calcula emparejando Over/Under del mismo bookmaker (distribución fair)
- BDI_jsd: Aproximación binaria (selección vs complemento)

También recalcula:
- BDI_std_p_fair y BDI_mad_p_fair
- BDI_std_p y BDI_mad_p
"""

import pandas as pd
import numpy as np
import os
import math
from typing import Dict, List


def remove_vig(odds: Dict[str, float]) -> Dict[str, float]:
    """Convertir cuotas decimales a probabilidades fair (sin margen)."""
    if not odds:
        return {}
    raw = {}
    for k, v in odds.items():
        try:
            if v is None or v <= 0:
                continue
            raw[k] = 1.0 / float(v)
        except Exception:
            continue
    if not raw:
        return {}
    s = sum(raw.values())
    if s <= 0:
        return {}
    return {k: (rv / s) for k, rv in raw.items()}


def _kl_divergence(p: List[float], q: List[float], base: float = 2.0) -> float:
    """KL divergence D(p||q)"""
    eps = 1e-12
    total = 0.0
    for pi, qi in zip(p, q):
        if pi <= 0:
            continue
        qi_safe = qi if qi > 0 else eps
        total += pi * (math.log(pi / qi_safe) / math.log(base))
    return total


def jensen_shannon(p: List[float], q: List[float], base: float = 2.0) -> float:
    """Compute Jensen-Shannon divergence between two distributions."""
    if len(p) != len(q):
        raise ValueError("Distributions must have the same length")
    m = [(pi + qi) / 2.0 for pi, qi in zip(p, q)]
    return 0.5 * (_kl_divergence(p, m, base=base) + _kl_divergence(q, m, base=base))


def bookmaker_disagreement(bookmaker_odds_list: List[Dict[str, float]]) -> Dict:
    """Compute disagreement metrics across bookmakers."""
    fair_list = []
    for odds in bookmaker_odds_list:
        fair = remove_vig(odds)
        if fair:
            fair_list.append(fair)
    
    if len(fair_list) < 2:
        return {'jsd_mean': 0.0, 'n_bookmakers': len(fair_list), 
                'per_outcome_std': {}, 'per_outcome_mad': {}}
    
    # Get outcome set
    outcomes = set()
    for f in fair_list:
        outcomes.update(f.keys())
    outcomes = sorted(outcomes)
    
    # Build matrix
    matrix = []
    for f in fair_list:
        row = [f.get(o, 0.0) for o in outcomes]
        if sum(row) > 0:
            matrix.append(row)
    
    if len(matrix) < 2:
        return {'jsd_mean': 0.0, 'n_bookmakers': len(matrix),
                'per_outcome_std': {}, 'per_outcome_mad': {}}
    
    matrix = np.array(matrix)
    
    # Consensus (mean distribution)
    consensus = np.mean(matrix, axis=0)
    
    # JSD mean
    jsd_values = []
    for row in matrix:
        jsd = jensen_shannon(list(row), list(consensus))
        if not np.isnan(jsd):
            jsd_values.append(jsd)
    
    jsd_mean = np.mean(jsd_values) if jsd_values else 0.0
    
    # Per-outcome std and mad
    per_outcome_std = {}
    per_outcome_mad = {}
    for i, o in enumerate(outcomes):
        col = matrix[:, i]
        per_outcome_std[o] = float(np.std(col))
        per_outcome_mad[o] = float(np.mean(np.abs(col - np.mean(col))))
    
    return {
        'jsd_mean': jsd_mean,
        'n_bookmakers': len(matrix),
        'per_outcome_std': per_outcome_std,
        'per_outcome_mad': per_outcome_mad,
        'outcomes': outcomes
    }


def parse_todas_las_cuotas(todas_cuotas: str) -> Dict[str, float]:
    """Parsear la columna Todas_Las_Cuotas a un diccionario {bookmaker: cuota}."""
    if pd.isna(todas_cuotas) or not todas_cuotas:
        return {}
    
    result = {}
    for item in str(todas_cuotas).split(';'):
        item = item.strip()
        if ':' in item:
            parts = item.split(':')
            if len(parts) == 2:
                bm = parts[0].strip()
                try:
                    cuota = float(parts[1].strip())
                    result[bm] = cuota
                except ValueError:
                    pass
    return result


def recalcular_bdi_fair(row: pd.Series, df: pd.DataFrame) -> dict:
    """
    Recalcula BDI_jsd_fair emparejando Over/Under del mismo bookmaker.
    
    Returns:
        Dict con los valores recalculados
    """
    mercado = row['Mercado']
    partido = row['Partido']
    
    # Solo para mercados Over/Under
    if 'Over' not in str(mercado) and 'Under' not in str(mercado):
        return None
    
    # Obtener cuotas de este mercado
    cuotas_actual = parse_todas_las_cuotas(row['Todas_Las_Cuotas'])
    if not cuotas_actual:
        return None
    
    # Determinar mercado opuesto
    parts = str(mercado).split()
    if len(parts) < 2:
        return None
    
    tipo = parts[0]
    linea = ' '.join(parts[1:])
    tipo_opuesto = 'Under' if tipo == 'Over' else 'Over'
    mercado_opuesto = f"{tipo_opuesto} {linea}"
    
    # Buscar el mercado opuesto en el mismo partido
    opuesto = df[(df['Partido'] == partido) & (df['Mercado'] == mercado_opuesto)]
    
    if opuesto.empty:
        return None
    
    cuotas_opuesto = parse_todas_las_cuotas(opuesto.iloc[0]['Todas_Las_Cuotas'])
    if not cuotas_opuesto:
        return None
    
    # Emparejar bookmakers que tienen ambos mercados
    fair_list = []
    bookmakers_comunes = set(cuotas_actual.keys()) & set(cuotas_opuesto.keys())
    
    for bm in bookmakers_comunes:
        odds_pair = {mercado: cuotas_actual[bm], mercado_opuesto: cuotas_opuesto[bm]}
        fair_list.append(odds_pair)
    
    if len(fair_list) < 2:
        return None
    
    # Calcular BDI fair
    bdi_res = bookmaker_disagreement(fair_list)
    
    return {
        'BDI_jsd_fair': bdi_res.get('jsd_mean', 0.0),
        'BDI_n_bookmakers_fair': bdi_res.get('n_bookmakers', len(fair_list)),
        'BDI_std_p_fair': bdi_res.get('per_outcome_std', {}).get(mercado, 0.0),
        'BDI_mad_p_fair': bdi_res.get('per_outcome_mad', {}).get(mercado, 0.0)
    }


def recalcular_bdi_nofair(row: pd.Series) -> dict:
    """
    Recalcula BDI_jsd (aproximación binaria: selección vs complemento).
    """
    mercado = row['Mercado']
    cuotas = parse_todas_las_cuotas(row['Todas_Las_Cuotas'])
    
    if not cuotas or len(cuotas) < 2:
        return None
    
    # Crear pares binarios: [prob_seleccion, prob_complemento]
    odds_list = []
    for bm, cuota in cuotas.items():
        if cuota > 1:
            p = 1.0 / cuota
            # Par binario aproximado
            odds_list.append({mercado: cuota, f"{mercado}_other": 1.0 / max(1e-9, 1.0 - p)})
    
    if len(odds_list) < 2:
        return None
    
    bdi_res = bookmaker_disagreement(odds_list)
    
    return {
        'BDI_jsd': bdi_res.get('jsd_mean', 0.0),
        'BDI_n_bookmakers': bdi_res.get('n_bookmakers', len(odds_list)),
        'BDI_std_p': bdi_res.get('per_outcome_std', {}).get(mercado, 0.0),
        'BDI_mad_p': bdi_res.get('per_outcome_mad', {}).get(mercado, 0.0)
    }


def procesar_archivo(filepath: str) -> dict:
    """Procesa un archivo y recalcula los BDI de registros problemáticos."""
    filename = os.path.basename(filepath)
    print(f"\n{'='*60}")
    print(f"Procesando: {filename}")
    print('='*60)
    
    df = pd.read_csv(filepath)
    
    # Identificar registros problemáticos (BDI_jsd_fair == BDI_jsd)
    mask_problematico = (df['BDI_jsd_fair'] == df['BDI_jsd']) & df['BDI_jsd_fair'].notna()
    n_problematicos = mask_problematico.sum()
    
    print(f"  Registros con BDI_jsd_fair == BDI_jsd: {n_problematicos}")
    
    if n_problematicos == 0:
        return {'archivo': filename, 'corregidos': 0, 'total': len(df)}
    
    corregidos = 0
    
    for idx in df[mask_problematico].index:
        row = df.loc[idx]
        
        # Recalcular BDI fair
        bdi_fair = recalcular_bdi_fair(row, df)
        if bdi_fair:
            df.loc[idx, 'BDI_jsd_fair'] = bdi_fair['BDI_jsd_fair']
            df.loc[idx, 'BDI_n_bookmakers_fair'] = bdi_fair['BDI_n_bookmakers_fair']
            df.loc[idx, 'BDI_std_p_fair'] = bdi_fair['BDI_std_p_fair']
            df.loc[idx, 'BDI_mad_p_fair'] = bdi_fair['BDI_mad_p_fair']
        
        # Recalcular BDI no-fair
        bdi_nofair = recalcular_bdi_nofair(row)
        if bdi_nofair:
            df.loc[idx, 'BDI_jsd'] = bdi_nofair['BDI_jsd']
            df.loc[idx, 'BDI_n_bookmakers'] = bdi_nofair['BDI_n_bookmakers']
            df.loc[idx, 'BDI_std_p'] = bdi_nofair['BDI_std_p']
            df.loc[idx, 'BDI_mad_p'] = bdi_nofair['BDI_mad_p']
        
        corregidos += 1
    
    # Guardar
    df.to_csv(filepath, index=False)
    
    # Verificar
    df_check = pd.read_csv(filepath)
    mask_aun_problematico = (df_check['BDI_jsd_fair'] == df_check['BDI_jsd']) & df_check['BDI_jsd_fair'].notna()
    
    print(f"  Registros corregidos: {corregidos}")
    print(f"  Aún problemáticos después de corrección: {mask_aun_problematico.sum()}")
    
    # Mostrar ejemplo de corrección
    if corregidos > 0:
        ejemplo = df_check.loc[df[mask_problematico].index[0]]
        print(f"\n  Ejemplo después de corrección:")
        print(f"    Partido: {ejemplo['Partido']}")
        print(f"    Mercado: {ejemplo['Mercado']}")
        print(f"    BDI_jsd_fair: {ejemplo['BDI_jsd_fair']}")
        print(f"    BDI_jsd: {ejemplo['BDI_jsd']}")
        print(f"    (Ahora son diferentes: {ejemplo['BDI_jsd_fair'] != ejemplo['BDI_jsd']})")
    
    return {'archivo': filename, 'corregidos': corregidos, 'total': len(df)}


def main():
    data_dir = 'historical_con_resultados'
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and 'backup' not in f]
    files.sort()
    
    print("="*70)
    print("RECALCULANDO BDI PARA REGISTROS PROBLEMÁTICOS")
    print("="*70)
    
    estadisticas = []
    for f in files:
        filepath = os.path.join(data_dir, f)
        stats = procesar_archivo(filepath)
        estadisticas.append(stats)
    
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    
    total_corregidos = sum(s['corregidos'] for s in estadisticas)
    print(f"\nTotal registros corregidos: {total_corregidos}")
    
    for s in estadisticas:
        if s['corregidos'] > 0:
            print(f"  {s['archivo']}: {s['corregidos']} corregidos")


if __name__ == "__main__":
    main()
