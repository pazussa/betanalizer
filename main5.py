#!/usr/bin/env python3
"""
main5.py - Análisis con TRIPLE API de Odds (basado en main3.py)

Combina:
- THE_ODDS_API: ~58 bookmakers (Pinnacle, Betfair, DraftKings, etc.)
- API-FOOTBALL: ~11 bookmakers (Bet365, SBO, 1xBet, Pinnacle, etc.)
- SPORTS_GAME_ODDS: ~4+ bookmakers US (Bovada, BetMGM, BetRivers, etc.)

IMPORTANTE sobre BDI:
- BDI_jsd: Calculado con cuotas crudas de UN solo lado (Over o Under)
- BDI_jsd_fair: Calculado usando AMBOS lados (Over Y Under) por bookmaker,
  eliminando el vig primero. Requiere que el bookmaker tenga cuotas para
  ambos lados del mercado.

Run: `python main5.py analyze` para análisis completo
"""

import asyncio
import logging
import os
import sys
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

import click
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import httpx

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.models import ValidationError, BookmakerType, MarketType
from src.apis.the_odds_api import TheOddsAPIClient
from src.apis.api_football import APIFootballClient, BOOKMAKER_ID_MAP, LEAGUE_IDS
from src.disagreement import remove_vig, jensen_shannon, bookmaker_disagreement


# ========== CONFIGURACIÓN ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('triple_api_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv(override=True)

# API Keys
THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY", "")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
SPORTS_GAME_ODDS_KEY = os.getenv("SPORTS_GAME_ODDS_KEY", "")


# ========== FILTROS DE BOOKMAKERS POR API ==========
# THE_ODDS_API: Bookmakers principales (los del enum BookmakerType)
THE_ODDS_API_BOOKMAKERS = {
    # Principales europeas
    "pinnacle", "bet365", "betfair", "betfair_ex_eu", "betfair_ex_uk", "betfair_ex_au",
    "unibet", "unibet_uk", "unibet_nl", "unibet_se",
    "williamhill", "betsson", "marathonbet", "bwin",
    "ladbrokes", "ladbrokes_uk", "coral", "betclic_fr",
    "betvictor", "betway", "casumo", "coolbet", "grosvenor",
    "leovegas", "leovegas_se", "nordicbet", "paddypower",
    "skybet", "smarkets", "sport888", "tipico_de", "virginbet",
    "winamax_fr", "winamax_de", "codere_it",
    # Americanas
    "betmgm", "bovada", "draftkings", "fanduel", "mybookieag",
    # Australianas
    "tab", "tabtouch", "pointsbetau",
    # Extras comunes en THE_ODDS_API
    "betonlineag", "betus", "lowvig", "gtbets", "betrivers", "superbook",
    "twinspires", "foxbet", "barstool", "sisportsbook", "circasports",
    "wynnbet", "betparx", "espnbet", "fliff", "hardrockbet",
}

# API-FOOTBALL: Solo estos 3 bookmakers principales
API_FOOTBALL_BOOKMAKERS = {"Bet365", "Bwin", "SBO"}

# SportsGameOdds: Bookmakers exclusivos (diferentes a THE_ODDS_API y API-FOOTBALL)
# Se filtrarán dinámicamente para excluir los anteriores
SPORTSGAMEODDS_EXCLUDED = {
    # Excluir los de THE_ODDS_API (en minúsculas)
    "pinnacle", "bet365", "betfair", "unibet", "williamhill", "betsson",
    "marathonbet", "bwin", "ladbrokes", "betvictor", "betway",
    "draftkings", "fanduel", "betmgm", "bovada", "pointsbet",
    "betonlineag", "betus", "betrivers", "superbook", "foxbet",
    # Excluir los de API-FOOTBALL
    "sbo", "sbobet",
}


# ========== NORMALIZACIÓN DE NOMBRES ==========
TEAM_NAME_MAPPING = {
    # Nombres cortos a nombres completos
    'man utd': 'manchester united',
    'man united': 'manchester united',
    'manchester utd': 'manchester united',
    'man city': 'manchester city',
    'manchester c': 'manchester city',
    'newcastle': 'newcastle united',
    'newcastle utd': 'newcastle united',
    'tottenham': 'tottenham hotspur',
    'spurs': 'tottenham hotspur',
    'wolves': 'wolverhampton wanderers',
    'wolverhampton': 'wolverhampton wanderers',
    'nottingham': 'nottingham forest',
    "nott'm forest": 'nottingham forest',
    'west ham': 'west ham united',
    'leicester': 'leicester city',
    'brighton': 'brighton and hove albion',
    'brighton hove': 'brighton and hove albion',
    # Serie A
    'inter': 'inter milan',
    'internazionale': 'inter milan',
    'inter milano': 'inter milan',
    'ac milan': 'milan',
    'roma': 'as roma',
    'napoli': 'ssc napoli',
    'lazio': 'ss lazio',
    'juventus': 'juventus fc',
    'juve': 'juventus fc',
    'atalanta': 'atalanta bc',
    'fiorentina': 'acf fiorentina',
    # La Liga
    'atletico madrid': 'atlético madrid',
    'atletico': 'atlético madrid',
    'real sociedad': 'real sociedad san sebastián',
    'athletic bilbao': 'athletic club',
    'athletic': 'athletic club',
    'betis': 'real betis',
    'real betis balompie': 'real betis',
    # Bundesliga
    'bayern': 'bayern munich',
    'bayern münchen': 'bayern munich',
    'fc bayern': 'bayern munich',
    'dortmund': 'borussia dortmund',
    'bvb': 'borussia dortmund',
    'leverkusen': 'bayer leverkusen',
    'bayer 04': 'bayer leverkusen',
    'leipzig': 'rb leipzig',
    'rasenballsport': 'rb leipzig',
    'gladbach': 'borussia mönchengladbach',
    "m'gladbach": 'borussia mönchengladbach',
    'monchengladbach': 'borussia mönchengladbach',
    'frankfurt': 'eintracht frankfurt',
    'wolfsburg': 'vfl wolfsburg',
    # Ligue 1
    'psg': 'paris saint-germain',
    'paris sg': 'paris saint-germain',
    'paris saint germain': 'paris saint-germain',
    'marseille': 'olympique marseille',
    'om': 'olympique marseille',
    'lyon': 'olympique lyonnais',
    'ol': 'olympique lyonnais',
    'monaco': 'as monaco',
    'lille': 'losc lille',
    # Otros
    'benfica': 'sl benfica',
    'porto': 'fc porto',
    'sporting': 'sporting cp',
    'sporting lisbon': 'sporting cp',
    'ajax': 'afc ajax',
    'psv': 'psv eindhoven',
}


