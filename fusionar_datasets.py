import argparse
from datetime import datetime

import numpy as np
import pandas as pd


DEFAULT_FILES = [
    "analisis_mercados_20251124_001340.csv",
    "analisis_mercados_20251124_002559.csv",
    "analisis_mercados_20251124_003036.csv",
    "analisis_mercados_20251124_003313.csv",
]


def calcular_confianza(df: pd.DataFrame) -> pd.Series:
    """Calcula el score de Confianza según `ESTRATEGIA_APUESTAS.md`.

    Confianza = (ROI_Histórico × 0.3) + (10 / Volatilidad_Pct) + (20 / Margen_Casa_Pct) + (Score_Final × 30)
    """

    roi_historico_por_mercado = {
        # Valores históricos (Nov 2025) documentados
        "Under 3.5": 80.0,
        "X2": 97.0,
        "Over 2.5": 100.0,
        "Under 2.5": 54.0,
    }

    roi_hist = df.get("Mercado", pd.Series(index=df.index, dtype=object)).map(roi_historico_por_mercado).fillna(0.0)

    volatilidad = pd.to_numeric(df.get("Volatilidad_Pct", 0.0), errors="coerce").fillna(0.0)
    margen = pd.to_numeric(df.get("Margen_Casa_Pct", 0.0), errors="coerce").fillna(0.0)
    score_final = pd.to_numeric(df.get("Score_Final", 0.0), errors="coerce").fillna(0.0)

    term_roi = roi_hist * 0.3
    term_vol = np.where(volatilidad > 0, 10.0 / volatilidad, 0.0)
    term_margen = np.where(margen > 0, 20.0 / margen, 0.0)
    term_score = score_final * 30.0

    return pd.Series(term_roi + term_vol + term_margen + term_score, index=df.index).round(2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fusiona datasets de análisis de mercados y (opcional) calcula Confianza.")
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=DEFAULT_FILES,
        help="Lista de CSVs a fusionar (por defecto: los 4 CSVs históricos).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Ruta de salida. Si no se indica, se genera `analisis_mercados_fusionado_<timestamp>.csv`.",
    )
    parser.add_argument(
        "--no-dedupe",
        action="store_true",
        help="No elimina filas duplicadas tras fusionar.",
    )
    parser.add_argument(
        "--add-confidence",
        action="store_true",
        help="Añade columna `Confianza` usando la fórmula documentada.",
    )

    args = parser.parse_args()

    frames = []
    for f in args.inputs:
        try:
            df = pd.read_csv(f)
            frames.append(df)
            print(f"✅ {f} leído ({len(df)} filas)")
        except Exception as e:
            print(f"❌ Error leyendo {f}: {e}")

    if not frames:
        print("❌ No se pudo leer ningún archivo.")
        return 1

    fusionado = pd.concat(frames, ignore_index=True)
    print(f"🔗 Total filas fusionadas (bruto): {len(fusionado)}")

    if not args.no_dedupe:
        before = len(fusionado)
        fusionado = fusionado.drop_duplicates()
        print(f"🧹 Duplicados eliminados: {before - len(fusionado)}")

    if args.add_confidence:
        fusionado["Confianza"] = calcular_confianza(fusionado)
        print("🧮 Columna `Confianza` calculada y añadida")

    output = args.output
    if not output:
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"analisis_mercados_fusionado_{fecha}.csv"

    fusionado.to_csv(output, index=False, encoding="utf-8")
    print(f"✅ Archivo fusionado guardado como: {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
