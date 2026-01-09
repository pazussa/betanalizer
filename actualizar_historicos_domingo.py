#!/usr/bin/env python3
"""
Script para actualizar datos históricos con partidos del domingo tarde (9 AM - 9 PM)

Los snapshots originales fueron tomados hasta las 9 AM del domingo.
Este script agrega los partidos que se jugaron entre 9 AM y 9 PM del domingo.
"""

import asyncio
import httpx
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional
import logging
import os
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Keys
THE_ODDS_API_KEYS = [
    "71bf811f7d188e95e23785f793b94185",
    "2172cf43249121d14f0f851c037d6ad6",
    "a4f8886d0f51a44abf623af42327f6da",
    "4a717f7542e3c4362ddf8f8b59c03754",
    "2c141cbd97634510a0edb715acb37e4c",
    "2b9a248f5870d1f1e19b85bae7c6b313",
    "30e5f3c7f8d38475175d6b3e920ebb6c",
    "1375f6f4aef4a8a0994207f08d2a7490",
    "2855ea30b14dd550f95fab246178baec",
    "ae6dc3a151fae15a337fc4d363d726fd",
]

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
    ("soccer_germany_bundesliga3", "3. Liga"),
]

ALLOWED_BOOKMAKERS = {
    'betway', 'pinnacle', 'unibet', 'betfair', 'williamhill',
    'betvictor', 'marathonbet', 'betfred', 'bwin', '1xbet',
    'bet365', 'ladbrokes', 'paddypower', 'skybet', 'coral',
    'betclic', 'sportingbet', 'interwetten', 'tipico', 'betsson',
    'boylesports', 'leovegas', 'matchbook', 'coolbet', 'nordicbet'
}


