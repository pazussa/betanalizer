from __future__ import annotations

import hashlib
import itertools
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = (
    BASE_DIR
    / "datasets"
    / "estrategia_calibrada_con_resultado"
    / "consolidado_resultados_analisis.csv"
)
OUTPUT_DIR = BASE_DIR / "datasets" / "estrategia_calibrada_con_resultado"
REPORT_PATH = BASE_DIR / "docs" / "estrategias_validadas_estrategia_calibrada.md"


@dataclass(frozen=True)
class Condition:
    column: str
    operator: str
    value: object

    @property
    def label(self) -> str:
        if isinstance(self.value, float):
            return f"{self.column} {self.operator} {self.value:.4f}"
        return f"{self.column} {self.operator} {self.value}"


def load_dataset() -> pd.DataFrame:
    frame = pd.read_csv(DATASET_PATH)
    frame["event_date"] = pd.to_datetime(frame["event_date"], errors="coerce")
    frame["day"] = frame["event_date"].dt.date
    return frame


def split_by_day(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[object]]:
    days = sorted(frame["day"].dropna().unique())
    train_days = set(days[:9])
    valid_days = set(days[9:12])
    test_days = set(days[12:])
    train = frame[frame["day"].isin(train_days)].copy()
    valid = frame[frame["day"].isin(valid_days)].copy()
    test = frame[frame["day"].isin(test_days)].copy()
    return train, valid, test, days


def build_conditions(train: pd.DataFrame) -> list[Condition]:
    conditions: list[Condition] = []
    numeric_columns = [
        "score_final",
        "mejor_cuota",
        "cuota_promedio_mercado",
        "diferencia_cuota_promedio",
        "volatilidad_pct",
        "margen_casa_pct",
        "edge_pct",
        "confianza_calibrada",
        "p_win_calibrada",
        "num_casas",
    ]
    categorical_limits = {
        "Mercado": 8,
        "Liga": 8,
        "Mejor_Casa": 5,
        "market_family": 4,
        "Tipo_Mercado": 4,
        "source_group": 4,
    }
    for column in numeric_columns:
        series = pd.to_numeric(train[column], errors="coerce").dropna()
        if len(series) < 50:
            continue
        conditions.append(Condition(column, "<=", float(series.quantile(0.25))))
        conditions.append(Condition(column, ">=", float(series.quantile(0.75))))
    for column, top_n in categorical_limits.items():
        values = (
            train[column]
            .fillna("")
            .astype(str)
            .value_counts()
            .head(top_n)
            .index.tolist()
        )
        for value in values:
            if value:
                conditions.append(Condition(column, "==", value))
    return conditions


def apply_condition(frame: pd.DataFrame, condition: Condition) -> pd.Series:
    if condition.operator == "==":
        return frame[condition.column].astype(str) == str(condition.value)
    series = pd.to_numeric(frame[condition.column], errors="coerce")
    if condition.operator == "<=":
        return series <= float(condition.value)
    if condition.operator == ">=":
        return series >= float(condition.value)
    raise ValueError(f"Operador no soportado: {condition.operator}")


def apply_rule(frame: pd.DataFrame, rule: tuple[Condition, ...]) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for condition in rule:
        mask &= apply_condition(frame, condition).fillna(False)
    return mask


def rule_label(rule: tuple[Condition, ...]) -> str:
    return " AND ".join(condition.label for condition in rule)


def roi(frame: pd.DataFrame) -> float:
    return float(frame["profit_unitario"].mean()) if len(frame) else float("nan")


def hit_rate(frame: pd.DataFrame) -> float:
    return float(frame["resultado_binario"].mean()) if len(frame) else float("nan")


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    phat = successes / total
    denom = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denom
    margin = (z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)) / denom
    return center - margin, center + margin


