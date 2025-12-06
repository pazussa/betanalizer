#!/usr/bin/env python3
"""
Script para actualizar el dataset analisis_mercados_20251125_065555.csv
con los resultados de los partidos que ya jugaron.

Fecha actual: 26 de noviembre de 2025
"""

import pandas as pd
import asyncio
import os
import sys
from datetime import datetime
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
    "Super League": "soccer_turkey_super_league",
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
    "Primera División": "soccer_argentina_primera_division",
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
                        logger.debug(f"Resultado: {partido_nombre} = {goles_local}-{goles_visitante}")
            
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
    """
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
            parts = mercado.split()
            if len(parts) >= 2:
                tipo = parts[0]
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
    """Normaliza el nombre del partido para comparación"""
    return " ".join(partido.lower().split())


def buscar_resultado(partido: str, resultados: dict) -> tuple:
    """
    Busca el resultado de un partido en el diccionario de resultados.
    """
    if partido in resultados:
        return resultados[partido]
    
    partido_norm = normalizar_nombre_partido(partido)
    
    for nombre, scores in resultados.items():
        if normalizar_nombre_partido(nombre) == partido_norm:
            return scores
        
        nombre_norm = normalizar_nombre_partido(nombre)
        partido_parts = partido_norm.split(" vs ")
        nombre_parts = nombre_norm.split(" vs ")
        
        if len(partido_parts) == 2 and len(nombre_parts) == 2:
            if (partido_parts[0] in nombre_norm and partido_parts[1] in nombre_norm):
                return scores
    
    return None


async def main():
    """Función principal"""
    # Archivos
    input_file = "analisis_mercados_20251125_065555.csv"
    output_file = "analisis_mercados_20251125_065555.csv"  # Sobreescribimos
    
    if not os.path.exists(input_file):
        logger.error(f"No se encontró el archivo {input_file}")
        sys.exit(1)
    
    # Leer el CSV
    df = pd.read_csv(input_file)
    logger.info(f"Leídas {len(df)} filas del archivo {input_file}")
    
    # Fecha actual: 26 de noviembre de 2025
    ahora = datetime(2025, 11, 26, 23, 59, 59)
    
    # Convertir fecha a datetime
    df['Fecha_Hora_DT'] = pd.to_datetime(df['Fecha_Hora_Colombia'])
    
    # Identificar partidos ya jugados
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
            await asyncio.sleep(0.3)
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
    
    # Eliminar columnas temporales
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
    
    partidos_verificados = len(acertados) + len(fallidos)
    
    if partidos_verificados > 0:
        suma_cuotas_acertados = acertados['Mejor_Cuota'].sum()
        rendimiento = suma_cuotas_acertados - partidos_verificados
        porcentaje_acierto = (len(acertados) / partidos_verificados) * 100
        roi = (rendimiento / partidos_verificados) * 100
        
        print("\n" + "-"*60)
        print("RENDIMIENTO (partidos ya jugados con resultado)")
        print("-"*60)
        print(f"  Partidos verificados: {partidos_verificados}")
        print(f"  Pronósticos acertados: {len(acertados)}")
        print(f"  Porcentaje de acierto: {porcentaje_acierto:.2f}%")
        print(f"\n  Suma de cuotas de acertados: {suma_cuotas_acertados:.2f}")
        print(f"  Inversión (1 unidad por apuesta): {partidos_verificados}")
        print(f"\n  📊 RENDIMIENTO NETO: {rendimiento:+.2f} unidades")
        print(f"  📈 ROI: {roi:+.2f}%")
        
        if rendimiento > 0:
            print(f"\n  💰 ¡GANANCIA! Si apostaste 1€ por apuesta, ganaste {rendimiento:.2f}€")
        elif rendimiento < 0:
            print(f"\n  💸 PÉRDIDA: Si apostaste 1€ por apuesta, perdiste {abs(rendimiento):.2f}€")
        else:
            print(f"\n  🔄 EMPATE: No hubo ganancia ni pérdida")
    else:
        print("\n⚠️  No hay partidos con resultado verificado")
    
    # Detalle por tipo de mercado
    if partidos_verificados > 0:
        print("\n" + "-"*60)
        print("RENDIMIENTO POR TIPO DE MERCADO")
        print("-"*60)
        
        for tipo in df['Tipo_Mercado'].unique():
            df_tipo = df[df['Tipo_Mercado'] == tipo]
            acertados_tipo = df_tipo[df_tipo['Resultado'] == 'Acertado']
            fallidos_tipo = df_tipo[df_tipo['Resultado'] == 'Fallido']
            verificados_tipo = len(acertados_tipo) + len(fallidos_tipo)
            
            if verificados_tipo > 0:
                suma_cuotas = acertados_tipo['Mejor_Cuota'].sum()
                rendimiento_tipo = suma_cuotas - verificados_tipo
                pct_acierto = (len(acertados_tipo) / verificados_tipo) * 100
                roi_tipo = (rendimiento_tipo / verificados_tipo) * 100
                
                emoji = "✅" if rendimiento_tipo > 0 else ("❌" if rendimiento_tipo < 0 else "🔄")
                print(f"\n  {tipo}:")
                print(f"    Verificados: {verificados_tipo} | Aciertos: {len(acertados_tipo)} ({pct_acierto:.1f}%)")
                print(f"    {emoji} Rendimiento: {rendimiento_tipo:+.2f} | ROI: {roi_tipo:+.1f}%")
    
    # Detalle de partidos
    print("\n" + "-"*60)
    print("DETALLE DE PRONÓSTICOS VERIFICADOS")
    print("-"*60)
    
    verificados_df = df[df['Resultado'].isin(['Acertado', 'Fallido'])]
    for _, row in verificados_df.iterrows():
        emoji = "✅" if row['Resultado'] == 'Acertado' else "❌"
        print(f"  {emoji} {row['Partido'][:40]:40s} | {row['Mercado']:12s} | Cuota: {row['Mejor_Cuota']:.2f}")
    
    print("\n" + "="*60)
    print(f"💾 Archivo actualizado: {output_file}")
    print("="*60)
    
    return output_file


if __name__ == "__main__":
    asyncio.run(main())
