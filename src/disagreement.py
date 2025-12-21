"""
Bookmaker disagreement metrics

This module implements a Bookmaker Disagreement Index (BDI) based on the
Jensen-Shannon divergence between each bookmaker's *fair* probability
distribution (vig removed) and the consensus (mean) distribution.

Key functions:
- remove_vig(odds) -> fair probability distribution for a bookmaker
- jensen_shannon(p, q, base=2) -> JSD between two distributions (bounded [0,1] for base=2 when k=2)
- bookmaker_disagreement(bookmaker_odds_list) -> returns dict with:
    - `jsd_mean`: mean JSD (BDI) in [0,1]
    - `per_outcome_std`: std dev of fair probabilities per outcome
    - `per_outcome_mad`: mean absolute deviation per outcome
    - `n_bookmakers`: number of bookmakers used
    - `outcomes`: ordered list of outcomes

Why JSD?
- JSD is symmetric, finite and interpretable as the average information
  distance between each bookmaker and the consensus. For binary markets
  (like Over/Under) JSD in base-2 is in [0,1]. It generalizes to >2 outcomes.

Example usage:
    bookmakers = [
        {"Over 2.5": 1.80, "Under 2.5": 2.05},
        {"Over 2.5": 1.85, "Under 2.5": 2.00},
    ]
    from src.disagreement import bookmaker_disagreement
    res = bookmaker_disagreement(bookmakers)
    print(res['jsd_mean'])

Notes on inputs:
- Each bookmaker entry is a mapping outcome->odds (decimal odds, float).
- Missing outcomes for a bookmaker will cause that bookmaker to be skipped
  for the calculation; consider pre-validating or imputing if needed.
"""

from typing import Dict, List, Tuple
import math


def remove_vig(odds: Dict[str, float]) -> Dict[str, float]:
    """Convert raw decimal odds into a fair probability distribution.

    For a bookmaker with outcomes i and odds o_i, compute r_i = 1/o_i,
    then normalize: p_i = r_i / sum_j r_j. This removes the bookmaker's
    overround (vig) and yields a probability vector summing to 1.

    Returns a dict outcome->probability.
    """
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
    # KL divergence D(p||q) where p and q are lists of probabilities
    eps = 1e-12
    total = 0.0
    for pi, qi in zip(p, q):
        if pi <= 0:
            continue
        qi_safe = qi if qi > 0 else eps
        total += pi * (math.log(pi / qi_safe) / math.log(base))
    return total


def jensen_shannon(p: List[float], q: List[float], base: float = 2.0) -> float:
    """Compute Jensen-Shannon divergence between two distributions.

    Returns a value >= 0. For base=2 and binary outcomes the result is in [0,1].
    """
    if len(p) != len(q):
        raise ValueError("Distributions must have the same length")
    m = [(pi + qi) / 2.0 for pi, qi in zip(p, q)]
    return 0.5 * (_kl_divergence(p, m, base=base) + _kl_divergence(q, m, base=base))


def bookmaker_disagreement(bookmaker_odds_list: List[Dict[str, float]]) -> Dict:
    """Compute disagreement metrics across bookmakers.

    Input: list of bookmakers, each a dict outcome->decimal_odds.
    Output: dict with keys `jsd_mean`, `per_outcome_std`, `per_outcome_mad`,
    `n_bookmakers`, and `outcomes`.
    """
    # Build fair distributions for each bookmaker and gather outcome set
    fair_list: List[Dict[str, float]] = []
    outcomes_set = set()
    for odds in bookmaker_odds_list:
        fair = remove_vig(odds)
        if fair:
            fair_list.append(fair)
            outcomes_set.update(fair.keys())

    n = len(fair_list)
    if n == 0:
        return {
            'jsd_mean': None,
            'per_outcome_std': {},
            'per_outcome_mad': {},
            'n_bookmakers': 0,
            'outcomes': [],
        }
    outcomes = sorted(outcomes_set)

    # Build matrix: rows = bookmakers, cols = outcomes (missing -> 0)
    matrix: List[List[float]] = []
    for fair in fair_list:
        row = [fair.get(o, 0.0) for o in outcomes]
        matrix.append(row)

    # Compute consensus distribution (mean across bookmakers)
    k = len(outcomes)
    mean_dist = [0.0] * k
    for col in range(k):
        for row in matrix:
            mean_dist[col] += row[col]
        mean_dist[col] /= float(n)

    # Compute JSD of each bookmaker vs mean
    jsds = []
    for row in matrix:
        jsd = jensen_shannon(row, mean_dist, base=2.0)
        jsds.append(jsd)

    # Per-outcome dispersion stats
    per_outcome_std = {}
    per_outcome_mad = {}
    for col_idx, o in enumerate(outcomes):
        vals = [row[col_idx] for row in matrix]
        mean_v = sum(vals) / float(n)
        # std
        var = sum((v - mean_v) ** 2 for v in vals) / float(n)
        std = math.sqrt(var)
        # MAD
        mad = sum(abs(v - mean_v) for v in vals) / float(n)
        per_outcome_std[o] = std
        per_outcome_mad[o] = mad

    return {
        'jsd_mean': sum(jsds) / float(len(jsds)),
        'jsd_list': jsds,
        'per_outcome_std': per_outcome_std,
        'per_outcome_mad': per_outcome_mad,
        'n_bookmakers': n,
        'outcomes': outcomes,
    }


if __name__ == '__main__':
    # tiny self-check example
    bookmakers = [
        {"Over 2.5": 1.80, "Under 2.5": 2.05},
        {"Over 2.5": 1.85, "Under 2.5": 2.00},
        {"Over 2.5": 1.90, "Under 2.5": 1.95},
    ]
    print(bookmaker_disagreement(bookmakers))
