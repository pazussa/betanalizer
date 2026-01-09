#!/usr/bin/env python3
"""
completar_domingos.py - Completa datos de cuotas del domingo tarde (09:00-21:00 UTC)

Los datasets actuales solo tienen datos hasta las 09:00 del domingo.
Este script consulta la API histórica para obtener los partidos del domingo tarde.

IMPORTANTE: Requiere API key con acceso a historical odds (plan de pago).
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
import httpx

# Configuración
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('completar_domingos.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Key con acceso a historical (verificada)
API_KEY = "379007b4a3bbcda5cf2216a4258b118d"

# Ligas de fútbol a consultar
SOCCER_LEAGUES = [
    ("soccer_epl", "Premier League"),
    ("soccer_spain_la_liga", "La Liga"),
    ("soccer_germany_bundesliga", "Bundesliga"),
    ("soccer_italy_serie_a", "Serie A"),
    ("soccer_france_ligue_one", "Ligue 1"),
    ("soccer_efl_champ", "Championship"),
    ("soccer_spain_segunda_division", "La Liga 2"),
    ("soccer_germany_bundesliga2", "Bundesliga 2"),
    ("soccer_italy_serie_b", "Serie B"),
    ("soccer_france_ligue_two", "Ligue 2"),
    ("soccer_netherlands_eredivisie", "Eredivisie"),
    ("soccer_portugal_primeira_liga", "Liga Portugal"),
    ("soccer_belgium_first_div", "Pro League"),
    ("soccer_turkey_super_league", "Süper Lig"),
    ("soccer_greece_super_league", "Super League Greece"),
    ("soccer_switzerland_superleague", "Super League Switzerland"),
    ("soccer_poland_ekstraklasa", "Ekstraklasa"),
    ("soccer_spl", "Scottish Premiership"),
    ("soccer_england_league1", "League One"),
    ("soccer_england_league2", "League Two"),
    ("soccer_mexico_ligamx", "Liga MX"),
    ("soccer_argentina_primera_division", "Liga Profesional"),
    ("soccer_australia_aleague", "A-League"),
]

# Bookmakers permitidos
ALLOWED_BOOKMAKERS = {
    'pinnacle', 'betfair', 'betfair_ex_eu', 'matchbook', 'betsson', 'nordicbet',
    'unibet', 'unibet_eu', 'betrivers', 'williamhill', 'coolbet', 'onexbet',
    'marathonbet', 'tipico_de', 'betway', 'betus', 'betonlineag', 'bovada',
    'draftkings', 'fanduel', 'caesars', 'pointsbetus', 'superbook', 'playup'
}


class HistoricalOddsClient:
    """Cliente para THE_ODDS_API Historical Odds"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self.requests_remaining = "?"
    
    async def close(self):
        await self.client.aclose()
    
    async def get_historical_odds(
        self,
        sport_key: str,
        snapshot_date: datetime,
        commence_time_from: datetime = None,
        commence_time_to: datetime = None,
    ) -> Tuple[Optional[List], str]:
        """Obtiene odds históricos para un deporte."""
        url = f"{self.BASE_URL}/historical/sports/{sport_key}/odds"
        
        params = {
            "apiKey": self.api_key,
            "date": snapshot_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "regions": "eu,us,uk,au",
            "markets": "totals",
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }
        
        if commence_time_from:
            params["commenceTimeFrom"] = commence_time_from.strftime("%Y-%m-%dT%H:%M:%SZ")
        if commence_time_to:
            params["commenceTimeTo"] = commence_time_to.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        try:
            response = await self.client.get(url, params=params)
            self.requests_remaining = response.headers.get("x-requests-remaining", "?")
            
            if response.status_code == 401:
                logger.error(f"API Key inválida para {sport_key}")
                return None, ""
            
            if response.status_code == 422:
                return None, ""
            
            response.raise_for_status()
            data = response.json()
            
            return data.get("data", []), data.get("timestamp", "")
            
        except Exception as e:
            logger.warning(f"Error obteniendo {sport_key}: {e}")
            return None, ""


