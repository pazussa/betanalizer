#!/usr/bin/env python3
"""Sweep de estrategia en TEST (sin leakage).

Objetivo
- Recalibrar (regresión logística) usando SOLO TRAIN con split temporal.
- Evaluar estrategias (umbrales + filtros) SOLO en TEST.

Entrada esperada
- Un CSV con columnas como `Resultado`, `Fecha_Hora_Colombia`, `Mejor_Cuota` y features numéricas.
- Recomendado: `data/master_dataset_deduped_verified.csv` (solo Acertado/Fallido).

Salida
- Un CSV con resultados del sweep.
- Un reporte Markdown resumido.

Nota
- Esto NO es consejo de apuestas; es evaluación estadística sobre histórico verificado.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

# Reutilizamos exactamente el diseño/modelo del calibrador para evitar divergencias.
from calibrar_confianza import build_design, fit_logistic, predict_proba


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _profit(y: np.ndarray, odds: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=int)
    odds = np.asarray(odds, dtype=float)
    return np.where(y == 1, odds - 1.0, -1.0)


def _auc(scores: np.ndarray, y: np.ndarray) -> float:
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y, dtype=int)
    pos = y == 1
    n_pos = int(pos.sum())
    n_neg = int((~pos).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")

    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)

    sorted_scores = scores[order]
    i = 0
    while i < len(sorted_scores):
        j = i
        while j + 1 < len(sorted_scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        if j > i:
            avg_rank = (i + 1 + j + 1) / 2.0
            ranks[order[i : j + 1]] = avg_rank
        i = j + 1

    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


@dataclass(frozen=True)
class Split:
    train: pd.DataFrame
    test: pd.DataFrame


def time_split(df: pd.DataFrame, date_col: str, test_frac: float) -> Split:
    d = df.copy()
    d["_dt"] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.sort_values("_dt")
    n = len(d)
    cut = int(np.floor((1.0 - test_frac) * n))
    train = d.iloc[:cut].drop(columns=["_dt"], errors="ignore")
    test = d.iloc[cut:].drop(columns=["_dt"], errors="ignore")
    return Split(train=train, test=test)


def _eval_subset(d: pd.DataFrame) -> dict[str, float]:
    y = (d["Resultado"].astype(str).str.strip() == "Acertado").astype(int).to_numpy()
    odds = _to_num(d["Mejor_Cuota"]).to_numpy(dtype=float)
    p = _to_num(d["P_Win_Calibrada"]).to_numpy(dtype=float)
    mask = np.isfinite(odds) & np.isfinite(p)
    if mask.sum() == 0:
        return {"n": 0, "winrate": float("nan"), "roi_pct": float("nan"), "avg_odds": float("nan"), "auc": float("nan")}

    y = y[mask]
    odds = odds[mask]
    p = p[mask]
    profits = _profit(y, odds)
    return {
        "n": float(len(y)),
        "winrate": float(y.mean() * 100.0),
        "roi_pct": float(profits.mean() * 100.0),
        "avg_odds": float(odds.mean()),
        "auc": float(_auc(p, y)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Sweep de estrategia en TEST (sin leakage)")
    ap.add_argument("--input", default="data/master_dataset_deduped_verified.csv")
    ap.add_argument("--date-col", default="Fecha_Hora_Colombia")
    ap.add_argument("--test-frac", type=float, default=0.3)
    ap.add_argument("--min-n", type=int, default=15, help="Mínimo n en TEST para considerar una estrategia")
    ap.add_argument("--output-csv", default=None)
    ap.add_argument("--output-md", default=None)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df = df[df["Resultado"].astype(str).str.strip().isin(["Acertado", "Fallido"])].copy()
    if df.empty:
        raise SystemExit("No hay filas verificadas (Acertado/Fallido) en el input")

    split = time_split(df, args.date_col, args.test_frac)

    # Fit SOLO en train
    y_train = (split.train["Resultado"].astype(str).str.strip() == "Acertado").astype(int).to_numpy()
    y_test = (split.test["Resultado"].astype(str).str.strip() == "Acertado").astype(int).to_numpy()

    design_train = build_design(split.train, fit=True)
    w = fit_logistic(design_train.X, y_train)

    design_test = build_design(
        split.test,
        fit=False,
        means=design_train.means,
        stds=design_train.stds,
        medians=design_train.medians,
        cat_levels=design_train.cat_levels,
    )

    p_train = predict_proba(design_train.X, w)
    p_test = predict_proba(design_test.X, w)

    train_scored = split.train.copy()
    test_scored = split.test.copy()
    train_scored["P_Win_Calibrada"] = p_train
    test_scored["P_Win_Calibrada"] = p_test

    # Baselines
    base_train = _eval_subset(train_scored)
    base_test = _eval_subset(test_scored)

    # Grids ("con todo" pero acotado para no explotar combinaciones)
    thr_grid = [0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
    vol_max_grid = [None, 5.0, 3.0, 2.0, 1.5]
    margen_max_grid = [None, 7.0, 6.0, 5.0, 4.0]
    num_casas_min_grid = [None, 3, 4, 5]
    diff_min_grid = [None, 0.02, 0.05]
    min_odds_grid = [None, 1.20, 1.30]
    max_odds_grid = [None, 3.0, 4.0]

    rows: list[dict[str, float | str | int | None]] = []

    # Pre-coerce numeric cols once
    for col in ["Volatilidad_Pct", "Margen_Casa_Pct", "Num_Casas", "Diferencia_Cuota_Promedio", "Mejor_Cuota"]:
        if col in test_scored.columns:
            test_scored[col] = _to_num(test_scored[col])

    for thr in thr_grid:
        for vol_max in vol_max_grid:
            for margen_max in margen_max_grid:
                for num_min in num_casas_min_grid:
                    for diff_min in diff_min_grid:
                        for min_odds in min_odds_grid:
                            for max_odds in max_odds_grid:
                                d = test_scored.copy()
                                m = np.isfinite(d["P_Win_Calibrada"]) & (d["P_Win_Calibrada"] >= thr)

                                if vol_max is not None and "Volatilidad_Pct" in d.columns:
                                    m &= np.isfinite(d["Volatilidad_Pct"]) & (d["Volatilidad_Pct"] <= vol_max)
                                if margen_max is not None and "Margen_Casa_Pct" in d.columns:
                                    m &= np.isfinite(d["Margen_Casa_Pct"]) & (d["Margen_Casa_Pct"] <= margen_max)
                                if num_min is not None and "Num_Casas" in d.columns:
                                    m &= np.isfinite(d["Num_Casas"]) & (d["Num_Casas"] >= num_min)
                                if diff_min is not None and "Diferencia_Cuota_Promedio" in d.columns:
                                    m &= np.isfinite(d["Diferencia_Cuota_Promedio"]) & (d["Diferencia_Cuota_Promedio"] >= diff_min)
                                if min_odds is not None and "Mejor_Cuota" in d.columns:
                                    m &= np.isfinite(d["Mejor_Cuota"]) & (d["Mejor_Cuota"] >= min_odds)
                                if max_odds is not None and "Mejor_Cuota" in d.columns:
                                    m &= np.isfinite(d["Mejor_Cuota"]) & (d["Mejor_Cuota"] <= max_odds)

                                pick = d.loc[m].copy()
                                if len(pick) < args.min_n:
                                    continue

                                met = _eval_subset(pick)
                                rows.append(
                                    {
                                        "thr_pwin": thr,
                                        "vol_max": vol_max,
                                        "margen_max": margen_max,
                                        "num_casas_min": num_min,
                                        "diff_min": diff_min,
                                        "min_odds": min_odds,
                                        "max_odds": max_odds,
                                        "n": int(met["n"]),
                                        "winrate_pct": float(met["winrate"]),
                                        "roi_pct": float(met["roi_pct"]),
                                        "avg_odds": float(met["avg_odds"]),
                                    }
                                )

    res = pd.DataFrame(rows)
    if res.empty:
        raise SystemExit("Sweep vacío (prueba bajar --min-n o ampliar grids)")

    res = res.sort_values(["roi_pct", "n"], ascending=[False, False]).reset_index(drop=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = args.output_csv or f"docs/sweep_estrategia_test_{ts}.csv"
    out_md = args.output_md or f"docs/sweep_estrategia_test_{ts}.md"
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    os.makedirs(os.path.dirname(out_md), exist_ok=True)

    res.to_csv(out_csv, index=False)

    top = res.head(30).copy()

    lines: list[str] = []
    lines.append(f"# Sweep de Estrategia en TEST ({ts})\n")
    lines.append(f"Input: `{args.input}`\n")
    lines.append(f"Split: time-based ({args.date_col}), test_frac={args.test_frac}\n")
    lines.append(f"Verificados: total={len(df)} train={len(split.train)} test={len(split.test)}\n")

    lines.append("## Baseline (sin filtros, usando TODO el TEST)\n")
    lines.append(f"- TEST: n={int(base_test['n'])} winrate={base_test['winrate']:.1f}% ROI={base_test['roi_pct']:+.2f}% avg_odds={base_test['avg_odds']:.3f} AUC(P_Win)={base_test['auc']:.4f}\n")

    lines.append("## Baseline (sin filtros, usando TODO el TRAIN)\n")
    lines.append(f"- TRAIN: n={int(base_train['n'])} winrate={base_train['winrate']:.1f}% ROI={base_train['roi_pct']:+.2f}% avg_odds={base_train['avg_odds']:.3f} AUC(P_Win)={base_train['auc']:.4f}\n")

    lines.append("## Top 30 estrategias por ROI (TEST)\n")
    lines.append(top.to_markdown(index=False))
    lines.append("\n")
    lines.append(f"CSV completo: `{out_csv}`\n")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("=" * 60)
    print("SWEEP COMPLETADO")
    print("=" * 60)
    print("Reporte:", out_md)
    print("CSV   :", out_csv)
    print("Top 5 (ROI, n, thr):")
    for i, r in top.head(5).iterrows():
        print(f"  {i+1:>2}. ROI={r['roi_pct']:+.2f}% n={int(r['n'])} thr={r['thr_pwin']:.2f} vol_max={r['vol_max']} margen_max={r['margen_max']} num_min={r['num_casas_min']} diff_min={r['diff_min']} odds=[{r['min_odds']},{r['max_odds']}] ")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
