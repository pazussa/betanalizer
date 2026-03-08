from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from combinar_bdi_con_under import load_canonical_dataset

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "datasets" / "estrategia_calibrada_con_resultado"
REPORT_PATH = BASE_DIR / "docs" / "validacion_estrategias_solo_pinnacle.md"


def parse_odds_map(text: object) -> dict[str, float]:
    pairs = re.findall(r"([^:;]+):([0-9]+(?:\.[0-9]+)?)", str(text))
    out: dict[str, float] = {}
    for book, odd in pairs:
        key = book.strip().lower()
        if not key:
            continue
        try:
            out[key] = float(odd)
        except ValueError:
            continue
    return out


def build_base() -> pd.DataFrame:
    frame = load_canonical_dataset().copy()
    frame["casa_best"] = frame["Mejor_Casa"].astype(str).str.lower().str.strip()

    odds_maps = []
    for _, row in frame[["Todas_Las_Cuotas", "casa_best", "Mejor_Cuota"]].iterrows():
        mapped = parse_odds_map(row["Todas_Las_Cuotas"])
        if row["casa_best"] and pd.notna(row["Mejor_Cuota"]):
            mapped[row["casa_best"]] = float(row["Mejor_Cuota"])
        odds_maps.append(mapped)

    frame["odds_map"] = odds_maps
    frame["pinnacle_odds"] = frame["odds_map"].apply(lambda x: x.get("pinnacle", np.nan))
    frame["is_pinnacle_best"] = frame["casa_best"].eq("pinnacle")
    frame["dow"] = frame["Fecha_Hora_Colombia"].dt.weekday
    frame["week_id"] = frame["Fecha_Hora_Colombia"].dt.strftime("%G-W%V")
    return frame


def mode_view(frame: pd.DataFrame, mode: str) -> pd.DataFrame:
    if mode == "strict_best_pinnacle":
        out = frame[frame["is_pinnacle_best"]].copy()
        out["quote"] = out["Mejor_Cuota"]
    elif mode == "pinnacle_available":
        out = frame[frame["pinnacle_odds"].notna()].copy()
        out["quote"] = out["pinnacle_odds"]
    else:
        raise ValueError(mode)

    out["profit_pin"] = np.where(out["result_bin"] == 1, out["quote"] - 1.0, -1.0)
    return out


def split_weeks(weeks: list[str]) -> tuple[list[str], list[str], list[str]]:
    if not weeks:
        return [], [], []
    n = len(weeks)
    train_n = max(1, int(round(n * 0.6)))
    valid_n = max(1, int(round(n * 0.2)))
    if train_n + valid_n >= n:
        train_n = max(1, n - 2)
        valid_n = 1 if n > 1 else 0
    test_n = n - train_n - valid_n
    if test_n <= 0:
        if train_n > 1:
            train_n -= 1
        test_n = n - train_n - valid_n
    train = weeks[:train_n]
    valid = weeks[train_n : train_n + valid_n]
    test = weeks[train_n + valid_n :]
    return train, valid, test


def summarize(df: pd.DataFrame) -> dict[str, float]:
    bets = len(df)
    if bets == 0:
        return {
            "bets": 0,
            "hits": 0,
            "hit_rate": np.nan,
            "profit_total": np.nan,
            "roi": np.nan,
            "avg_odds": np.nan,
            "weeks": 0,
            "profitable_weeks": 0,
        }
    weekly = df.groupby("week_id")["profit_pin"].sum()
    return {
        "bets": int(bets),
        "hits": int(df["result_bin"].sum()),
        "hit_rate": float(df["result_bin"].mean()),
        "profit_total": float(df["profit_pin"].sum()),
        "roi": float(df["profit_pin"].mean()),
        "avg_odds": float(df["quote"].mean()),
        "weeks": int(df["week_id"].nunique()),
        "profitable_weeks": int((weekly > 0).sum()),
    }


def evaluate_strategy(df: pd.DataFrame, rule: str, name: str, mode: str) -> dict[str, object]:
    subset = df.query(rule).copy()
    weeks = sorted(subset["week_id"].dropna().unique().tolist())
    train_w, valid_w, test_w = split_weeks(weeks)

    train = subset[subset["week_id"].isin(train_w)].copy()
    valid = subset[subset["week_id"].isin(valid_w)].copy()
    test = subset[subset["week_id"].isin(test_w)].copy()
    oos = subset[subset["week_id"].isin(valid_w + test_w)].copy()

    all_m = summarize(subset)
    train_m = summarize(train)
    valid_m = summarize(valid)
    test_m = summarize(test)
    oos_m = summarize(oos)

    return {
        "mode": mode,
        "strategy": name,
        "rule": rule,
        **{f"all_{k}": v for k, v in all_m.items()},
        **{f"train_{k}": v for k, v in train_m.items()},
        **{f"valid_{k}": v for k, v in valid_m.items()},
        **{f"test_{k}": v for k, v in test_m.items()},
        **{f"oos_{k}": v for k, v in oos_m.items()},
        "valid_positive": bool(valid_m["roi"] > 0) if pd.notna(valid_m["roi"]) else False,
        "test_positive": bool(test_m["roi"] > 0) if pd.notna(test_m["roi"]) else False,
        "oos_positive": bool(oos_m["roi"] > 0) if pd.notna(oos_m["roi"]) else False,
    }