def parse_events_to_records(events: List[Dict], liga: str, snapshot_date: str) -> List[Dict]:
    """Convierte eventos de la API a registros del formato CSV."""
    records = []
    
    for event in events:
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")
        commence_time = event.get("commence_time", "")
        
        # Convertir a hora Colombia (UTC-5)
        if commence_time:
            dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
            dt_colombia = dt - timedelta(hours=5)
            fecha_hora_colombia = dt_colombia.strftime("%Y-%m-%d %H:%M:%S")
        else:
            fecha_hora_colombia = ""
        
        partido = f"{home_team} vs {away_team}"
        
        # Procesar cada bookmaker
        for bookmaker in event.get("bookmakers", []):
            bookmaker_key = bookmaker.get("key", "").lower()
            
            if bookmaker_key not in ALLOWED_BOOKMAKERS:
                continue
            
            for market in bookmaker.get("markets", []):
                if market.get("key") != "totals":
                    continue
                
                # Agrupar outcomes por punto (línea)
                lines = {}
                for outcome in market.get("outcomes", []):
                    point = outcome.get("point")
                    name = outcome.get("name")  # Over o Under
                    price = outcome.get("price")
                    
                    if point is not None and name and price:
                        if point not in lines:
                            lines[point] = {}
                        lines[point][name] = price
                
                # Crear registros para cada línea completa
                for point, outcomes in lines.items():
                    if "Over" in outcomes and "Under" in outcomes:
                        # Over
                        records.append({
                            "Partido": partido,
                            "Fecha_Hora_Colombia": fecha_hora_colombia,
                            "Mercado": f"Over {point}",
                            "Mejor_Cuota": outcomes["Over"],
                            "Cuota_Promedio_Mercado": outcomes["Over"],
                            "Liga": liga,
                            "Tipo_Mercado": "Goles (Over/Under)",
                            "Snapshot_Date": snapshot_date,
                            "Bookmaker": bookmaker_key
                        })
                        # Under
                        records.append({
                            "Partido": partido,
                            "Fecha_Hora_Colombia": fecha_hora_colombia,
                            "Mercado": f"Under {point}",
                            "Mejor_Cuota": outcomes["Under"],
                            "Cuota_Promedio_Mercado": outcomes["Under"],
                            "Liga": liga,
                            "Tipo_Mercado": "Goles (Over/Under)",
                            "Snapshot_Date": snapshot_date,
                            "Bookmaker": bookmaker_key
                        })
    
    return records


async def obtener_datos_domingo_tarde(domingo: datetime) -> List[Dict]:
    """
    Obtiene datos de cuotas para partidos del domingo entre 09:00 y 21:00 UTC.
    
    Args:
        domingo: Fecha del domingo (ej: 2025-01-05)
    """
    # Snapshot a las 21:00 UTC del domingo
    snapshot_date = domingo.replace(hour=21, minute=0, second=0, tzinfo=timezone.utc)
    
    # Filtrar partidos que comienzan entre 09:00 y 21:00 UTC
    commence_from = domingo.replace(hour=9, minute=0, second=0, tzinfo=timezone.utc)
    commence_to = domingo.replace(hour=21, minute=0, second=0, tzinfo=timezone.utc)
    
    logger.info(f"Consultando snapshot: {snapshot_date}")
    logger.info(f"Filtrando partidos: {commence_from} a {commence_to}")
    
    client = HistoricalOddsClient(API_KEY)
    all_records = []
    
    try:
        for sport_key, liga_name in SOCCER_LEAGUES:
            logger.info(f"  Obteniendo {liga_name}...")
            
            events, timestamp = await client.get_historical_odds(
                sport_key=sport_key,
                snapshot_date=snapshot_date,
                commence_time_from=commence_from,
                commence_time_to=commence_to
            )
            
            if events:
                records = parse_events_to_records(events, liga_name, domingo.strftime("%Y-%m-%d"))
                all_records.extend(records)
                logger.info(f"    → {len(events)} eventos, {len(records)} registros")
            
            # Pausa para evitar rate limiting
            await asyncio.sleep(0.3)
        
        logger.info(f"Requests restantes: {client.requests_remaining}")
        
    finally:
        await client.close()
    
    return all_records


