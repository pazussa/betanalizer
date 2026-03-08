from __future__ import annotations

from pathlib import Path

import pandas as pd

from combinar_bdi_con_under import load_canonical_dataset

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "datasets" / "estrategia_calibrada_con_resultado"
REPORT_PATH = BASE_DIR / "docs" / "autopsia_estrategia_bdi.md"


def build_chosen_weekend_universe(canonical: pd.DataFrame) -> pd.DataFrame:
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
        "strategy": label,
        "bets": bets,
        "hits": hits,
        "misses": bets - hits,
        "hit_rate": float(frame["result_bin"].mean()),
        "profit_total": float(frame["profit"].sum()),
        "roi": float(frame["profit"].mean()),
        "avg_odds": float(frame["Mejor_Cuota"].mean()),
        "avg_bdi": float(frame["BDI_jsd_fair"].mean()),
        "over_share": float((frame["Mercado"] == "Over 2.5").mean()),
    }


def aggregate(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    grouped = (
        frame.groupby(group_cols, dropna=False, observed=False)
        .agg(
            bets=("profit", "size"),
            hits=("result_bin", "sum"),
            hit_rate=("result_bin", "mean"),
            profit_total=("profit", "sum"),
            roi=("profit", "mean"),
            avg_odds=("Mejor_Cuota", "mean"),
            avg_bdi=("BDI_jsd_fair", "mean"),
            avg_margin=("Margen_Casa_Pct", "mean"),
        )
        .reset_index()
    )
    grouped["hits"] = grouped["hits"].astype(int)
    grouped["misses"] = grouped["bets"] - grouped["hits"]
    return grouped


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


def main() -> None:
    canonical = load_canonical_dataset()
    chosen = build_chosen_weekend_universe(canonical)
    chosen["selected_top8"] = chosen["rank_desc"] <= 8
    chosen["selected_top9"] = chosen["rank_desc"] <= 9

    summary_rows = [
        summarize(chosen[chosen["selected_top8"]].copy(), "BDI weekend top8 cuota mayor"),
        summarize(chosen[chosen["selected_top9"]].copy(), "BDI weekend top9 cuota mayor"),
    ]
    summary_df = pd.DataFrame(summary_rows)

    selected_vs_rest_rows = []
    for top_n, flag in [(8, "selected_top8"), (9, "selected_top9")]:
        work = chosen.copy()
        work["selection"] = work[flag].map({True: f"top{top_n}", False: "resto"})
        grouped = aggregate(work, ["selection"])
        grouped.insert(0, "top_n", top_n)
        selected_vs_rest_rows.append(grouped)
    selected_vs_rest_df = pd.concat(selected_vs_rest_rows, ignore_index=True)

    weekly_rows = []
    market_rows = []
    odds_rows = []
    bookmaker_rows = []
    league_rows = []
    for top_n, flag in [(8, "selected_top8"), (9, "selected_top9")]:
        picks = chosen[chosen[flag]].copy()
        picks["top_n"] = top_n
        picks["odds_bin"] = pd.cut(
            picks["Mejor_Cuota"],
            bins=[0, 2.0, 2.2, 2.4, 2.6, 10],
            right=False,
        )
        weekly_rows.append(aggregate(picks, ["top_n", "week_id"]).sort_values(["top_n", "week_id"]))
        market_rows.append(aggregate(picks, ["top_n", "Mercado"]).sort_values(["top_n", "Mercado"]))
        odds_rows.append(aggregate(picks, ["top_n", "Mercado", "odds_bin"]).sort_values(["top_n", "Mercado", "odds_bin"]))
        bookmaker_rows.append(
            aggregate(picks, ["top_n", "Mejor_Casa"]).sort_values(["top_n", "profit_total", "bets"])
        )
        league_rows.append(aggregate(picks, ["top_n", "Liga"]).sort_values(["top_n", "profit_total", "bets"]))

    weekly_df = pd.concat(weekly_rows, ignore_index=True)
    market_df = pd.concat(market_rows, ignore_index=True)
    odds_df = pd.concat(odds_rows, ignore_index=True)
    bookmaker_df = pd.concat(bookmaker_rows, ignore_index=True)
    league_df = pd.concat(league_rows, ignore_index=True)

    rank_df = aggregate(chosen, ["rank_desc"]).sort_values("rank_desc")

    cumulative_rows = []
    for top_n in range(1, int(chosen["rank_desc"].max()) + 1):
        cumulative_rows.append(summarize(chosen[chosen["rank_desc"] <= top_n].copy(), f"top_{top_n}"))
    cumulative_df = pd.DataFrame(cumulative_rows)
    cumulative_df["top_n"] = range(1, len(cumulative_df) + 1)

    chosen["rank_bucket"] = pd.cut(
        chosen["rank_desc"],
        bins=[0, 3, 8, 20, 1000],
        labels=["1-3", "4-8", "9-20", "21+"],
    )
    bucket_market_df = aggregate(chosen, ["rank_bucket", "Mercado"]).sort_values(["rank_bucket", "Mercado"])

    bdi_odds_rows = []
    for label, frame in [
        ("all_chosen", chosen),
        ("top8", chosen[chosen["selected_top8"]].copy()),
        ("top9", chosen[chosen["selected_top9"]].copy()),
    ]:
        bdi_odds_rows.append(
            {
                "scope": label,
                "bets": len(frame),
                "hit_rate": float(frame["result_bin"].mean()),
                "profit_total": float(frame["profit"].sum()),
                "roi": float(frame["profit"].mean()),
                "avg_odds": float(frame["Mejor_Cuota"].mean()),
                "avg_bdi": float(frame["BDI_jsd_fair"].mean()),
                "over_share": float((frame["Mercado"] == "Over 2.5").mean()),
                "pearson_bdi_odds": float(frame["BDI_jsd_fair"].corr(frame["Mejor_Cuota"], method="pearson")),
                "spearman_bdi_odds": float(frame["BDI_jsd_fair"].corr(frame["Mejor_Cuota"], method="spearman")),
            }
        )
    bdi_odds_df = pd.DataFrame(bdi_odds_rows)

    summary_df.to_csv(OUT_DIR / "bdi_autopsia_summary.csv", index=False)
    selected_vs_rest_df.to_csv(OUT_DIR / "bdi_autopsia_selected_vs_rest.csv", index=False)
    weekly_df.to_csv(OUT_DIR / "bdi_autopsia_weekly.csv", index=False)
    market_df.to_csv(OUT_DIR / "bdi_autopsia_market.csv", index=False)
    odds_df.to_csv(OUT_DIR / "bdi_autopsia_market_odds.csv", index=False)
    bookmaker_df.to_csv(OUT_DIR / "bdi_autopsia_bookmaker.csv", index=False)
    league_df.to_csv(OUT_DIR / "bdi_autopsia_league.csv", index=False)
    rank_df.to_csv(OUT_DIR / "bdi_autopsia_rank.csv", index=False)
    cumulative_df.to_csv(OUT_DIR / "bdi_autopsia_cumulative_topn.csv", index=False)
    bucket_market_df.to_csv(OUT_DIR / "bdi_autopsia_rank_bucket_market.csv", index=False)
    bdi_odds_df.to_csv(OUT_DIR / "bdi_autopsia_bdi_odds_link.csv", index=False)

    top8 = summary_df[summary_df["strategy"] == "BDI weekend top8 cuota mayor"].iloc[0]
    top9 = summary_df[summary_df["strategy"] == "BDI weekend top9 cuota mayor"].iloc[0]
    top8_vs_rest = selected_vs_rest_df[(selected_vs_rest_df["top_n"] == 8)].copy()
    top9_vs_rest = selected_vs_rest_df[(selected_vs_rest_df["top_n"] == 9)].copy()
    top8_market = market_df[market_df["top_n"] == 8].copy()
    top9_market = market_df[market_df["top_n"] == 9].copy()
    top8_odds = odds_df[(odds_df["top_n"] == 8) & (odds_df["bets"] > 0)].copy()
    top9_odds = odds_df[(odds_df["top_n"] == 9) & (odds_df["bets"] > 0)].copy()
    top8_bookmakers = bookmaker_df[(bookmaker_df["top_n"] == 8) & (bookmaker_df["bets"] >= 5)].head(5).copy()
    top9_bookmakers = bookmaker_df[(bookmaker_df["top_n"] == 9) & (bookmaker_df["bets"] >= 5)].head(5).copy()
    top8_leagues = league_df[(league_df["top_n"] == 8) & (league_df["bets"] >= 5)].head(5).copy()
    top9_leagues = league_df[(league_df["top_n"] == 9) & (league_df["bets"] >= 5)].head(5).copy()
    top8_bottom_weeks = weekly_df[weekly_df["top_n"] == 8].sort_values("profit_total").head(5).copy()
    top9_bottom_weeks = weekly_df[weekly_df["top_n"] == 9].sort_values("profit_total").head(5).copy()
    top8_bottom_sum = float(top8_bottom_weeks["profit_total"].sum())
    top9_bottom_sum = float(top9_bottom_weeks["profit_total"].sum())
    cumulative_15 = cumulative_df[cumulative_df["top_n"] <= 15].copy()

    lines = [
        "# Autopsia de la estrategia BDI",
        "",
        "Autopsia de la regla `sabado-domingo -> top BDI_jsd_fair -> elegir la cuota mayor entre Over 2.5 y Under 2.5` usando el dataset robusto con parseo de resultados por `Resultado`, `Acerto`, marcador y goles.",
        "",
        "## Diagnostico",
        "",
        f"- `top 8`: **{int(top8['hits'])}/{int(top8['bets'])}** aciertos, profit **{top8['profit_total']:.2f}**, ROI **{top8['roi']:.3f}**.",
        f"- `top 9`: **{int(top9['hits'])}/{int(top9['bets'])}** aciertos, profit **{top9['profit_total']:.2f}**, ROI **{top9['roi']:.3f}**.",
        "- Veredicto: la estrategia, tal como esta definida, **no tiene edge robusto** en el historico completo.",
        "",
        "## Que la mata",
        "",
        "- El `top BDI` no mejora el universo base; queda ligeramente peor que el resto de partidos elegidos por cuota mayor.",
        "- El ranking por BDI esta demasiado pegado a cuotas altas. En la seleccion `top 8`, la correlacion Pearson `BDI -> cuota` es muy alta y la cuota media sube claramente frente al resto.",
        "- El lado `Under 2.5` cuando es la cuota mayor es el mayor drenaje de profit.",
        "- Las perdidas estan concentradas en pocas semanas grandes; la estrategia tiene riesgo de caida por bloques.",
        "",
        "## Top vs resto",
        "",
    ]
    lines.extend(render_table(top8_vs_rest, ["top_n", "selection", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend([""])
    lines.extend(render_table(top9_vs_rest, ["top_n", "selection", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend(
        [
            "",
            "Lectura:",
            "",
            "- `top 8` selecciona apuestas con cuota media **2.478** frente a **2.202** del resto.",
            "- `top 9` selecciona apuestas con cuota media **2.450** frente a **2.202** del resto.",
            "- El filtro BDI no esta comprando mas valor; esta comprando apuestas mas agresivas y no las compensa con suficiente acierto.",
            "",
            "## Relacion BDI con cuota",
            "",
        ]
    )
    lines.extend(render_table(bdi_odds_df, ["scope", "bets", "hit_rate", "profit_total", "roi", "avg_odds", "avg_bdi", "over_share", "pearson_bdi_odds", "spearman_bdi_odds"]))
    lines.extend(
        [
            "",
            "Lectura:",
            "",
            "- En `top 8` la correlacion Pearson entre `BDI_jsd_fair` y `Mejor_Cuota` queda en **0.987**.",
            "- En `top 9` queda en **0.986**.",
            "- Operativamente, el BDI termina funcionando casi como un selector de cuotas mas extremas, no como un detector limpio de valor.",
            "",
            "## Desglose por lado",
            "",
        ]
    )
    lines.extend(render_table(top8_market, ["top_n", "Mercado", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend([""])
    lines.extend(render_table(top9_market, ["top_n", "Mercado", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend(
        [
            "",
            "Lectura:",
            "",
            f"- En `top 8`, `Over 2.5` pierde poco (**{top8_market[top8_market['Mercado'] == 'Over 2.5']['roi'].iloc[0]:.3f}**) y `Under 2.5` pierde mucho mas (**{top8_market[top8_market['Mercado'] == 'Under 2.5']['roi'].iloc[0]:.3f}**).",
            f"- En `top 9`, `Over 2.5` queda practicamente en break-even (**{top9_market[top9_market['Mercado'] == 'Over 2.5']['roi'].iloc[0]:.3f}**) y `Under 2.5` vuelve a ser el drenaje principal (**{top9_market[top9_market['Mercado'] == 'Under 2.5']['roi'].iloc[0]:.3f}**).",
            "",
            "## Desglose por lado y cuota",
            "",
        ]
    )
    lines.extend(render_table(top8_odds, ["top_n", "Mercado", "odds_bin", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend([""])
    lines.extend(render_table(top9_odds, ["top_n", "Mercado", "odds_bin", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend(
        [
            "",
            "Lectura:",
            "",
            "- El punto mas toxico es `Under 2.5` con cuotas entre `2.2` y `2.4`: ahi la estrategia se rompe fuerte.",
            "- La unica zona que se ve defendible dentro de la idea original es `Over 2.5` entre `2.2` y `2.4`, pero sigue siendo una hipotesis post-hoc, no una estrategia validada.",
            "",
            "## Riesgo semanal",
            "",
        ]
    )
    lines.extend(render_table(top8_bottom_weeks, ["top_n", "week_id", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend([""])
    lines.extend(render_table(top9_bottom_weeks, ["top_n", "week_id", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend(
        [
            "",
            f"- En `top 8`, las 5 peores semanas suman **{top8_bottom_sum:.2f}** de profit frente a un total final de **{top8['profit_total']:.2f}**.",
            f"- En `top 9`, las 5 peores semanas suman **{top9_bottom_sum:.2f}** frente a un total final de **{top9['profit_total']:.2f}**.",
            "- Eso significa que el problema no es solo un promedio flojo: hay semanas de choque que destruyen lo ganado en las semanas buenas.",
            "",
            "## Rango de BDI",
            "",
        ]
    )
    lines.extend(render_table(rank_df.head(12), ["rank_desc", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend([""])
    lines.extend(render_table(cumulative_15, ["top_n", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend(
        [
            "",
            "Lectura:",
            "",
            "- Ni siquiera los puestos mas altos del ranking BDI salvan la regla. El `rank 1` sale negativo y con cuota media muy inflada.",
            "- `top 1` a `top 15` se mantienen en terreno negativo; no aparece un umbral claro que rescate la estrategia completa.",
            "",
            "## Bookmakers mas problematicos",
            "",
        ]
    )
    lines.extend(render_table(top8_bookmakers, ["top_n", "Mejor_Casa", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend([""])
    lines.extend(render_table(top9_bookmakers, ["top_n", "Mejor_Casa", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend(
        [
            "",
            "Lectura:",
            "",
            "- `betrivers` y `onexbet` destacan como los peores focos de perdida en esta regla.",
            "- `pinnacle` no sale mal, pero la muestra es muy chica para convertirlo en regla util por si sola.",
            "",
            "## Ligas mas problematicas",
            "",
        ]
    )
    lines.extend(render_table(top8_leagues, ["top_n", "Liga", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend([""])
    lines.extend(render_table(top9_leagues, ["top_n", "Liga", "bets", "hits", "hit_rate", "profit_total", "roi", "avg_odds"]))
    lines.extend(
        [
            "",
            "## Posibles rescates",
            "",
            "- `Over 2.5` dentro del `top 8/9`, especialmente alrededor de cuotas `2.2` a `2.4`, es la unica veta que parece tener algo de aire.",
            "- `Under 2.5` como cuota mayor dentro del top BDI no merece confianza; hoy lo trataria como un filtro de exclusion, no como una senal.",
            "- Cualquier ajuste que salga de esta autopsia debe considerarse **hipotesis nueva**, porque esta construido mirando el historico perdedor.",
            "",
            "## Conclusion",
            "",
            "- Tu intuicion sobre usar BDI para detectar desacuerdo era razonable, pero en este historico robusto la regla final termina sesgada hacia cuotas demasiado agresivas.",
            "- La muerte de la estrategia no viene por falta total de semanas buenas; viene porque las semanas malas y el lado `Under 2.5` de cuota mayor destruyen el edge.",
            "- Si quieres seguir explotando BDI, yo no lo usaria mas como estrategia standalone. Solo lo dejaria como variable auxiliar para filtrar otras reglas que ya sean positivas por si mismas.",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
