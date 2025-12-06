#!/usr/bin/env python3
"""
Script para actualizar el dataset de mejores_oportunidades_apuestas.csv
con los resultados de los partidos que ya jugaron y calcular el rendimiento.

Autor: BetAnalizer
Fecha: 25 de noviembre de 2025
"""

import pandas as pd
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
import httpx
from dotenv import load_dotenv
import logging

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Mapeo de ligas del CSV a sport_keys de The Odds API
LIGA_A_SPORT_KEY = {
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
    "Super League": "soccer_turkey_super_league",  # Turquía y Grecia usan el mismo nombre
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
    "Primera División": "soccer_argentina_primera_division",  # Argentina o Chile
    "Liga MX": "soccer_mexico_ligamx",
    "MLS": "soccer_usa_mls",
    "J League": "soccer_japan_j_league",
    "K League 1": "soccer_korea_kleague1",
    "A-League": "soccer_australia_aleague",
}


class ResultadosUpdater:
    """Clase para actualizar resultados de partidos desde The Odds API"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self):
        self.api_key = os.getenv("THE_ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("THE_ODDS_API_KEY es requerida en el archivo .env")
        
        self.client = httpx.AsyncClient(timeout=30.0)
        self.resultados_cache = {}
    
    async def obtener_scores(self, sport_key: str) -> dict:
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
                "daysFrom": 3,  # Últimos 3 días
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
            logger.warning(f"Error HTTP {e.response.status_code} obteniendo scores de {sport_key}")
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
    return " ".join(partido.lower().split())


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
    # Archivos
    input_file = "mejores_oportunidades_apuestas.csv"
    output_file = "mejores_oportunidades_apuestas.csv"  # Sobreescribimos
    
    if not os.path.exists(input_file):
        logger.error(f"No se encontró el archivo {input_file}")
        sys.exit(1)
    
    # Leer el CSV
    df = pd.read_csv(input_file)
    logger.info(f"Leídas {len(df)} filas del archivo {input_file}")
    
    # Verificar columnas necesarias
    columnas_requeridas = ['Partido', 'Fecha_Hora_Colombia', 'Liga', 'Tipo_Mercado', 'Mercado', 'Mejor_Cuota']
    for col in columnas_requeridas:
        if col not in df.columns:
            logger.error(f"Falta la columna requerida: {col}")
            sys.exit(1)
    
    # Fecha actual (25 de noviembre de 2025, hora Colombia = UTC-5)
    # Usamos naive datetime para comparar con el CSV
    ahora = datetime(2025, 11, 25, 23, 59, 59)
    
    # Convertir fecha a datetime (naive)
    df['Fecha_Hora_DT'] = pd.to_datetime(df['Fecha_Hora_Colombia'])
    
    # Identificar partidos ya jugados (fecha < ahora)
    df['Ya_Jugado'] = df['Fecha_Hora_DT'] < pd.Timestamp(ahora)
    
    partidos_jugados = df[df['Ya_Jugado']]['Partido'].unique()
    logger.info(f"Partidos que ya se jugaron: {len(partidos_jugados)}")
    
    # Obtener las ligas únicas de los partidos jugados
    ligas_jugadas = df[df['Ya_Jugado']]['Liga'].unique()
    logger.info(f"Ligas a consultar: {list(ligas_jugadas)}")
    
    # Inicializar actualizador
    updater = ResultadosUpdater()
    
    # Obtener resultados de cada liga
    todos_resultados = {}
    for liga in ligas_jugadas:
        sport_key = LIGA_A_SPORT_KEY.get(liga)
        if sport_key:
            resultados = await updater.obtener_scores(sport_key)
            todos_resultados.update(resultados)
            await asyncio.sleep(0.3)  # Rate limiting
        else:
            logger.warning(f"No se encontró sport_key para la liga: {liga}")
    
    await updater.close()
    
    logger.info(f"Total de resultados obtenidos: {len(todos_resultados)}")
    
    # Mostrar resultados obtenidos
    if todos_resultados:
        print("\n" + "="*60)
        print("RESULTADOS OBTENIDOS DE LA API")
        print("="*60)
        for partido, (gl, gv) in sorted(todos_resultados.items()):
            print(f"  {partido}: {gl}-{gv}")
    
    # Agregar columna de resultado
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
    
    df['Resultado'] = df.apply(obtener_resultado_str, axis=1)
    
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