def agregar_a_dataset(filepath: str, nuevos_records: List[Dict]) -> int:
    """
    Agrega nuevos registros a un dataset existente.
    
    Returns:
        Número de registros nuevos agregados
    """
    if not nuevos_records:
        return 0
    
    df_existente = pd.read_csv(filepath)
    df_nuevos = pd.DataFrame(nuevos_records)
    
    # Identificar registros únicos (por Partido + Mercado + Bookmaker)
    if 'Bookmaker' not in df_existente.columns:
        # El formato actual puede no tener Bookmaker individual
        # En ese caso, agregar por Partido + Mercado + Fecha
        existentes = set(zip(df_existente['Partido'], df_existente['Mercado'], df_existente['Fecha_Hora_Colombia']))
        
        nuevos_unicos = df_nuevos[
            ~df_nuevos.apply(lambda x: (x['Partido'], x['Mercado'], x['Fecha_Hora_Colombia']) in existentes, axis=1)
        ]
    else:
        existentes = set(zip(df_existente['Partido'], df_existente['Mercado'], df_existente['Bookmaker']))
        nuevos_unicos = df_nuevos[
            ~df_nuevos.apply(lambda x: (x['Partido'], x['Mercado'], x['Bookmaker']) in existentes, axis=1)
        ]
    
    if len(nuevos_unicos) == 0:
        return 0
    
    # Concatenar
    df_final = pd.concat([df_existente, nuevos_unicos], ignore_index=True)
    df_final.to_csv(filepath, index=False)
    
    return len(nuevos_unicos)


# Configuración de actualizaciones por archivo
ACTUALIZACIONES = [
    # Enero 2025
    ("historical_analysis/2025/enero/historical_20250103.csv", "2025-01-05"),  # Domingo 5 enero
    ("historical_analysis/2025/enero/historical_20250110.csv", "2025-01-12"),  # Domingo 12 enero
    ("historical_analysis/2025/enero/historical_20250117.csv", "2025-01-19"),  # Domingo 19 enero
    ("historical_analysis/2025/enero/historical_20250124.csv", "2025-01-26"),  # Domingo 26 enero
    ("historical_analysis/2025/enero/historical_20250131.csv", "2025-02-02"),  # Domingo 2 febrero
    
    # Febrero 2025
    ("historical_analysis/2025/febrero/historical_20250207.csv", "2025-02-09"),  # Domingo 9 febrero
    ("historical_analysis/2025/febrero/historical_20250214.csv", "2025-02-16"),  # Domingo 16 febrero
    ("historical_analysis/2025/febrero/historical_20250221.csv", "2025-02-23"),  # Domingo 23 febrero
    ("historical_analysis/2025/febrero/historical_20250228.csv", "2025-03-02"),  # Domingo 2 marzo
    
    # Marzo 2025
    ("historical_analysis/2025/marzo/historical_20250307.csv", "2025-03-09"),  # Domingo 9 marzo
    ("historical_analysis/2025/marzo/historical_20250314.csv", "2025-03-16"),  # Domingo 16 marzo
    ("historical_analysis/2025/marzo/historical_20250321.csv", "2025-03-23"),  # Domingo 23 marzo
    ("historical_analysis/2025/marzo/historical_20250328.csv", "2025-03-30"),  # Domingo 30 marzo
]


async def main():
    """Ejecuta la actualización de todos los datasets."""
    print("=" * 60)
    print("COMPLETAR DATOS DEL DOMINGO TARDE (09:00-21:00 UTC)")
    print("=" * 60)
    print(f"API Key: {API_KEY[:10]}...")
    print(f"Datasets a actualizar: {len(ACTUALIZACIONES)}")
    print()
    
    total_agregados = 0
    
    for filepath, domingo_str in ACTUALIZACIONES:
        print(f"\n{'='*60}")
        print(f"📁 {filepath}")
        print(f"📅 Domingo: {domingo_str}")
        print("=" * 60)
        
        if not os.path.exists(filepath):
            print(f"  ⚠️  Archivo no existe, saltando...")
            continue
        
        # Verificar rango actual
        df = pd.read_csv(filepath)
        df['Fecha_Hora_Colombia'] = pd.to_datetime(df['Fecha_Hora_Colombia'])
        hora_max = df['Fecha_Hora_Colombia'].max()
        print(f"  Hora máxima actual: {hora_max}")
        
        # Obtener datos del domingo tarde
        domingo = datetime.strptime(domingo_str, "%Y-%m-%d")
        records = await obtener_datos_domingo_tarde(domingo)
        
        if records:
            agregados = agregar_a_dataset(filepath, records)
            total_agregados += agregados
            print(f"  ✅ Agregados: {agregados} registros nuevos")
        else:
            print(f"  ⚠️  No se encontraron datos")
        
        # Pausa entre archivos
        await asyncio.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"COMPLETADO: {total_agregados} registros agregados en total")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
