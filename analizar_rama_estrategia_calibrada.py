from __future__ import annotations

import itertools
import math
import re
import subprocess
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BRANCH = "origin/estrategia-confianza-calibrada"
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "datasets" / "estrategia_calibrada_con_resultado"
REPORT_PATH = BASE_DIR / "docs" / "analisis_estrategia_calibrada_resultados.md"

RESULT_COLUMNS = [
    "Resultado",
    "Resultado_Cumplido",
    "Resultado_Segunda",
    "Acerto",
    "Marcador",
    "Score",
    "Verified_Score",
    "Total_Goles",
    "Goles_Local",
    "Goles_Visitante",
]

NUMERIC_SOURCE_COLUMNS = [
    "Mejor_Cuota",
    "Cuota_Promedio_Mercado",
    "Num_Casas",
    "Score_Final",
    "Diferencia_Cuota_Promedio",
    "Volatilidad_Pct",
    "Margen_Casa_Pct",
    "BDI_jsd",
    "BDI_n_bookmakers",
    "BDI_std_p",
    "BDI_mad_p",
    "BDI_jsd_fair",
    "BDI_n_bookmakers_fair",
    "BDI_std_p_fair",
    "BDI_mad_p_fair",
    "Confianza",
    "P_Win_Calibrada",
    "Confianza_Calibrada",
    "Goles_Local",
    "Goles_Visitante",
    "Total_Goles",
]

PREMATCH_NUMERIC_COLUMNS = [
    "mejor_cuota",
    "cuota_promedio_mercado",
    "num_casas",
    "score_final",
    "diferencia_cuota_promedio",
    "volatilidad_pct",
    "margen_casa_pct",
    "bdi_jsd",
    "bdi_n_bookmakers",
    "bdi_std_p",
    "bdi_mad_p",
    "bdi_jsd_fair",
    "bdi_n_bookmakers_fair",
    "bdi_std_p_fair",
    "bdi_mad_p_fair",
    "confianza",
    "p_win_calibrada",
    "confianza_calibrada",
    "edge_pct",
    "score_minus_margin",
]

CATEGORICAL_COLUMNS = [
    "market_family",
    "Liga",
    "Tipo_Mercado",
    "Mercado",
    "Mejor_Casa",
    "source_group",
]


@dataclass
class SelectedFile:
    git_path: str
    export_name: str
    rows: int
    usable_result_rows: int
    result_columns: list[str]
    raw_csv: str
    dataframe: pd.DataFrame


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=BASE_DIR,
    )


def safe_read_csv(raw_csv: str) -> pd.DataFrame:
    return pd.read_csv(
        StringIO(raw_csv),
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        engine="python",
    )


def slugify_git_path(path: str) -> str:
    return path.replace("/", "__")


