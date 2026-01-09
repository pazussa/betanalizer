#!/usr/bin/env python3
"""
main5.py - Análisis con TRES APIs de Odds

Combina:
- THE_ODDS_API: 58 bookmakers (Pinnacle, Betfair, DraftKings, etc.)
- API-FOOTBALL: Bookmakers adicionales (Bet365, Bwin, SBO/Sbobet, etc.)
- SPORTS_GAME_ODDS: 80+ bookmakers adicionales (1xBet, BetMGM, Caesars, ESPN BET, etc.)

Run: `python main5.py analyze` para análisis completo con todas las fuentes
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

import click
import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
from dotenv import load_dotenv

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.analyzer import FootballOddsAnalyzer
from src.reporter import ReportGenerator
from src.models import ValidationError, BookmakerType, OddsData, H2HOdds, MarketType
from src.apis.the_odds_api import TheOddsAPIClient
from src.apis.api_football import APIFootballClient, BOOKMAKER_ID_MAP, LEAGUE_IDS

import httpx


# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('betting_analysis_triple_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# SPORTS GAME ODDS API CLIENT
# ============================================================================

class SportsGameOddsClient:
    """
    Cliente para la API de SportsGameOdds
    80+ bookmakers incluyendo: 1xBet, BetMGM, Caesars, ESPN BET, DraftKings, FanDuel, etc.
    """
    
    BASE_URL = "https://api.sportsgameodds.com/v2"
    
    # Ligas de fútbol soportadas
    SOCCER_LEAGUES = {
        "EPL": "Premier League",
        "BUNDESLIGA": "Bundesliga", 
        "LA_LIGA": "La Liga",
        "IT_SERIE_A": "Serie A",
        "FR_LIGUE_1": "Ligue 1",
        "MLS": "MLS",
        "LIGA_MX": "Liga MX",
        "BR_SERIE_A": "Brasileiro Série A",
        "UEFA_CHAMPIONS_LEAGUE": "Champions League",
        "UEFA_EUROPA_LEAGUE": "Europa League",
        "INTERNATIONAL_SOCCER": "International Soccer",
    }
    
    # Mapeo de bookmaker IDs de SportsGameOdds
    BOOKMAKER_MAPPING = {
        "1xbet": "1xBet",
        "888sport": "888 Sport",
        "ballybet": "Bally Bet",
        "bet365": "Bet365",
        "betfairexchange": "Betfair Exchange",
        "betfairsportsbook": "Betfair Sportsbook",
        "betmgm": "BetMGM",
        "betonline": "BetOnline",
        "betparx": "BetPARX",
        "betrivers": "BetRivers",
        "betsson": "Betsson",
        "betus": "BetUS",
        "betway": "Betway",
        "bovada": "Bovada",
        "boylesports": "BoyleSports",
        "caesars": "Caesars",
        "coolbet": "Coolbet",
        "coral": "Coral",
        "draftkings": "DraftKings",
        "espnbet": "ESPN BET",
        "everygame": "Everygame",
        "fanatics": "Fanatics",
        "fanduel": "FanDuel",
        "fliff": "Fliff",
        "gtbets": "GTbets",
        "hardrockbet": "Hard Rock Bet",
        "ladbrokes": "Ladbrokes",
        "leovegas": "LeoVegas",
        "livescorebet": "LiveScore Bet",
        "lowvig": "LowVig",
        "marathonbet": "Marathon Bet",
        "matchbook": "Matchbook",
        "mybookie": "MyBookie",
        "neds": "Neds",
        "nordicbet": "NordicBet",
        "paddypower": "Paddy Power",
        "pinnacle": "Pinnacle",
        "playup": "PlayUp",
        "pointsbet": "PointsBet",
        "skybet": "Sky Bet",
        "sportsbet": "SportsBet",
        "suprabets": "Suprabets",
        "tab": "TAB",
        "tabtouch": "TABtouch",
        "tipico": "Tipico",
        "unibet": "Unibet",
        "virginbet": "Virgin Bet",
        "williamhill": "William Hill",
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SPORTS_GAME_ODDS_KEY")
        if not self.api_key:
            raise ValueError("SPORTS_GAME_ODDS_KEY no proporcionada")
        
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "X-Api-Key": self.api_key,
                "Accept": "application/json"
            }
        )
    
    async def close(self):
        """Cerrar conexión HTTP"""
        await self.client.aclose()
    
    async def get_soccer_events(self, leagues: List[str] = None, hours_ahead: int = 72) -> List[Dict]:
        """
        Obtener eventos de fútbol con odds disponibles
        
        Args:
            leagues: Lista de leagueIDs (ej: ["EPL", "BUNDESLIGA"])
            hours_ahead: Horas hacia adelante para buscar
            
        Returns:
            Lista de eventos con odds
        """
        if leagues is None:
            leagues = list(self.SOCCER_LEAGUES.keys())
        
        all_events = []
        
        # Calcular rango de fechas
        starts_before = (datetime.now(timezone.utc) + timedelta(hours=hours_ahead)).isoformat()
        
        for league_id in leagues:
            try:
                params = {
                    "leagueID": league_id,
                    "oddsAvailable": "true",
                    "startsBefore": starts_before,
                }
                
                response = await self.client.get(f"{self.BASE_URL}/events/", params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("success") and data.get("data"):
                    events = data["data"]
                    for event in events:
                        event["_league_id"] = league_id
                        event["_league_name"] = self.SOCCER_LEAGUES.get(league_id, league_id)
                    all_events.extend(events)
                    logger.info(f"  SportsGameOdds {league_id}: {len(events)} eventos")
                
                # Pausa para respetar rate limits
                await asyncio.sleep(0.2)
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limit alcanzado para {league_id}")
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"Error HTTP para {league_id}: {e}")
            except Exception as e:
                logger.warning(f"Error obteniendo eventos de {league_id}: {e}")
        
        return all_events
    
    def parse_totals_odds(self, events: List[Dict]) -> List[Dict]:
        """
        Parsear odds de Over/Under de los eventos
        
        Returns:
            Lista de dicts con info de Over/Under
        """
        totals_data = []
        
        for event in events:
            event_id = event.get("eventID")
            league_name = event.get("_league_name", "Unknown")
            
            teams = event.get("teams", {})
            home_team = teams.get("home", {}).get("names", {}).get("medium", "Home")
            away_team = teams.get("away", {}).get("names", {}).get("medium", "Away")
            match_name = f"{home_team} vs {away_team}"
            
            status = event.get("status", {})
            starts_at = status.get("startsAt", "")
            
            odds = event.get("odds", {})
            
            # Buscar mercados Over/Under (points-all-reg-ou-over/under)
            for odd_id, odd_data in odds.items():
                # Solo Over/Under de goles totales
                if not odd_data.get("betTypeID") == "ou":
                    continue
                if not odd_data.get("statEntityID") == "all":
                    continue
                if not odd_data.get("periodID") == "reg":
                    continue
                
                side_id = odd_data.get("sideID")
                if side_id not in ["over", "under"]:
                    continue
                
                line = odd_data.get("bookOverUnder")
                if line is None:
                    continue
                
                by_bookmaker = odd_data.get("byBookmaker", {})
                
                for bookmaker_id, bm_data in by_bookmaker.items():
                    if not bm_data.get("available"):
                        continue
                    
                    odds_value = bm_data.get("odds")
                    if odds_value is None:
                        continue
                    
                    # Convertir odds americanas a decimales
                    decimal_odds = self._american_to_decimal(odds_value)
                    if decimal_odds is None:
                        continue
                    
                    bookmaker_name = self.BOOKMAKER_MAPPING.get(bookmaker_id, bookmaker_id.title())
                    
                    totals_data.append({
                        "event_id": event_id,
                        "match": match_name,
                        "league": league_name,
                        "starts_at": starts_at,
                        "bookmaker": bookmaker_name,
                        "bookmaker_id": bookmaker_id,
                        "line": float(line),
                        "side": side_id,  # "over" o "under"
                        "odds_american": odds_value,
                        "odds_decimal": decimal_odds,
                        "source": "SportsGameOdds",
                    })
        
        return totals_data
    
    def parse_h2h_odds(self, events: List[Dict]) -> List[Dict]:
        """
        Parsear odds H2H (1X2) de los eventos
        
        Returns:
            Lista de dicts con info de H2H/Doble Oportunidad
        """
        h2h_data = []
        
        for event in events:
            event_id = event.get("eventID")
            league_name = event.get("_league_name", "Unknown")
            
            teams = event.get("teams", {})
            home_team = teams.get("home", {}).get("names", {}).get("medium", "Home")
            away_team = teams.get("away", {}).get("names", {}).get("medium", "Away")
            match_name = f"{home_team} vs {away_team}"
            
            status = event.get("status", {})
            starts_at = status.get("startsAt", "")
            
            odds = event.get("odds", {})
            
            # Buscar odds 3-way moneyline por bookmaker
            # Necesitamos: home, away, draw para cada bookmaker
            bookmaker_odds = {}
            
            for odd_id, odd_data in odds.items():
                # Solo 3-way moneyline
                if odd_data.get("betTypeID") != "ml3way":
                    continue
                if odd_data.get("periodID") != "reg":
                    continue
                
                side_id = odd_data.get("sideID")  # "home", "away", "draw"
                if side_id not in ["home", "away", "draw"]:
                    # También puede haber "home+draw" y "away+draw" (double chance)
                    continue
                
                by_bookmaker = odd_data.get("byBookmaker", {})
                
                for bookmaker_id, bm_data in by_bookmaker.items():
                    if not bm_data.get("available"):
                        continue
                    
                    odds_value = bm_data.get("odds")
                    if odds_value is None:
                        continue
                    
                    decimal_odds = self._american_to_decimal(odds_value)
                    if decimal_odds is None:
                        continue
                    
                    if bookmaker_id not in bookmaker_odds:
                        bookmaker_odds[bookmaker_id] = {}
                    
                    bookmaker_odds[bookmaker_id][side_id] = decimal_odds
            
            # Crear registros completos (home + draw + away)
            for bookmaker_id, bm_odds in bookmaker_odds.items():
                if len(bm_odds) < 3:
                    continue  # Necesitamos las 3 cuotas
                
                home_odds = bm_odds.get("home")
                draw_odds = bm_odds.get("draw")
                away_odds = bm_odds.get("away")
                
                if not all([home_odds, draw_odds, away_odds]):
                    continue
                
                bookmaker_name = self.BOOKMAKER_MAPPING.get(bookmaker_id, bookmaker_id.title())
                
                # Calcular doble oportunidad
                try:
                    odds_1x = 1 / ((1/home_odds) + (1/draw_odds))
                    odds_x2 = 1 / ((1/draw_odds) + (1/away_odds))
                except:
                    continue
                
                h2h_data.append({
                    "event_id": event_id,
                    "match": match_name,
                    "league": league_name,
                    "home_team": home_team,
                    "away_team": away_team,
                    "starts_at": starts_at,
                    "bookmaker": bookmaker_name,
                    "bookmaker_id": bookmaker_id,
                    "home_odds": round(home_odds, 3),
                    "draw_odds": round(draw_odds, 3),
                    "away_odds": round(away_odds, 3),
                    "odds_1x": round(odds_1x, 4),
                    "odds_x2": round(odds_x2, 4),
                    "prob_1x": round((1/odds_1x) * 100, 2),
                    "prob_x2": round((1/odds_x2) * 100, 2),
                    "source": "SportsGameOdds",
                })
        
        return h2h_data
    
    def _american_to_decimal(self, american_odds: str) -> Optional[float]:
        """Convertir odds americanas a decimales"""
        try:
            odds_str = str(american_odds).replace("+", "")
            odds_int = int(odds_str)
            
            if odds_int > 0:
                return 1 + (odds_int / 100)
            elif odds_int < 0:
                return 1 + (100 / abs(odds_int))
            else:
                return None
        except:
            return None


# ============================================================================
# MULTI API ANALYZER (TRIPLE API)
# ============================================================================

class AllBookmakersTheOddsAPIClient(TheOddsAPIClient):
    """
    Cliente THE_ODDS_API que procesa TODOS los bookmakers disponibles
    """

    async def get_match_odds(self, match_id: str, sport_key: str = "soccer_epl"):
        """Obtiene cuotas para un partido específico e intenta incluir todas las casas"""
        try:
            url = f"{self.BASE_URL}/sports/{sport_key}/events/{match_id}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,us,uk,au",
                "markets": "h2h",
                "oddsFormat": "decimal",
                "dateFormat": "iso"
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            all_odds = []
            h2h_odds = []

            for bookmaker_data in data.get("bookmakers", []):
                bookmaker_name = bookmaker_data.get("key")
                try:
                    bookmaker_enum = BookmakerType(bookmaker_name)
                except Exception:
                    continue

                for market_data in bookmaker_data.get("markets", []):
                    if market_data.get("key") != "h2h":
                        continue

                    outcomes = market_data.get("outcomes", [])
                    timestamp = datetime.fromisoformat(market_data.get("last_update").replace("Z", "+00:00")) if market_data.get("last_update") else datetime.now(timezone.utc)

                    home_odds = next((o.get("price") for o in outcomes if o.get("name") == data.get("home_team")), None)
                    draw_odds = next((o.get("price") for o in outcomes if o.get("name") == "Draw"), None)
                    away_odds = next((o.get("price") for o in outcomes if o.get("name") == data.get("away_team")), None)

                    if home_odds and draw_odds and away_odds:
                        try:
                            h2h_odds.append(H2HOdds(
                                bookmaker=bookmaker_enum,
                                home_odds=float(home_odds),
                                draw_odds=float(draw_odds),
                                away_odds=float(away_odds),
                                timestamp=timestamp
                            ))
                        except Exception:
                            continue

                    try:
                        if home_odds and draw_odds:
                            prob_1x = (1/float(home_odds)) + (1/float(draw_odds))
                            odds_1x = 1 / prob_1x
                            all_odds.append(OddsData(bookmaker=bookmaker_enum, market="1X", odds=round(odds_1x, 4), timestamp=timestamp))
                        if draw_odds and away_odds:
                            prob_x2 = (1/float(draw_odds)) + (1/float(away_odds))
                            odds_x2 = 1 / prob_x2
                            all_odds.append(OddsData(bookmaker=bookmaker_enum, market="X2", odds=round(odds_x2, 4), timestamp=timestamp))
                    except Exception:
                        continue

            return all_odds, h2h_odds

        except Exception as e:
            logger.warning(f"Error obteniendo cuotas (all bookies) para match {match_id}: {e}")
            return [], []


class TripleAPIAnalyzer:
    """
    Analizador que combina datos de TRES APIs de odds:
    - THE_ODDS_API
    - API-FOOTBALL
    - SPORTS_GAME_ODDS
    """
    
    def __init__(self):
        self.odds_api_client = AllBookmakersTheOddsAPIClient()
        self.api_football_client = None
        self.sports_game_odds_client = None
        
        # Inicializar API-FOOTBALL
        api_football_key = os.getenv("API_FOOTBALL_KEY")
        if api_football_key:
            self.api_football_client = APIFootballClient(api_football_key)
            logger.info("✅ API-FOOTBALL inicializado")
        else:
            logger.warning("⚠️ API_FOOTBALL_KEY no encontrada")
        
        # Inicializar SportsGameOdds
        sports_game_odds_key = os.getenv("SPORTS_GAME_ODDS_KEY")
        if sports_game_odds_key:
            try:
                self.sports_game_odds_client = SportsGameOddsClient(sports_game_odds_key)
                logger.info("✅ SPORTS_GAME_ODDS inicializado")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando SPORTS_GAME_ODDS: {e}")
        else:
            logger.warning("⚠️ SPORTS_GAME_ODDS_KEY no encontrada")
    
    async def cleanup(self):
        """Cerrar conexiones"""
        await self.odds_api_client.close()
        if self.api_football_client:
            await self.api_football_client.close()
        if self.sports_game_odds_client:
            await self.sports_game_odds_client.close()
    
    async def validate_connections(self):
        """Validar conexiones a todas las APIs"""
        # Validar THE_ODDS_API
        try:
            remaining = await self.odds_api_client.get_remaining_requests()
            logger.info(f"✅ THE_ODDS_API conectado - {remaining} requests restantes")
        except Exception as e:
            logger.warning(f"⚠️ THE_ODDS_API: error verificando estado: {e}")
        
        # Validar API-FOOTBALL
        if self.api_football_client:
            status = await self.api_football_client.get_status()
            if status:
                requests_info = status.get("requests", {})
                logger.info(f"✅ API-FOOTBALL conectado - {requests_info.get('current', 0)}/{requests_info.get('limit_day', 100)} requests hoy")
            else:
                logger.warning("⚠️ API-FOOTBALL: no se pudo verificar estado")
        
        # Validar SportsGameOdds
        if self.sports_game_odds_client:
            try:
                # Hacer una petición simple para verificar
                response = await self.sports_game_odds_client.client.get(
                    f"{self.sports_game_odds_client.BASE_URL}/leagues/",
                    params={"sportID": "SOCCER"}
                )
                if response.status_code == 200:
                    logger.info("✅ SPORTS_GAME_ODDS conectado")
                else:
                    logger.warning(f"⚠️ SPORTS_GAME_ODDS: status {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ SPORTS_GAME_ODDS: error verificando estado: {e}")
    
    async def get_api_football_odds(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Obtener odds de API-FOOTBALL"""
        if not self.api_football_client:
            return pd.DataFrame(), pd.DataFrame()
        
        all_h2h_odds = []
        all_totals_odds = []
        
        # Mapeo de fixture_id a información del partido
        fixture_info_map = {}
        
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        # Primero obtener fixtures para tener los nombres de equipos
        for date in [today, tomorrow, day_after]:
            try:
                fixtures_response = await self.api_football_client.client.get(
                    f"{self.api_football_client.BASE_URL}/fixtures",
                    params={"date": date},
                    headers={"x-rapidapi-key": self.api_football_client.api_key}
                )
                if fixtures_response.status_code == 200:
                    fixtures_data = fixtures_response.json().get("response", [])
                    for fix in fixtures_data:
                        fixture_info = fix.get("fixture", {})
                        teams = fix.get("teams", {})
                        league = fix.get("league", {})
                        
                        fixture_id = fixture_info.get("id")
                        if fixture_id and teams:
                            home_team = teams.get("home", {}).get("name", "Home")
                            away_team = teams.get("away", {}).get("name", "Away")
                            match_name = f"{home_team} vs {away_team}"
                            league_name = league.get("name", "Unknown")
                            starts_at = fixture_info.get("date", "")
                            
                            fixture_info_map[fixture_id] = {
                                'match': match_name,
                                'league': league_name,
                                'starts_at': starts_at
                            }
                    logger.info(f"  Fixtures {date}: {len(fixtures_data)} partidos mapeados")
            except Exception as e:
                logger.warning(f"Error obteniendo fixtures para {date}: {e}")
        
        logger.info(f"  Total fixtures mapeados: {len(fixture_info_map)}")
        
        # Ahora obtener odds
        for date in [today, tomorrow, day_after]:
            try:
                odds_data = await self.api_football_client.get_odds_by_date(date)
                
                if odds_data:
                    h2h_odds = self.api_football_client.parse_h2h_odds(odds_data)
                    all_h2h_odds.extend(h2h_odds)
                    
                    totals_odds = self.api_football_client.parse_totals_odds(odds_data)
                    all_totals_odds.extend(totals_odds)
                    
                    logger.info(f"  API-FOOTBALL {date}: {len(h2h_odds)} H2H, {len(totals_odds)} O/U")
                
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.warning(f"Error API-FOOTBALL para {date}: {e}")
        
        h2h_df = pd.DataFrame(all_h2h_odds) if all_h2h_odds else pd.DataFrame()
        totals_df = pd.DataFrame(all_totals_odds) if all_totals_odds else pd.DataFrame()
        
        # Enriquecer con información del partido
        if not h2h_df.empty and 'fixture_id' in h2h_df.columns:
            h2h_df['match'] = h2h_df['fixture_id'].map(lambda fid: fixture_info_map.get(fid, {}).get('match', ''))
            h2h_df['league'] = h2h_df['fixture_id'].map(lambda fid: fixture_info_map.get(fid, {}).get('league', ''))
            h2h_df['starts_at'] = h2h_df['fixture_id'].map(lambda fid: fixture_info_map.get(fid, {}).get('starts_at', ''))
            h2h_df['source'] = 'API-FOOTBALL'
            
        if not totals_df.empty and 'fixture_id' in totals_df.columns:
            totals_df['match'] = totals_df['fixture_id'].map(lambda fid: fixture_info_map.get(fid, {}).get('match', ''))
            totals_df['league'] = totals_df['fixture_id'].map(lambda fid: fixture_info_map.get(fid, {}).get('league', ''))
            totals_df['starts_at'] = totals_df['fixture_id'].map(lambda fid: fixture_info_map.get(fid, {}).get('starts_at', ''))
            totals_df['source'] = 'API-FOOTBALL'
            
            # Expandir over/under en dos filas separadas (over y under)
            expanded_rows = []
            for _, row in totals_df.iterrows():
                # Fila para Over
                over_row = row.copy()
                over_row['side'] = 'over'
                over_row['odds_decimal'] = row['over_odds']
                expanded_rows.append(over_row)
                
                # Fila para Under
                under_row = row.copy()
                under_row['side'] = 'under'
                under_row['odds_decimal'] = row['under_odds']
                expanded_rows.append(under_row)
            
            totals_df = pd.DataFrame(expanded_rows)
        
        return h2h_df, totals_df
    
    async def get_sports_game_odds(self, hours_ahead: int = 72) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Obtener odds de SportsGameOdds"""
        if not self.sports_game_odds_client:
            return pd.DataFrame(), pd.DataFrame()
        
        try:
            logger.info("  Obteniendo eventos de SportsGameOdds...")
            events = await self.sports_game_odds_client.get_soccer_events(hours_ahead=hours_ahead)
            
            if not events:
                logger.warning("  No se encontraron eventos en SportsGameOdds")
                return pd.DataFrame(), pd.DataFrame()
            
            logger.info(f"  SportsGameOdds: {len(events)} eventos encontrados")
            
            # Parsear Over/Under
            totals_data = self.sports_game_odds_client.parse_totals_odds(events)
            totals_df = pd.DataFrame(totals_data) if totals_data else pd.DataFrame()
            
            # Parsear H2H
            h2h_data = self.sports_game_odds_client.parse_h2h_odds(events)
            h2h_df = pd.DataFrame(h2h_data) if h2h_data else pd.DataFrame()
            
            logger.info(f"  SportsGameOdds: {len(totals_df)} O/U, {len(h2h_df)} H2H")
            
            return h2h_df, totals_df
            
        except Exception as e:
            logger.warning(f"Error obteniendo datos de SportsGameOdds: {e}")
            return pd.DataFrame(), pd.DataFrame()


# ============================================================================
# NORMALIZACIÓN DE NOMBRES DE EQUIPOS
# ============================================================================

def normalize_team_name(name: str) -> str:
    """Normalizar nombre de equipo para comparación consistente"""
    if not name:
        return ""
    
    # Mapeo de abreviaciones/variantes comunes
    replacements = {
        # Inglaterra
        'Man Utd': 'Manchester United',
        'Man United': 'Manchester United',
        'Man City': 'Manchester City',
        'Newcastle': 'Newcastle United',
        'Tottenham': 'Tottenham Hotspur',
        'Spurs': 'Tottenham Hotspur',
        'Forest': 'Nottingham Forest',
        'Nottm Forest': 'Nottingham Forest',
        'West Ham': 'West Ham United',
        'Brighton': 'Brighton & Hove Albion',
        'Wolves': 'Wolverhampton Wanderers',
        'Sheffield Utd': 'Sheffield United',
        'Leeds': 'Leeds United',
        # Italia
        'AS Roma': 'Roma',
        'AC Milan': 'Milan',
        'Inter Milan': 'Inter',
        'Napoli': 'SSC Napoli',
        # España
        'Atletico Madrid': 'Atlético Madrid',
        'Atletico': 'Atlético Madrid',
        'Real': 'Real Madrid',
        'Barca': 'Barcelona',
        # Alemania
        'Bayern': 'Bayern Munich',
        'Bayern München': 'Bayern Munich',
        'Dortmund': 'Borussia Dortmund',
        'BVB': 'Borussia Dortmund',
        "M'gladbach": 'Borussia Mönchengladbach',
        'Gladbach': 'Borussia Mönchengladbach',
        # Francia
        'PSG': 'Paris Saint-Germain',
        'Paris SG': 'Paris Saint-Germain',
    }
    
    result = name.strip()
    for old, new in replacements.items():
        if old.lower() == result.lower():
            return new
    
    return result


def normalize_match_name(match: str) -> str:
    """Normalizar nombre de partido para matching entre APIs"""
    if not match or ' vs ' not in match:
        return match
    
    parts = match.split(' vs ')
    if len(parts) != 2:
        return match
    
    home = normalize_team_name(parts[0].strip())
    away = normalize_team_name(parts[1].strip())
    
    return f"{home} vs {away}"


# ============================================================================
# BDI CALCULATION (Bookmaker Disagreement Index)
# ============================================================================

def calculate_bdi_jsd(odds_dict: Dict[str, float]) -> Optional[float]:
    """
    Calcular BDI usando Jensen-Shannon Divergence
    
    Args:
        odds_dict: Dict con bookmaker -> odds decimal
        
    Returns:
        BDI score (0-1, mayor = más desacuerdo)
    """
    if len(odds_dict) < 2:
        return None
    
    # Convertir odds a probabilidades normalizadas
    probabilities = []
    for odds in odds_dict.values():
        if odds and odds > 1:
            prob = 1 / odds
            probabilities.append(prob)
    
    if len(probabilities) < 2:
        return None
    
    # Normalizar
    total = sum(probabilities)
    probs_normalized = [p / total for p in probabilities]
    
    # Calcular distribución uniforme como referencia
    uniform = [1 / len(probs_normalized)] * len(probs_normalized)
    
    # JSD
    try:
        jsd = jensenshannon(probs_normalized, uniform)
        return round(jsd, 4)
    except:
        return None


def calculate_fair_odds(odds_list: List[float]) -> Optional[float]:
    """Calcular cuota justa (promedio ponderado sin margen)"""
    if not odds_list:
        return None
    
    # Usar mediana como estimador robusto
    odds_array = np.array([o for o in odds_list if o and o > 1])
    if len(odds_array) == 0:
        return None
    
    return round(float(np.median(odds_array)), 4)


# ============================================================================
# CLI COMMANDS
# ============================================================================

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """CLI para análisis TRIPLE-API de cuotas de apuestas"""
    load_dotenv(override=True)


@cli.command()
def status():
    """Verificar estado de las TRES APIs"""
    async def _run():
        click.echo("🔍 Verificando estado de las 3 APIs...\n")
        
        # THE_ODDS_API
        click.echo("📡 THE_ODDS_API:")
        api_key = os.getenv("THE_ODDS_API_KEY")
        if api_key:
            try:
                client = TheOddsAPIClient()
                sports = await client.client.get(
                    f"{client.BASE_URL}/sports",
                    params={"apiKey": client.api_key}
                )
                sports.raise_for_status()
                click.echo("  ✅ Conexión OK (58 bookmakers)")
                await client.close()
            except Exception as e:
                click.echo(f"  ❌ Error: {e}")
        else:
            click.echo("  ⚠️ THE_ODDS_API_KEY no configurada")
        
        # API-FOOTBALL
        click.echo("\n📡 API-FOOTBALL:")
        api_key = os.getenv("API_FOOTBALL_KEY")
        if api_key:
            try:
                client = APIFootballClient(api_key)
                status = await client.get_status()
                if status:
                    requests = status.get("requests", {})
                    subscription = status.get("subscription", {})
                    click.echo(f"  ✅ Conexión OK")
                    click.echo(f"  📊 Plan: {subscription.get('plan', 'Unknown')}")
                    click.echo(f"  📊 Requests: {requests.get('current', 0)}/{requests.get('limit_day', 100)} hoy")
                    click.echo("  📋 Bookmakers exclusivos: Bet365, Bwin, SBO")
                await client.close()
            except Exception as e:
                click.echo(f"  ❌ Error: {e}")
        else:
            click.echo("  ⚠️ API_FOOTBALL_KEY no configurada")
        
        # SPORTS_GAME_ODDS
        click.echo("\n📡 SPORTS_GAME_ODDS:")
        api_key = os.getenv("SPORTS_GAME_ODDS_KEY")
        if api_key:
            try:
                client = SportsGameOddsClient(api_key)
                response = await client.client.get(
                    f"{client.BASE_URL}/leagues/",
                    params={"sportID": "SOCCER"}
                )
                if response.status_code == 200:
                    click.echo("  ✅ Conexión OK (80+ bookmakers)")
                    click.echo("  📋 Bookmakers exclusivos: 1xBet, BetMGM, Caesars, ESPN BET, etc.")
                else:
                    click.echo(f"  ⚠️ Status: {response.status_code}")
                await client.close()
            except Exception as e:
                click.echo(f"  ❌ Error: {e}")
        else:
            click.echo("  ⚠️ SPORTS_GAME_ODDS_KEY no configurada")
        
        click.echo("\n✅ Verificación completada")
    
    asyncio.run(_run())


@cli.command()
def bookmakers():
    """Listar todos los bookmakers disponibles en las 3 APIs"""
    click.echo("📚 Bookmakers disponibles en las 3 APIs:\n")
    
    click.echo("═══ THE_ODDS_API (58 bookmakers) ═══")
    the_odds = ["pinnacle", "betfair", "williamhill", "unibet", "betway", 
                "draftkings", "fanduel", "betmgm", "marathonbet", "betsson"]
    for bm in the_odds:
        click.echo(f"  • {bm}")
    click.echo("  ... y 48 más\n")
    
    click.echo("═══ API-FOOTBALL (34 bookmakers) ═══")
    click.echo("⭐ Exclusivos:")
    exclusive_af = ["Bet365", "Bwin", "SBO (Sbobet)", "Dafabet", "188Bet", "10Bet"]
    for bm in exclusive_af:
        click.echo(f"  ⭐ {bm}")
    click.echo("")
    
    click.echo("═══ SPORTS_GAME_ODDS (80+ bookmakers) ═══")
    click.echo("⭐ Destacados:")
    sgo_bookmakers = [
        "1xBet", "BetMGM", "Caesars", "ESPN BET", "DraftKings", "FanDuel",
        "Hard Rock Bet", "PointsBet", "BetRivers", "BetParx", "Bally Bet",
        "Pinnacle", "Betfair", "Bovada", "MyBookie", "GTbets"
    ]
    for bm in sgo_bookmakers:
        click.echo(f"  ⭐ {bm}")
    click.echo("  ... y 64+ más")


@cli.command()
@click.option('--hours-ahead', '-h', default=72, type=click.IntRange(1, 336), help='Horas hacia adelante')
@click.option('--hours-from', default=0, type=click.IntRange(0, 336), help='Horas desde ahora')
@click.option('--min-bookmakers', '-b', default=3, type=click.IntRange(1, 50), help='Mínimo de bookmakers por mercado')
@click.option('--only-totals/--all-markets', default=True, help='Solo Over/Under (sin 1X/X2)')
@click.option('--export-csv/--no-csv', default=True, help='Exportar a CSV')
def analyze(hours_ahead, hours_from, min_bookmakers, only_totals, export_csv):
    """
    Análisis completo combinando THE_ODDS_API + API-FOOTBALL + SPORTS_GAME_ODDS
    
    Obtiene cuotas de ~140+ bookmakers incluyendo:
    - THE_ODDS_API: Pinnacle, Betfair, DraftKings, FanDuel, etc.
    - API-FOOTBALL: Bet365, Bwin, Sbobet (SBO), etc.
    - SPORTS_GAME_ODDS: 1xBet, BetMGM, Caesars, ESPN BET, etc.
    """
    async def _run():
        click.echo("🚀 Iniciando análisis TRIPLE-API...")
        click.echo(f"   • THE_ODDS_API: ~58 bookmakers")
        click.echo(f"   • API-FOOTBALL: ~34 bookmakers (Bet365, Bwin, SBO)")
        click.echo(f"   • SPORTS_GAME_ODDS: ~80 bookmakers (1xBet, BetMGM, ESPN BET)")
        click.echo(f"   • Horas: {hours_from}h - {hours_ahead}h")
        click.echo("")
        
        analyzer = TripleAPIAnalyzer()
        
        try:
            await analyzer.validate_connections()
        except Exception as e:
            click.echo(f"⚠️ Error validando APIs: {e}")
        
        # Coleccionar todos los datos
        all_h2h = []
        all_totals = []
        
        # 1. THE_ODDS_API
        click.echo("\n📡 [1/3] Obteniendo datos de THE_ODDS_API...")
        try:
            main_analyzer = FootballOddsAnalyzer()
            main_analyzer.odds_client = AllBookmakersTheOddsAPIClient()
            await main_analyzer.validate_api_connections()
            
            results = await main_analyzer.analyze_all_matches(
                min_probability=0.0,
                min_odds=1.0,
                hours_ahead=hours_ahead,
                hours_from=hours_from,
                only_totals=True,
            )
            click.echo(f"   ✅ {len(results) if results else 0} mercados")
            await main_analyzer.cleanup()
        except Exception as e:
            click.echo(f"   ⚠️ Error: {e}")
            results = []
        
        # 2. API-FOOTBALL
        click.echo("\n📡 [2/3] Obteniendo datos de API-FOOTBALL...")
        af_h2h_df, af_totals_df = await analyzer.get_api_football_odds()
        
        if not af_totals_df.empty:
            click.echo(f"   ✅ {len(af_totals_df)} O/U de {af_totals_df['bookmaker'].nunique()} bookmakers")
        if not af_h2h_df.empty:
            click.echo(f"   ✅ {len(af_h2h_df)} H2H de {af_h2h_df['bookmaker'].nunique()} bookmakers")
        
        # 3. SPORTS_GAME_ODDS
        click.echo("\n📡 [3/3] Obteniendo datos de SPORTS_GAME_ODDS...")
        sgo_h2h_df, sgo_totals_df = await analyzer.get_sports_game_odds(hours_ahead=hours_ahead)
        
        if not sgo_totals_df.empty:
            click.echo(f"   ✅ {len(sgo_totals_df)} O/U de {sgo_totals_df['bookmaker'].nunique()} bookmakers")
        if not sgo_h2h_df.empty:
            click.echo(f"   ✅ {len(sgo_h2h_df)} H2H de {sgo_h2h_df['bookmaker'].nunique()} bookmakers")
        
        # Combinar datos de todas las APIs
        click.echo("\n🔄 Combinando datos de las 3 APIs...")
        all_totals_dfs = []
        
        # Añadir API-FOOTBALL totals
        if not af_totals_df.empty:
            # Normalizar nombres de partidos
            af_totals_df['match'] = af_totals_df['match'].apply(normalize_match_name)
            all_totals_dfs.append(af_totals_df)
            click.echo(f"   • API-FOOTBALL: {len(af_totals_df)} registros, {af_totals_df['bookmaker'].nunique()} bookmakers")
        
        # Añadir SportsGameOdds totals
        if not sgo_totals_df.empty:
            # Normalizar nombres de partidos
            sgo_totals_df['match'] = sgo_totals_df['match'].apply(normalize_match_name)
            all_totals_dfs.append(sgo_totals_df)
            click.echo(f"   • SPORTS_GAME_ODDS: {len(sgo_totals_df)} registros, {sgo_totals_df['bookmaker'].nunique()} bookmakers")
        
        # Combinar todos los DataFrames
        if all_totals_dfs:
            combined_totals_df = pd.concat(all_totals_dfs, ignore_index=True)
            click.echo(f"   ✅ Total combinado: {len(combined_totals_df)} registros, {combined_totals_df['bookmaker'].nunique()} bookmakers únicos")
            
            # Mostrar partidos que aparecen en ambas APIs
            if not af_totals_df.empty and not sgo_totals_df.empty:
                af_matches = set(af_totals_df['match'].unique())
                sgo_matches = set(sgo_totals_df['match'].unique())
                common_matches = af_matches & sgo_matches
                if common_matches:
                    click.echo(f"   🔗 Partidos con datos de AMBAS APIs: {len(common_matches)}")
        else:
            combined_totals_df = pd.DataFrame()
        
        # Procesar y agrupar Over/Under
        combined_totals = []
        
        if not combined_totals_df.empty:
            # Agrupar por partido y línea (usando DataFrame combinado)
            grouped = combined_totals_df.groupby(['match', 'line', 'side'])
            
            for (match, line, side), group in grouped:
                if len(group) < min_bookmakers:
                    continue
                
                # Filtrar valores inválidos
                valid_group = group[group['odds_decimal'].notna() & (group['odds_decimal'] > 1)]
                if len(valid_group) < min_bookmakers:
                    continue
                
                # Crear diccionario preservando orden
                bookmakers_list = list(valid_group['bookmaker'])
                odds_list = list(valid_group['odds_decimal'])
                odds_dict = dict(zip(bookmakers_list, odds_list))
                
                # Identificar APIs que contribuyen a este mercado
                apis_in_market = set(valid_group['source'].unique())
                apis_str = ', '.join(sorted(apis_in_market))
                
                # BDI calculations
                bdi_jsd_fair = calculate_bdi_jsd(odds_dict)
                fair_odds = calculate_fair_odds(odds_list)
                
                # Calcular métricas adicionales
                odds_array = np.array(odds_list)
                probs = 1 / odds_array
                probs_normalized = probs / probs.sum()
                
                std_p = np.std(probs_normalized)
                mad_p = np.median(np.abs(probs_normalized - np.median(probs_normalized)))
                
                # Calcular BDI sin normalización "fair" (usando probabilidades brutas)
                bdi_jsd_raw = calculate_bdi_jsd(odds_dict)  # Mismo cálculo, se usa para consistencia
                
                # Mejor cuota y casa (usando la lista de bookmakers en orden)
                best_idx = np.argmax(odds_list)
                best_odds = odds_list[best_idx]
                best_bookmaker = bookmakers_list[best_idx]
                
                # Cuota promedio
                avg_odds = np.mean(odds_list)
                
                # Volatilidad y margen
                volatility_pct = (std_p / np.mean(probs_normalized)) * 100 if np.mean(probs_normalized) > 0 else 0
                margin_pct = (probs.sum() - 1) * 100
                
                league = group['league'].iloc[0]
                starts_at = group['starts_at'].iloc[0]
                
                # Formatear fecha a Colombia (UTC-5)
                try:
                    dt = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                    dt_colombia = dt.astimezone(timezone(timedelta(hours=-5)))
                    fecha_colombia = dt_colombia.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    fecha_colombia = starts_at
                
                # Formatear todas las cuotas
                todas_cuotas = '; '.join([f"{bm}:{odd:.4f}" for bm, odd in odds_dict.items()])
                
                combined_totals.append({
                    'Partido': match,
                    'Fecha_Hora_Colombia': fecha_colombia,
                    'Mercado': f"{'Over' if side == 'over' else 'Under'} {line}",
                    'Mejor_Cuota': round(best_odds, 4),
                    'Cuota_Promedio_Mercado': round(avg_odds, 4),
                    'BDI_jsd_fair': round(bdi_jsd_fair, 4) if bdi_jsd_fair else None,
                    'BDI_n_bookmakers_fair': len(valid_group),
                    'BDI_std_p_fair': round(std_p, 4),
                    'BDI_mad_p_fair': round(mad_p, 4),
                    'BDI_jsd': round(bdi_jsd_raw, 4) if bdi_jsd_raw else None,
                    'BDI_n_bookmakers': len(valid_group),
                    'BDI_std_p': round(std_p, 4),
                    'BDI_mad_p': round(mad_p, 4),
                    'Mejor_Casa': best_bookmaker,
                    'Num_Casas': len(valid_group),
                    'Diferencia_Cuota_Promedio': round(best_odds - avg_odds, 4),
                    'Volatilidad_Pct': round(volatility_pct, 2),
                    'Margen_Casa_Pct': round(margin_pct, 2),
                    'Liga': league,
                    'Tipo_Mercado': 'Over/Under',
                    'Score_Final': None,
                    'Todas_Las_Cuotas': todas_cuotas,
                    'APIs_Usadas': apis_str,
                })
        
        # Convertir a DataFrame
        combined_df = pd.DataFrame(combined_totals) if combined_totals else pd.DataFrame()
        
        if combined_df.empty:
            click.echo("\n❌ No se encontraron datos suficientes")
            await analyzer.cleanup()
            return
        
        # Ordenar por BDI descendente
        combined_df = combined_df.sort_values('BDI_jsd_fair', ascending=False)
        
        # Mostrar resumen
        click.echo("\n" + "="*70)
        click.echo("📊 RESULTADOS COMBINADOS - OVER/UNDER")
        click.echo("="*70)
        
        # Estadísticas
        click.echo(f"\n📈 Estadísticas:")
        click.echo(f"   • Total mercados: {len(combined_df)}")
        click.echo(f"   • Partidos únicos: {combined_df['Partido'].nunique()}")
        click.echo(f"   • BDI promedio: {combined_df['BDI_jsd_fair'].mean():.4f}")
        click.echo(f"   • BDI máximo: {combined_df['BDI_jsd_fair'].max():.4f}")
        
        # Top 20 por BDI
        click.echo(f"\n🔥 TOP 20 por BDI (Mayor desacuerdo entre bookmakers):\n")
        
        top_20 = combined_df.head(20)
        for idx, row in top_20.iterrows():
            click.echo(f"  {row['Partido']}")
            click.echo(f"    📌 {row['Mercado']} | Liga: {row['Liga']}")
            click.echo(f"    💰 Mejor: {row['Mejor_Cuota']:.3f} | Promedio: {row['Cuota_Promedio_Mercado']:.3f}")
            click.echo(f"    📊 BDI: {row['BDI_jsd_fair']:.4f} | 📚 {row['Num_Casas']} bookmakers")
            click.echo(f"    🏠 Mejor casa: {row['Mejor_Casa']}")
            click.echo("")
        
        # Exportar CSV
        if export_csv:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = f"analisis_mercados_{timestamp}.csv"
            combined_df.to_csv(csv_path, index=False)
            click.echo(f"\n💾 Exportado: {csv_path}")
            
            # También exportar datos crudos combinados
            if not combined_totals_df.empty:
                combined_raw_csv = f"combined_totals_raw_{timestamp}.csv"
                combined_totals_df.to_csv(combined_raw_csv, index=False)
                click.echo(f"💾 Datos crudos combinados: {combined_raw_csv}")
                
                # Mostrar estadísticas por API
                click.echo(f"\n📊 Contribución por API:")
                for api_source in combined_totals_df['bookmaker'].unique():
                    count = len(combined_totals_df[combined_totals_df['bookmaker'] == api_source])
                    if count > 0:
                        click.echo(f"   • {api_source}: {count} registros")
        
        await analyzer.cleanup()
        click.echo("\n✅ Análisis completado")
    
    asyncio.run(_run())


@cli.command()
def test_sgo():
    """Prueba rápida de SportsGameOdds API"""
    async def _run():
        click.echo("🧪 Probando SPORTS_GAME_ODDS API...\n")
        
        api_key = os.getenv("SPORTS_GAME_ODDS_KEY")
        if not api_key:
            click.echo("❌ SPORTS_GAME_ODDS_KEY no encontrada en .env")
            return
        
        try:
            client = SportsGameOddsClient(api_key)
            
            # 1. Verificar ligas disponibles
            click.echo("1️⃣ Ligas de fútbol disponibles:")
            response = await client.client.get(
                f"{client.BASE_URL}/leagues/",
                params={"sportID": "SOCCER"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    for league in data["data"][:10]:
                        click.echo(f"   • {league.get('leagueID')}: {league.get('name')}")
            
            # 2. Obtener eventos de muestra (Premier League)
            click.echo("\n2️⃣ Eventos de Premier League:")
            events = await client.get_soccer_events(leagues=["EPL"], hours_ahead=168)
            click.echo(f"   ✅ {len(events)} eventos encontrados")
            
            if events:
                # Parsear odds
                totals = client.parse_totals_odds(events)
                h2h = client.parse_h2h_odds(events)
                
                click.echo(f"\n3️⃣ Odds parseadas:")
                click.echo(f"   • Over/Under: {len(totals)} registros")
                click.echo(f"   • H2H (1X2): {len(h2h)} registros")
                
                if totals:
                    df = pd.DataFrame(totals)
                    bookmakers = df['bookmaker'].unique()
                    click.echo(f"\n4️⃣ Bookmakers encontrados ({len(bookmakers)}):")
                    for bm in sorted(bookmakers)[:20]:
                        click.echo(f"   • {bm}")
                    if len(bookmakers) > 20:
                        click.echo(f"   ... y {len(bookmakers) - 20} más")
            
            await client.close()
            click.echo("\n✅ Prueba completada")
            
        except Exception as e:
            click.echo(f"❌ Error: {e}")
    
    asyncio.run(_run())


def main():
    cli()


if __name__ == '__main__':
    main()
