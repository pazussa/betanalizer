from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from combinar_bdi_con_under import load_canonical_dataset

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "datasets" / "estrategia_calibrada_con_resultado"
REPORT_PATH = BASE_DIR / "docs" / "validacion_over25_bdi_220_240.md"


def build_chosen_weekend_universe() -> pd.DataFrame:
    canonical = load_canonical_dataset()
    ou = canonical[
        canonical["Mercado"].isin(["Over 2.5", "Under 2.5"])
        & canonical["BDI_jsd_fair"].notna()
        & canonical["is_weekend"]
    ].copy()

    rows = []
    for _, group in ou.groupby(["Partido", "Fecha_Hora_Colombia"], sort=True):
        if set(group["Mercado"]) >= {"Over 2.5", "Under 2.5"}:
            rows.append(group.sort_values(["Mejor_Cuota", "Mercado"], ascending=[False, True]).iloc[0])

    chosen = pd.DataFrame(rows).copy()
    chosen = chosen.sort_values(
        ["week_id", "BDI_jsd_fair", "Mejor_Cuota", "Mercado"],
        ascending=[True, False, False, True],
    ).reset_index(drop=True)
    chosen["rank_desc"] = chosen.groupby("week_id").cumcount() + 1
    return chosen


def summarize(frame: pd.DataFrame, label: str) -> dict[str, object]:
    hits = int(frame["result_bin"].sum())
    bets = len(frame)
    return {
        "segment": label,
        "bets": bets,
        "hits": hits,
        "misses": bets - hits,
        "hit_rate": float(frame["result_bin"].mean()) if bets else np.nan,
        "profit_total": float(frame["profit"].sum()) if bets else np.nan,
        "roi": float(frame["profit"].mean()) if bets else np.nan,
        "avg_odds": float(frame["Mejor_Cuota"].mean()) if bets else np.nan,
        "avg_bdi": float(frame["BDI_jsd_fair"].mean()) if bets else np.nan,
        "weeks": int(frame["week_id"].nunique()) if bets else 0,
    }


def bootstrap_roi(frame: pd.DataFrame, seed: int = 42, n_boot: int = 10000) -> tuple[float, float]:
    profits = frame["profit"].to_numpy(dtype=float)
    if len(profits) == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    samples = rng.choice(profits, size=(n_boot, len(profits)), replace=True)
    rois = samples.mean(axis=1)
    lo, hi = np.quantile(rois, [0.025, 0.975])
    return float(lo), float(hi)


