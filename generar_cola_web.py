#!/usr/bin/env python3
"""Genera una cola de verificación web para partidos sin resultado.

Crea un CSV con partidos únicos (Partido+Fecha+Liga) donde Resultado es NA/Sin datos
(o Pendiente si quieres) y la fecha ya pasó.

Uso:
    python generar_cola_web.py --input mejores_oportunidades_apuestas_con_resultados_refresco_web_aplicado.csv \
        --output data/cola_web_top100.csv --limit 100

Luego puedes rellenar manualmente las columnas `Marcador_Final` y `Fuente_URL`.
"""

from __future__ import annotations

import argparse
from datetime import datetime

import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser(description="Genera cola para verificación web")
    ap.add_argument(
        "--input",
        default="mejores_oportunidades_apuestas_con_resultados_refresco_web_aplicado.csv",
        help="CSV con pronósticos (default: mejores_oportunidades_apuestas_con_resultados_refresco_web_aplicado.csv)",
    )
    ap.add_argument(
        "--output",
        default="data/cola_web_top100.csv",
        help="CSV de salida (cola) (default: data/cola_web_top100.csv)",
    )
    ap.add_argument(
        "--include-pendiente",
        action="store_true",
        help="Incluir también filas con Resultado == 'Pendiente'",
    )
    ap.add_argument(
        "--as-of",
        default=None,
        help="Fecha/hora de corte para considerar 'ya jugado' (YYYY-MM-DD HH:MM:SS). Por defecto: ahora.",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limitar a top N partidos por frecuencia (0 = sin límite)",
    )
    ap.add_argument(
        "--with-query",
        action="store_true",
        help="Añade columna Query pre-armada para buscar el marcador (recomendado)",
    )

    args = ap.parse_args()

    df = pd.read_csv(args.input)
    dt = pd.to_datetime(df.get("Fecha_Hora_Colombia"), errors="coerce")
    if args.as_of:
        now = pd.to_datetime(args.as_of, errors="raise")
    else:
        now = pd.Timestamp(datetime.now())
    played = dt.notna() & (dt < now)

    res = df.get("Resultado")
    if res is None:
        raise SystemExit("El input no tiene columna 'Resultado'")

    res_norm = res.fillna("NA").astype(str).str.strip()
    unresolved = res_norm.isin(["Sin datos", "NA", ""]) | (args.include_pendiente & res_norm.eq("Pendiente"))

    d = df[played & unresolved].copy()
    if d.empty:
        print("No hay filas jugadas sin resultado")
        d.to_csv(args.output, index=False)
        return 0

    # partido unique key
    out = (
        d.groupby(["Partido", "Fecha_Hora_Colombia", "Liga"], dropna=False)
        .agg(
            filas=("Partido", "size"),
            tipo_mercados=("Tipo_Mercado", lambda s: ",".join(sorted(set(map(str, s.dropna().tolist()))))[:200]),
            mercados=("Mercado", lambda s: ",".join(sorted(set(map(str, s.dropna().tolist()))))[:200]),
        )
        .reset_index()
        .sort_values("filas", ascending=False)
    )

    if args.limit and args.limit > 0:
        out = out.head(args.limit)

    if args.with_query:
        # Query genérica (sirve para ESPN/BBC/SkySports/FotMob/etc)
        out["Query"] = out.apply(
            lambda r: f"{r['Partido']} {str(r['Fecha_Hora_Colombia'])[:10]} {r['Liga']} final score",
            axis=1,
        )

    out["Marcador_Final"] = ""
    out["Fuente_URL"] = ""
    out.to_csv(args.output, index=False)
    print(f"Cola generada: {args.output} (partidos únicos: {len(out)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
