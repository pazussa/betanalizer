#!/usr/bin/env python3
"""Calibra una Confianza_Calibrada con validación train/test.

- Input: `data/master_dataset_deduped.csv` (o el que indiques)
- Solo filas verificadas: Resultado in {Acertado, Fallido}
- Split principal: time-based (por Fecha_Hora_Colombia)
- Modelo: regresión logística (numpy) con estandarización + one-hot Tipo_Mercado

Outputs:
- CSV: `data/master_dataset_deduped_calibrado.csv`
- Reporte: `docs/calibracion_confianza_<timestamp>.md`

Nota: esto NO es consejo de apuestas; solo evaluación estadística del histórico.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


NUM_FEATURES = [
    "Score_Final",
    "Volatilidad_Pct",
    "Margen_Casa_Pct",
    "Num_Casas",
    "Cuota_Promedio_Mercado",
    "Diferencia_Cuota_Promedio",
    "Mejor_Cuota",
]

CAT_FEATURES = ["Tipo_Mercado"]


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -35, 35)
    return 1.0 / (1.0 + np.exp(-z))


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


def _logloss(p: np.ndarray, y: np.ndarray) -> float:
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    p = np.clip(p, 1e-12, 1.0 - 1e-12)
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


def _brier(p: np.ndarray, y: np.ndarray) -> float:
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    return float(np.mean((p - y) ** 2))


def _profit(y: np.ndarray, odds: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=int)
    odds = np.asarray(odds, dtype=float)
    return np.where(y == 1, odds - 1.0, -1.0)


@dataclass
class Design:
    X: np.ndarray
    feature_names: list[str]
    means: np.ndarray
    stds: np.ndarray
    medians: np.ndarray
    cat_levels: dict[str, list[str]]


def build_design(
    df: pd.DataFrame,
    *,
    fit: bool = True,
    means: np.ndarray | None = None,
    stds: np.ndarray | None = None,
    medians: np.ndarray | None = None,
    cat_levels: dict[str, list[str]] | None = None,
) -> Design:
    d = df.copy()

    # numeric
    X_num = []
    for c in NUM_FEATURES:
        if c not in d.columns:
            d[c] = np.nan
        X_num.append(_to_num(d[c]).astype(float).values)
    Xn = np.vstack(X_num).T

    # impute (fit on train; reuse on test/full)
    if fit:
        col_medians = np.nanmedian(Xn, axis=0)
    else:
        assert medians is not None
        col_medians = medians
    inds = np.where(~np.isfinite(Xn))
    Xn[inds] = np.take(col_medians, inds[1])

    if fit:
        means_ = Xn.mean(axis=0)
        stds_ = Xn.std(axis=0)
        stds_[stds_ == 0] = 1.0
    else:
        assert means is not None and stds is not None
        means_ = means
        stds_ = stds

    Xn = (Xn - means_) / stds_
    feature_names = [f"num:{c}" for c in NUM_FEATURES]

    # categorical one-hot
    X_cat_parts = []
    cat_names = []
    cat_levels_out: dict[str, list[str]] = {}
    for c in CAT_FEATURES:
        if c not in d.columns:
            d[c] = ""
        vals = d[c].fillna("").astype(str)
        if fit:
            levels = sorted(vals.unique().tolist())
        else:
            assert cat_levels is not None and c in cat_levels
            levels = cat_levels[c]
        cat_levels_out[c] = levels
        for lv in levels:
            col = (vals == lv).astype(float).values
            X_cat_parts.append(col)
            cat_names.append(f"cat:{c}={lv}")

    if X_cat_parts:
        Xc = np.vstack(X_cat_parts).T
        X = np.hstack([Xn, Xc])
        feature_names.extend(cat_names)
    else:
        X = Xn

    return Design(
        X=X,
        feature_names=feature_names,
        means=means_,
        stds=stds_,
        medians=col_medians,
        cat_levels=cat_levels_out,
    )


def fit_logistic(X: np.ndarray, y: np.ndarray, lr: float = 0.05, l2: float = 0.5, iters: int = 2000) -> np.ndarray:
    n, p = X.shape
    w = np.zeros(p + 1, dtype=float)  # bias + weights

    for _ in range(iters):
        z = w[0] + X @ w[1:]
        p_hat = _sigmoid(z)
        # gradient (with L2 on weights only)
        grad0 = (p_hat - y).mean()
        gradw = (X.T @ (p_hat - y)) / n + l2 * w[1:]
        w[0] -= lr * grad0
        w[1:] -= lr * gradw

    return w


def predict_proba(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    z = w[0] + X @ w[1:]
    return _sigmoid(z)


def time_split(df: pd.DataFrame, date_col: str, test_frac: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = df.copy()
    d["_dt"] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.sort_values("_dt")
    n = len(d)
    cut = int(np.floor((1.0 - test_frac) * n))
    train = d.iloc[:cut].drop(columns=["_dt"], errors="ignore")
    test = d.iloc[cut:].drop(columns=["_dt"], errors="ignore")
    return train, test


def roi_top_k(df: pd.DataFrame, score_col: str, k_frac: float = 0.2) -> dict:
    d = df.copy()
    y = (d["Resultado"].astype(str).str.strip() == "Acertado").astype(int).values
    odds = _to_num(d["Mejor_Cuota"]).astype(float).values
    scores = _to_num(d[score_col]).astype(float).values

    mask = np.isfinite(scores) & np.isfinite(odds)
    d = d.loc[mask].copy()
    y = y[mask]
    odds = odds[mask]
    scores = scores[mask]

    n = len(scores)
    if n == 0:
        return {"n": 0, "roi_pct": float("nan"), "winrate": float("nan")}

    k = max(1, int(np.floor(k_frac * n)))
    idx = np.argsort(scores)
    top = idx[-k:]

    profits = _profit(y[top], odds[top])
    return {
        "n": int(k),
        "roi_pct": float(np.mean(profits) * 100.0),
        "winrate": float(np.mean(y[top]) * 100.0),
        "avg_odds": float(np.mean(odds[top])),
    }


def calibration_table(p: np.ndarray, y: np.ndarray, bins: int = 10) -> pd.DataFrame:
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=int)
    mask = np.isfinite(p)
    p = p[mask]
    y = y[mask]
    if p.size == 0:
        return pd.DataFrame(columns=["bin", "n", "p_min", "p_max", "p_mean", "winrate", "gap"])  # pragma: no cover

    # qcut on probability; duplicates drop if not enough unique values
    q = pd.qcut(p, q=bins, duplicates="drop")
    d = pd.DataFrame({"p": p, "y": y, "bin": q})
    g = d.groupby("bin", observed=True).agg(n=("y", "size"), p_min=("p", "min"), p_max=("p", "max"), p_mean=("p", "mean"), winrate=("y", "mean"))
    g = g.reset_index(drop=True)
    g["winrate"] = g["winrate"] * 100.0
    g["gap"] = (g["winrate"] / 100.0) - g["p_mean"]
    g.insert(0, "bin", np.arange(len(g), dtype=int))
    return g


def _metrics(p: np.ndarray, y: np.ndarray) -> dict[str, float]:
    return {
        "auc": _auc(p, y),
        "logloss": _logloss(p, y),
        "brier": _brier(p, y),
    }


def _fit_and_eval(train: pd.DataFrame, test: pd.DataFrame, *, lr: float, l2: float, iters: int) -> dict[str, Any]:
    y_train = (train["Resultado"].astype(str).str.strip() == "Acertado").astype(int).values
    y_test = (test["Resultado"].astype(str).str.strip() == "Acertado").astype(int).values

    design_train = build_design(train, fit=True)
    w = fit_logistic(design_train.X, y_train, lr=lr, l2=l2, iters=iters)
    design_test = build_design(
        test,
        fit=False,
        means=design_train.means,
        stds=design_train.stds,
        medians=design_train.medians,
        cat_levels=design_train.cat_levels,
    )
    p_train = predict_proba(design_train.X, w)
    p_test = predict_proba(design_test.X, w)

    return {
        "w": w,
        "design_train": design_train,
        "p_train": p_train,
        "p_test": p_test,
        "y_train": y_train,
        "y_test": y_test,
        "train_metrics": _metrics(p_train, y_train),
        "test_metrics": _metrics(p_test, y_test),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Calibra Confianza_Calibrada con regresión logística y train/test")
    ap.add_argument("--input", default="data/master_dataset_deduped.csv")
    ap.add_argument("--date-col", default="Fecha_Hora_Colombia")
    ap.add_argument("--test-frac", type=float, default=0.2)
    ap.add_argument(
        "--sweep-test-fracs",
        default=None,
        help="Opcional: lista separada por comas (ej: 0.2,0.3,0.4,0.5) para ver cómo cambian las métricas al aumentar el TEST",
    )
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--l2", type=float, default=0.5)
    ap.add_argument("--iters", type=int, default=2000)
    ap.add_argument("--output-csv", default="data/master_dataset_deduped_calibrado.csv")
    ap.add_argument("--output-md", default=None)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    ver = df[df["Resultado"].astype(str).str.strip().isin(["Acertado", "Fallido"])].copy()
    if ver.empty:
        raise SystemExit("No hay filas verificadas (Acertado/Fallido) en el input")

    train, test = time_split(ver, args.date_col, args.test_frac)
    fitres = _fit_and_eval(train, test, lr=args.lr, l2=args.l2, iters=args.iters)
    w = fitres["w"]
    design_train: Design = fitres["design_train"]
    p_train = fitres["p_train"]
    p_test = fitres["p_test"]
    y_train = fitres["y_train"]
    y_test = fitres["y_test"]

    # Compare vs original Confianza (if present)
    conf_train = _to_num(train.get("Confianza", pd.Series(index=train.index, dtype=float))).astype(float).values
    conf_test = _to_num(test.get("Confianza", pd.Series(index=test.index, dtype=float))).astype(float).values
    auc_conf_train = _auc(conf_train[np.isfinite(conf_train)], y_train[np.isfinite(conf_train)]) if np.isfinite(conf_train).any() else float("nan")
    auc_conf_test = _auc(conf_test[np.isfinite(conf_test)], y_test[np.isfinite(conf_test)]) if np.isfinite(conf_test).any() else float("nan")

    # ROI top-k
    # Compute P_Win/Confianza_Calibrada for ALL rows (no solo verificadas)
    design_all = build_design(
        df,
        fit=False,
        means=design_train.means,
        stds=design_train.stds,
        medians=design_train.medians,
        cat_levels=design_train.cat_levels,
    )
    p_all = predict_proba(design_all.X, w)

    out_df = df.copy()
    out_df["P_Win_Calibrada"] = p_all
    out_df["Confianza_Calibrada"] = (p_all * 100.0).round(2)

    # Marca split solo para filas verificadas (Acertado/Fallido)
    split_col = pd.Series("", index=out_df.index, dtype="string")
    key_cols = ["Partido", args.date_col, "Liga", "Tipo_Mercado", "Mercado"]
    # merge by key columns when available; fallback to index alignment within ver
    can_key = all(c in out_df.columns for c in key_cols)
    if can_key:
        train_keys = train[key_cols].astype(str)
        test_keys = test[key_cols].astype(str)
        out_keys = out_df[key_cols].astype(str)
        train_set = set(map(tuple, train_keys.values.tolist()))
        test_set = set(map(tuple, test_keys.values.tolist()))
        for i, tup in enumerate(map(tuple, out_keys.values.tolist())):
            if tup in train_set:
                split_col.iloc[i] = "train"
            elif tup in test_set:
                split_col.iloc[i] = "test"
    out_df["Split_Calibracion"] = split_col

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    out_df.to_csv(args.output_csv, index=False)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_md = args.output_md or f"docs/calibracion_confianza_{ts}.md"
    os.makedirs(os.path.dirname(out_md), exist_ok=True)

    # Coefs table (en espacio estandarizado)
    coef_names = ["bias"] + design_train.feature_names
    coefs = w
    coef_df = pd.DataFrame({"feature": coef_names, "coef": coefs})
    coef_df["abs_coef"] = coef_df["coef"].abs()
    coef_df["odds_ratio"] = np.exp(coef_df["coef"].clip(-10, 10))
    coef_df = coef_df.sort_values("abs_coef", ascending=False).drop(columns=["abs_coef"]) 

    # ROI comparisons (top 20%)
    train_out = train.copy()
    test_out = test.copy()
    train_out["P_Win_Calibrada"] = p_train
    test_out["P_Win_Calibrada"] = p_test
    train_out["Confianza_Calibrada"] = (p_train * 100.0).round(2)
    test_out["Confianza_Calibrada"] = (p_test * 100.0).round(2)

    roi_train_cal = roi_top_k(train_out, "P_Win_Calibrada", 0.2)
    roi_test_cal = roi_top_k(test_out, "P_Win_Calibrada", 0.2)

    # For baseline Confianza, reuse same selection method
    if "Confianza" in train.columns:
        train_out["Confianza"] = _to_num(train_out["Confianza"]).astype(float)
        test_out["Confianza"] = _to_num(test_out["Confianza"]).astype(float)
        roi_train_conf = roi_top_k(train_out, "Confianza", 0.2)
        roi_test_conf = roi_top_k(test_out, "Confianza", 0.2)
    else:
        roi_train_conf = roi_test_conf = {"n": 0, "roi_pct": float("nan"), "winrate": float("nan"), "avg_odds": float("nan")}

    lines: list[str] = []
    lines.append(f"# Calibración de Confianza ({ts})\n")
    lines.append(f"Input: `{args.input}`\n")
    lines.append(f"Output CSV: `{args.output_csv}`\n")
    lines.append(f"Split: time-based ({args.date_col}), test_frac={args.test_frac}\n")
    lines.append(f"Filas verificadas (Acertado/Fallido): {len(ver)} (train={len(train)} test={len(test)})\n")
    lines.append("## Métricas\n")
    tm = fitres["train_metrics"]
    sm = fitres["test_metrics"]
    lines.append(f"- Calibrada: AUC train={tm['auc']:.4f} test={sm['auc']:.4f}")
    lines.append(f"- Calibrada: LogLoss train={tm['logloss']:.4f} test={sm['logloss']:.4f}")
    lines.append(f"- Calibrada: Brier train={tm['brier']:.4f} test={sm['brier']:.4f}")
    lines.append(f"- Confianza actual (AUC): train={auc_conf_train:.4f} test={auc_conf_test:.4f}\n")

    lines.append("## Calibración (TEST, deciles de P_Win_Calibrada)\n")
    cal = calibration_table(p_test, y_test, bins=10)
    if not cal.empty:
        lines.append(cal.to_markdown(index=False))
    else:
        lines.append("(sin datos)\n")
    lines.append("\n")

    if args.sweep_test_fracs:
        fracs = []
        for raw in str(args.sweep_test_fracs).split(","):
            raw = raw.strip()
            if not raw:
                continue
            fracs.append(float(raw))
        rows = []
        for frac in fracs:
            tr, te = time_split(ver, args.date_col, frac)
            res = _fit_and_eval(tr, te, lr=args.lr, l2=args.l2, iters=args.iters)
            rows.append(
                {
                    "test_frac": frac,
                    "n_train": len(tr),
                    "n_test": len(te),
                    "auc_train": res["train_metrics"]["auc"],
                    "auc_test": res["test_metrics"]["auc"],
                    "logloss_test": res["test_metrics"]["logloss"],
                    "brier_test": res["test_metrics"]["brier"],
                }
            )
        sweep_df = pd.DataFrame(rows)
        lines.append("## Stress test: subiendo tamaño de TEST\n")
        lines.append(sweep_df.to_markdown(index=False))
        lines.append("\n")

    lines.append("## ROI top 20% (seleccionando por score)\n")
    lines.append("| score | split | n | winrate | ROI | avg_odds |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    lines.append(
        f"| Calibrada(P_Win) | train | {roi_train_cal['n']} | {roi_train_cal['winrate']:.1f}% | {roi_train_cal['roi_pct']:+.2f}% | {roi_train_cal['avg_odds']:.3f} |"
    )
    lines.append(
        f"| Calibrada(P_Win) | test | {roi_test_cal['n']} | {roi_test_cal['winrate']:.1f}% | {roi_test_cal['roi_pct']:+.2f}% | {roi_test_cal['avg_odds']:.3f} |"
    )
    lines.append(
        f"| Confianza actual | train | {roi_train_conf['n']} | {roi_train_conf['winrate']:.1f}% | {roi_train_conf['roi_pct']:+.2f}% | {roi_train_conf['avg_odds']:.3f} |"
    )
    lines.append(
        f"| Confianza actual | test | {roi_test_conf['n']} | {roi_test_conf['winrate']:.1f}% | {roi_test_conf['roi_pct']:+.2f}% | {roi_test_conf['avg_odds']:.3f} |\n"
    )

    lines.append("## Coeficientes (logit)\n")
    lines.append(coef_df.to_markdown(index=False))
    lines.append("\n")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("=" * 60)
    print("CALIBRACIÓN COMPLETADA")
    print("=" * 60)
    print("AUC Calibrada train/test:", round(tm["auc"], 4), round(sm["auc"], 4))
    print("AUC Confianza  train/test:", round(auc_conf_train, 4), round(auc_conf_test, 4))
    print("CSV:", args.output_csv)
    print("MD :", out_md)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