def normalize_team_name(name: str) -> str:
    """Normaliza el nombre de un equipo para hacer matching entre APIs"""
    if not name:
        return name
    
    # Convertir a minúsculas y limpiar
    normalized = name.lower().strip()
    
    # Eliminar sufijos comunes
    for suffix in [' fc', ' cf', ' sc', ' ac', ' afc', ' ssc', ' ss']:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    # Buscar en el mapeo
    if normalized in TEAM_NAME_MAPPING:
        return TEAM_NAME_MAPPING[normalized]
    
    return normalized


def normalize_match_name(match: str) -> str:
    """Normaliza el nombre de un partido (Equipo1 vs Equipo2)"""
    if not match:
        return match
    
    # Separar por 'vs' o ' - '
    parts = match.replace(' - ', ' vs ').split(' vs ')
    if len(parts) != 2:
        return match.lower().strip()
    
    home = normalize_team_name(parts[0].strip())
    away = normalize_team_name(parts[1].strip())
    
    return f"{home} vs {away}"


# ========== CLIENTES DE API ==========

class SportsGameOddsClient:
    """
    Cliente para SportsGameOdds API v2
    
    Esta API devuelve eventos con odds embebidas directamente en la respuesta.
    NO necesita llamadas separadas para obtener odds.
    
    Estructura de la API:
    - /events?leagueID=EPL&started=false&oddsAvailable=true
    - Las odds vienen en event['odds'][oddID]['byBookmaker']
    - oddID para Over/Under: "points-all-game-ou-over", "points-all-game-ou-under"
    """
    
    BASE_URL = "https://api.sportsgameodds.com/v2"
    
    # Mapeo de ligas soportadas
    LEAGUE_MAP = {
        "EPL": "EPL",
        "BUNDESLIGA": "BUNDESLIGA",
        "LA_LIGA": "LA_LIGA",
        "IT_SERIE_A": "IT_SERIE_A",
        "FR_LIGUE_1": "FR_LIGUE_1",
        "UEFA_CHAMPIONS_LEAGUE": "UEFA_CHAMPIONS_LEAGUE",
        "UEFA_EUROPA_LEAGUE": "UEFA_EUROPA_LEAGUE",
        "BR_SERIE_A": "BR_SERIE_A",
        "MLS": "MLS",
        "LIGA_MX": "LIGA_MX",
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    def _american_to_decimal(self, american_odds: str) -> float:
        """Convierte odds americanas (+150, -120) a decimales"""
        try:
            odds = int(american_odds.replace('+', ''))
            if odds > 0:
                return round((odds / 100) + 1, 4)
            else:
                return round((100 / abs(odds)) + 1, 4)
        except (ValueError, TypeError):
            return 0.0
    
    async def get_soccer_events(self, leagues: List[str], hours_ahead: int = 168) -> List[Dict]:
        """
        Obtener eventos de fútbol con odds disponibles.
        
        Args:
            leagues: Lista de IDs de ligas (EPL, BUNDESLIGA, etc.)
            hours_ahead: Horas hacia adelante para buscar
            
        Returns:
            Lista de eventos con odds embebidas
        """
        all_events = []
        
        # Construir lista de leagueIDs válidos
        valid_leagues = [self.LEAGUE_MAP.get(l, l) for l in leagues]
        league_str = ','.join(valid_leagues)
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/events",
                params={
                    "sportID": "SOCCER",
                    "leagueID": league_str,
                    "started": "false",
                    "oddsAvailable": "true",
                    "limit": 100
                },
                headers={"x-api-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            all_events = data.get("data", [])
            logger.info(f"SportsGameOdds: {len(all_events)} eventos encontrados para {league_str}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error SportsGameOdds: {e.response.status_code} - {e.response.text[:200]}")
        except Exception as e:
            logger.warning(f"Error SportsGameOdds: {e}")
        
        return all_events
    
    def parse_totals_from_events(self, events: List[Dict]) -> List[Dict]:
        """
        Extrae datos de Over/Under de los eventos.
        
        Los markets de Over/Under están en:
        - event['odds']['points-all-game-ou-over']['byBookmaker']
        - event['odds']['points-all-game-ou-under']['byBookmaker']
        """
        records = []
        
        for event in events:
            try:
                # Info del partido
                teams = event.get('teams', {})
                home_team = teams.get('home', {}).get('names', {}).get('long', '')
                away_team = teams.get('away', {}).get('names', {}).get('long', '')
                league_id = event.get('leagueID', '')
                starts_at = event.get('status', {}).get('startsAt', '')
                
                if not home_team or not away_team:
                    continue
                
                match_name = f"{home_team} vs {away_team}"
                
                # Obtener odds
                odds = event.get('odds', {})
                
                # Over/Under Full Match (points-all-game-ou-over, points-all-game-ou-under)
                # También puede ser points-all-reg-ou-* en algunos casos
                over_key = None
                under_key = None
                
                for key in odds.keys():
                    if 'ou-over' in key and ('game' in key or 'reg' in key) and 'points-all' in key:
                        over_key = key
                    if 'ou-under' in key and ('game' in key or 'reg' in key) and 'points-all' in key:
                        under_key = key
                
                if not over_key or not under_key:
                    continue
                
                over_odds_data = odds.get(over_key, {})
                under_odds_data = odds.get(under_key, {})
                
                # Obtener línea (O/U value)
                line = over_odds_data.get('bookOverUnder', over_odds_data.get('fairOverUnder', '2.5'))
                try:
                    line = float(line)
                except:
                    line = 2.5
                
                # Procesar bookmakers para Over
                over_by_book = over_odds_data.get('byBookmaker', {})
                for bookmaker, book_data in over_by_book.items():
                    if bookmaker == 'unknown':
                        continue
                    
                    # FILTRO: Excluir bookmakers que ya están en THE_ODDS_API o API-FOOTBALL
                    if bookmaker.lower() in SPORTSGAMEODDS_EXCLUDED:
                        continue
                    
                    american_odds = book_data.get('odds', '')
                    if not american_odds:
                        continue
                    
                    decimal_odds = self._american_to_decimal(american_odds)
                    if decimal_odds <= 1.0:
                        continue
                    
                    # También verificar la línea específica del bookmaker
                    book_line = book_data.get('overUnder', line)
                    try:
                        book_line = float(book_line)
                    except:
                        book_line = line
                    
                    records.append({
                        'match': match_name,
                        'match_normalized': normalize_match_name(match_name),
                        'league': league_id,
                        'starts_at': starts_at,
                        'line': book_line,
                        'side': 'over',
                        'bookmaker': f"sgo_{bookmaker}",  # Prefijo para evitar colisiones
                        'odds_decimal': decimal_odds,
                        'source': 'SportsGameOdds'
                    })
                
                # Procesar bookmakers para Under
                # Procesar bookmakers para Under
                under_by_book = under_odds_data.get('byBookmaker', {})
                for bookmaker, book_data in under_by_book.items():
                    if bookmaker == 'unknown':
                        continue
                    
                    # FILTRO: Excluir bookmakers que ya están en THE_ODDS_API o API-FOOTBALL
                    if bookmaker.lower() in SPORTSGAMEODDS_EXCLUDED:
                        continue
                    
                    american_odds = book_data.get('odds', '')
                    if not american_odds:
                        continue
                    
                    decimal_odds = self._american_to_decimal(american_odds)
                    if decimal_odds <= 1.0:
                        continue
                    
                    book_line = book_data.get('overUnder', line)
                    try:
                        book_line = float(book_line)
                    except:
                        book_line = line
                    
                    records.append({
                        'match': match_name,
                        'match_normalized': normalize_match_name(match_name),
                        'league': league_id,
                        'starts_at': starts_at,
                        'line': book_line,
                        'side': 'under',
                        'bookmaker': f"sgo_{bookmaker}",
                        'odds_decimal': decimal_odds,
                        'source': 'SportsGameOdds'
                    })
                
            except Exception as e:
                logger.warning(f"Error parseando evento SportsGameOdds: {e}")
                continue
        
        return records


class TripleAPIAnalyzer:
    """Analizador que combina datos de las 3 APIs"""
    
    def __init__(self):
        # THE_ODDS_API
        self.odds_api_client = None
        if THE_ODDS_API_KEY:
            self.odds_api_client = TheOddsAPIClient()
            logger.info("✅ THE_ODDS_API inicializado")
        
        # API-FOOTBALL
        self.api_football_client = None
        if API_FOOTBALL_KEY:
            self.api_football_client = APIFootballClient(API_FOOTBALL_KEY)
            logger.info("✅ API-FOOTBALL inicializado")
        
        # SPORTS_GAME_ODDS
        self.sgo_client = None
        if SPORTS_GAME_ODDS_KEY:
            self.sgo_client = SportsGameOddsClient(SPORTS_GAME_ODDS_KEY)
            logger.info("✅ SPORTS_GAME_ODDS inicializado")
    
    async def cleanup(self):
        """Cerrar conexiones"""
        if self.odds_api_client:
            await self.odds_api_client.close()
        if self.api_football_client:
            await self.api_football_client.close()
        if self.sgo_client:
            await self.sgo_client.close()
    
    async def get_the_odds_api_totals(self, hours_ahead: int = 168) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Obtener Over/Under de THE_ODDS_API
        
        Returns:
            Tuple[pd.DataFrame, Dict]: DataFrame con datos y diccionario con info de requests
        """
        requests_info = {'remaining': 500, 'used': 0, 'last': 0}
        
        if not self.odds_api_client:
            return pd.DataFrame(), requests_info
        
        all_records = []
        
        # Calcular fecha límite (commenceTimeTo)
        now = datetime.now(timezone.utc)
        max_time = now + timedelta(hours=hours_ahead)
        commence_time_to = max_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Lista completa de ligas (igual que main3.py)
        soccer_leagues = [
            # Top 5 Ligas Europeas
            ("soccer_epl", "Premier League"),
            ("soccer_spain_la_liga", "La Liga"),
            ("soccer_germany_bundesliga", "Bundesliga"),
            ("soccer_italy_serie_a", "Serie A"),
            ("soccer_france_ligue_one", "Ligue 1"),
            
            # Segunda División Europa
            ("soccer_efl_champ", "Championship"),
            ("soccer_spain_segunda_division", "La Liga 2"),
            ("soccer_germany_bundesliga2", "Bundesliga 2"),
            ("soccer_italy_serie_b", "Serie B"),
            ("soccer_france_ligue_two", "Ligue 2"),
            
            # Otras Ligas Europeas
            ("soccer_netherlands_eredivisie", "Eredivisie"),
            ("soccer_portugal_primeira_liga", "Primeira Liga"),
            ("soccer_belgium_first_div", "Belgium First Div"),
            ("soccer_turkey_super_league", "Super League Turkey"),
            ("soccer_greece_super_league", "Super League Greece"),
            ("soccer_austria_bundesliga", "Austrian Bundesliga"),
            ("soccer_switzerland_superleague", "Swiss Superleague"),
            ("soccer_denmark_superliga", "Superliga"),
            ("soccer_sweden_allsvenskan", "Allsvenskan"),
            ("soccer_norway_eliteserien", "Eliteserien"),
            ("soccer_poland_ekstraklasa", "Ekstraklasa"),
            ("soccer_spl", "Scottish Premiership"),
            
            # Ligas Inglesas Inferiores
            ("soccer_england_league1", "League One"),
            ("soccer_england_league2", "League Two"),
            ("soccer_germany_liga3", "3. Liga"),
            
            # Competiciones Europeas
            ("soccer_uefa_champs_league", "Champions League"),
            ("soccer_uefa_europa_league", "Europa League"),
            ("soccer_uefa_europa_conference_league", "Conference League"),
            
            # América
            ("soccer_brazil_campeonato", "Brasileirão"),
            ("soccer_argentina_primera_division", "Primera División Argentina"),
            ("soccer_chile_campeonato", "Primera División Chile"),
            ("soccer_mexico_ligamx", "Liga MX"),
            ("soccer_usa_mls", "MLS"),
            ("soccer_conmebol_copa_libertadores", "Copa Libertadores"),
            
            # Asia y Oceanía
            ("soccer_japan_j_league", "J League"),
            ("soccer_korea_kleague1", "K League 1"),
            ("soccer_australia_aleague", "A-League"),
        ]
        
        for sport_key, league_name in soccer_leagues:
            try:
                # Obtener eventos de la liga
                url = f"{self.odds_api_client.BASE_URL}/sports/{sport_key}/odds"
                params = {
                    "apiKey": self.odds_api_client.api_key,
                    "regions": "eu,us,uk,au",
                    "markets": "totals",
                    "oddsFormat": "decimal",
                    "dateFormat": "iso",
                    "commenceTimeTo": commence_time_to
                }
                
                response = await self.odds_api_client.client.get(url, params=params)
                
                # Capturar headers de requests
                if 'x-requests-remaining' in response.headers:
                    requests_info['remaining'] = int(response.headers.get('x-requests-remaining', 500))
                    requests_info['used'] = int(response.headers.get('x-requests-used', 0))
                    requests_info['last'] = int(response.headers.get('x-requests-last', 0))
                
                if response.status_code == 404:
                    logger.debug(f"THE_ODDS_API: Sin eventos para {sport_key}")
                    continue
                    
                response.raise_for_status()
                events = response.json()
                
                for event in events:
                    home_team = event.get("home_team", "")
                    away_team = event.get("away_team", "")
                    match_name = f"{home_team} vs {away_team}"
                    starts_at = event.get("commence_time", "")
                    
                    # Procesar bookmakers
                    for bookmaker in event.get("bookmakers", []):
                        bookmaker_name = bookmaker.get("key", "")
                        
                        # FILTRO: Solo bookmakers permitidos para THE_ODDS_API
                        if bookmaker_name not in THE_ODDS_API_BOOKMAKERS:
                            continue
                        
                        for market in bookmaker.get("markets", []):
                            if market.get("key") != "totals":
                                continue
                            
                            outcomes = market.get("outcomes", [])
                            
                            # Buscar Over y Under
                            for outcome in outcomes:
                                side = outcome.get("name", "").lower()
                                if side not in ["over", "under"]:
                                    continue
                                
                                odds_decimal = outcome.get("price", 0)
                                point = outcome.get("point", 2.5)
                                
                                if odds_decimal <= 1.0:
                                    continue
                                
                                all_records.append({
                                    'match': match_name,
                                    'match_normalized': normalize_match_name(match_name),
                                    'league': league_name,
                                    'starts_at': starts_at,
                                    'line': point,
                                    'side': side,
                                    'bookmaker': f"toa_{bookmaker_name}",  # Prefijo para identificar
                                    'odds_decimal': odds_decimal,
                                    'source': 'THE_ODDS_API'
                                })
                
                await asyncio.sleep(0.3)
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 404:
                    logger.warning(f"THE_ODDS_API error {sport_key}: {e.response.status_code}")
            except Exception as e:
                logger.warning(f"THE_ODDS_API error {sport_key}: {e}")
        
        if all_records:
            logger.info(f"THE_ODDS_API: {len(all_records)} registros")
        
        return pd.DataFrame(all_records) if all_records else pd.DataFrame(), requests_info
    
    async def get_api_football_totals(self, hours_ahead: int = 168) -> pd.DataFrame:
        """Obtener Over/Under de API-FOOTBALL"""
        if not self.api_football_client:
            return pd.DataFrame()
        
        all_totals = []
        
        # Obtener odds de los próximos días
        for days_offset in range(min(hours_ahead // 24 + 1, 7)):
            date = (datetime.now() + timedelta(days=days_offset)).strftime("%Y-%m-%d")
            try:
                odds_data = await self.api_football_client.get_odds_by_date(date)
                if odds_data:
                    totals = self.api_football_client.parse_totals_odds(odds_data)
                    all_totals.extend(totals)
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.warning(f"Error API-FOOTBALL {date}: {e}")
        
        if not all_totals:
            return pd.DataFrame()
        
        # Convertir a formato estándar
        records = []
        for t in all_totals:
            bookmaker = t.get('bookmaker', '')
            
            # FILTRO: Solo Bet365, Bwin, SBO para API-FOOTBALL
            if bookmaker not in API_FOOTBALL_BOOKMAKERS:
                continue
            
            match_name = f"{t.get('home_team', '')} vs {t.get('away_team', '')}"
            
            # Over
            records.append({
                'match': match_name,
                'match_normalized': normalize_match_name(match_name),
                'league': t.get('league_name', ''),
                'starts_at': t.get('match_date', ''),
                'line': t.get('line', 2.5),
                'side': 'over',
                'bookmaker': bookmaker,
                'odds_decimal': t.get('over_odds', 0),
                'source': 'API-FOOTBALL'
            })
            
            # Under
            records.append({
                'match': match_name,
                'match_normalized': normalize_match_name(match_name),
                'league': t.get('league_name', ''),
                'starts_at': t.get('match_date', ''),
                'line': t.get('line', 2.5),
                'side': 'under',
                'bookmaker': bookmaker,
                'odds_decimal': t.get('under_odds', 0),
                'source': 'API-FOOTBALL'
            })
        
        return pd.DataFrame(records)
    
    async def get_sportsgameodds_totals(self, leagues: List[str], hours_ahead: int = 168) -> pd.DataFrame:
        """Obtener Over/Under de SportsGameOdds"""
        if not self.sgo_client:
            return pd.DataFrame()
        
        try:
            # Obtener todos los eventos con una sola llamada
            events = await self.sgo_client.get_soccer_events(leagues, hours_ahead)
            
            if not events:
                logger.info("SportsGameOdds: No se encontraron eventos")
                return pd.DataFrame()
            
            # Parsear los datos de totales
            records = self.sgo_client.parse_totals_from_events(events)
            
            if not records:
                logger.info("SportsGameOdds: No se encontraron mercados Over/Under")
                return pd.DataFrame()
            
            logger.info(f"SportsGameOdds: {len(records)} registros de {len(events)} eventos")
            return pd.DataFrame(records)
            
        except Exception as e:
            logger.warning(f"Error SportsGameOdds: {e}")
            return pd.DataFrame()


# ========== CÁLCULOS DE BDI ==========

def calculate_bdi_raw(odds_dict: Dict[str, float]) -> Dict:
    """
    Calcula BDI usando cuotas crudas (sin eliminar vig).
    Este es BDI_jsd - calculado solo con un lado del mercado.
    
    Args:
        odds_dict: {bookmaker: odds_decimal}
    
    Returns:
        Dict con jsd_mean, std_p, mad_p, n_bookmakers
    """
    if len(odds_dict) < 2:
        return {'jsd_mean': None, 'std_p': None, 'mad_p': None, 'n_bookmakers': 0}
    
    # Convertir cuotas a probabilidades implícitas
    probs = {}
    for bm, odds in odds_dict.items():
        if odds and odds > 0:
            probs[bm] = 1.0 / odds
    
    if len(probs) < 2:
        return {'jsd_mean': None, 'std_p': None, 'mad_p': None, 'n_bookmakers': 0}
    
    # Calcular probabilidad promedio (consenso)
    prob_list = list(probs.values())
    mean_prob = sum(prob_list) / len(prob_list)
    
    # Calcular JSD de cada bookmaker vs el consenso
    # Para un solo outcome, tratamos como distribución [p, 1-p]
    jsds = []
    for p in prob_list:
        # Distribución del bookmaker
        dist_bm = [p, 1 - p]
        # Distribución consenso
        dist_consensus = [mean_prob, 1 - mean_prob]
        
        jsd = jensen_shannon(dist_bm, dist_consensus, base=2.0)
        jsds.append(jsd)
    
    # Estadísticas de dispersión
    n = len(prob_list)
    var = sum((p - mean_prob) ** 2 for p in prob_list) / n
    std_p = math.sqrt(var)
    mad_p = sum(abs(p - mean_prob) for p in prob_list) / n
    
    return {
        'jsd_mean': sum(jsds) / len(jsds) if jsds else None,
        'std_p': std_p,
        'mad_p': mad_p,
        'n_bookmakers': n
    }


def calculate_bdi_fair(over_odds: Dict[str, float], under_odds: Dict[str, float]) -> Dict:
    """
    Calcula BDI_fair usando AMBOS lados (Over Y Under) por bookmaker.
    Elimina el vig primero para obtener probabilidades justas.
    
    Args:
        over_odds: {bookmaker: over_odds_decimal}
        under_odds: {bookmaker: under_odds_decimal}
    
    Returns:
        Dict con jsd_mean, std_p, mad_p, n_bookmakers
    """
    # Encontrar bookmakers comunes
    common_bookmakers = set(over_odds.keys()) & set(under_odds.keys())
    common_bookmakers = [b for b in common_bookmakers 
                         if over_odds.get(b) and over_odds[b] > 0 
                         and under_odds.get(b) and under_odds[b] > 0]
    
    if len(common_bookmakers) < 2:
        return {'jsd_mean': None, 'std_p': None, 'mad_p': None, 'n_bookmakers': 0}
    
    # Calcular distribuciones justas por bookmaker
    fair_dists = []
    p_over_list = []
    
    for bm in common_bookmakers:
        o_over = over_odds[bm]
        o_under = under_odds[bm]
        
        # Eliminar vig
        fair = remove_vig({'over': o_over, 'under': o_under})
        if not fair or 'over' not in fair:
            continue
        
        p_over = fair['over']
        p_under = fair['under']
        fair_dists.append([p_over, p_under])
        p_over_list.append(p_over)
    
    if len(fair_dists) < 2:
        return {'jsd_mean': None, 'std_p': None, 'mad_p': None, 'n_bookmakers': 0}
    
    # Calcular distribución consenso (promedio)
    n = len(fair_dists)
    mean_dist = [
        sum(d[0] for d in fair_dists) / n,
        sum(d[1] for d in fair_dists) / n
    ]
    
    # Calcular JSD de cada bookmaker vs consenso
    jsds = []
    for dist in fair_dists:
        jsd = jensen_shannon(dist, mean_dist, base=2.0)
        jsds.append(jsd)
    
    # Estadísticas de dispersión de p_over
    mean_p = sum(p_over_list) / n
    var = sum((p - mean_p) ** 2 for p in p_over_list) / n
    std_p = math.sqrt(var)
    mad_p = sum(abs(p - mean_p) for p in p_over_list) / n
    
    return {
        'jsd_mean': sum(jsds) / len(jsds) if jsds else None,
        'std_p': std_p,
        'mad_p': mad_p,
        'n_bookmakers': n
    }


def calculate_fair_odds(odds_list: List[float]) -> float:
    """Calcular cuota justa promedio eliminando margen"""
    if not odds_list:
        return 0.0
    
    probs = [1.0 / o for o in odds_list if o and o > 0]
    if not probs:
        return 0.0
    
    avg_prob = sum(probs) / len(probs)
    return 1.0 / avg_prob if avg_prob > 0 else 0.0


# ========== CLI ==========

@click.group()
@click.version_option(version='5.0.0')
def cli():
    """CLI para análisis TRIPLE-API de cuotas de apuestas"""
    pass


@cli.command()
def status():
    """Verificar estado de las 3 APIs"""
    async def _run():
        click.echo("🔍 Verificando estado de las APIs...\n")
        
        # THE_ODDS_API
        click.echo("📡 THE_ODDS_API:")
        if THE_ODDS_API_KEY:
            try:
                client = TheOddsAPIClient()
                remaining = await client.get_remaining_requests()
                click.echo(f"  ✅ Conexión OK - {remaining} requests restantes")
                await client.close()
            except Exception as e:
                click.echo(f"  ❌ Error: {e}")
        else:
            click.echo("  ⚠️ API key no configurada")
        
        # API-FOOTBALL
        click.echo("\n📡 API-FOOTBALL:")
        if API_FOOTBALL_KEY:
            try:
                client = APIFootballClient(API_FOOTBALL_KEY)
                status = await client.get_status()
                if status:
                    requests = status.get("requests", {})
                    click.echo(f"  ✅ Conexión OK")
                    click.echo(f"  📊 Requests: {requests.get('current', 0)}/{requests.get('limit_day', 100)}")
                await client.close()
            except Exception as e:
                click.echo(f"  ❌ Error: {e}")
        else:
            click.echo("  ⚠️ API key no configurada")
        
        # SPORTS_GAME_ODDS
        click.echo("\n📡 SPORTS_GAME_ODDS:")
        if SPORTS_GAME_ODDS_KEY:
            try:
                client = SportsGameOddsClient(SPORTS_GAME_ODDS_KEY)
                events = await client.get_soccer_events(["EPL", "IT_SERIE_A"], hours_ahead=72)
                if events:
                    click.echo(f"  ✅ Conexión OK - {len(events)} eventos de fútbol")
                    # Mostrar algunas ligas
                    leagues = set(e.get('leagueID', '') for e in events)
                    click.echo(f"  📊 Ligas: {', '.join(sorted(leagues))}")
                else:
                    click.echo("  ⚠️ Sin eventos disponibles actualmente")
                await client.close()
            except Exception as e:
                click.echo(f"  ❌ Error: {e}")
        else:
            click.echo("  ⚠️ API key no configurada")
        
        click.echo("\n✅ Verificación completada")
    
    asyncio.run(_run())


@cli.command()
@click.option('--hours-ahead', '-h', default=168, type=click.IntRange(24, 336), help='Horas hacia adelante')
@click.option('--min-bookmakers', '-m', default=3, type=click.IntRange(2, 20), help='Mínimo de bookmakers')
@click.option('--export-csv/--no-csv', default=True, help='Exportar a CSV')
def analyze(hours_ahead, min_bookmakers, export_csv):
    """
    Análisis completo combinando las 3 APIs.
    
    Genera un CSV con:
    - BDI_jsd: calculado con cuotas crudas (un solo lado)
    - BDI_jsd_fair: calculado con ambos lados (Over Y Under), sin vig
    - APIs_Usadas: qué APIs contribuyeron a cada mercado
    """
    async def _run():
        click.echo("🚀 Iniciando análisis TRIPLE-API...\n")
        
        analyzer = TripleAPIAnalyzer()
        
        all_data = []
        
        # 1. Obtener datos de THE_ODDS_API
        click.echo("📡 THE_ODDS_API...")
        toa_df, requests_info = await analyzer.get_the_odds_api_totals(hours_ahead)
        
        # Mostrar estado de requests
        remaining = requests_info['remaining']
        used = requests_info['used']
        pct_used = (used / 500) * 100 if used > 0 else 0
        pct_remaining = (remaining / 500) * 100
        click.echo(f"   📊 Requests: {remaining}/500 restantes ({pct_remaining:.1f}%) | Usados: {used} ({pct_used:.1f}%)")
        
        if not toa_df.empty:
            click.echo(f"   ✅ {len(toa_df)} registros")
            all_data.append(toa_df)
        else:
            click.echo("   ⚠️ Sin datos")
        
        # 2. Obtener datos de API-FOOTBALL
        click.echo("\n📡 API-FOOTBALL...")
        af_df = await analyzer.get_api_football_totals(hours_ahead)
        if not af_df.empty:
            click.echo(f"   ✅ {len(af_df)} registros")
            all_data.append(af_df)
        else:
            click.echo("   ⚠️ Sin datos")
        
        # 3. Obtener datos de SportsGameOdds
        click.echo("\n📡 SPORTS_GAME_ODDS...")
        sgo_df = await analyzer.get_sportsgameodds_totals(
            leagues=["EPL", "BUNDESLIGA", "LA_LIGA", "IT_SERIE_A", "FR_LIGUE_1"],
            hours_ahead=hours_ahead
        )
        if not sgo_df.empty:
            click.echo(f"   ✅ {len(sgo_df)} registros")
            all_data.append(sgo_df)
        else:
            click.echo("   ⚠️ Sin datos")
        
        if not all_data:
            click.echo("\n❌ No se encontraron datos")
            await analyzer.cleanup()
            return
        
        # 3. Combinar datos
        click.echo("\n⚙️ Combinando y procesando...")
        combined_df = pd.concat(all_data, ignore_index=True)
        click.echo(f"   Total registros: {len(combined_df)}")
        
        # 4. Agrupar por partido normalizado, línea
        # Necesitamos ambos lados (over y under) para calcular BDI_fair
        
        results = []
        
        # Agrupar por (match_normalized, line)
        for (match_norm, line), group in combined_df.groupby(['match_normalized', 'line']):
            # Separar Over y Under
            over_data = group[group['side'] == 'over']
            under_data = group[group['side'] == 'under']
            
            if over_data.empty and under_data.empty:
                continue
            
            # Procesar cada lado
            for side, side_data in [('over', over_data), ('under', under_data)]:
                if side_data.empty:
                    continue
                
                # Eliminar duplicados por bookmaker (quedarse con el primero)
                side_unique = side_data.drop_duplicates(subset=['bookmaker'], keep='first')
                
                if len(side_unique) < min_bookmakers:
                    continue
                
                # Crear diccionario de cuotas
                odds_dict = dict(zip(side_unique['bookmaker'], side_unique['odds_decimal']))
                odds_list = list(side_unique['odds_decimal'])
                
                # APIs que contribuyeron
                apis = sorted(side_unique['source'].unique().tolist())
                apis_str = ', '.join(apis)
                
                # Información del partido
                first_row = side_unique.iloc[0]
                match_original = side_data['match'].mode().iloc[0] if not side_data['match'].mode().empty else match_norm
                league = first_row.get('league', '')
                starts_at = first_row.get('starts_at', '')
                
                # === CALCULAR BDI_jsd (cuotas crudas, un solo lado) ===
                bdi_raw = calculate_bdi_raw(odds_dict)
                
                # === CALCULAR BDI_jsd_fair (usando ambos lados) ===
                # Necesitamos las cuotas del lado opuesto
                opposite_side = 'under' if side == 'over' else 'over'
                opposite_data = over_data if side == 'under' else under_data
                
                bdi_fair = {'jsd_mean': None, 'std_p': None, 'mad_p': None, 'n_bookmakers': 0}
                
                if not opposite_data.empty:
                    opposite_unique = opposite_data.drop_duplicates(subset=['bookmaker'], keep='first')
                    opposite_odds = dict(zip(opposite_unique['bookmaker'], opposite_unique['odds_decimal']))
                    
                    if side == 'over':
                        bdi_fair = calculate_bdi_fair(odds_dict, opposite_odds)
                    else:
                        bdi_fair = calculate_bdi_fair(opposite_odds, odds_dict)
                
                # Métricas adicionales
                odds_array = np.array(odds_list)
                best_idx = np.argmax(odds_array)
                best_odds = odds_list[best_idx]
                best_bookmaker = list(odds_dict.keys())[best_idx]
                avg_odds = np.mean(odds_array)
                
                # Probabilidades implícitas
                probs = 1 / odds_array
                probs_norm = probs / probs.sum()
                std_p = np.std(probs_norm)
                mad_p = np.median(np.abs(probs_norm - np.median(probs_norm)))
                volatility_pct = (std_p / np.mean(probs_norm)) * 100 if np.mean(probs_norm) > 0 else 0
                margin_pct = (probs.sum() - 1) * 100
                
                # Formatear fecha a Colombia (UTC-5)
                try:
                    if isinstance(starts_at, str) and starts_at:
                        dt = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                    else:
                        dt = pd.to_datetime(starts_at)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                    dt_colombia = dt.astimezone(timezone(timedelta(hours=-5)))
                    fecha_colombia = dt_colombia.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    fecha_colombia = str(starts_at) if starts_at else ''
                
                # Formatear todas las cuotas
                todas_cuotas = '; '.join([f"{bm}:{odd:.4f}" for bm, odd in sorted(odds_dict.items())])
                
                # Construir registro con formato de 22 columnas + APIs_Usadas
                results.append({
                    'Partido': match_original,
                    'Fecha_Hora_Colombia': fecha_colombia,
                    'Mercado': f"{'Over' if side == 'over' else 'Under'} {line}",
                    'Mejor_Cuota': round(best_odds, 4),
                    'Cuota_Promedio_Mercado': round(avg_odds, 4),
                    # BDI_fair (usando ambos lados)
                    'BDI_jsd_fair': round(bdi_fair['jsd_mean'], 6) if bdi_fair['jsd_mean'] else None,
                    'BDI_n_bookmakers_fair': bdi_fair['n_bookmakers'] if bdi_fair['n_bookmakers'] else None,
                    'BDI_std_p_fair': round(bdi_fair['std_p'], 6) if bdi_fair['std_p'] else None,
                    'BDI_mad_p_fair': round(bdi_fair['mad_p'], 6) if bdi_fair['mad_p'] else None,
                    # BDI raw (un solo lado)
                    'BDI_jsd': round(bdi_raw['jsd_mean'], 6) if bdi_raw['jsd_mean'] else None,
                    'BDI_n_bookmakers': bdi_raw['n_bookmakers'],
                    'BDI_std_p': round(bdi_raw['std_p'], 6) if bdi_raw['std_p'] else None,
                    'BDI_mad_p': round(bdi_raw['mad_p'], 6) if bdi_raw['mad_p'] else None,
                    'Mejor_Casa': best_bookmaker,
                    'Num_Casas': len(side_unique),
                    'Diferencia_Cuota_Promedio': round(best_odds - avg_odds, 4),
                    'Volatilidad_Pct': round(volatility_pct, 2),
                    'Margen_Casa_Pct': round(margin_pct, 2),
                    'Liga': league,
                    'Tipo_Mercado': 'Over/Under',
                    'Score_Final': None,
                    'Todas_Las_Cuotas': todas_cuotas,
                    'APIs_Usadas': apis_str
                })
        
        await analyzer.cleanup()
        
        if not results:
            click.echo("\n❌ No hay mercados con suficientes bookmakers")
            return
        
        # 5. Crear DataFrame y ordenar
        df = pd.DataFrame(results)
        
        # FILTRO: Solo mercados que tengan datos de THE_ODDS_API
        total_antes = len(df)
        df = df[df['APIs_Usadas'].str.contains('THE_ODDS_API', na=False)]
        click.echo(f"\n🔍 Filtrado: {total_antes} → {len(df)} mercados (solo con THE_ODDS_API)")
        
        if df.empty:
            click.echo("\n❌ No hay mercados con datos de THE_ODDS_API")
            return
        
        # Ordenar por BDI_jsd_fair descendente (None al final)
        df = df.sort_values('BDI_jsd_fair', ascending=False, na_position='last')
        
        # 6. Mostrar resumen
        click.echo(f"\n📊 Resumen:")
        click.echo(f"   • Total mercados: {len(df)}")
        click.echo(f"   • Partidos únicos: {df['Partido'].nunique()}")
        
        # Estadísticas de BDI
        bdi_fair_valid = df['BDI_jsd_fair'].dropna()
        bdi_raw_valid = df['BDI_jsd'].dropna()
        
        if len(bdi_fair_valid) > 0:
            click.echo(f"   • BDI_jsd_fair promedio: {bdi_fair_valid.mean():.6f}")
            click.echo(f"   • BDI_jsd_fair máximo: {bdi_fair_valid.max():.6f}")
        
        if len(bdi_raw_valid) > 0:
            click.echo(f"   • BDI_jsd promedio: {bdi_raw_valid.mean():.6f}")
            click.echo(f"   • BDI_jsd máximo: {bdi_raw_valid.max():.6f}")
        
        # APIs usadas
        click.echo(f"\n📡 Distribución por APIs:")
        for api_combo, count in df['APIs_Usadas'].value_counts().items():
            click.echo(f"   • {api_combo}: {count}")
        
        # Top 10
        click.echo(f"\n🔥 Top 10 por BDI_jsd_fair:")
        for _, row in df.head(10).iterrows():
            bdi_fair = row['BDI_jsd_fair']
            bdi_raw = row['BDI_jsd']
            bdi_fair_str = f"{bdi_fair:.6f}" if pd.notna(bdi_fair) else "N/A"
            bdi_raw_str = f"{bdi_raw:.6f}" if pd.notna(bdi_raw) else "N/A"
            click.echo(f"   • {row['Partido']} - {row['Mercado']}")
            click.echo(f"     BDI_fair: {bdi_fair_str} | BDI_raw: {bdi_raw_str} | {row['Num_Casas']} casas | {row['APIs_Usadas']}")
        
        # 7. Exportar CSV
        if export_csv:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = f"analisis_mercados_{timestamp}.csv"
            df.to_csv(csv_path, index=False)
            click.echo(f"\n💾 Exportado: {csv_path}")
        
        click.echo("\n✅ Análisis completado")
    
    asyncio.run(_run())


def main():
    cli()


if __name__ == '__main__':
    main()