class HistoricalOddsClient:
    """Cliente para THE_ODDS_API Historical Odds endpoint"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.client = httpx.AsyncClient(timeout=30.0)
        self.requests_remaining = {}
    
    async def close(self):
        await self.client.aclose()
    
    def get_current_key(self) -> str:
        return self.api_keys[self.current_key_index]
    
    def rotate_key(self):
        """Rota a la siguiente API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"Rotando a API key {self.current_key_index + 1}/{len(self.api_keys)}")
    
    async def get_historical_odds(
        self,
        sport_key: str,
        snapshot_date: datetime,
        commence_time_from: Optional[datetime] = None,
        commence_time_to: Optional[datetime] = None,
    ) -> Tuple[Optional[List], str]:
        """Obtiene odds históricos para un deporte en una fecha específica."""
        url = f"{self.BASE_URL}/historical/sports/{sport_key}/odds"
        
        params = {
            "apiKey": self.get_current_key(),
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
            
            remaining = response.headers.get("x-requests-remaining", "?")
            self.requests_remaining[self.get_current_key()] = remaining
            
            if response.status_code == 401:
                logger.error("API Key inválida")
                self.rotate_key()
                return None, ""
            
            if response.status_code == 422:
                return None, ""
            
            if response.status_code == 429:  # Rate limit
                logger.warning("Rate limit alcanzado, rotando key...")
                self.rotate_key()
                await asyncio.sleep(1)
                return await self.get_historical_odds(sport_key, snapshot_date, commence_time_from, commence_time_to)
            
            response.raise_for_status()
            data = response.json()
            
            timestamp = data.get("timestamp", "")
            events = data.get("data", [])
            
            return events, timestamp
            
        except Exception as e:
            logger.warning(f"Error obteniendo historical odds para {sport_key}: {e}")
            return None, ""


def calcular_bdi(cuotas: List[float]) -> Dict:
    """Calcula métricas BDI (Bookmaker Disagreement Index)"""
    if len(cuotas) < 2:
        return {
            'jsd': None, 'n_bookmakers': len(cuotas),
            'std_p': None, 'mad_p': None
        }
    
    # Convertir cuotas a probabilidades implícitas
    probs = [1/c for c in cuotas]
    prob_mean = np.mean(probs)
    
    return {
        'jsd': np.std(probs),  # Aproximación simple
        'n_bookmakers': len(cuotas),
        'std_p': np.std(probs),
        'mad_p': np.median(np.abs(probs - prob_mean))
    }


def parse_events_to_records(events: List[Dict], league_name: str, snapshot_date: str) -> List[Dict]:
    """Convierte eventos a registros para el DataFrame"""
    records = []
    
    for event in events:
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")
        commence_time = event.get("commence_time", "")
        
        # Convertir a hora Colombia (UTC-5)
        try:
            dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
            dt_colombia = dt - timedelta(hours=5)
            fecha_hora_colombia = dt_colombia.strftime("%Y-%m-%d %H:%M:%S")
        except:
            fecha_hora_colombia = commence_time
        
        partido = f"{home_team} vs {away_team}"
        
        # Recopilar todas las cuotas por línea
        lines_over = {}  # {2.5: [cuotas]}
        lines_under = {}
        bookmakers_over = {}  # {2.5: [bookmakers]}
        bookmakers_under = {}
        
        for bookmaker in event.get("bookmakers", []):
            bookmaker_key = bookmaker.get("key", "").lower()
            
            if bookmaker_key not in ALLOWED_BOOKMAKERS:
                continue
            
            for market in bookmaker.get("markets", []):
                if market.get("key") != "totals":
                    continue
                
                for outcome in market.get("outcomes", []):
                    name = outcome.get("name", "").lower()
                    point = outcome.get("point")
                    price = outcome.get("price")
                    
                    if point is None or price is None:
                        continue
                    
                    if "over" in name:
                        if point not in lines_over:
                            lines_over[point] = []
                            bookmakers_over[point] = []
                        lines_over[point].append(price)
                        bookmakers_over[point].append(bookmaker_key)
                    elif "under" in name:
                        if point not in lines_under:
                            lines_under[point] = []
                            bookmakers_under[point] = []
                        lines_under[point].append(price)
                        bookmakers_under[point].append(bookmaker_key)
        
        # Crear registros para Over
        for line, cuotas in lines_over.items():
            if not cuotas:
                continue
            
            mejor_cuota = max(cuotas)
            idx_mejor = cuotas.index(mejor_cuota)
            mejor_casa = bookmakers_over[line][idx_mejor]
            
            bdi = calcular_bdi(cuotas)
            cuota_promedio = np.mean(cuotas)
            
            record = {
                'Partido': partido,
                'Fecha_Hora_Colombia': fecha_hora_colombia,
                'Mercado': f"Over {line}",
                'Mejor_Cuota': mejor_cuota,
                'Cuota_Promedio_Mercado': cuota_promedio,
                'BDI_jsd_fair': bdi['jsd'],
                'BDI_n_bookmakers_fair': bdi['n_bookmakers'],
                'BDI_std_p_fair': bdi['std_p'],
                'BDI_mad_p_fair': bdi['mad_p'],
                'BDI_jsd': bdi['jsd'],
                'BDI_n_bookmakers': bdi['n_bookmakers'],
                'BDI_std_p': bdi['std_p'],
                'BDI_mad_p': bdi['mad_p'],
                'Mejor_Casa': mejor_casa,
                'Num_Casas': len(cuotas),
                'Diferencia_Cuota_Promedio': mejor_cuota - cuota_promedio,
                'Volatilidad_Pct': 100 * np.std(cuotas) / cuota_promedio if cuota_promedio > 0 else 0,
                'Margen_Casa_Pct': 0,  # Simplificado
                'Liga': league_name,
                'Tipo_Mercado': 'totals',
                'Snapshot_Date': snapshot_date,
                'Todas_Las_Cuotas': json.dumps({b: c for b, c in zip(bookmakers_over[line], cuotas)})
            }
            records.append(record)
        
        # Crear registros para Under
        for line, cuotas in lines_under.items():
            if not cuotas:
                continue
            
            mejor_cuota = max(cuotas)
            idx_mejor = cuotas.index(mejor_cuota)
            mejor_casa = bookmakers_under[line][idx_mejor]
            
            bdi = calcular_bdi(cuotas)
            cuota_promedio = np.mean(cuotas)
            
            record = {
                'Partido': partido,
                'Fecha_Hora_Colombia': fecha_hora_colombia,
                'Mercado': f"Under {line}",
                'Mejor_Cuota': mejor_cuota,
                'Cuota_Promedio_Mercado': cuota_promedio,
                'BDI_jsd_fair': bdi['jsd'],
                'BDI_n_bookmakers_fair': bdi['n_bookmakers'],
                'BDI_std_p_fair': bdi['std_p'],
                'BDI_mad_p_fair': bdi['mad_p'],
                'BDI_jsd': bdi['jsd'],
                'BDI_n_bookmakers': bdi['n_bookmakers'],
                'BDI_std_p': bdi['std_p'],
                'BDI_mad_p': bdi['mad_p'],
                'Mejor_Casa': mejor_casa,
                'Num_Casas': len(cuotas),
                'Diferencia_Cuota_Promedio': mejor_cuota - cuota_promedio,
                'Volatilidad_Pct': 100 * np.std(cuotas) / cuota_promedio if cuota_promedio > 0 else 0,
                'Margen_Casa_Pct': 0,
                'Liga': league_name,
                'Tipo_Mercado': 'totals',
                'Snapshot_Date': snapshot_date,
                'Todas_Las_Cuotas': json.dumps({b: c for b, c in zip(bookmakers_under[line], cuotas)})
            }
            records.append(record)
    
    return records


async def obtener_datos_domingo(
    client: HistoricalOddsClient,
    snapshot_date: str,  # YYYY-MM-DD del viernes
    domingo_date: str,   # YYYY-MM-DD del domingo
) -> pd.DataFrame:
    """
    Obtiene datos del domingo entre 9 AM y 9 PM UTC (14:00 - 02:00 UTC del lunes = domingo tarde Colombia)
    """
    # El snapshot del domingo a las 9 PM UTC
    snapshot_dt = datetime.strptime(f"{domingo_date}T21:00:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    
    # Filtrar partidos que comienzan después de las 9 AM UTC del domingo
    commence_from = datetime.strptime(f"{domingo_date}T09:00:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    # Hasta las 9 PM UTC del domingo
    commence_to = datetime.strptime(f"{domingo_date}T21:00:00Z", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    
    all_records = []
    
    for sport_key, league_name in SOCCER_LEAGUES:
        logger.info(f"Obteniendo {league_name} ({sport_key}) para {domingo_date}...")
        
        events, timestamp = await client.get_historical_odds(
            sport_key=sport_key,
            snapshot_date=snapshot_dt,
            commence_time_from=commence_from,
            commence_time_to=commence_to
        )
        
        if events:
            records = parse_events_to_records(events, league_name, snapshot_date)
            all_records.extend(records)
            logger.info(f"  -> {len(records)} registros de {league_name}")
        
        await asyncio.sleep(0.2)  # Rate limiting
    
    if all_records:
        return pd.DataFrame(all_records)
    return pd.DataFrame()


async def actualizar_archivo_historico(
    client: HistoricalOddsClient,
    archivo_original: str,
    domingo_date: str
):
    """Actualiza un archivo histórico agregando datos del domingo tarde"""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Actualizando: {archivo_original}")
    logger.info(f"Agregando datos del domingo: {domingo_date}")
    logger.info(f"{'='*60}")
    
    # Cargar archivo original
    df_original = pd.read_csv(archivo_original)
    snapshot_date = df_original['Snapshot_Date'].iloc[0]
    
    # Obtener partidos existentes para evitar duplicados
    partidos_existentes = set(df_original['Partido'].unique())
    logger.info(f"Partidos existentes: {len(partidos_existentes)}")
    
    # Obtener nuevos datos
    df_nuevos = await obtener_datos_domingo(client, snapshot_date, domingo_date)
    
    if df_nuevos.empty:
        logger.warning("No se encontraron datos nuevos")
        return 0
    
    # Filtrar duplicados
    df_nuevos = df_nuevos[~df_nuevos['Partido'].isin(partidos_existentes)]
    
    if df_nuevos.empty:
        logger.info("Todos los partidos ya estaban en el archivo")
        return 0
    
    logger.info(f"Nuevos registros a agregar: {len(df_nuevos)}")
    
    # Combinar
    df_combinado = pd.concat([df_original, df_nuevos], ignore_index=True)
    
    # Guardar
    df_combinado.to_csv(archivo_original, index=False)
    logger.info(f"Archivo actualizado: {len(df_original)} -> {len(df_combinado)} registros")
    
    return len(df_nuevos)


async def main():
    """Actualiza todos los archivos históricos"""
    
    # Definir actualizaciones
    actualizaciones = [
        # Enero
        ('historical_analysis/2025/enero/historical_20250103.csv', '2025-01-05'),
        ('historical_analysis/2025/enero/historical_20250110.csv', '2025-01-12'),
        ('historical_analysis/2025/enero/historical_20250117.csv', '2025-01-19'),
        ('historical_analysis/2025/enero/historical_20250124.csv', '2025-01-26'),
        ('historical_analysis/2025/enero/historical_20250131.csv', '2025-02-02'),
        # Febrero
        ('historical_analysis/2025/febrero/historical_20250207.csv', '2025-02-09'),
        ('historical_analysis/2025/febrero/historical_20250214.csv', '2025-02-16'),
        ('historical_analysis/2025/febrero/historical_20250221.csv', '2025-02-23'),
        ('historical_analysis/2025/febrero/historical_20250228.csv', '2025-03-02'),
        # Marzo
        ('historical_analysis/2025/marzo/historical_20250307.csv', '2025-03-09'),
        ('historical_analysis/2025/marzo/historical_20250314.csv', '2025-03-16'),
        ('historical_analysis/2025/marzo/historical_20250321.csv', '2025-03-23'),
        ('historical_analysis/2025/marzo/historical_20250328.csv', '2025-03-30'),
    ]
    
    client = HistoricalOddsClient(THE_ODDS_API_KEYS)
    
    try:
        total_nuevos = 0
        
        for archivo, domingo in actualizaciones:
            if not os.path.exists(archivo):
                logger.warning(f"Archivo no encontrado: {archivo}")
                continue
            
            nuevos = await actualizar_archivo_historico(client, archivo, domingo)
            total_nuevos += nuevos
            
            # Mostrar requests restantes
            logger.info(f"Requests restantes: {client.requests_remaining}")
            
            await asyncio.sleep(0.5)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"COMPLETADO: {total_nuevos} registros nuevos agregados en total")
        logger.info(f"{'='*60}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
