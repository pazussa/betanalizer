#!/usr/bin/env python3
"""Actualizar un CSV con estados/marcadores obtenidos manualmente (web).

Objetivo:
- Reemplazar filas con Resultado == 'Sin datos' por:
  - Resultado recalculado (Acertado/Fallido) si el partido está Finalizado y hay marcador.
  - Resultado = 'Pendiente' si el partido está en juego/HT o aplazado.
- Añadir columnas informativas: Estado_Partido, Fuente_Web, Actualizado_Web_UTC.

Nota: este script NO hace scraping ni llama a APIs; aplica un set de overrides.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import unicodedata

import pandas as pd


def normalizar(text: str) -> str:
    if text is None:
        return ""
    text = " ".join(str(text).lower().split())
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )


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


@dataclass(frozen=True)
class WebOverride:
    partido: str
    estado: str
    marcador: str | None
    fuente: str


WEB_OVERRIDES: list[WebOverride] = [
    WebOverride("Levante vs Villarreal", "Aplazado", None, "ESPN"),
    WebOverride("CD Castellón vs CD Mirandés", "En juego", "1-1", "ESPN / LiveScore"),
    WebOverride("Boulogne vs Troyes", "Descanso", "1-1", "ESPN"),
    WebOverride("Rangers vs Hibernian", "Descanso", "1-0", "Sky Sports"),
    WebOverride("Nacional vs Tondela", "Finalizado", "3-1", "BBC"),
    WebOverride("Braga vs Santa Clara", "En juego", "1-0", "BBC"),
    WebOverride("AS Roma vs Como", "Descanso", "0-0", "ESPN"),
]


def _mask_for_partido(df: pd.DataFrame, partido: str) -> pd.Series:
    """Match robusto por nombre de partido: exacto normalizado o parcial por equipos."""
    target = normalizar(partido)
    partido_norm = df["Partido"].map(normalizar)
    if (partido_norm == target).any():
        return partido_norm == target

    # Match parcial: ambos equipos aparecen
    parts = target.split(" vs ")
    if len(parts) != 2:
        return partido_norm == target

    home, away = parts
    return partido_norm.str.contains(home, na=False) & partido_norm.str.contains(away, na=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aplica overrides web a un CSV de pronósticos")
    parser.add_argument(
        "--input",
        default="analisis_mercados_fusionado_20251213_con_confianza_con_resultados.csv",
        help="CSV de entrada",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="CSV de salida (por defecto: <input>_web_actualizado.csv)",
    )
    parser.add_argument(
        "--only-sin-datos",
        action="store_true",
        help="Solo actualiza filas con Resultado == 'Sin datos' (recomendado)",
    )
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output or input_path.replace(".csv", "_web_actualizado.csv")

    df = pd.read_csv(input_path)

    for col in ["Marcador", "Resultado", "Estado_Partido", "Fuente_Web", "Actualizado_Web_UTC"]:
        if col not in df.columns:
            df[col] = ""

    updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    updated_rows = 0
    for ov in WEB_OVERRIDES:
        mask = _mask_for_partido(df, ov.partido)
        if args.only_sin_datos:
            mask = mask & df["Resultado"].astype(str).str.strip().eq("Sin datos")

        if not mask.any():
            continue

        df.loc[mask, "Estado_Partido"] = ov.estado
        df.loc[mask, "Fuente_Web"] = ov.fuente
        df.loc[mask, "Actualizado_Web_UTC"] = updated_at

        if ov.marcador:
            df.loc[mask, "Marcador"] = ov.marcador

        if ov.estado == "Finalizado" and ov.marcador and "-" in ov.marcador:
            try:
                gl_s, gv_s = ov.marcador.split("-", 1)
                gl, gv = int(gl_s.strip()), int(gv_s.strip())
            except ValueError:
                df.loc[mask, "Resultado"] = "Sin datos"
            else:
                df.loc[mask, "Resultado"] = df.loc[mask].apply(
                    lambda r: verificar_pronostico(str(r.get("Mercado")), str(r.get("Tipo_Mercado")), gl, gv),
                    axis=1,
                )
        else:
            # En juego / descanso / aplazado => aún no hay veredicto
            df.loc[mask, "Resultado"] = "Pendiente"

        updated_rows += int(mask.sum())

    df.to_csv(output_path, index=False)

    # Resumen rápido
    vc = df["Resultado"].fillna("NA").value_counts()
    print("=" * 60)
    print("ACTUALIZACIÓN WEB APLICADA")
    print("=" * 60)
    print(f"Entrada: {input_path}")
    print(f"Salida:  {output_path}")
    print(f"Filas actualizadas: {updated_rows}")
    print("\nResultado counts:\n", vc.to_string())

    # Rendimiento solo para Acertado/Fallido
    acertados = df[df["Resultado"] == "Acertado"]
    fallidos = df[df["Resultado"] == "Fallido"]
    verificados = len(acertados) + len(fallidos)
    if verificados:
        suma_cuotas = float(acertados["Mejor_Cuota"].sum())
        rendimiento = suma_cuotas - verificados
        roi = (rendimiento / verificados) * 100.0
        print("\n" + "-" * 60)
        print("RENDIMIENTO (solo verificados)")
        print("-" * 60)
        print(f"Verificados: {verificados}")
        print(f"Suma cuotas acertados: {suma_cuotas:.4f}")
        print(f"Rendimiento neto: {rendimiento:+.4f}")
        print(f"ROI: {roi:+.2f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
