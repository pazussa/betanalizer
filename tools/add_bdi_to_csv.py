"""Add BDI (bookmaker disagreement) columns to a CSV of market analysis.

This script reads a CSV like `analisis_mercados_20251220_214421.csv`,
parses the `Todas_Las_Cuotas` column which contains semicolon-separated
entries `bookie:odd`, computes a simple BDI per row as the mean
Jensen-Shannon divergence between each bookmaker's Bernoulli distribution
([p,1-p], where p=1/odd) and the consensus Bernoulli ([p_bar,1-p_bar]).

Outputs a new CSV with suffix `_con_BDI.csv` including columns:
  - `BDI_jsd`
  - `BDI_n_bookmakers`
  - `BDI_std_p`
  - `BDI_mad_p`

Usage:
  python3 tools/add_bdi_to_csv.py \
      --input analisis_mercados_20251220_214421.csv \
      --output analisis_mercados_20251220_214421_con_BDI.csv
"""

import argparse
import math
import csv
import os
import sys
from typing import List

# ensure repo root is on sys.path so `src` package can be imported when
# running the script from tools/ or other cwd
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.disagreement import jensen_shannon


def parse_todas_las_cuotas(cell: str) -> List[float]:
    """Parse 'tipico_de:2.3; nordicbet:2.15' -> list of odds (floats).
    Returns empty list if parsing fails.
    """
    if not isinstance(cell, str):
        return []
    parts = [p.strip() for p in cell.split(";") if p.strip()]
    odds = []
    for part in parts:
        if ":" not in part:
            continue
        _, val = part.split(":", 1)
        try:
            odds.append(float(val))
        except Exception:
            continue
    return odds


def compute_bdi_from_odds_list(odds_list: List[float]) -> dict:
    """Given a list of decimal odds for the SAME selection across bookies,
    compute a disagreement index (mean JSD of Bernoulli distributions).

    For each odd o_i compute p_i = 1/o_i. Consensus p_bar = mean(p_i).
    For each bookmaker compute JSD between [p_i,1-p_i] and [p_bar,1-p_bar].
    Return statistics.
    """
    if not odds_list:
        return {
            'BDI_jsd': None,
            'BDI_n_bookmakers': 0,
            'BDI_std_p': None,
            'BDI_mad_p': None,
        }
    ps = [1.0 / o for o in odds_list if o > 0]
    if not ps:
        return {
            'BDI_jsd': None,
            'BDI_n_bookmakers': 0,
            'BDI_std_p': None,
            'BDI_mad_p': None,
        }
    n = len(ps)
    p_bar = sum(ps) / float(n)

    # consensus distribution
    consensus = [p_bar, 1.0 - p_bar]

    jsds = []
    for p in ps:
        dist = [p, 1.0 - p]
        try:
            jsd = jensen_shannon(dist, consensus, base=2.0)
        except Exception:
            jsd = None
        if jsd is not None:
            jsds.append(jsd)

    bdi = sum(jsds) / len(jsds) if jsds else None

    # dispersion stats on p
    mean_p = p_bar
    var = sum((x - mean_p) ** 2 for x in ps) / float(n)
    std_p = math.sqrt(var)
    mad_p = sum(abs(x - mean_p) for x in ps) / float(n)

    return {
        'BDI_jsd': bdi,
        'BDI_n_bookmakers': n,
        'BDI_std_p': std_p,
        'BDI_mad_p': mad_p,
    }


def process(input_csv: str, output_csv: str):
    with open(input_csv, newline='', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        rows = list(reader)

    # compute BDI per row
    for row in rows:
        cell = row.get('Todas_Las_Cuotas', None)
        odds = parse_todas_las_cuotas(cell)
        res = compute_bdi_from_odds_list(odds)
        # store as string-friendly values
        row['BDI_jsd'] = '' if res['BDI_jsd'] is None else f"{res['BDI_jsd']:.6f}"
        row['BDI_n_bookmakers'] = str(res['BDI_n_bookmakers'])
        row['BDI_std_p'] = '' if res['BDI_std_p'] is None else f"{res['BDI_std_p']:.6f}"
        row['BDI_mad_p'] = '' if res['BDI_mad_p'] is None else f"{res['BDI_mad_p']:.6f}"

    # write out with original fieldnames + new columns
    fieldnames = list(rows[0].keys()) if rows else []
    # ensure BDI columns at end
    for col in ['BDI_jsd', 'BDI_n_bookmakers', 'BDI_std_p', 'BDI_mad_p']:
        if col not in fieldnames:
            fieldnames.append(col)

    with open(output_csv, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {output_csv}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--output', '-o', required=True)
    args = parser.parse_args()
    process(args.input, args.output)


if __name__ == '__main__':
    main()