def render_table(df: pd.DataFrame, cols: list[str]) -> list[str]:
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df[cols].iterrows():
        cells: list[str] = []
        for col in cols:
            val = row[col]
            if isinstance(val, float):
                cells.append(f"{val:.3f}")
            else:
                cells.append(str(val))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def main() -> None:
    base = build_base()
    strategies = [
        ("S1_sat_u25_m375", "dow == 5 and Mercado == 'Under 2.5' and Margen_Casa_Pct <= 3.75"),
        ("S2_sun_u35", "dow == 6 and Mercado == 'Under 3.5'"),
        (
            "P_user_combo",
            "(dow == 5 and Mercado == 'Under 2.5' and Margen_Casa_Pct <= 3.75) or (dow == 6 and Mercado == 'Under 3.5')",
        ),
        ("S1_sat_u25_m32", "dow == 5 and Mercado == 'Under 2.5' and Margen_Casa_Pct <= 3.2"),
        ("S1_sat_u25_m33", "dow == 5 and Mercado == 'Under 2.5' and Margen_Casa_Pct <= 3.3"),
        ("S1_sat_u25_m389", "dow == 5 and Mercado == 'Under 2.5' and Margen_Casa_Pct <= 3.89"),
        ("S_wknd_u25_m375", "dow in [5, 6] and Mercado == 'Under 2.5' and Margen_Casa_Pct <= 3.75"),
        ("S_wknd_u25_m389", "dow in [5, 6] and Mercado == 'Under 2.5' and Margen_Casa_Pct <= 3.89"),
        ("S_wknd_u35", "dow in [5, 6] and Mercado == 'Under 3.5'"),
        ("S_sun_u35_m65", "dow == 6 and Mercado == 'Under 3.5' and Margen_Casa_Pct <= 6.5"),
        ("S_sun_u35_m55", "dow == 6 and Mercado == 'Under 3.5' and Margen_Casa_Pct <= 5.5"),
    ]

    rows: list[dict[str, object]] = []
    for mode in ["strict_best_pinnacle", "pinnacle_available"]:
        view = mode_view(base, mode)
        for name, rule in strategies:
            rows.append(evaluate_strategy(view, rule, name, mode))

    results = pd.DataFrame(rows)
    results = results.sort_values(["mode", "oos_roi", "all_roi"], ascending=[True, False, False])
    results.to_csv(OUT_DIR / "pinnacle_strategy_validation_all.csv", index=False)

    recommended = results[
        (results["all_bets"] >= 20)
        & (results["valid_bets"] >= 5)
        & (results["test_bets"] >= 5)
        & (results["valid_positive"])
        & (results["test_positive"])
        & (results["oos_positive"])
    ].copy()
    recommended = recommended.sort_values(["mode", "oos_roi", "all_roi"], ascending=[True, False, False])
    recommended.to_csv(OUT_DIR / "pinnacle_strategy_validation_recommended.csv", index=False)

    lines = [
        "# Validacion de estrategias solo pinnacle",
        "",
        "Se validaron reglas en dos modos de ejecucion:",
        "- `strict_best_pinnacle`: solo filas donde `Mejor_Casa == pinnacle`.",
        "- `pinnacle_available`: apostar en pinnacle cuando su cuota esta disponible en el partido/mercado.",
        "",
        "Metodologia:",
        "- Profit por apuesta: `cuota_pinnacle - 1` si acierta, `-1` si falla.",
        "- Corte temporal por semanas con train/valid/test (60/20/20 aprox. segun cobertura de cada regla).",
        "",
    ]

    for mode in ["strict_best_pinnacle", "pinnacle_available"]:
        mode_df = results[results["mode"] == mode].copy()
        top = mode_df.head(8).copy()
        lines.extend([f"## Top reglas ({mode})", ""])
        lines.extend(
            render_table(
                top,
                [
                    "strategy",
                    "all_bets",
                    "all_hits",
                    "all_roi",
                    "all_profit_total",
                    "oos_bets",
                    "oos_roi",
                    "valid_roi",
                    "test_roi",
                ],
            )
        )
        lines.extend([""])

    if not recommended.empty:
        lines.extend(["## Reglas recomendadas (estables)", ""])
        lines.extend(
            render_table(
                recommended,
                [
                    "mode",
                    "strategy",
                    "all_bets",
                    "all_hits",
                    "all_roi",
                    "all_profit_total",
                    "oos_roi",
                    "valid_roi",
                    "test_roi",
                ],
            )
        )
    else:
        lines.extend(["## Reglas recomendadas (estables)", "", "No hubo reglas que cumplieran todos los filtros de estabilidad."])

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report: {REPORT_PATH}")
    print(f"All results: {OUT_DIR / 'pinnacle_strategy_validation_all.csv'}")
    print(f"Recommended: {OUT_DIR / 'pinnacle_strategy_validation_recommended.csv'}")


if __name__ == "__main__":
    main()
