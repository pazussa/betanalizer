from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = (
    BASE_DIR
    / "datasets"
    / "estrategia_calibrada_con_resultado"
    / "consolidado_resultados_raw.csv"
)
OUT_DIR = BASE_DIR / "datasets" / "estrategia_calibrada_con_resultado"
REPORT_PATH = BASE_DIR / "docs" / "combinacion_bdi_under.md"

SOURCE_PRIORITY = {
    "resultados_definitivos": 0,
    "historical_principal": 1,
    "revision_manual": 2,
    "analisis_mercados": 3,
    "bdi_top": 4,
    "historical_backup_reconstruido": 5,
    "historical_backup": 6,
}


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def parse_total_goals(row: pd.Series) -> float:
    for column in ["Marcador", "Score", "Verified_Score"]:
        value = row.get(column, np.nan)
        if pd.notna(value) and str(value).strip():
            match = re.search(r"(\d+)\s*[-:]\s*(\d+)", str(value))
            if match:
                return float(int(match.group(1)) + int(match.group(2)))
    goals_local = pd.to_numeric(row.get("Goles_Local", np.nan), errors="coerce")
    goals_away = pd.to_numeric(row.get("Goles_Visitante", np.nan), errors="coerce")
    total_goals = pd.to_numeric(row.get("Total_Goles", np.nan), errors="coerce")
    if pd.notna(goals_local) and pd.notna(goals_away):
        return float(goals_local + goals_away)
    return float(total_goals) if pd.notna(total_goals) else np.nan


def result_to_binary(row: pd.Series) -> float:
    for column in ["Resultado", "Resultado_Cumplido", "Resultado_Segunda", "Acerto"]:
        text = clean_text(row.get(column, np.nan))
        if not text:
            continue
        if text in {"sí", "si", "s", "yes", "acertado", "cumplido", "hit", "won", "win", "true", "1"}:
            return 1.0
        if text in {"no", "fallido", "miss", "lost", "loss", "false", "0"}:
            return 0.0
        if text == "pendiente":
            return np.nan
        if "acert" in text or text == "acerto" or "gan" in text:
            return 1.0
        if "fall" in text or "perd" in text:
            return 0.0

    market = str(row.get("Mercado", ""))
    total_goals = parse_total_goals(row)
    if pd.isna(total_goals):
        return np.nan
    match = re.search(r"(Over|Under)\s+(\d+(?:\.\d+)?)", market, flags=re.I)
    if not match:
        return np.nan
    side = match.group(1).lower()
    line = float(match.group(2))
    if side == "over":
        return 1.0 if total_goals > line else 0.0
    return 1.0 if total_goals < line else 0.0


