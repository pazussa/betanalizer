#!/usr/bin/env python3
"""Train/test validation to see which components correlate with outcomes.

This script:
- Loads `data/master_dataset_deduped.csv` (or an input CSV).
- Keeps only rows with Resultado in {Acertado, Fallido}.
- Builds outcome y=1 for Acertado.
- Computes per-feature correlations and univariate AUC on train and test.
- Reports ROI by confidence bins (quintiles/deciles) on train and test.

No ML dependencies required.
"""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


FEATURES = [
    # Señales (incluye calibradas si están en el CSV)
    "P_Win_Calibrada",
    "Confianza_Calibrada",
    "Confianza",
    "Score_Final",
    "Volatilidad_Pct",
    "Margen_Casa_Pct",
    "Mejor_Cuota",
    "Cuota_Promedio_Mercado",
    "Diferencia_Cuota_Promedio",
    "Num_Casas",
]


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def auc_from_scores(scores: np.ndarray, y: np.ndarray) -> float:
    """Compute AUC using rank statistic; handles ties with average ranks."""
    scores = np.asarray(scores, dtype=float)
    y = np.asarray(y, dtype=int)
    if scores.size == 0:
        return float("nan")

    pos = y == 1
    n_pos = int(pos.sum())
    n_neg = int((~pos).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")

    # rankdata equivalent (average ranks for ties)
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)

    # average ranks for ties
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

    auc = (ranks[pos].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def profit_per_bet(y: np.ndarray, odds: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=int)
    odds = np.asarray(odds, dtype=float)
    return np.where(y == 1, odds - 1.0, -1.0)


@dataclass
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


def random_split(df: pd.DataFrame, test_frac: float, seed: int) -> Split:
    d = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    n = len(d)
    cut = int(np.floor((1.0 - test_frac) * n))
    return Split(train=d.iloc[:cut].copy(), test=d.iloc[cut:].copy())


def eval_split(name: str, train: pd.DataFrame, test: pd.DataFrame) -> dict:
    out: dict = {"split": name}

    def _eval_one(label: str, part: pd.DataFrame) -> dict:
        y = (part["Resultado"].astype(str).str.strip() == "Acertado").astype(int).values
        odds = _to_num(part["Mejor_Cuota"]).fillna(np.nan).values
        profits = profit_per_bet(y, odds)

        res = {
            "n": int(len(part)),
            "wins": int(y.sum()),
            "losses": int((1 - y).sum()),
            "roi_pct": float(np.nanmean(profits) * 100.0),
        }

        # feature stats
        feat_rows = []
        for f in FEATURES:
            if f not in part.columns:
                continue
            x = _to_num(part[f]).values
            mask = np.isfinite(x)
            if mask.sum() < 20:
                continue
            x2 = x[mask]
            y2 = y[mask]
            # Pearson corr
            corr = float(np.corrcoef(x2, y2)[0, 1]) if len(np.unique(y2)) > 1 else float("nan")
            auc = auc_from_scores(x2, y2)
            feat_rows.append((f, int(mask.sum()), corr, auc))

        feats_df = pd.DataFrame(feat_rows, columns=["feature", "n", "pearson_corr", "auc"]).sort_values(
            "auc", ascending=False
        )

        def _dir_from_auc(v: float) -> int:
            if not np.isfinite(v):
                return 1
            return 1 if float(v) >= 0.5 else -1

        feats_df["direction"] = feats_df["auc"].map(_dir_from_auc)
        res["features"] = feats_df

        dir_map = {row.feature: int(row.direction) for row in feats_df.itertuples(index=False)}

        def _add_bins(col_name: str, key_prefix: str, *, direction: int = 1, include_deciles: bool = True) -> None:
            if col_name not in part.columns:
                return
            conf = _to_num(part[col_name])
            part2 = part.copy()
            part2["_conf"] = conf
            part2["_score"] = (direction * conf).astype(float)
            part2 = part2[np.isfinite(part2["_score"])].copy()
            if len(part2) < 50:
                return

            part2["_q5"] = pd.qcut(part2["_score"], 5, labels=False, duplicates="drop")
            bins_to_emit = [("_q5", f"{key_prefix}_q5")]
            if include_deciles:
                part2["_dec"] = pd.qcut(part2["_score"], 10, labels=False, duplicates="drop")
                bins_to_emit.append(("_dec", f"{key_prefix}_decile"))

            for col, label_bins in bins_to_emit:
                rows = []
                for b, g in part2.groupby(col):
                    yb = (g["Resultado"].astype(str).str.strip() == "Acertado").astype(int).values
                    ob = _to_num(g["Mejor_Cuota"]).values
                    pb = profit_per_bet(yb, ob)
                    rows.append(
                        (
                            int(b),
                            int(len(g)),
                            float(g["_conf"].min()),
                            float(g["_conf"].max()),
                            float(yb.mean()),
                            float(np.nanmean(pb) * 100.0),
                            float(np.nanmean(ob)),
                        )
                    )
                res[label_bins] = pd.DataFrame(
                    rows,
                    columns=["bin", "n", "conf_min", "conf_max", "winrate", "roi_pct", "avg_odds"],
                ).sort_values("bin")

        # ROI bins for available scoring columns (using inferred direction)
        _add_bins("Confianza", "Confianza", direction=dir_map.get("Confianza", 1), include_deciles=True)
        _add_bins(
            "Confianza_Calibrada",
            "Confianza_Calibrada",
            direction=dir_map.get("Confianza_Calibrada", 1),
            include_deciles=True,
        )
        _add_bins("P_Win_Calibrada", "P_Win_Calibrada", direction=dir_map.get("P_Win_Calibrada", 1), include_deciles=True)

        # Per-component bins (quintiles only to keep report readable)
        for extra in [
            "Volatilidad_Pct",
            "Margen_Casa_Pct",
            "Diferencia_Cuota_Promedio",
            "Num_Casas",
            "Score_Final",
            "Mejor_Cuota",
            "Cuota_Promedio_Mercado",
        ]:
            _add_bins(extra, extra, direction=dir_map.get(extra, 1), include_deciles=False)

        return res

    out["train"] = _eval_one("train", train)
    out["test"] = _eval_one("test", test)
    return out


def _df_to_md(df: pd.DataFrame, floatfmt: str = ".3f") -> str:
    if df is None or df.empty:
        return "(sin datos)"
    # format
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda v: ("" if pd.isna(v) else format(float(v), floatfmt)))
    return d.to_markdown(index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate which components correlate with betting outcomes")
    parser.add_argument(
        "--input",
        default="data/master_dataset_deduped.csv",
        help="Input CSV (default: data/master_dataset_deduped.csv)",
    )
    parser.add_argument(
        "--date-col",
        default="Fecha_Hora_Colombia",
        help="Datetime column for time split",
    )
    parser.add_argument("--test-frac", type=float, default=0.2, help="Fraction for test split")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for random split")
    parser.add_argument(
        "--output",
        default=None,
        help="Markdown report output (default: docs/validacion_componentes_<timestamp>.md)",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    # Keep only verified
    df = df[df["Resultado"].astype(str).str.strip().isin(["Acertado", "Fallido"])].copy()
    if df.empty:
        logger.error("No verified rows (Acertado/Fallido) in input")
        return 1

    # Splits
    s_time = time_split(df, args.date_col, args.test_frac)
    s_rand = random_split(df, args.test_frac, args.seed)

    res_time = eval_split("time", s_time.train, s_time.test)
    res_rand = eval_split("random", s_rand.train, s_rand.test)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = args.output or f"docs/validacion_componentes_{ts}.md"

    lines: list[str] = []
    lines.append(f"# Validación de Componentes ({ts})\n")
    lines.append(f"Fuente: `{args.input}`\n")
    lines.append(f"Filas verificadas: {len(df)}\n")

    def write_block(title: str, res: dict):
        lines.append(f"## Split: {title}\n")
        for part in ["train", "test"]:
            r = res[part]
            lines.append(f"### {part.upper()}\n")
            lines.append(f"- n={r['n']} wins={r['wins']} losses={r['losses']} ROI={r['roi_pct']:+.2f}%\n")
            lines.append("**Features (AUC y correlación, univariado)**\n")
            lines.append(_df_to_md(r["features"].head(20), floatfmt=".4f"))
            lines.append("\n")

            feat_dir = {}
            if isinstance(r.get("features"), pd.DataFrame) and not r["features"].empty and "direction" in r["features"].columns:
                feat_dir = dict(zip(r["features"]["feature"].astype(str), r["features"]["direction"].astype(int)))

            def _dir_label(feature: str) -> str:
                d = feat_dir.get(feature, 1)
                return "ALTO mejor" if d >= 0 else "BAJO mejor"

            for key, label in [
                ("P_Win_Calibrada_q5", "P_Win_Calibrada (quintiles)"),
                ("P_Win_Calibrada_decile", "P_Win_Calibrada (deciles)"),
                ("Confianza_Calibrada_q5", "Confianza_Calibrada (quintiles)"),
                ("Confianza_Calibrada_decile", "Confianza_Calibrada (deciles)"),
                ("Confianza_q5", "Confianza (quintiles)"),
                ("Confianza_decile", "Confianza (deciles)"),
            ]:
                if key in r:
                    lines.append(f"**{label} (ROI/winrate)**\n")
                    lines.append(_df_to_md(r[key], floatfmt=".3f"))
                    lines.append("\n")

            # Per-component tables (quintiles only)
            for feat in [
                "Volatilidad_Pct",
                "Margen_Casa_Pct",
                "Diferencia_Cuota_Promedio",
                "Num_Casas",
                "Score_Final",
                "Mejor_Cuota",
                "Cuota_Promedio_Mercado",
            ]:
                k = f"{feat}_q5"
                if k in r:
                    lines.append(f"**{feat} (quintiles, {_dir_label(feat)}) (ROI/winrate)**\n")
                    lines.append(_df_to_md(r[k], floatfmt=".3f"))
                    lines.append("\n")

    write_block("Time-based", res_time)
    write_block("Random", res_rand)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Wrote report: %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