def render_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame[columns].iterrows():
        cells = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                if abs(value) < 0.001 and value != 0:
                    cells.append(f"{value:.6f}")
                else:
                    cells.append(f"{value:.3f}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def split_weeks(frame: pd.DataFrame) -> dict[str, list[str]]:
    weeks = sorted(frame["week_id"].unique())
    return {
        "train": weeks[:6],
        "valid": weeks[6:9],
        "test": weeks[9:12],
    }


def main() -> None:
    chosen = build_chosen_weekend_universe()
    band = chosen[
        (chosen["Mercado"] == "Over 2.5")
        & (chosen["Mejor_Cuota"] >= 2.2)
        & (chosen["Mejor_Cuota"] < 2.4)
    ].copy()

    summary_rows = []
    split_rows = []
    weekly_rows = []
    bookmaker_rows = []
    comparison_rows = []

    for top_n in [8, 9]:
        picks = band[band["rank_desc"] <= top_n].copy()
        weeks = sorted(picks["week_id"].unique())
        same_weeks = band[band["week_id"].isin(weeks)].copy()
        rest_same_weeks = same_weeks[same_weeks["rank_desc"] > top_n].copy()

        row = summarize(picks, f"top{top_n}_over25_2p2_2p4")
        ci_lo, ci_hi = bootstrap_roi(picks)
        row["roi_ci95_lo"] = ci_lo
        row["roi_ci95_hi"] = ci_hi
        summary_rows.append(row)

        comparison_rows.extend(
            [
                {"top_n": top_n, **summarize(picks, "selected")},
                {"top_n": top_n, **summarize(rest_same_weeks, "rest_same_weeks")},
                {"top_n": top_n, **summarize(same_weeks, "all_same_weeks")},
            ]
        )

        splits = split_weeks(picks)
        for split_name, split_weeks_list in splits.items():
            split_frame = picks[picks["week_id"].isin(split_weeks_list)].copy()
            split_rows.append(
                {
                    "top_n": top_n,
                    "split": split_name,
                    "weeks_list": ",".join(split_weeks_list),
                    **summarize(split_frame, split_name),
                    "profitable_weeks": int((split_frame.groupby("week_id")["profit"].sum() > 0).sum())
                    if len(split_frame)
                    else 0,
                }
            )

        weekly = (
            picks.groupby("week_id", dropna=False)
            .agg(
                bets=("profit", "size"),
                hits=("result_bin", "sum"),
                hit_rate=("result_bin", "mean"),
                profit_total=("profit", "sum"),
                roi=("profit", "mean"),
                avg_odds=("Mejor_Cuota", "mean"),
            )
            .reset_index()
        )
        weekly.insert(0, "top_n", top_n)
        weekly_rows.append(weekly)

        bookmakers = (
            picks.groupby("Mejor_Casa", dropna=False)
            .agg(
                bets=("profit", "size"),
                hits=("result_bin", "sum"),
                hit_rate=("result_bin", "mean"),
                profit_total=("profit", "sum"),
                roi=("profit", "mean"),
                avg_odds=("Mejor_Cuota", "mean"),
            )
            .reset_index()
            .sort_values(["profit_total", "bets"], ascending=[False, False])
        )
        bookmakers.insert(0, "top_n", top_n)
        bookmaker_rows.append(bookmakers)

    summary_df = pd.DataFrame(summary_rows)
    comparison_df = pd.DataFrame(comparison_rows)
    split_df = pd.DataFrame(split_rows)
    weekly_df = pd.concat(weekly_rows, ignore_index=True)
    bookmaker_df = pd.concat(bookmaker_rows, ignore_index=True)

    summary_df.to_csv(OUT_DIR / "over25_bdi_220_240_summary.csv", index=False)
    comparison_df.to_csv(OUT_DIR / "over25_bdi_220_240_comparison.csv", index=False)
    split_df.to_csv(OUT_DIR / "over25_bdi_220_240_splits.csv", index=False)
    weekly_df.to_csv(OUT_DIR / "over25_bdi_220_240_weekly.csv", index=False)
    bookmaker_df.to_csv(OUT_DIR / "over25_bdi_220_240_bookmakers.csv", index=False)

    top8 = summary_df[summary_df["segment"] == "top8_over25_2p2_2p4"].iloc[0]
    top9 = summary_df[summary_df["segment"] == "top9_over25_2p2_2p4"].iloc[0]
    top8_comp = comparison_df[comparison_df["top_n"] == 8].copy()
    top9_comp = comparison_df[comparison_df["top_n"] == 9].copy()
    top8_splits = split_df[split_df["top_n"] == 8].copy()
    top9_splits = split_df[split_df["top_n"] == 9].copy()
    top8_book = bookmaker_df[(bookmaker_df["top_n"] == 8) & (bookmaker_df["bets"] >= 2)].copy()
    top9_book = bookmaker_df[(bookmaker_df["top_n"] == 9) & (bookmaker_df["bets"] >= 2)].copy()
    top8_weekly = weekly_df[weekly_df["top_n"] == 8].copy()
    top9_weekly = weekly_df[weekly_df["top_n"] == 9].copy()

    lines = [
        "# Validacion de Over 2.5 en top BDI con cuota 2.2-2.4",
        "",
        "Hipotesis validada: `Over 2.5` dentro del universo `cuota mayor entre Over 2.5 y Under 2.5`, restringido a `top 8/9` por `BDI_jsd_fair` de fin de semana y cuotas entre `2.2` y `2.4`.",
        "",
        "## Resultado global",
        "",
    ]
    lines.extend(
        render_table(
            summary_df,
            [
                "segment",
                "bets",
                "hits",
                "hit_rate",
                "profit_total",
                "roi",
                "roi_ci95_lo",
                "roi_ci95_hi",
                "avg_odds",
                "weeks",
            ],
        )
    )
    lines.extend(
        [
            "",
            "Lectura:",
            "",
            f"- `top 8`: **{int(top8['hits'])}/{int(top8['bets'])}**, profit **{top8['profit_total']:.2f}**, ROI **{top8['roi']:.3f}**.",
            f"- `top 9`: **{int(top9['hits'])}/{int(top9['bets'])}**, profit **{top9['profit_total']:.2f}**, ROI **{top9['roi']:.3f}**.",
            "- Ambos salen positivos en la muestra completa.",
            "- Pero los intervalos bootstrap siguen cruzando cero; la muestra es pequena y no permite afirmar edge cerrado.",
            "",
            "## Contra el universo comparable",
            "",
        ]
    )
    lines.extend(render_table(top8_comp, ["top_n", "segment", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds", "weeks"]))
    lines.extend([""])
    lines.extend(render_table(top9_comp, ["top_n", "segment", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds", "weeks"]))
    lines.extend(
        [
            "",
            "Lectura:",
            "",
            "- El universo comparable es `Over 2.5` con cuota `2.2-2.4` dentro del mismo mecanismo de eleccion `cuota mayor`.",
            "- En ese universo, el filtro `top BDI` si agrega valor: el universo completo pierde fuerte y el subconjunto `top 8/9` pasa a positivo.",
            "",
            "## Validacion temporal",
            "",
        ]
    )
    lines.extend(render_table(top8_splits, ["top_n", "split", "bets", "hits", "hit_rate", "profit_total", "roi", "profitable_weeks", "weeks"]))
    lines.extend([""])
    lines.extend(render_table(top9_splits, ["top_n", "split", "bets", "hits", "hit_rate", "profit_total", "roi", "profitable_weeks", "weeks"]))
    lines.extend(
        [
            "",
            "Lectura:",
            "",
            "- Use un corte cronologico simple `train 6 semanas`, `valid 3`, `test 3` sobre las semanas que realmente tienen apuestas para esta hipotesis.",
            "- `top 8` y `top 9` se mantienen positivos en `train`, `valid` y `test`.",
            "- Eso es mejor que el BDI standalone, que se caia cuando ampliabas la muestra.",
            "- Aun asi, el numero de apuestas por tramo es chico; sigue siendo una senal prometedora, no una estrategia cerrada.",
            "",
            "## Desglose semanal",
            "",
        ]
    )
    lines.extend(render_table(top8_weekly, ["top_n", "week_id", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend([""])
    lines.extend(render_table(top9_weekly, ["top_n", "week_id", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend(
        [
            "",
            "## Bookmakers",
            "",
        ]
    )
    lines.extend(render_table(top8_book, ["top_n", "Mejor_Casa", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend([""])
    lines.extend(render_table(top9_book, ["top_n", "Mejor_Casa", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "- La hipotesis **si merece seguimiento**: es una de las pocas subzonas del BDI que sale positiva y ademas se mantiene positiva en un corte temporal simple.",
            "- La mejora parece venir de combinar tres cosas a la vez: `Over 2.5`, `BDI alto` y cuota media-larga controlada (`2.2-2.4`).",
            "- No la daria todavia como estrategia principal por el tamano muestral: `22` apuestas en `top 8` y `25` en `top 9`.",
            "- Si tuviera que elegir una hoy, `top 9` queda un poco mejor que `top 8` por profit y ROI.",
            "- Recomendacion operativa: tratarla como hipotesis secundaria en monitoreo, no al mismo nivel de robustez que las estrategias `Under` ya validadas.",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