def to_float(series: pd.Series) -> pd.Series:
    cleaned = (
        series.fillna("")
        .astype(str)
        .str.strip()
        .replace({"": np.nan, "None": np.nan, "nan": np.nan})
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def clean_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def normalize_result_text(value: object) -> str:
    text = clean_text(value).lower()
    replacements = {
        "si": "si",
        "s": "si",
        "yes": "si",
        "acertado": "hit",
        "cumplido": "hit",
        "ok": "hit",
        "true": "hit",
        "1": "hit",
        "no": "miss",
        "fallido": "miss",
        "false": "miss",
        "0": "miss",
        "lost": "miss",
        "loss": "miss",
    }
    if text in replacements:
        return replacements[text]
    if text in {"si", "s", "yes"}:
        return "hit"
    if text in {"no"}:
        return "miss"
    if "acert" in text or "gan" in text or text == "acerto":
        return "hit"
    if "fall" in text or "perd" in text:
        return "miss"
    return text


def result_to_binary(value: object) -> float:
    text = normalize_result_text(value)
    if text in {"hit", "si"}:
        return 1.0
    if text == "miss":
        return 0.0
    return np.nan


def parse_score(value: object) -> tuple[float | None, float | None]:
    text = clean_text(value)
    if not text:
        return (None, None)
    match = re.search(r"(\d+)\s*[-:]\s*(\d+)", text)
    if not match:
        return (None, None)
    return (float(match.group(1)), float(match.group(2)))


def first_nonempty(row: pd.Series, candidates: Iterable[str]) -> str:
    for column in candidates:
        if column in row.index:
            value = clean_text(row[column])
            if value:
                return value
    return ""


def market_family(market: str, market_type: str) -> str:
    text = f"{market_type} {market}".lower()
    if "over" in text or "under" in text:
        return "totals"
    if "doble chance" in text or market in {"1X", "X2", "12"}:
        return "double_chance"
    if "btts" in text or "ambos" in text:
        return "btts"
    if market in {"1", "2", "X"} or "moneyline" in text:
        return "match_result"
    return "other"


def source_group(path: str) -> str:
    if path == "data/historico_completo.csv":
        return "historico_maestro"
    if path.startswith("resultados_definitivos/"):
        return "resultados_definitivos"
    if path.startswith("historical_con_resultados/backup_reconstruccion_"):
        return "historical_backup_reconstruido"
    if path.startswith("historical_con_resultados/backup/"):
        return "historical_backup"
    if path.startswith("historical_con_resultados/"):
        return "historical_principal"
    if path.startswith("REVISAR-"):
        return "revision_manual"
    if path.startswith("analisis_mercados_"):
        return "analisis_mercados"
    if path.startswith("filtro2_"):
        return "filtro2"
    if path.startswith("bdi_top_"):
        return "bdi_top"
    return "otros"


def source_priority(path: str) -> int:
    priorities = {
        "historico_maestro": 0,
        "resultados_definitivos": 1,
        "historical_principal": 2,
        "analisis_mercados": 3,
        "revision_manual": 4,
        "filtro2": 5,
        "bdi_top": 6,
        "historical_backup_reconstruido": 7,
        "historical_backup": 8,
        "otros": 9,
    }
    return priorities.get(source_group(path), 99)


def select_files_with_results() -> list[SelectedFile]:
    files = [
        line.strip()
        for line in git("ls-tree", "-r", "--name-only", BRANCH).splitlines()
        if line.strip().endswith(".csv")
    ]
    selected: list[SelectedFile] = []
    for path in sorted(files):
        raw_csv = git("show", f"{BRANCH}:{path}")
        if not raw_csv.strip():
            continue
        try:
            dataframe = safe_read_csv(raw_csv)
        except Exception:
            continue
        if "Partido" not in dataframe.columns:
            continue
        result_columns = [column for column in RESULT_COLUMNS if column in dataframe.columns]
        if not result_columns:
            continue
        usable_mask = dataframe[result_columns].apply(
            lambda col: col.astype(str).str.strip().ne("")
        ).any(axis=1)
        usable_rows = int(usable_mask.sum())
        if usable_rows == 0:
            continue
        selected.append(
            SelectedFile(
                git_path=path,
                export_name=slugify_git_path(path),
                rows=int(len(dataframe)),
                usable_result_rows=usable_rows,
                result_columns=result_columns,
                raw_csv=raw_csv,
                dataframe=dataframe,
            )
        )
    return selected


def enrich_dataframe(selected_file: SelectedFile) -> pd.DataFrame:
    frame = selected_file.dataframe.copy()
    frame["source_branch"] = BRANCH
    frame["source_git_path"] = selected_file.git_path
    frame["source_export_name"] = selected_file.export_name
    frame["source_group"] = source_group(selected_file.git_path)
    frame["source_priority"] = source_priority(selected_file.git_path)

    frame["resultado_texto"] = frame.apply(
        lambda row: first_nonempty(
            row,
            ["Resultado", "Resultado_Cumplido", "Resultado_Segunda", "Acerto"],
        ),
        axis=1,
    )
    frame["marcador_texto"] = frame.apply(
        lambda row: first_nonempty(row, ["Marcador", "Score", "Verified_Score"]),
        axis=1,
    )
    frame["total_goles_texto"] = frame.apply(
        lambda row: first_nonempty(row, ["Total_Goles"]),
        axis=1,
    )
    frame["resultado_binario"] = frame["resultado_texto"].map(result_to_binary)

    parsed_scores = frame["marcador_texto"].map(parse_score)
    frame["goles_local_norm"] = parsed_scores.map(lambda item: item[0] if item else None)
    frame["goles_visitante_norm"] = parsed_scores.map(lambda item: item[1] if item else None)
    frame["total_goles_norm"] = (
        frame["goles_local_norm"].fillna(0) + frame["goles_visitante_norm"].fillna(0)
    )
    has_any_score = frame["goles_local_norm"].notna() & frame["goles_visitante_norm"].notna()
    frame.loc[~has_any_score, "total_goles_norm"] = to_float(frame["total_goles_texto"])
    if "Goles_Local" in frame.columns:
        frame["goles_local_norm"] = frame["goles_local_norm"].fillna(to_float(frame["Goles_Local"]))
    if "Goles_Visitante" in frame.columns:
        frame["goles_visitante_norm"] = frame["goles_visitante_norm"].fillna(
            to_float(frame["Goles_Visitante"])
        )
    frame["total_goles_norm"] = frame["total_goles_norm"].fillna(
        frame["goles_local_norm"] + frame["goles_visitante_norm"]
    )

    for column in NUMERIC_SOURCE_COLUMNS:
        if column in frame.columns:
            frame[f"{column}__num"] = to_float(frame[column])

    frame["mejor_cuota"] = frame.get("Mejor_Cuota__num")
    frame["cuota_promedio_mercado"] = frame.get("Cuota_Promedio_Mercado__num")
    frame["num_casas"] = frame.get("Num_Casas__num")
    frame["score_final"] = frame.get("Score_Final__num")
    frame["diferencia_cuota_promedio"] = frame.get("Diferencia_Cuota_Promedio__num")
    frame["volatilidad_pct"] = frame.get("Volatilidad_Pct__num")
    frame["margen_casa_pct"] = frame.get("Margen_Casa_Pct__num")
    frame["bdi_jsd"] = frame.get("BDI_jsd__num")
    frame["bdi_n_bookmakers"] = frame.get("BDI_n_bookmakers__num")
    frame["bdi_std_p"] = frame.get("BDI_std_p__num")
    frame["bdi_mad_p"] = frame.get("BDI_mad_p__num")
    frame["bdi_jsd_fair"] = frame.get("BDI_jsd_fair__num")
    frame["bdi_n_bookmakers_fair"] = frame.get("BDI_n_bookmakers_fair__num")
    frame["bdi_std_p_fair"] = frame.get("BDI_std_p_fair__num")
    frame["bdi_mad_p_fair"] = frame.get("BDI_mad_p_fair__num")
    frame["confianza"] = frame.get("Confianza__num")
    frame["p_win_calibrada"] = frame.get("P_Win_Calibrada__num")
    frame["confianza_calibrada"] = frame.get("Confianza_Calibrada__num")

    frame["edge_pct"] = (
        (frame["mejor_cuota"] - frame["cuota_promedio_mercado"]) / frame["cuota_promedio_mercado"]
    ) * 100.0
    frame["score_minus_margin"] = frame["score_final"] - frame["margen_casa_pct"]
    frame["market_family"] = [
        market_family(market, market_type)
        for market, market_type in zip(
            frame.get("Mercado", pd.Series(index=frame.index, dtype=object)).fillna(""),
            frame.get("Tipo_Mercado", pd.Series(index=frame.index, dtype=object)).fillna(""),
        )
    ]

    frame["profit_unitario"] = np.where(
        frame["resultado_binario"] == 1,
        frame["mejor_cuota"] - 1,
        np.where(frame["resultado_binario"] == 0, -1.0, np.nan),
    )

    event_date = pd.to_datetime(frame.get("Fecha_Hora_Colombia"), errors="coerce")
    snapshot_date = pd.to_datetime(frame.get("Snapshot_Date"), errors="coerce")
    frame["event_date"] = event_date.fillna(snapshot_date)
    frame["resultado_disponible"] = (
        frame["resultado_texto"].astype(str).str.strip().ne("")
        | frame["marcador_texto"].astype(str).str.strip().ne("")
        | frame["total_goles_texto"].astype(str).str.strip().ne("")
    )
    for column in PREMATCH_NUMERIC_COLUMNS + ["goles_local_norm", "goles_visitante_norm", "total_goles_norm"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def deduplicate_for_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    candidate = frame.copy()
    candidate = candidate[candidate["resultado_binario"].isin([0.0, 1.0])].copy()
    mejor_cuota_key = pd.to_numeric(candidate["mejor_cuota"], errors="coerce").round(4).astype(str)
    cuota_promedio_key = (
        pd.to_numeric(candidate["cuota_promedio_mercado"], errors="coerce").round(4).astype(str)
    )
    score_final_key = pd.to_numeric(candidate["score_final"], errors="coerce").round(4).astype(str)
    diferencia_key = (
        pd.to_numeric(candidate["diferencia_cuota_promedio"], errors="coerce").round(4).astype(str)
    )
    volatilidad_key = pd.to_numeric(candidate["volatilidad_pct"], errors="coerce").round(4).astype(str)
    margen_key = pd.to_numeric(candidate["margen_casa_pct"], errors="coerce").round(4).astype(str)
    total_goles_key = pd.to_numeric(candidate["total_goles_norm"], errors="coerce").round(4).astype(str)
    candidate["dedupe_key"] = (
        candidate["Partido"].fillna("")
        + "||"
        + candidate.get("Fecha_Hora_Colombia", pd.Series(index=candidate.index, dtype=object)).fillna("")
        + "||"
        + candidate.get("Liga", pd.Series(index=candidate.index, dtype=object)).fillna("")
        + "||"
        + candidate.get("Tipo_Mercado", pd.Series(index=candidate.index, dtype=object)).fillna("")
        + "||"
        + candidate.get("Mercado", pd.Series(index=candidate.index, dtype=object)).fillna("")
        + "||"
        + candidate.get("Mejor_Casa", pd.Series(index=candidate.index, dtype=object)).fillna("")
        + "||"
        + mejor_cuota_key
        + "||"
        + cuota_promedio_key
        + "||"
        + score_final_key
        + "||"
        + diferencia_key
        + "||"
        + volatilidad_key
        + "||"
        + margen_key
        + "||"
        + candidate["resultado_binario"].astype(int).astype(str)
        + "||"
        + candidate["marcador_texto"].fillna("")
        + "||"
        + total_goles_key
        + "||"
        + pd.to_datetime(candidate["event_date"], errors="coerce").astype(str)
    )
    candidate = candidate.sort_values(
        by=["source_priority", "source_group", "event_date", "Partido", "Mercado"],
        ascending=[True, True, True, True, True],
    )
    candidate["is_duplicate_across_sources"] = candidate.duplicated("dedupe_key", keep="first")
    return candidate[~candidate["is_duplicate_across_sources"]].copy()


def numeric_feature_stats(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for feature in PREMATCH_NUMERIC_COLUMNS:
        if feature not in frame.columns:
            continue
        subset = frame[[feature, "resultado_binario"]].copy()
        subset[feature] = pd.to_numeric(subset[feature], errors="coerce")
        subset = subset.dropna()
        if subset["resultado_binario"].nunique() < 2 or len(subset) < 40:
            continue
        hit = subset.loc[subset["resultado_binario"] == 1, feature]
        miss = subset.loc[subset["resultado_binario"] == 0, feature]
        if min(len(hit), len(miss)) < 20:
            continue
        stat, p_value = mannwhitneyu(hit, miss, alternative="two-sided")
        mean_diff = float(hit.mean() - miss.mean())
        pooled_std = math.sqrt(
            max(
                (
                    ((len(hit) - 1) * hit.var(ddof=1)) + ((len(miss) - 1) * miss.var(ddof=1))
                )
                / max(len(hit) + len(miss) - 2, 1),
                0.0,
            )
        )
        cohens_d = mean_diff / pooled_std if pooled_std else 0.0
        rows.append(
            {
                "feature": feature,
                "n": len(subset),
                "hit_mean": hit.mean(),
                "miss_mean": miss.mean(),
                "mean_diff": mean_diff,
                "cohens_d": cohens_d,
                "mannwhitney_p": p_value,
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values(["mannwhitney_p", "cohens_d"], ascending=[True, False])
    return result


def summarise_categories(frame: pd.DataFrame, column: str, min_count: int = 25) -> pd.DataFrame:
    subset = frame[[column, "resultado_binario", "profit_unitario"]].copy()
    subset = subset[subset[column].fillna("").astype(str).str.strip().ne("")]
    grouped = (
        subset.groupby(column, dropna=False)
        .agg(
            n=("resultado_binario", "size"),
            hit_rate=("resultado_binario", "mean"),
            roi=("profit_unitario", "mean"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["n"] >= min_count].sort_values(
        ["roi", "hit_rate", "n"], ascending=[False, False, False]
    )
    return grouped


def build_rule_conditions(frame: pd.DataFrame) -> list[tuple[str, pd.Series]]:
    conditions: list[tuple[str, pd.Series]] = []
    numeric_candidates = [
        "score_final",
        "mejor_cuota",
        "diferencia_cuota_promedio",
        "volatilidad_pct",
        "margen_casa_pct",
        "num_casas",
        "bdi_jsd",
        "bdi_jsd_fair",
        "confianza_calibrada",
        "p_win_calibrada",
        "edge_pct",
    ]
    for feature in numeric_candidates:
        if feature not in frame.columns:
            continue
        series = frame[feature].dropna()
        if len(series) < 80:
            continue
        q25 = series.quantile(0.25)
        q75 = series.quantile(0.75)
        if pd.notna(q25):
            conditions.append((f"{feature} <= {q25:.4f}", frame[feature] <= q25))
        if pd.notna(q75):
            conditions.append((f"{feature} >= {q75:.4f}", frame[feature] >= q75))
    categorical_candidates = {
        "market_family": 5,
        "Mercado": 8,
        "Tipo_Mercado": 5,
        "Liga": 8,
        "Mejor_Casa": 5,
        "source_group": 6,
    }
    for column, top_n in categorical_candidates.items():
        if column not in frame.columns:
            continue
        values = (
            frame[column]
            .fillna("")
            .astype(str)
            .str.strip()
            .value_counts()
            .head(top_n)
            .index.tolist()
        )
        for value in values:
            if not value:
                continue
            conditions.append((f"{column} == {value}", frame[column].astype(str) == value))
    return conditions


def rule_mining(frame: pd.DataFrame, baseline_hit: float, baseline_roi: float) -> pd.DataFrame:
    conditions = build_rule_conditions(frame)
    rows: list[dict[str, object]] = []
    for size in (1, 2, 3):
        for combo in itertools.combinations(conditions, size):
            label = " AND ".join(item[0] for item in combo)
            mask = pd.Series(True, index=frame.index)
            for _, condition in combo:
                mask &= condition.fillna(False)
            subset = frame[mask]
            if len(subset) < 30:
                continue
            hit_rate = float(subset["resultado_binario"].mean())
            roi = float(subset["profit_unitario"].mean())
            rows.append(
                {
                    "rule": label,
                    "n": len(subset),
                    "hit_rate": hit_rate,
                    "roi": roi,
                    "hit_lift": hit_rate - baseline_hit,
                    "roi_lift": roi - baseline_roi,
                }
            )
    rules = pd.DataFrame(rows)
    if rules.empty:
        return rules
    rules = rules.drop_duplicates("rule")
    rules = rules[(rules["hit_lift"] > 0.02) | (rules["roi_lift"] > 0.02)]
    return rules.sort_values(["roi", "hit_rate", "n"], ascending=[False, False, False])


def temporal_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = frame.sort_values("event_date").copy()
    valid_dates = ordered["event_date"].notna()
    if valid_dates.sum() < max(100, int(len(ordered) * 0.6)):
        train = ordered.iloc[: int(len(ordered) * 0.8)].copy()
        test = ordered.iloc[int(len(ordered) * 0.8) :].copy()
        return train, test
    cutoff_index = max(int(len(ordered) * 0.8), 1)
    train = ordered.iloc[:cutoff_index].copy()
    test = ordered.iloc[cutoff_index:].copy()
    if test.empty:
        test = train.tail(max(1, len(train) // 5)).copy()
        train = train.iloc[: len(train) - len(test)].copy()
    return train, test


def model_data(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    available_numeric = [column for column in PREMATCH_NUMERIC_COLUMNS if column in frame.columns]
    available_categorical = [column for column in CATEGORICAL_COLUMNS if column in frame.columns]
    usable = frame.copy()
    usable = usable[usable["resultado_binario"].isin([0.0, 1.0])].copy()
    for column in available_numeric:
        usable[column] = pd.to_numeric(usable[column], errors="coerce")
    available_numeric = [column for column in available_numeric if usable[column].notna().any()]
    return usable, available_numeric, available_categorical


def run_models(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    usable, numeric_columns, categorical_columns = model_data(frame)
    train, test = temporal_split(usable)
    numeric_columns = [column for column in numeric_columns if train[column].notna().any()]
    categorical_columns = [column for column in categorical_columns if train[column].notna().any()]
    X_train = train[numeric_columns + categorical_columns]
    y_train = train["resultado_binario"].astype(int)
    X_test = test[numeric_columns + categorical_columns]
    y_test = test["resultado_binario"].astype(int)

    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_columns),
            ("cat", categorical_pipe, categorical_columns),
        ],
        remainder="drop",
    )

    models = {
        "logistic": LogisticRegression(max_iter=3000, class_weight="balanced"),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_leaf=20,
            random_state=42,
            class_weight="balanced_subsample",
        ),
    }

    metrics_rows: list[dict[str, object]] = []
    feature_rows: list[dict[str, object]] = []
    bands_rows: list[dict[str, object]] = []
    transformed_feature_names: list[str] | None = None
    for model_name, estimator in models.items():
        pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", estimator)])
        pipeline.fit(X_train, y_train)
        proba = pipeline.predict_proba(X_test)[:, 1]
        prediction = (proba >= 0.5).astype(int)
        metrics_rows.append(
            {
                "model": model_name,
                "train_rows": len(train),
                "test_rows": len(test),
                "accuracy": accuracy_score(y_test, prediction),
                "roc_auc": roc_auc_score(y_test, proba) if y_test.nunique() > 1 else np.nan,
                "brier": brier_score_loss(y_test, proba),
                "log_loss": log_loss(y_test, proba, labels=[0, 1]),
            }
        )

        probs = pd.DataFrame(
            {
                "model": model_name,
                "pred_proba": proba,
                "target": y_test.to_numpy(),
                "profit_unitario": test["profit_unitario"].to_numpy(),
            }
        )
        probs["prob_bin"] = pd.qcut(
            probs["pred_proba"],
            q=min(5, max(2, probs["pred_proba"].nunique())),
            duplicates="drop",
        )
        grouped = (
            probs.groupby("prob_bin", observed=False)
            .agg(
                n=("target", "size"),
                hit_rate=("target", "mean"),
                roi=("profit_unitario", "mean"),
                prob_min=("pred_proba", "min"),
                prob_max=("pred_proba", "max"),
            )
            .reset_index()
        )
        grouped["model"] = model_name
        bands_rows.extend(grouped.to_dict("records"))

        if transformed_feature_names is None:
            transformed_feature_names = list(
                pipeline.named_steps["preprocessor"].get_feature_names_out()
            )
        model = pipeline.named_steps["model"]
        importances = np.abs(model.coef_[0]) if model_name == "logistic" else model.feature_importances_
        top_idx = np.argsort(importances)[::-1][:20]
        for idx in top_idx:
            feature_rows.append(
                {
                    "model": model_name,
                    "feature": transformed_feature_names[idx],
                    "importance": float(importances[idx]),
                }
            )

    return (
        pd.DataFrame(metrics_rows).sort_values("roc_auc", ascending=False),
        pd.DataFrame(feature_rows).sort_values(["model", "importance"], ascending=[True, False]),
        pd.DataFrame(bands_rows),
    )


def render_markdown(
    selected_files: list[SelectedFile],
    manifest: pd.DataFrame,
    union_frame: pd.DataFrame,
    analysis_frame: pd.DataFrame,
    numeric_stats: pd.DataFrame,
    category_tables: dict[str, pd.DataFrame],
    rules: pd.DataFrame,
    model_metrics: pd.DataFrame,
    feature_importance: pd.DataFrame,
    probability_bands: pd.DataFrame,
) -> str:
    baseline_hit = float(analysis_frame["resultado_binario"].mean())
    baseline_roi = float(analysis_frame["profit_unitario"].mean())
    raw_binary_rows = int(union_frame["resultado_binario"].isin([0.0, 1.0]).sum())
    duplicate_rows = int(raw_binary_rows - len(analysis_frame))

    lines = [
        "# Analisis de resultados de la rama estrategia calibrada",
        "",
        f"Rama analizada: `{BRANCH}`.",
        "",
        "## Resumen ejecutivo",
        "",
        f"- CSV con resultado util extraidos: **{len(selected_files)}**.",
        f"- Filas en la union cruda: **{len(union_frame):,}**.",
        f"- Filas con target binario usable: **{raw_binary_rows:,}**.",
        f"- Filas deduplicadas para analisis: **{len(analysis_frame):,}**.",
        f"- Duplicados removidos entre backups/reconstrucciones/versiones: **{duplicate_rows:,}**.",
        f"- Hit rate global deduplicado: **{baseline_hit:.2%}**.",
        f"- ROI unitario medio deduplicado: **{baseline_roi:.3f}**.",
        "",
        "## Hallazgos principales",
        "",
    ]

    if not numeric_stats.empty:
        for _, row in numeric_stats.head(5).iterrows():
            direction = "mayor" if row["mean_diff"] > 0 else "menor"
            lines.append(
                f"- `{row['feature']}` tiende a ser {direction} en aciertos "
                f"(diff={row['mean_diff']:.4f}, p={row['mannwhitney_p']:.4g}, d={row['cohens_d']:.3f})."
            )
    if "Mercado" in category_tables and not category_tables["Mercado"].empty:
        for _, row in category_tables["Mercado"].head(3).iterrows():
            lines.append(
                f"- Mercado destacado: `{row['Mercado']}` con n={int(row['n'])}, "
                f"hit_rate={row['hit_rate']:.2%}, ROI={row['roi']:.3f}."
            )
    if not rules.empty:
        top_rule = rules.iloc[0]
        lines.append(
            f"- Mejor regla conjunta encontrada: `{top_rule['rule']}` "
            f"(n={int(top_rule['n'])}, hit_rate={top_rule['hit_rate']:.2%}, ROI={top_rule['roi']:.3f})."
        )
    if not model_metrics.empty:
        best_model = model_metrics.iloc[0]
        lines.append(
            f"- Mejor modelo fuera de muestra: `{best_model['model']}` "
            f"con ROC AUC={best_model['roc_auc']:.3f} y accuracy={best_model['accuracy']:.3f}."
        )

    lines.extend(["", "## Artefactos generados", ""])
    lines.extend(
        [
            f"- Carpeta de CSV con resultado: `{OUTPUT_DIR.relative_to(BASE_DIR)}`.",
            "- `manifest_resultados.csv`: inventario de archivos extraidos.",
            "- `consolidado_resultados_raw.csv`: union de todas las filas con metadatos de origen.",
            "- `consolidado_resultados_analisis.csv`: dataset deduplicado y normalizado usado para estadistica y ML.",
            "- `metricas_numericas.csv`, `reglas_segmentos.csv`, `metricas_modelos.csv`, `importancia_features.csv`, `bandas_probabilidad.csv`.",
            "",
            "## Inventario de archivos extraidos",
            "",
        ]
    )
    lines.append("| Archivo original | Filas | Filas con resultado | Columnas de resultado |")
    lines.append("| --- | ---: | ---: | --- |")
    for _, row in manifest.iterrows():
        lines.append(
            f"| `{row['source_git_path']}` | {int(row['rows'])} | {int(row['usable_result_rows'])} | {row['result_columns']} |"
        )

    def append_table(title: str, frame: pd.DataFrame, keep_columns: list[str], limit: int = 10) -> None:
        lines.extend(["", f"## {title}", ""])
        if frame.empty:
            lines.append("Sin filas suficientes para este corte.")
            return
        display = frame[keep_columns].head(limit).copy()
        lines.append("| " + " | ".join(keep_columns) + " |")
        lines.append("| " + " | ".join(["---"] * len(keep_columns)) + " |")
        for _, row in display.iterrows():
            rendered: list[str] = []
            for column in keep_columns:
                value = row[column]
                if isinstance(value, float):
                    rendered.append(f"{value:.4f}")
                else:
                    rendered.append(str(value))
            lines.append("| " + " | ".join(rendered) + " |")

    append_table(
        "Variables numericas con mas senal",
        numeric_stats,
        ["feature", "n", "hit_mean", "miss_mean", "mean_diff", "cohens_d", "mannwhitney_p"],
    )
    for name, frame in category_tables.items():
        append_table(f"Segmentacion por {name}", frame, [name, "n", "hit_rate", "roi"])
    append_table(
        "Reglas conjuntas candidatas",
        rules,
        ["rule", "n", "hit_rate", "roi", "hit_lift", "roi_lift"],
        limit=20,
    )
    append_table(
        "Metricas de modelos",
        model_metrics,
        ["model", "train_rows", "test_rows", "accuracy", "roc_auc", "brier", "log_loss"],
        limit=10,
    )
    append_table(
        "Features mas importantes",
        feature_importance,
        ["model", "feature", "importance"],
        limit=25,
    )
    append_table(
        "Bandas de probabilidad del test",
        probability_bands,
        ["model", "prob_bin", "n", "hit_rate", "roi", "prob_min", "prob_max"],
        limit=15,
    )
    lines.extend(
        [
            "",
            "## Notas metodologicas",
            "",
            "- La union cruda conserva todos los archivos con resultado disponible por fila; esto incluye backups y reconstrucciones.",
            "- El analisis usa la version deduplicada para evitar que un mismo evento repetido en backups sesgue tendencias y modelos.",
            "- El target binario se toma solo de columnas explicitamente observadas (`Resultado`, `Acerto`, etc.).",
            "- Los modelos usan solo variables prepartido o de mercado, no columnas de resultado real.",
        ]
    )
    return "\n".join(lines) + "\n"


def ensure_output_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_output_dirs()
    selected_files = select_files_with_results()
    if not selected_files:
        raise SystemExit("No se encontraron CSV con resultado util.")

    manifest_rows: list[dict[str, object]] = []
    enriched_frames: list[pd.DataFrame] = []

    for selected_file in selected_files:
        export_path = OUTPUT_DIR / selected_file.export_name
        export_path.write_text(selected_file.raw_csv, encoding="utf-8")
        manifest_rows.append(
            {
                "source_git_path": selected_file.git_path,
                "export_name": selected_file.export_name,
                "rows": selected_file.rows,
                "usable_result_rows": selected_file.usable_result_rows,
                "result_columns": ", ".join(selected_file.result_columns),
                "source_group": source_group(selected_file.git_path),
            }
        )
        enriched_frames.append(enrich_dataframe(selected_file))

    manifest = pd.DataFrame(manifest_rows).sort_values(
        ["source_group", "source_git_path"], ascending=[True, True]
    )
    union_frame = pd.concat(enriched_frames, ignore_index=True, sort=False)
    analysis_frame = deduplicate_for_analysis(union_frame)
    numeric_stats = numeric_feature_stats(analysis_frame)
    category_tables = {
        name: summarise_categories(analysis_frame, name)
        for name in ["market_family", "Mercado", "Tipo_Mercado", "Liga", "Mejor_Casa", "source_group"]
    }
    baseline_hit = float(analysis_frame["resultado_binario"].mean())
    baseline_roi = float(analysis_frame["profit_unitario"].mean())
    rules = rule_mining(analysis_frame, baseline_hit=baseline_hit, baseline_roi=baseline_roi)
    model_metrics, feature_importance, probability_bands = run_models(analysis_frame)

    manifest.to_csv(OUTPUT_DIR / "manifest_resultados.csv", index=False)
    union_frame.to_csv(OUTPUT_DIR / "consolidado_resultados_raw.csv", index=False)
    analysis_frame.to_csv(OUTPUT_DIR / "consolidado_resultados_analisis.csv", index=False)
    numeric_stats.to_csv(OUTPUT_DIR / "metricas_numericas.csv", index=False)
    rules.to_csv(OUTPUT_DIR / "reglas_segmentos.csv", index=False)
    model_metrics.to_csv(OUTPUT_DIR / "metricas_modelos.csv", index=False)
    feature_importance.to_csv(OUTPUT_DIR / "importancia_features.csv", index=False)
    probability_bands.to_csv(OUTPUT_DIR / "bandas_probabilidad.csv", index=False)
    for name, frame in category_tables.items():
        frame.to_csv(OUTPUT_DIR / f"segmentacion_{name}.csv", index=False)

    report = render_markdown(
        selected_files=selected_files,
        manifest=manifest,
        union_frame=union_frame,
        analysis_frame=analysis_frame,
        numeric_stats=numeric_stats,
        category_tables=category_tables,
        rules=rules,
        model_metrics=model_metrics,
        feature_importance=feature_importance,
        probability_bands=probability_bands,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Archivos exportados: {len(selected_files)}")
    print(f"Union cruda: {len(union_frame)} filas")
    print(f"Analisis deduplicado: {len(analysis_frame)} filas")
    print(f"Reporte: {REPORT_PATH}")


if __name__ == "__main__":
    main()
