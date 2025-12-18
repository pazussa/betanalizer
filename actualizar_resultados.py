#!/usr/bin/env python3
"""
Script para actualizar el dataset de mejores_oportunidades_apuestas.csv
con los resultados de los partidos que ya jugaron y calcular el rendimiento.

Autor: BetAnalizer
Fecha: 25 de noviembre de 2025
"""

import argparse
import asyncio
import logging
import os
import sys
import unicodedata
from datetime import datetime

import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Evitar que httpx imprima URLs completas con `apiKey` en INFO
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


# Mapeo de ligas del CSV a sport_keys de The Odds API
# Nota: algunas ligas comparten nombre en el CSV (p.ej. "Super League", "Primera División").
# En esos casos, consultamos múltiples sport_keys y unimos resultados.
LIGA_A_SPORT_KEYS = {
    "EPL": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "La Liga 2": "soccer_spain_segunda_division",
    "Bundesliga": "soccer_germany_bundesliga",
    "Bundesliga 2": "soccer_germany_bundesliga2",
    "Serie A": "soccer_italy_serie_a",
    "Serie B": "soccer_italy_serie_b",
    "Ligue 1": "soccer_france_ligue_one",
    "Ligue 2": "soccer_france_ligue_two",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "Primeira Liga": "soccer_portugal_primeira_liga",
    "Super League": ["soccer_turkey_super_league", "soccer_greece_super_league"],
    "Austrian Bundesliga": "soccer_austria_bundesliga",
    "Swiss Superleague": "soccer_switzerland_superleague",
    "Superliga": "soccer_denmark_superliga",
    "Ekstraklasa": "soccer_poland_ekstraklasa",
    "Premiership": "soccer_spl",
    "League 1": "soccer_england_league1",
    "League 2": "soccer_england_league2",
    "3. Liga": "soccer_germany_liga3",
    "Championship": "soccer_efl_champ",
    "Champions League": "soccer_uefa_champs_league",
    "Europa League": "soccer_uefa_europa_league",
    "Conference League": "soccer_uefa_europa_conference_league",
    "Brasileirão": "soccer_brazil_campeonato",
    "Primera División": ["soccer_argentina_primera_division", "soccer_chile_campeonato"],
    "Liga MX": "soccer_mexico_ligamx",
    "MLS": "soccer_usa_mls",
    "J League": "soccer_japan_j_league",
    "K League 1": "soccer_korea_kleague1",
    "A-League": "soccer_australia_aleague",
    "Belgium First Div": "soccer_belgium_first_div",
}


class APIAuthError(RuntimeError):
    pass