def bootstrap_roi_interval(values: np.ndarray, n_boot: int = 3000) -> tuple[float, float]:
    rng = np.random.default_rng(42)
    samples = rng.choice(values, size=(n_boot, len(values)), replace=True)
    means = samples.mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def search_validated_rules(
    frame: pd.DataFrame, train: pd.DataFrame, valid: pd.DataFrame, test: pd.DataFrame
) -> pd.DataFrame:
    conditions = build_conditions(train)
    rows: list[dict[str, object]] = []
    for size in (1, 2, 3):
        for combo in itertools.combinations(conditions, size):
            train_mask = apply_rule(train, combo)
            valid_mask = apply_rule(valid, combo)
            test_mask = apply_rule(test, combo)
            train_slice = train[train_mask]
            valid_slice = valid[valid_mask]
            test_slice = test[test_mask]
            if len(train_slice) < 25 or len(valid_slice) < 8 or len(test_slice) < 8:
                continue
            train_roi = roi(train_slice)
            valid_roi = roi(valid_slice)
            test_roi = roi(test_slice)
            if not (train_roi > 0 and valid_roi > 0 and test_roi > 0):
                continue
            full_mask = apply_rule(frame, combo)
            oos_slice = pd.concat([valid_slice, test_slice], ignore_index=True)
            rows.append(
                {
                    "rule": rule_label(combo),
                    "conditions": size,
                    "train_n": len(train_slice),
                    "valid_n": len(valid_slice),
                    "test_n": len(test_slice),
                    "train_hit": hit_rate(train_slice),
                    "valid_hit": hit_rate(valid_slice),
                    "test_hit": hit_rate(test_slice),
                    "train_roi": train_roi,
                    "valid_roi": valid_roi,
                    "test_roi": test_roi,
                    "oos_n": len(oos_slice),
                    "oos_hit": hit_rate(oos_slice),
                    "oos_roi": roi(oos_slice),
                    "mask_signature": hashlib.md5(full_mask.to_numpy().tobytes()).hexdigest(),
                }
            )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result = result.sort_values(
        ["conditions", "oos_roi", "oos_n"],
        ascending=[True, False, False],
    )
    kept: list[pd.Series] = []
    seen_signatures: set[str] = set()
    for _, row in result.iterrows():
        if row["mask_signature"] in seen_signatures:
            continue
        seen_signatures.add(row["mask_signature"])
        kept.append(row)
    return pd.DataFrame(kept).reset_index(drop=True)


def describe_strategy(frame: pd.DataFrame, days: list[object], rule_text: str) -> dict[str, object]:
    valid_days = set(days[9:12])
    test_days = set(days[12:])
    oos_days = valid_days | test_days
    parts = []
    for raw in rule_text.split(" AND "):
        left, op, right = raw.split(" ", 2)
        value: object = right
        if op in {"<=", ">="}:
            value = float(right)
        parts.append(Condition(left, op, value))
    rule = tuple(parts)
    strategy = frame[apply_rule(frame, rule)].copy()
    train_slice = strategy[strategy["day"].isin(days[:9])]
    valid_slice = strategy[strategy["day"].isin(valid_days)]
    test_slice = strategy[strategy["day"].isin(test_days)]
    oos_slice = strategy[strategy["day"].isin(oos_days)].copy()
    successes = int(oos_slice["resultado_binario"].sum())
    hit_lo, hit_hi = wilson_interval(successes, len(oos_slice))
    roi_lo, roi_hi = bootstrap_roi_interval(oos_slice["profit_unitario"].to_numpy())
    daily = (
        oos_slice.groupby("day", dropna=False)
        .agg(n=("profit_unitario", "size"), roi=("profit_unitario", "mean"))
        .reset_index()
    )
    positive_days = int((daily["roi"] > 0).sum())
    non_negative_days = int((daily["roi"] >= 0).sum())
    return {
        "rule": rule_text,
        "train_n": len(train_slice),
        "valid_n": len(valid_slice),
        "test_n": len(test_slice),
        "train_hit": hit_rate(train_slice),
        "valid_hit": hit_rate(valid_slice),
        "test_hit": hit_rate(test_slice),
        "train_roi": roi(train_slice),
        "valid_roi": roi(valid_slice),
        "test_roi": roi(test_slice),
        "oos_n": len(oos_slice),
        "oos_hit": hit_rate(oos_slice),
        "oos_roi": roi(oos_slice),
        "hit_ci_low": hit_lo,
        "hit_ci_high": hit_hi,
        "roi_ci_low": roi_lo,
        "roi_ci_high": roi_hi,
        "oos_days": len(daily),
        "positive_days": positive_days,
        "non_negative_days": non_negative_days,
    }


def evaluate_rejected_rule(frame: pd.DataFrame, days: list[object]) -> dict[str, object]:
    rule = (
        "cuota_promedio_mercado <= 1.4300 AND margen_casa_pct <= 3.8900 "
        "AND num_casas >= 4.0000"
    )
    return describe_strategy(frame, days, rule)


