"""Recompute BDI using both sides (Over and Under) per bookmaker when available.

Algorithm:
- Read CSV with columns including `Partido`, `Mercado`, `Todas_Las_Cuotas`.
- Group rows by `(Partido, threshold)` where `threshold` is the numeric part of the market
  (e.g. '2.5' from 'Under 2.5' / 'Over 2.5').
- For groups with both an Over and an Under row, parse `Todas_Las_Cuotas` for each side
  into dict(bookie->odd). For each bookmaker present in both sides compute the fair
  probabilities p_over,p_under by normalizing r=1/odd across the two sides.
- Compute consensus distribution (mean across bookmakers) and JSD per bookmaker vs
  consensus (using `src.disagreement.jensen_shannon`). The group's BDI is the mean JSD.
- Assign the group's fair BDI and per-outcome dispersion (std/mad of p_over) to both
  the Over and Under rows in the output CSV. If not enough paired bookies available,
  keep the original BDI columns.

Writes a new CSV with suffix `_fairBDI.csv`.
"""

import csv
import os
import sys
import math
from typing import Dict

# Ensure repo root is importable
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.disagreement import remove_vig, jensen_shannon


def parse_todas_las_cuotas(cell: str) -> Dict[str, float]:
    """Parse semicolon-separated 'bookie:odd' strings into dict."""
    d = {}
    if not isinstance(cell, str):
        return d
    parts = [p.strip() for p in cell.split(';') if p.strip()]
    for part in parts:
        if ':' not in part:
            continue
        name, val = part.split(':', 1)
        try:
            d[name.strip()] = float(val)
        except Exception:
            continue
    return d


def market_key(market: str):
    """Return (side, threshold) for market strings like 'Under 2.5' or 'Over 3.0'."""
    if not isinstance(market, str):
        return None, None
    s = market.strip().lower()
    parts = s.split()
    if len(parts) < 2:
        return None, None
    side = parts[0]
    thr = parts[-1]
    return side, thr


def compute_fair_bdi_for_group(over_odds: Dict[str, float], under_odds: Dict[str, float]):
    # find common bookies
    common = [b for b in over_odds.keys() if b in under_odds]
    if len(common) < 2:
        return None
    # build per-bookie fair distributions
    bookie_dists = []
    p_over_list = []
    for b in common:
        o_over = over_odds[b]
        o_under = under_odds[b]
        # remove vig by normalizing the two sides
        fair = remove_vig({'over': o_over, 'under': o_under})
        # remove_vig returns {} on bad input
        if not fair or 'over' not in fair:
            continue
        p_over = fair['over']
        p_under = fair['under']
        bookie_dists.append((p_over, p_under))
        p_over_list.append(p_over)

    if len(bookie_dists) < 2:
        return None

    # consensus
    k = 2
    mean_dist = [0.0, 0.0]
    for p_over, p_under in bookie_dists:
        mean_dist[0] += p_over
        mean_dist[1] += p_under
    mean_dist[0] /= len(bookie_dists)
    mean_dist[1] /= len(bookie_dists)

    jsds = []
    for p_over, p_under in bookie_dists:
        jsd = jensen_shannon([p_over, p_under], mean_dist, base=2.0)
        jsds.append(jsd)

    # dispersion of p_over
    n = len(p_over_list)
    mean_p = sum(p_over_list) / n
    var = sum((p - mean_p) ** 2 for p in p_over_list) / n
    std_p = math.sqrt(var)
    mad_p = sum(abs(p - mean_p) for p in p_over_list) / n

    return {
        'fair_BDI_jsd': sum(jsds) / len(jsds),
        'fair_BDI_n_bookmakers': len(bookie_dists),
        'fair_BDI_std_p': std_p,
        'fair_BDI_mad_p': mad_p,
    }


def process(input_csv: str, output_csv: str):
    rows = []
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for r in reader:
            rows.append(r)

    # build map (Partido, threshold) -> {'over': idx, 'under': idx}
    groups = {}
    for idx, r in enumerate(rows):
        partido = r.get('Partido')
        market = r.get('Mercado') or r.get('Tipo_Mercado') or ''
        side, thr = market_key(market)
        if partido is None or side is None or thr is None:
            continue
        key = (partido.strip(), thr)
        groups.setdefault(key, {})[side] = idx

    # compute fair BDI for keys with both sides
    results_by_idx = {}
    for key, mapping in groups.items():
        if 'over' in mapping and 'under' in mapping:
            over_idx = mapping['over']
            under_idx = mapping['under']
            over_row = rows[over_idx]
            under_row = rows[under_idx]
            over_odds = parse_todas_las_cuotas(over_row.get('Todas_Las_Cuotas',''))
            under_odds = parse_todas_las_cuotas(under_row.get('Todas_Las_Cuotas',''))
            res = compute_fair_bdi_for_group(over_odds, under_odds)
            if res:
                # assign to both rows
                results_by_idx[over_idx] = res
                results_by_idx[under_idx] = res

    # prepare output fieldnames (add fair columns)
    add_cols = ['BDI_jsd_fair', 'BDI_n_bookmakers_fair', 'BDI_std_p_fair', 'BDI_mad_p_fair']
    out_fieldnames = list(fieldnames)
    for c in add_cols:
        if c not in out_fieldnames:
            out_fieldnames.append(c)

    # write output CSV: copy original rows and add fair values when available
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        for idx, r in enumerate(rows):
            rr = dict(r)
            if idx in results_by_idx:
                res = results_by_idx[idx]
                rr['BDI_jsd_fair'] = f"{res['fair_BDI_jsd']:.6f}"
                rr['BDI_n_bookmakers_fair'] = str(res['fair_BDI_n_bookmakers'])
                rr['BDI_std_p_fair'] = f"{res['fair_BDI_std_p']:.6f}"
                rr['BDI_mad_p_fair'] = f"{res['fair_BDI_mad_p']:.6f}"
            else:
                rr['BDI_jsd_fair'] = ''
                rr['BDI_n_bookmakers_fair'] = ''
                rr['BDI_std_p_fair'] = ''
                rr['BDI_mad_p_fair'] = ''
            writer.writerow(rr)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--output', '-o')
    args = parser.parse_args()
    inp = args.input
    out = args.output or (os.path.splitext(inp)[0] + '_fairBDI.csv')
    process(inp, out)
    print('Wrote', out)


if __name__ == '__main__':
    main()
