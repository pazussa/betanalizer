#!/usr/bin/env python3
"""Build a deduplicated master dataset from all local analysis CSVs.

- Loads every `analisis_mercados_*.csv` found in the repo root.
- Normalizes schema (adds missing columns as empty).
- Preserves existing results columns if present.
- Computes `Confianza` if not present (same formula as `fusionar_datasets.py`).
- Deduplicates using a robust key built from core identifiers.

Outputs:
- `data/master_dataset.csv`
- `data/master_dataset_deduped.csv`
"""

from __future__ import annotations

import argparse
import glob
import logging
import os
from datetime import datetime

import pandas as pd


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


CORE_COLS = [
    "Partido",
    "Fecha_Hora_Colombia",
    "Liga",
    "Tipo_Mercado",
    "Mercado",
    "Mejor_Casa",
    "Mejor_Cuota",
]

OPTIONAL_COLS = [
    "Score_Final",
    "Volatilidad_Pct",
    "Margen_Casa_Pct",
    "Num_Casas",
    "Cuota_Promedio_Mercado",
    "Diferencia_Cuota_Promedio",
    "Todas_Las_Cuotas",
    "Marcador",
    "Resultado",
    "Estado_Partido",
    "Fuente_Web",
    "Actualizado_Web_UTC",
    "Confianza",
]


def _normalize_str_series(s: pd.Series) -> pd.Series:
    s = s.fillna("").astype(str)
    s = s.str.replace(r"\s+", " ", regex=True).str.strip()
    return s


def _safe_to_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _build_dedupe_key(df: pd.DataFrame) -> pd.Series:
    parts = []
    for c in CORE_COLS:
        if c not in df.columns:
            df[c] = ""
        if c in ("Mejor_Cuota",):
            parts.append(_safe_to_numeric(df[c]).round(4).fillna(-1).astype(str))
        else:
            parts.append(_normalize_str_series(df[c]).str.lower())

    # Date normalization (best effort)
    dt = pd.to_datetime(df.get("Fecha_Hora_Colombia", ""), errors="coerce", utc=False)
    dt_norm = dt.dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")

    key = (
        parts[0]
        + "|"
        + dt_norm
        + "|"
        + parts[2]
        + "|"
        + parts[3]
        + "|"
        + parts[4]
        + "|"
        + parts[5]
        + "|"
        + parts[6]
    )
    return key


def _coalesce_result_columns(group: pd.DataFrame) -> pd.Series:
    """Pick the best row in a duplicate group.

    Preference order:
    - Has Resultado in {Acertado, Fallido}
    - Has Marcador
    - Has Resultado == Pendiente
    - Otherwise keep the last (most recently generated file tends to be later in glob)
    """

    def score_row(r: pd.Series) -> int:
        res = str(r.get("Resultado", "")).strip()
        marcador = str(r.get("Marcador", "")).strip()
        s = 0
        if res in {"Acertado", "Fallido"}:
            s += 100
        elif res == "Pendiente":
            s += 10
        if marcador and marcador.lower() != "nan":
            s += 5
        # Keep web updated rows slightly preferred
        if str(r.get("Actualizado_Web_UTC", "")).strip():
            s += 2
        return s

    scores = group.apply(score_row, axis=1)
    best_idx = scores.idxmax()
    return group.loc[best_idx]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a master dataset from all analysis CSVs")
    parser.add_argument(
        "--pattern",
        default="analisis_mercados_*.csv",
        help="Glob pattern to load (default: analisis_mercados_*.csv)",
    )
    parser.add_argument(
        "--extra-pattern",
        default="mejores_oportunidades_apuestas*.csv",
        help="Extra glob pattern to include (default: mejores_oportunidades_apuestas*.csv)",
    )
    parser.add_argument(
        "--output-raw",
        default="data/master_dataset.csv",
        help="Output path for raw concatenation",
    )
    parser.add_argument(
        "--output-dedup",
        default="data/master_dataset_deduped.csv",
        help="Output path for deduplicated dataset",
    )
    args = parser.parse_args()

    files = sorted(set(glob.glob(args.pattern) + glob.glob(args.extra_pattern)))
    if not files:
        logger.error("No files matched patterns: %s, %s", args.pattern, args.extra_pattern)
        return 1

    frames: list[pd.DataFrame] = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df["_source_file"] = os.path.basename(f)
            df["_loaded_at"] = datetime.now().isoformat(timespec="seconds")
            frames.append(df)
            logger.info("Loaded %s (%s rows)", f, len(df))
        except Exception as e:
            logger.warning("Failed reading %s: %s", f, e)

    if not frames:
        logger.error("No CSVs could be loaded")
        return 1

    master = pd.concat(frames, ignore_index=True)

    # Ensure optional columns exist
    for c in CORE_COLS + OPTIONAL_COLS:
        if c not in master.columns:
            master[c] = ""

    # Compute Confianza if missing or empty
    try:
        import fusionar_datasets

        conf = fusionar_datasets.calcular_confianza(master)
        # Overwrite only where Confianza is missing/blank
        conf_existing = pd.to_numeric(master["Confianza"], errors="coerce")
        needs = conf_existing.isna()
        master.loc[needs, "Confianza"] = conf.loc[needs].values
    except Exception as e:
        logger.warning("Could not compute Confianza via fusionar_datasets.py: %s", e)

    # Write raw
    os.makedirs(os.path.dirname(args.output_raw), exist_ok=True)
    master.to_csv(args.output_raw, index=False)
    logger.info("Wrote raw master: %s (%s rows)", args.output_raw, len(master))

    # Write verified-only (raw)
    verified_raw_path = os.path.join("data", "master_dataset_verified.csv")
    verified_raw = master[master["Resultado"].astype(str).str.strip().isin(["Acertado", "Fallido"])].copy()
    verified_raw.to_csv(verified_raw_path, index=False)
    logger.info("Wrote verified-only raw: %s (%s rows)", verified_raw_path, len(verified_raw))

    # Deduplicate
    master["_dedupe_key"] = _build_dedupe_key(master)

    grouped = master.groupby("_dedupe_key", sort=False, dropna=False)
    dedup = grouped.apply(_coalesce_result_columns).reset_index(drop=True)

    # Drop internal columns
    dedup = dedup.drop(columns=["_dedupe_key"], errors="ignore")

    dedup.to_csv(args.output_dedup, index=False)
    logger.info("Wrote deduped master: %s (%s rows)", args.output_dedup, len(dedup))

    # Write verified-only (deduped)
    verified_dedup_path = os.path.join("data", "master_dataset_deduped_verified.csv")
    verified_dedup = dedup[dedup["Resultado"].astype(str).str.strip().isin(["Acertado", "Fallido"])].copy()
    verified_dedup.to_csv(verified_dedup_path, index=False)
    logger.info("Wrote verified-only deduped: %s (%s rows)", verified_dedup_path, len(verified_dedup))

    # Quick summary
    if "Resultado" in dedup.columns:
        vc = dedup["Resultado"].fillna("NA").astype(str).str.strip().replace({"": "NA"}).value_counts()
        logger.info("Resultado counts (deduped): %s", dict(vc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