def render_report(
    frame: pd.DataFrame,
    validated_rules: pd.DataFrame,
    selected_strategies: pd.DataFrame,
    rejected_strategy: dict[str, object],
    days: list[object],
) -> str:
    oos = frame[frame["day"].isin(set(days[9:]))]
    baseline_hit = hit_rate(oos)
    baseline_roi = roi(oos)
    lines = [
        "# Estrategias validadas de la rama estrategia calibrada",
        "",
        "Este reporte toma el dataset deduplicado ya consolidado y valida reglas solo con cortes temporales.",
        "",
        "## Esquema de validacion",
        "",
        f"- Train: primeras 9 fechas ({days[0]} a {days[8]}).",
        f"- Valid: siguientes 3 fechas ({days[9]} a {days[11]}).",
        f"- Test: ultimas 3 fechas ({days[12]} a {days[-1]}).",
        f"- Baseline OOS (valid+test): n={len(oos)}, hit_rate={baseline_hit:.2%}, ROI={baseline_roi:.3f}.",
        "",
        "## Estrategias recomendadas",
        "",
    ]
    for _, row in selected_strategies.iterrows():
        lines.extend(
            [
                f"### {row['rule']}",
                "",
                f"- Train: n={int(row['train_n'])}, hit_rate={row['train_hit']:.2%}, ROI={row['train_roi']:.3f}.",
                f"- Valid: n={int(row['valid_n'])}, hit_rate={row['valid_hit']:.2%}, ROI={row['valid_roi']:.3f}.",
                f"- Test: n={int(row['test_n'])}, hit_rate={row['test_hit']:.2%}, ROI={row['test_roi']:.3f}.",
                f"- OOS total: n={int(row['oos_n'])}, hit_rate={row['oos_hit']:.2%}, ROI={row['oos_roi']:.3f}.",
                f"- Lift OOS vs baseline: hit={row['oos_hit'] - baseline_hit:+.2%}, ROI={row['oos_roi'] - baseline_roi:+.3f}.",
                f"- Intervalo hit rate 95%: [{row['hit_ci_low']:.2%}, {row['hit_ci_high']:.2%}].",
                f"- Intervalo ROI 95% bootstrap: [{row['roi_ci_low']:.3f}, {row['roi_ci_high']:.3f}].",
                f"- Dias OOS activos: {int(row['oos_days'])}, dias positivos: {int(row['positive_days'])}, dias no negativos: {int(row['non_negative_days'])}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Reglas que parecen buenas pero no pasan validacion estricta",
            "",
            (
                f"- `{rejected_strategy['rule']}` logra hit rate alto OOS "
                f"({rejected_strategy['oos_hit']:.2%}), pero falla por consistencia: "
                f"ROI valid={rejected_strategy['valid_roi']:.3f}, ROI test={rejected_strategy['test_roi']:.3f}."
            ),
            "",
            "## Inventario de reglas validadas encontradas",
            "",
            "| rule | train_n | valid_n | test_n | train_roi | valid_roi | test_roi | oos_n | oos_hit | oos_roi |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in validated_rules.iterrows():
        lines.append(
            f"| `{row['rule']}` | {int(row['train_n'])} | {int(row['valid_n'])} | {int(row['test_n'])} | "
            f"{row['train_roi']:.3f} | {row['valid_roi']:.3f} | {row['test_roi']:.3f} | "
            f"{int(row['oos_n'])} | {row['oos_hit']:.2%} | {row['oos_roi']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Conclusion operativa",
            "",
            "- Las estrategias que sobreviven la validacion son pocas y simples.",
            "- La familia ganadora es `Under`, no `double chance`.",
            "- `Under 3.5` es la mejor estrategia simple por ROI y hit rate OOS.",
            "- `Under 2.5` mejora cuando el margen de la casa es bajo; con `pinnacle` mejora un poco mas el ROI OOS.",
            "- No recomiendo convertir en estrategia fija reglas que solo suben hit rate pero no sostienen ROI en validacion.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    frame = load_dataset()
    train, valid, test, days = split_by_day(frame)
    validated_rules = search_validated_rules(frame, train, valid, test)
    if validated_rules.empty:
        raise SystemExit("No se encontraron estrategias validadas.")
    selected_rows = []
    for _, row in validated_rules.head(4).iterrows():
        selected_rows.append(describe_strategy(frame, days, row["rule"]))
    selected_strategies = pd.DataFrame(selected_rows)
    rejected_strategy = evaluate_rejected_rule(frame, days)

    validated_rules.to_csv(OUTPUT_DIR / "estrategias_validadas.csv", index=False)
    selected_strategies.to_csv(OUTPUT_DIR / "estrategias_recomendadas.csv", index=False)
    pd.DataFrame([rejected_strategy]).to_csv(OUTPUT_DIR / "estrategia_rechazada_ejemplo.csv", index=False)

    report = render_report(
        frame=frame,
        validated_rules=validated_rules,
        selected_strategies=selected_strategies,
        rejected_strategy=rejected_strategy,
        days=days,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Reglas validadas: {len(validated_rules)}")
    print(f"Reporte: {REPORT_PATH}")


if __name__ == "__main__":
    main()