class ResultadosUpdater:
    """Clase para actualizar resultados de partidos desde The Odds API"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self):
        self.api_key = os.getenv("THE_ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("THE_ODDS_API_KEY es requerida en el archivo .env")
        
        self.client = httpx.AsyncClient(timeout=30.0)
        self.resultados_cache = {}
    
    async def obtener_scores(self, sport_key: str, days_from: int = 3) -> dict:
        """
        Obtiene los resultados de partidos completados para una liga específica
        
        Args:
            sport_key: Clave de la liga en The Odds API
            
        Returns:
            Diccionario con resultados {partido_nombre: (goles_local, goles_visitante)}
        """
        if sport_key in self.resultados_cache:
            return self.resultados_cache[sport_key]
        
        try:
            url = f"{self.BASE_URL}/sports/{sport_key}/scores"
            params = {
                "apiKey": self.api_key,
                "daysFrom": days_from,
                "dateFormat": "iso"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            resultados = {}
            
            for evento in data:
                if evento.get("completed") and evento.get("scores"):
                    home_team = evento["home_team"]
                    away_team = evento["away_team"]
                    partido_nombre = f"{home_team} vs {away_team}"
                    
                    # Extraer scores
                    scores = evento["scores"]
                    goles_local = None
                    goles_visitante = None
                    
                    for score in scores:
                        if score["name"] == home_team:
                            goles_local = int(score["score"])
                        elif score["name"] == away_team:
                            goles_visitante = int(score["score"])
                    
                    if goles_local is not None and goles_visitante is not None:
                        resultados[partido_nombre] = (goles_local, goles_visitante)
                        logger.debug(f"Resultado obtenido: {partido_nombre} = {goles_local}-{goles_visitante}")
            
            self.resultados_cache[sport_key] = resultados
            logger.info(f"Obtenidos {len(resultados)} resultados de {sport_key}")
            return resultados
            
        except httpx.HTTPStatusError as e:
            detalle = ""
            try:
                detalle = e.response.text or ""
            except Exception:
                detalle = ""

            if e.response.status_code == 401:
                raise APIAuthError(
                    "The Odds API respondió 401 (Unauthorized). Revisa THE_ODDS_API_KEY y/o tu cuota del plan."
                )

            if e.response.status_code == 422:
                logger.warning(
                    f"Error HTTP 422 obteniendo scores de {sport_key}. "
                    f"Revisa el parámetro daysFrom (en The Odds API suele estar limitado; prueba 1-3)."
                )
            else:
                logger.warning(f"Error HTTP {e.response.status_code} obteniendo scores de {sport_key}")

            if detalle:
                logger.debug(f"Detalle HTTP error {sport_key}: {detalle}")
            return {}
        except Exception as e:
            logger.warning(f"Error obteniendo scores de {sport_key}: {e}")
            return {}
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()


def verificar_pronostico(partido: str, mercado: str, tipo_mercado: str, 
                         goles_local: int, goles_visitante: int) -> str:
    """
    Verifica si el pronóstico se cumplió basándose en el resultado real
    
    Args:
        partido: Nombre del partido
        mercado: Mercado específico (1X, X2, Over 2.5, Under 2.5, etc.)
        tipo_mercado: Tipo de mercado (Doble Chance, Goles (Over/Under), etc.)
        goles_local: Goles del equipo local
        goles_visitante: Goles del equipo visitante
        
    Returns:
        "Acertado", "Fallido", o "Error" si no se puede determinar
    """
    total_goles = goles_local + goles_visitante
    
    # Evaluar según el tipo de mercado
    if tipo_mercado == "Doble Chance":
        if mercado == "1X":
            # 1X = Local gana O Empate
            cumplido = goles_local >= goles_visitante
        elif mercado == "X2":
            # X2 = Empate O Visitante gana
            cumplido = goles_visitante >= goles_local
        elif mercado == "12":
            # 12 = Local gana O Visitante gana (no empate)
            cumplido = goles_local != goles_visitante
        else:
            return "Error"
            
    elif tipo_mercado == "Goles (Over/Under)":
        # Extraer el punto (ej: "Over 2.5" -> 2.5)
        try:
            parts = mercado.split()
            if len(parts) >= 2:
                tipo = parts[0]  # "Over" o "Under"
                punto = float(parts[1])
                
                if tipo == "Over":
                    cumplido = total_goles > punto
                elif tipo == "Under":
                    cumplido = total_goles < punto
                else:
                    return "Error"
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


def normalizar_nombre_partido(partido: str) -> str:
    """
    Normaliza el nombre del partido para comparación
    Elimina espacios extra y convierte a minúsculas
    """
    if partido is None:
        return ""
    text = " ".join(str(partido).lower().split())
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )


def _sport_keys_for_liga(liga: str) -> list[str]:
    keys = LIGA_A_SPORT_KEYS.get(liga)
    if not keys:
        return []
    if isinstance(keys, list):
        return keys
    return [keys]


def buscar_resultado(partido: str, resultados: dict) -> tuple:
    """
    Busca el resultado de un partido en el diccionario de resultados.
    Intenta coincidencia exacta primero, luego búsqueda parcial.
    
    Returns:
        Tupla (goles_local, goles_visitante) o None si no se encuentra
    """
    # Coincidencia exacta
    if partido in resultados:
        return resultados[partido]
    
    # Normalizar y buscar
    partido_norm = normalizar_nombre_partido(partido)
    
    for nombre, scores in resultados.items():
        if normalizar_nombre_partido(nombre) == partido_norm:
            return scores
        
        # Buscar coincidencia parcial (ambos equipos presentes)
        nombre_norm = normalizar_nombre_partido(nombre)
        partido_parts = partido_norm.split(" vs ")
        nombre_parts = nombre_norm.split(" vs ")
        
        if len(partido_parts) == 2 and len(nombre_parts) == 2:
            # Verificar si los equipos coinciden (pueden estar en diferente orden en algunos casos)
            if (partido_parts[0] in nombre_norm and partido_parts[1] in nombre_norm):
                return scores
    
    return None


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Actualiza un CSV con resultados reales desde The Odds API y evalúa si el pronóstico se cumplió."
    )
    parser.add_argument("--input", default="mejores_oportunidades_apuestas.csv", help="CSV de entrada")
    parser.add_argument("--output", default=None, help="CSV de salida (por defecto: <input>_con_resultados.csv)")
    parser.add_argument("--days-from", type=int, default=3, help="Días hacia atrás para consultar scores en The Odds API")
    parser.add_argument(
        "--only-leagues",
        default=None,
        help="Lista de ligas (separadas por coma) a consultar. Si no se indica, consulta todas las ligas presentes.",
    )
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Si el CSV ya tiene columna 'Resultado', consulta solo las ligas que tienen filas 'Sin datos'.",
    )
    parser.add_argument(
        "--only-unresolved",
        action="store_true",
        help="Si el CSV ya tiene columna 'Resultado', preserva Acertado/Fallido y recalcula solo filas 'Sin datos' o 'Pendiente'.",
    )
    parser.add_argument(
        "--as-of",
        default=None,
        help="Fecha/hora de corte para considerar 'ya jugado' (formato: YYYY-MM-DD HH:MM:SS). Por defecto: ahora.",
    )
    args = parser.parse_args()

    # /scores (The Odds API) suele limitar daysFrom (p.ej. a 3). Para evitar 422, lo acotamos.
    if args.days_from < 1:
        logger.error("--days-from debe ser >= 1")
        sys.exit(1)
    if args.days_from > 3:
        logger.warning("--days-from=%s no es soportado por /scores; usando 3", args.days_from)
        args.days_from = 3

    input_file = args.input
    output_file = args.output or input_file.replace('.csv', '_con_resultados.csv')
    
    if not os.path.exists(input_file):
        logger.error(f"No se encontró el archivo {input_file}")
        sys.exit(1)
    
    # Leer el CSV
    df = pd.read_csv(input_file)
    logger.info(f"Leídas {len(df)} filas del archivo {input_file}")

    # Si vamos a rellenar solo faltantes, preservamos resultados existentes
    preserve_existing = (args.only_missing or args.only_unresolved) and ('Resultado' in df.columns)
    original_resultado = df['Resultado'].copy() if 'Resultado' in df.columns else None
    original_marcador = df['Marcador'].copy() if 'Marcador' in df.columns else None
    
    # Verificar columnas necesarias
    columnas_requeridas = ['Partido', 'Fecha_Hora_Colombia', 'Liga', 'Tipo_Mercado', 'Mercado', 'Mejor_Cuota']
    for col in columnas_requeridas:
        if col not in df.columns:
            logger.error(f"Falta la columna requerida: {col}")
            sys.exit(1)
    
    # Fecha de corte (naive) para comparar con la columna Fecha_Hora_Colombia
    if args.as_of:
        try:
            ahora = datetime.strptime(args.as_of, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.error("Formato inválido para --as-of. Usa: YYYY-MM-DD HH:MM:SS")
            sys.exit(1)
    else:
        ahora = datetime.now()

    # La API de /scores refleja el estado actual. Si el corte está en el futuro,
    # no podremos verificar partidos que aún no han finalizado.
    if args.as_of:
        ahora_real = datetime.now()
        if ahora > ahora_real:
            logger.warning(
                "--as-of (%s) está en el futuro; usando ahora (%s) como corte efectivo para Ya_Jugado",
                args.as_of,
                ahora_real.strftime("%Y-%m-%d %H:%M:%S"),
            )
            ahora = ahora_real
    
    # Convertir fecha a datetime (naive)
    df['Fecha_Hora_DT'] = pd.to_datetime(df['Fecha_Hora_Colombia'])
    
    # Identificar partidos ya jugados (fecha < ahora)
    df['Ya_Jugado'] = df['Fecha_Hora_DT'] < pd.Timestamp(ahora)

    # Filtrar ligas objetivo para reducir consumo de cuota en la API
    ligas_objetivo = None
    if args.only_leagues:
        ligas_objetivo = [x.strip() for x in args.only_leagues.split(",") if x.strip()]
    elif (args.only_missing or args.only_unresolved) and 'Resultado' in df.columns:
        if args.only_missing:
            mask_unresolved = df['Resultado'].astype(str).str.strip().eq('Sin datos')
        else:
            mask_unresolved = df['Resultado'].astype(str).str.strip().isin(['Sin datos', 'Pendiente'])
        ligas_objetivo = df.loc[mask_unresolved, 'Liga'].dropna().unique().tolist()
    
    partidos_jugados = df[df['Ya_Jugado']]['Partido'].unique()
    logger.info(f"Partidos que ya se jugaron: {len(partidos_jugados)}")
    
    # Obtener las ligas únicas de los partidos jugados
    ligas_jugadas = df[df['Ya_Jugado']]['Liga'].unique()
    if ligas_objetivo is not None:
        ligas_jugadas = [l for l in ligas_jugadas if l in set(ligas_objetivo)]
    logger.info(f"Ligas a consultar: {list(ligas_jugadas)}")
    
    # Inicializar actualizador
    updater = ResultadosUpdater()

    todos_resultados = {}
    try:
        # Obtener resultados de cada liga
        for liga in ligas_jugadas:
            sport_keys = _sport_keys_for_liga(liga)
            if not sport_keys:
                logger.warning(f"No se encontró sport_key para la liga: {liga}")
                continue

            for sport_key in sport_keys:
                resultados = await updater.obtener_scores(sport_key, days_from=args.days_from)
                todos_resultados.update(resultados)
                await asyncio.sleep(0.3)  # Rate limiting
    except APIAuthError as e:
        logger.error(str(e))
        logger.error("Abortando sin generar archivo de salida para evitar resultados incompletos.")
        sys.exit(1)
    finally:
        await updater.close()
    
    logger.info(f"Total de resultados obtenidos: {len(todos_resultados)}")
    
    # Mostrar resultados obtenidos
    if todos_resultados:
        print("\n" + "="*60)
        print("RESULTADOS OBTENIDOS DE LA API")
        print("="*60)
        for partido, (gl, gv) in sorted(todos_resultados.items()):
            print(f"  {partido}: {gl}-{gv}")
    
    # Agregar columnas de resultado
    def obtener_marcador(row):
        if not row['Ya_Jugado']:
            return ""

        resultado = buscar_resultado(row['Partido'], todos_resultados)
        if resultado is None:
            return ""

        goles_local, goles_visitante = resultado
        return f"{goles_local}-{goles_visitante}"

    def obtener_resultado_str(row):
        if not row['Ya_Jugado']:
            return "Pendiente"
        
        resultado = buscar_resultado(row['Partido'], todos_resultados)
        if resultado is None:
            return "Sin datos"
        
        goles_local, goles_visitante = resultado
        return verificar_pronostico(
            row['Partido'],
            row['Mercado'],
            row['Tipo_Mercado'],
            goles_local,
            goles_visitante
        )

    df['Marcador'] = df.apply(obtener_marcador, axis=1)

    df['Resultado'] = df.apply(obtener_resultado_str, axis=1)

    if preserve_existing and original_resultado is not None:
        if args.only_missing:
            mask_update = original_resultado.astype(str).str.strip().eq('Sin datos')
        else:
            mask_update = original_resultado.astype(str).str.strip().isin(['Sin datos', 'Pendiente'])
        # Mantener valores anteriores donde no se actualiza
        df.loc[~mask_update, 'Resultado'] = original_resultado.loc[~mask_update].values
        if original_marcador is not None:
            df.loc[~mask_update, 'Marcador'] = original_marcador.loc[~mask_update].fillna('').values
    
    # Eliminar columna temporal
    df = df.drop(columns=['Fecha_Hora_DT', 'Ya_Jugado'])
    
    # Guardar archivo actualizado
    df.to_csv(output_file, index=False)
    
    # Calcular estadísticas y rendimiento
    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)
    
    total = len(df)
    acertados = df[df['Resultado'] == 'Acertado']
    fallidos = df[df['Resultado'] == 'Fallido']
    pendientes = df[df['Resultado'] == 'Pendiente']
    sin_datos = df[df['Resultado'] == 'Sin datos']
    
    print(f"\nTotal de pronósticos: {total}")
    print(f"  ✅ Acertados: {len(acertados)}")
    print(f"  ❌ Fallidos: {len(fallidos)}")
    print(f"  ⏳ Pendientes: {len(pendientes)}")
    print(f"  ❓ Sin datos: {len(sin_datos)}")
    
    # Calcular rendimiento SOLO para partidos ya jugados con resultado
    partidos_verificados = len(acertados) + len(fallidos)
    
    if partidos_verificados > 0:
        # Rendimiento = (Suma de cuotas de acertados) - (Cantidad de partidos jugados)
        suma_cuotas_acertados = acertados['Mejor_Cuota'].sum()
        rendimiento = suma_cuotas_acertados - partidos_verificados
        
        # Porcentaje de acierto
        porcentaje_acierto = (len(acertados) / partidos_verificados) * 100
        
        # ROI (Return on Investment)
        roi = (rendimiento / partidos_verificados) * 100
        
        print("\n" + "-"*60)
        print("RENDIMIENTO (partidos ya jugados con resultado)")
        print("-"*60)
        print(f"  Partidos verificados: {partidos_verificados}")
        print(f"  Pronósticos acertados: {len(acertados)}")
        print(f"  Porcentaje de acierto: {porcentaje_acierto:.2f}%")
        print(f"\n  Suma de cuotas de acertados: {suma_cuotas_acertados:.4f}")
        print(f"  Inversión (1 unidad por apuesta): {partidos_verificados}")
        print(f"\n  📊 RENDIMIENTO NETO: {rendimiento:+.4f} unidades")
        print(f"  📈 ROI: {roi:+.2f}%")
        
        if rendimiento > 0:
            print(f"\n  💰 ¡GANANCIA! Si apostaste 1€ por apuesta, ganaste {rendimiento:.2f}€")
        elif rendimiento < 0:
            print(f"\n  💸 PÉRDIDA: Si apostaste 1€ por apuesta, perdiste {abs(rendimiento):.2f}€")
        else:
            print(f"\n  🔄 EMPATE: No hubo ganancia ni pérdida")
    else:
        print("\n⚠️  No hay partidos con resultado verificado para calcular rendimiento")
    
    # Detalle por estrategia
    if 'Estrategia' in df.columns and partidos_verificados > 0:
        print("\n" + "-"*60)
        print("RENDIMIENTO POR ESTRATEGIA")
        print("-"*60)
        
        for estrategia in df['Estrategia'].unique():
            df_est = df[df['Estrategia'] == estrategia]
            acertados_est = df_est[df_est['Resultado'] == 'Acertado']
            fallidos_est = df_est[df_est['Resultado'] == 'Fallido']
            verificados_est = len(acertados_est) + len(fallidos_est)
            
            if verificados_est > 0:
                suma_cuotas_est = acertados_est['Mejor_Cuota'].sum()
                rendimiento_est = suma_cuotas_est - verificados_est
                pct_acierto_est = (len(acertados_est) / verificados_est) * 100
                roi_est = (rendimiento_est / verificados_est) * 100
                
                emoji = "✅" if rendimiento_est > 0 else ("❌" if rendimiento_est < 0 else "🔄")
                print(f"\n  {estrategia}:")
                print(f"    Verificados: {verificados_est} | Aciertos: {len(acertados_est)} ({pct_acierto_est:.1f}%)")
                print(f"    {emoji} Rendimiento: {rendimiento_est:+.4f} | ROI: {roi_est:+.1f}%")
    
    print("\n" + "="*60)
    print(f"💾 Archivo actualizado: {output_file}")
    print("="*60)
    
    return output_file


if __name__ == "__main__":
    asyncio.run(main())
