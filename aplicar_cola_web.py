#!/usr/bin/env python3
"""Aplica una cola de marcadores verificados (web/manual) a un CSV de picks.

- NO hace scraping.
- Lee `data/cola_web_top20.csv` (o similar) con columnas:
  Partido, Fecha_Hora_Colombia, Liga, Marcador_Final, Fuente_URL
- Para cada partido con marcador, actualiza en el CSV de entrada:
  - `Marcador` (goles_local-goles_visitante)
  - `Resultado` (Acertado/Fallido) según `Tipo_Mercado` y `Mercado`
  - `Fuente_Web` y `Actualizado_Web_UTC` (si existen o se crean)

Uso típico:
  python aplicar_cola_web.py --input mejores_oportunidades_apuestas_con_resultados_refresco.csv \
    --cola data/cola_web_top20.csv --only-sin-datos
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import re
import unicodedata

import pandas as pd


def _normalizar(text: str) -> str:
    if text is None:
        return ""
    text = " ".join(str(text).lower().split())
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )


def _mask_for_partido(df: pd.DataFrame, partido: str) -> pd.Series:
    """Match robusto por nombre de partido: exacto normalizado o parcial por equipos."""
    target = _normalizar(partido)
    partido_norm = df["Partido"].map(_normalizar)
    if (partido_norm == target).any():
        return partido_norm == target

    parts = target.split(" vs ")
    if len(parts) != 2:
        return partido_norm == target

    home, away = parts
    return partido_norm.str.contains(home, na=False) & partido_norm.str.contains(away, na=False)


def _parse_marcador(marcador: str) -> tuple[int, int] | None:
    if marcador is None:
        return None
    s = str(marcador).strip()
    if not s:
        return None

    # Normaliza guiones raros
    s = s.replace("–", "-").replace("—", "-")

    m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def verificar_pronostico(mercado: str, tipo_mercado: str, goles_local: int, goles_visitante: int) -> str:
    total_goles = goles_local + goles_visitante

    if tipo_mercado == "Doble Chance":
        if mercado == "1X":
            cumplido = goles_local >= goles_visitante
        elif mercado == "X2":
            cumplido = goles_visitante >= goles_local
        elif mercado == "12":
            cumplido = goles_local != goles_visitante
        else:
            return "Error"

    elif tipo_mercado == "Goles (Over/Under)":
        try:
            parts = str(mercado).split()
            if len(parts) < 2:
                return "Error"
            tipo = parts[0]
            punto = float(parts[1])
            if tipo == "Over":
                cumplido = total_goles > punto
            elif tipo == "Under":
                cumplido = total_goles < punto
            else:
                return "Error"
        except (ValueError, IndexError):
            return "Error"

    elif tipo_mercado == "Ambos Equipos Marcan (BTTS)":
        if mercado == "Yes":
            cumplido = goles_local > 0 and goles_visitante > 0
        elif mercado == "No":
            cumplido = goles_local == 0 or goles_visitante == 0
        else:
            return "Error"

    else:
        return "Error"

    return "Acertado" if cumplido else "Fallido"


def main() -> int:
    parser = argparse.ArgumentParser(description="Aplica una cola web de marcadores a un CSV")
    parser.add_argument(
        "--input",
        default="mejores_oportunidades_apuestas_con_resultados_refresco.csv",
        help="CSV de entrada",
    )
    parser.add_argument(
        "--cola",
        default="data/cola_web_top20.csv",
        help="CSV de cola con marcador final y fuente URL",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="CSV de salida (por defecto: <input>_web_aplicado.csv)",
    )
    parser.add_argument(
        "--only-sin-datos",
        action="store_true",
        help="Solo actualiza filas con Resultado == 'Sin datos' (recomendado)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Sobrescribe Resultado/Marcador incluso si ya están verificados",
    )

    args = parser.parse_args()

    input_path = args.input
    cola_path = args.cola
    output_path = args.output or input_path.replace(".csv", "_web_aplicado.csv")

    df = pd.read_csv(input_path)
    cola = pd.read_csv(cola_path)

    for col in ["Marcador", "Resultado", "Fuente_Web", "Actualizado_Web_UTC"]:
        if col not in df.columns:
            df[col] = ""

    # Asegura dtype string para evitar warnings/futuros errores de asignación
    for col in ["Marcador", "Resultado", "Fuente_Web", "Actualizado_Web_UTC"]:
        df[col] = df[col].astype("string")

    updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Parse datetimes una sola vez
    df_fecha = pd.to_datetime(df.get("Fecha_Hora_Colombia"), errors="coerce")
    cola_fecha = pd.to_datetime(cola.get("Fecha_Hora_Colombia"), errors="coerce")

    updated_rows = 0
    matched_partidos = 0
    applied_partidos = 0

    for i, row in cola.iterrows():
        marcador = row.get("Marcador_Final")
        parsed = _parse_marcador(marcador)
        if not parsed:
            continue

        partido = str(row.get("Partido") or "").strip()
        liga = str(row.get("Liga") or "").strip()
        fuente_url = str(row.get("Fuente_URL") or "").strip()
        fecha_dt = cola_fecha.iloc[i] if len(cola_fecha) > i else pd.NaT

        if not partido:
            continue

        base_mask = _mask_for_partido(df, partido)
        if liga and "Liga" in df.columns:
            base_mask = base_mask & df["Liga"].astype(str).str.strip().eq(liga)

        # 1) Intento estricto: partido+liga+fecha
        mask = base_mask
        if pd.notna(fecha_dt) and "Fecha_Hora_Colombia" in df.columns:
            mask = mask & (df_fecha == fecha_dt)

        # 2) Fallback: partido+liga
        if not mask.any():
            mask = base_mask

        if args.only_sin_datos and "Resultado" in df.columns:
            mask = mask & df["Resultado"].astype(str).str.strip().eq("Sin datos")

        if not args.overwrite:
            # Evita pisar verificados
            mask = mask & ~df["Resultado"].astype(str).str.strip().isin(["Acertado", "Fallido"])

        if not base_mask.any():
            continue

        matched_partidos += 1
        if not mask.any():
            continue

        gl, gv = parsed
        df.loc[mask, "Marcador"] = f"{gl}-{gv}"
        df.loc[mask, "Resultado"] = df.loc[mask].apply(
            lambda r: verificar_pronostico(str(r.get("Mercado")), str(r.get("Tipo_Mercado")), gl, gv),
            axis=1,
        )
        if fuente_url:
            df.loc[mask, "Fuente_Web"] = fuente_url
        df.loc[mask, "Actualizado_Web_UTC"] = updated_at

        updated_rows += int(mask.sum())
        applied_partidos += 1

    df.to_csv(output_path, index=False)

    vc = df["Resultado"].fillna("NA").value_counts()
    print("=" * 60)
    print("COLA WEB APLICADA")
    print("=" * 60)
    print(f"Entrada: {input_path}")
    print(f"Cola:    {cola_path}")
    print(f"Salida:  {output_path}")
    print(f"Partidos con match en dataset: {matched_partidos}")
    print(f"Partidos aplicados: {applied_partidos}")
    print(f"Filas actualizadas: {updated_rows}")
    print("\nResultado counts:\n", vc.to_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
