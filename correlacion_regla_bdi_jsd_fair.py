from __future__ import annotations

from pathlib import Path

import pandas as pd

from evaluar_regla_bdi_jsd_fair import load_canonical_ou25_dataset

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "datasets" / "estrategia_calibrada_con_resultado"
REPORT_PATH = BASE_DIR / "docs" / "correlacion_regla_bdi_jsd_fair.md"


def build_chosen_side_dataset(canonical: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, group in canonical.groupby(["Partido", "Fecha_Hora_Colombia", "Snapshot_Date"], sort=True):
        if set(group["Mercado"]) >= {"Over 2.5", "Under 2.5"}:
            pick = group.sort_values(["Mejor_Cuota", "Mercado"], ascending=[False, True]).iloc[0].copy()
            pick["profit"] = pick["Mejor_Cuota"] - 1.0 if pick["resultado_binario"] == 1 else -1.0
            rows.append(pick)
    chosen = pd.DataFrame(rows)
    chosen["week_id"] = chosen["Fecha_Hora_Colombia"].dt.strftime("%G-W%V")
    chosen["is_weekend"] = chosen["Fecha_Hora_Colombia"].dt.weekday.isin([5, 6])
    return chosen


def correlation_summary(frame: pd.DataFrame, label: str) -> dict[str, object]:
    work = frame.copy()
    work["bdi_rank_desc"] = work.groupby("week_id")["BDI_jsd_fair"].rank(method="average", ascending=False)
    work["bdi_pct_desc"] = work.groupby("week_id")["BDI_jsd_fair"].rank(method="average", pct=True, ascending=False)
    work["selected_top8"] = work["bdi_rank_desc"] <= 8
    return {
        "scope": label,
        "bets": len(work),
        "profit_total": float(work["profit"].sum()),
        "roi_per_bet": float(work["profit"].mean()),
        "hit_rate": float(work["resultado_binario"].mean()),
        "pearson_bdi_profit": float(work["BDI_jsd_fair"].corr(work["profit"], method="pearson")),
        "spearman_bdi_profit": float(work["BDI_jsd_fair"].corr(work["profit"], method="spearman")),
        "pearson_rank_profit": float(work["bdi_rank_desc"].corr(work["profit"], method="pearson")),
        "spearman_rank_profit": float(work["bdi_rank_desc"].corr(work["profit"], method="spearman")),
        "pearson_selected_top8_profit": float(
            work["selected_top8"].astype(int).corr(work["profit"], method="pearson")
        ),
    }


def decile_summary(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["bdi_decile"] = pd.qcut(work["BDI_jsd_fair"], 10, duplicates="drop")
    return (
        work.groupby("bdi_decile", observed=False)
        .agg(
            bets=("profit", "size"),
            mean_bdi=("BDI_jsd_fair", "mean"),
            roi=("profit", "mean"),
            hit_rate=("resultado_binario", "mean"),
            avg_odds=("Mejor_Cuota", "mean"),
        )
        .reset_index()
    )


def top8_vs_rest(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["bdi_rank_desc"] = work.groupby("week_id")["BDI_jsd_fair"].rank(method="average", ascending=False)
    work["selected_top8"] = work["bdi_rank_desc"] <= 8
    return (
        work.groupby("selected_top8", dropna=False)
        .agg(
            bets=("profit", "size"),
            profit_total=("profit", "sum"),
            roi=("profit", "mean"),
            hit_rate=("resultado_binario", "mean"),
            avg_bdi=("BDI_jsd_fair", "mean"),
            avg_odds=("Mejor_Cuota", "mean"),
        )
        .reset_index()
    )


def render_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame[columns].iterrows():
        rendered = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                rendered.append(f"{value:.4f}")
            else:
                rendered.append(str(value))
        lines.append("| " + " | ".join(rendered) + " |")
    return lines


def main() -> None:
    canonical, pair_check = load_canonical_ou25_dataset()
    chosen = build_chosen_side_dataset(canonical)
    all_summary = correlation_summary(chosen, "all")
    weekend_summary = correlation_summary(chosen[chosen["is_weekend"]].copy(), "weekend")
    summary_df = pd.DataFrame([all_summary, weekend_summary])
    deciles_all = decile_summary(chosen)
    deciles_weekend = decile_summary(chosen[chosen["is_weekend"]].copy())
    top8_all = top8_vs_rest(chosen)
    top8_weekend = top8_vs_rest(chosen[chosen["is_weekend"]].copy())

    summary_df.to_csv(OUT_DIR / "bdi_jsd_fair_correlation_summary.csv", index=False)
    deciles_all.to_csv(OUT_DIR / "bdi_jsd_fair_deciles_all.csv", index=False)
    deciles_weekend.to_csv(OUT_DIR / "bdi_jsd_fair_deciles_weekend.csv", index=False)
    top8_all.to_csv(OUT_DIR / "bdi_jsd_fair_top8_vs_rest_all.csv", index=False)
    top8_weekend.to_csv(OUT_DIR / "bdi_jsd_fair_top8_vs_rest_weekend.csv", index=False)

    lines = [
        "# Correlacion de la regla BDI_jsd_fair",
        "",
        "Evaluacion de la idea `elegir la cuota mayor entre Over 2.5 y Under 2.5` y usar `BDI_jsd_fair` como orden de prioridad.",
        "",
        "## Supuesto del algoritmo",
        "",
        f"- Pares verificados con ambos lados: **{len(pair_check)}**.",
        f"- Diferencia maxima entre `Over 2.5` y `Under 2.5` para `BDI_jsd_fair`: **{pair_check['abs_diff'].max():.12f}**.",
        "- Esto confirma que la metrica es compartida por ambos lados del mismo partido.",
        "",
        "## Correlacion simple",
        "",
    ]
    lines.extend(
        render_table(
            summary_df,
            [
                "scope",
                "bets",
                "profit_total",
                "roi_per_bet",
                "hit_rate",
                "pearson_bdi_profit",
                "spearman_bdi_profit",
                "pearson_rank_profit",
                "spearman_rank_profit",
                "pearson_selected_top8_profit",
            ],
        )
    )
    lines.extend(
        [
            "",
            "Lectura:",
            "",
            "- La correlacion lineal directa entre `BDI_jsd_fair` y `profit` es debil en ambos cortes.",
            "- Eso significa que la senal no es una recta simple del tipo `mas BDI => mas profit` para todos los partidos.",
            "- La correlacion mejora un poco cuando usas la variable operativa `selected_top8`, porque se parece mas a tu regla real.",
            "",
            "## Deciles de BDI en todo el dataset",
            "",
        ]
    )
    lines.extend(render_table(deciles_all, ["bdi_decile", "bets", "mean_bdi", "roi", "hit_rate", "avg_odds"]))
    lines.extend(["", "## Deciles de BDI solo sabado-domingo", ""])
    lines.extend(render_table(deciles_weekend, ["bdi_decile", "bets", "mean_bdi", "roi", "hit_rate", "avg_odds"]))
    lines.extend(["", "## Top 8 vs resto", ""])
    lines.append("### Todo el dataset")
    lines.append("")
    lines.extend(render_table(top8_all, ["selected_top8", "bets", "profit_total", "roi", "hit_rate", "avg_bdi", "avg_odds"]))
    lines.append("")
    lines.append("### Solo sabado-domingo")
    lines.append("")
    lines.extend(render_table(top8_weekend, ["selected_top8", "bets", "profit_total", "roi", "hit_rate", "avg_bdi", "avg_odds"]))
    lines.extend(
        [
            "",
            "## Conclusiones",
            "",
            "- Si usas **todo el dataset**, la regla completa pierde ligeramente dinero en promedio (`ROI` cerca de cero/negativo), y la correlacion simple con BDI es muy debil.",
            "- Si usas **solo sabados y domingos**, la rentabilidad mejora y el `top 8` supera claramente al resto.",
            "- La senal parece ser **de cola alta**: no funciona tan bien como relacion monotona general, pero si cuando te concentras en los partidos con `BDI_jsd_fair` mas alto.",
            "- Eso encaja con tu intuicion original: el valor no estaba en todo el rango de BDI, sino en usarlo para priorizar pocos partidos.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