def load_canonical_dataset() -> pd.DataFrame:
    frame = pd.read_csv(RAW_PATH, low_memory=False)
    frame["priority"] = frame["source_group"].map(SOURCE_PRIORITY).fillna(99)
    frame["Fecha_Hora_Colombia"] = pd.to_datetime(frame["Fecha_Hora_Colombia"], errors="coerce")
    for column in ["Mejor_Cuota", "Margen_Casa_Pct", "BDI_jsd_fair"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["result_bin"] = frame.apply(result_to_binary, axis=1)
    canonical = frame[
        frame["Fecha_Hora_Colombia"].notna()
        & frame["Mejor_Cuota"].notna()
        & frame["result_bin"].isin([0, 1])
    ].copy()
    canonical = canonical.sort_values(["priority", "source_git_path"])
    canonical["dedupe_key"] = (
        canonical["Partido"].astype(str)
        + "||"
        + canonical["Fecha_Hora_Colombia"].astype(str)
        + "||"
        + canonical["Mercado"].astype(str)
    )
    canonical = canonical.drop_duplicates("dedupe_key", keep="first").copy()
    canonical["profit"] = np.where(
        canonical["result_bin"] == 1,
        canonical["Mejor_Cuota"] - 1.0,
        -1.0,
    )
    canonical["week_id"] = canonical["Fecha_Hora_Colombia"].dt.strftime("%G-W%V")
    canonical["is_weekend"] = canonical["Fecha_Hora_Colombia"].dt.weekday.isin([5, 6])
    return canonical


def summarize(name: str, frame: pd.DataFrame) -> dict[str, object]:
    return {
        "strategy": name,
        "bets": len(frame),
        "profit_total": float(frame["profit"].sum()),
        "roi": float(frame["profit"].mean()),
        "hit_rate": float(frame["result_bin"].mean()),
        "avg_odds": float(frame["Mejor_Cuota"].mean()),
        "weekend_share": float(frame["is_weekend"].mean()),
    }


def top_bdi_matches(canonical: pd.DataFrame, top_n: int) -> pd.DataFrame:
    ou25 = canonical[
        canonical["Mercado"].isin(["Over 2.5", "Under 2.5"])
        & canonical["BDI_jsd_fair"].notna()
        & canonical["is_weekend"]
    ].copy()
    pair_rows = []
    for _, group in ou25.groupby(["Partido", "Fecha_Hora_Colombia"], sort=True):
        if set(group["Mercado"]) >= {"Over 2.5", "Under 2.5"}:
            row = group.iloc[0]
            pair_rows.append(
                {
                    "Partido": row["Partido"],
                    "Fecha_Hora_Colombia": row["Fecha_Hora_Colombia"],
                    "week_id": row["week_id"],
                    "BDI_jsd_fair": row["BDI_jsd_fair"],
                }
            )
    pairs = pd.DataFrame(pair_rows)
    selected = []
    for _, group in pairs.groupby("week_id", sort=True):
        selected.append(group.sort_values("BDI_jsd_fair", ascending=False).head(top_n))
    return pd.concat(selected, ignore_index=True)


def bdi_original(canonical: pd.DataFrame, top_n: int) -> pd.DataFrame:
    ou25 = canonical[
        canonical["Mercado"].isin(["Over 2.5", "Under 2.5"])
        & canonical["BDI_jsd_fair"].notna()
        & canonical["is_weekend"]
    ].copy()
    pair_rows = []
    for _, group in ou25.groupby(["Partido", "Fecha_Hora_Colombia"], sort=True):
        if set(group["Mercado"]) >= {"Over 2.5", "Under 2.5"}:
            pair_rows.append(group.sort_values(["Mejor_Cuota", "Mercado"], ascending=[False, True]).iloc[0])
    chosen = pd.DataFrame(pair_rows)
    picks = []
    for _, group in chosen.groupby("week_id", sort=True):
        picks.append(group.sort_values(["BDI_jsd_fair", "Mejor_Cuota"], ascending=[False, False]).head(top_n))
    return pd.concat(picks, ignore_index=True)


def union_portfolio(frames: list[pd.DataFrame]) -> pd.DataFrame:
    portfolio = pd.concat(frames, ignore_index=True)
    portfolio["portfolio_key"] = (
        portfolio["Partido"].astype(str)
        + "||"
        + portfolio["Fecha_Hora_Colombia"].astype(str)
        + "||"
        + portfolio["Mercado"].astype(str)
    )
    return portfolio.drop_duplicates("portfolio_key", keep="first").copy()


def main() -> None:
    canonical = load_canonical_dataset()

    under35 = canonical[canonical["Mercado"] == "Under 3.5"].copy()
    under25_margin = canonical[
        (canonical["Mercado"] == "Under 2.5")
        & (canonical["Margen_Casa_Pct"] <= 3.89)
    ].copy()
    under25_margin_pinnacle = under25_margin[
        under25_margin["Mejor_Casa"].astype(str) == "pinnacle"
    ].copy()

    results = [
        summarize("Under 3.5", under35),
        summarize("Under 2.5 + margen<=3.89", under25_margin),
        summarize("Under 2.5 + margen<=3.89 + pinnacle", under25_margin_pinnacle),
    ]

    for top_n in [8, 9]:
        bdi_pick = bdi_original(canonical, top_n)
        results.append(summarize(f"BDI weekend top{top_n} cuota mayor", bdi_pick))

        selected_matches = top_bdi_matches(canonical, top_n)[["Partido", "Fecha_Hora_Colombia"]].drop_duplicates()
        combo_under35 = under35.merge(selected_matches, on=["Partido", "Fecha_Hora_Colombia"], how="inner")
        combo_under25 = under25_margin.merge(selected_matches, on=["Partido", "Fecha_Hora_Colombia"], how="inner")
        combo_under25_pinnacle = under25_margin_pinnacle.merge(
            selected_matches, on=["Partido", "Fecha_Hora_Colombia"], how="inner"
        )

        if not combo_under35.empty:
            results.append(summarize(f"Combo match-BDI top{top_n} -> Under 3.5", combo_under35))
        if not combo_under25.empty:
            results.append(summarize(f"Combo match-BDI top{top_n} -> Under 2.5 + margen<=3.89", combo_under25))
        if not combo_under25_pinnacle.empty:
            results.append(
                summarize(
                    f"Combo match-BDI top{top_n} -> Under 2.5 + margen<=3.89 + pinnacle",
                    combo_under25_pinnacle,
                )
            )

        results.append(
            summarize(
                f"Portafolio top{top_n} BDI + Under 3.5",
                union_portfolio([bdi_pick, under35]),
            )
        )
        results.append(
            summarize(
                f"Portafolio top{top_n} BDI + Under 2.5 + margen<=3.89",
                union_portfolio([bdi_pick, under25_margin]),
            )
        )
        results.append(
            summarize(
                f"Portafolio top{top_n} BDI + Under 3.5 + Under 2.5 + margen<=3.89",
                union_portfolio([bdi_pick, under35, under25_margin]),
            )
        )

    results_df = pd.DataFrame(results).sort_values(["roi", "profit_total"], ascending=[False, False])
    results_df.to_csv(OUT_DIR / "combinacion_bdi_under.csv", index=False)

    lines = [
        "# Combinacion entre BDI y estrategias Under",
        "",
        "Evaluacion usando el dataset crudo deduplicado y parseo robusto de resultados (`Resultado`, `Acerto`, marcador y goles).",
        "",
        f"- Universo canonico usado: **{len(canonical)}** apuestas con resultado.",
        "",
        "## Resultado resumido",
        "",
        "| strategy | bets | profit_total | roi | hit_rate | avg_odds |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in results_df.iterrows():
        lines.append(
            f"| `{row['strategy']}` | {int(row['bets'])} | {row['profit_total']:.2f} | "
            f"{row['roi']:.3f} | {row['hit_rate']:.2%} | {row['avg_odds']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Lectura",
            "",
            "- `Under 2.5 + margen<=3.89 + pinnacle` es la estrategia con mejor ROI estable en este dataset anual.",
            "- `Under 3.5` tiene mas volumen y tambien funciona, pero con ROI menor.",
            "- La estrategia BDI original (`cuota mayor`, `top 8/9` fin de semana) pierde dinero en el dataset anual completo.",
            "- Si agregas la estrategia BDI original a un portafolio Under, el ROI del portafolio baja. Es una dilucion, no una mejora.",
            "- La unica combinacion que sale muy bien es usar BDI solo como **selector de partido** y luego apostar `Under 2.5 + margen<=3.89`, pero el soporte es muy chico (7 apuestas).",
            "- Para `Under 3.5` casi no hay solape util con el filtro BDI de partidos; no es una combinacion defendible por volumen.",
            "",
            "## Conclusion",
            "",
            "- Como regla original completa, `BDI` **no conviene mezclarlo** con las estrategias Under porque empeora el portafolio.",
            "- La combinacion que merece seguimiento es: `partidos top BDI del fin de semana` -> si ademas cumplen `Under 2.5 + margen<=3.89`, tomar el Under. Pero hoy la muestra es demasiado chica para considerarla validada.",
            "- Si tu objetivo es rentabilidad robusta hoy, me quedaria con las estrategias Under por separado y dejaria la variante BDI+Under2.5 como hipotesis en monitoreo, no como estrategia principal.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
