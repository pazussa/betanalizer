#!/usr/bin/env python3
"""
Cliente para API-FOOTBALL (api-sports.io)
Proporciona acceso a odds de bookmakers adicionales como Bet365, Bwin, SBO
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class APIFootballBookmaker(str, Enum):
    """Bookmakers disponibles en API-FOOTBALL"""
    BET10 = "10Bet"
    MARATHONBET = "Marathonbet"
    BETFAIR = "Betfair"
    PINNACLE = "Pinnacle"
    SBO = "SBO"  # Sbobet - Casa asiática importante
    BWIN = "Bwin"  # No disponible en THE_ODDS_API gratis
    WILLIAM_HILL = "William Hill"
    BET365 = "Bet365"  # No disponible en THE_ODDS_API gratis
    DAFABET = "Dafabet"
    LADBROKES = "Ladbrokes"
    ONEXBET = "1xBet"
    BETFRED = "BetFred"
    BET188 = "188Bet"
    INTERWETTEN = "Interwetten"
    UNIBET = "Unibet"
    DIMES5 = "5Dimes"
    INTERTOPS = "Intertops"
    BOVADA = "Bovada"
    BETCRIS = "Betcris"
    SPORT888 = "888Sport"
    TIPICO = "Tipico"
    SPORTINGBET = "Sportingbet"
    BETWAY = "Betway"
    EXPEKT = "Expekt"
    BETSSON = "Betsson"
    NORDICBET = "NordicBet"
    COMEON = "ComeOn"
    NETBET = "Netbet"
    BETANO = "Betano"
    FONBET = "Fonbet"
    SUPERBET = "Superbet"


# Mapeo de IDs de API-FOOTBALL a nombres
BOOKMAKER_ID_MAP = {
    1: "10Bet",
    2: "Marathonbet",
    3: "Betfair",
    4: "Pinnacle",
    5: "SBO",
    6: "Bwin",
    7: "William Hill",
    8: "Bet365",
    9: "Dafabet",
    10: "Ladbrokes",
    11: "1xBet",
    12: "BetFred",
    13: "188Bet",
    15: "Interwetten",
    16: "Unibet",
    17: "5Dimes",
    18: "Intertops",
    19: "Bovada",
    20: "Betcris",
    21: "888Sport",
    22: "Tipico",
    23: "Sportingbet",
    24: "Betway",
    25: "Expekt",
    26: "Betsson",
    27: "NordicBet",
    28: "ComeOn",
    30: "Netbet",
    32: "Betano",
    33: "Fonbet",
    34: "Superbet",
}

# Ligas principales con sus IDs en API-FOOTBALL
LEAGUE_IDS = {
    "premier_league": 39,      # England Premier League
    "la_liga": 140,            # Spain La Liga
    "serie_a": 135,            # Italy Serie A
    "bundesliga": 78,          # Germany Bundesliga
    "ligue_1": 61,             # France Ligue 1
    "eredivisie": 88,          # Netherlands Eredivisie
    "primeira_liga": 94,       # Portugal Primeira Liga
    "champions_league": 2,     # UEFA Champions League
    "europa_league": 3,        # UEFA Europa League
    "copa_libertadores": 13,   # Copa Libertadores
    "mls": 253,                # USA MLS
    "liga_mx": 262,            # Mexico Liga MX
}


class APIFootballClient:
    """
    Cliente para API-FOOTBALL (api-sports.io)
    
    Proporciona acceso a odds de bookmakers no disponibles en THE_ODDS_API gratuito:
    - Bet365 (la casa más importante)
    - Bwin
    - SBO (Sbobet - casa asiática)
    - Y más...
    """
    
    BASE_URL = "https://v3.football.api-sports.io"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")
        if not self.api_key:
            raise ValueError("API_FOOTBALL_KEY no encontrada")
        
        # NO pasar headers al constructor, se pasan en cada request
        self.client = httpx.AsyncClient(timeout=30.0)
        self._requests_used = 0
        self._requests_limit = 100  # Free tier
    
    def _get_headers(self) -> Dict:
        """Headers para las peticiones"""
        return {"x-apisports-key": self.api_key}
    
    async def close(self):
        """Cerrar el cliente HTTP"""
        await self.client.aclose()
    
    async def get_status(self) -> Dict:
        """Verificar estado de la cuenta y requests disponibles"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/status",
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("response"):
                account = data["response"]
                self._requests_used = account.get("requests", {}).get("current", 0)
                self._requests_limit = account.get("requests", {}).get("limit_day", 100)
                logger.info(f"API-FOOTBALL: {self._requests_used}/{self._requests_limit} requests usados hoy")
            
            return data.get("response", {})
        except Exception as e:
            logger.error(f"Error verificando estado API-FOOTBALL: {e}")
            return {}
    
    async def get_bookmakers(self) -> List[Dict]:
        """Obtener lista de bookmakers disponibles"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/odds/bookmakers",
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", [])
        except Exception as e:
            logger.error(f"Error obteniendo bookmakers: {e}")
            return []
    
    async def get_fixtures_by_date(self, date: str, league_id: int = None) -> List[Dict]:
        """
        Obtener partidos por fecha
        
        Args:
            date: Fecha en formato YYYY-MM-DD
            league_id: ID de la liga (opcional)
        
        Returns:
            Lista de fixtures
        """
        try:
            params = {"date": date}
            if league_id:
                params["league"] = league_id
            
            response = await self.client.get(
                f"{self.BASE_URL}/fixtures", 
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("response", [])
        except Exception as e:
            logger.error(f"Error obteniendo fixtures para {date}: {e}")
            return []
    
    async def get_fixtures_by_league_season(self, league_id: int, season: int) -> List[Dict]:
        """
        Obtener partidos por liga y temporada
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada (ej: 2024)
        
        Returns:
            Lista de fixtures
        """
        try:
            params = {"league": league_id, "season": season}
            response = await self.client.get(
                f"{self.BASE_URL}/fixtures", 
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("response", [])
        except Exception as e:
            logger.error(f"Error obteniendo fixtures para liga {league_id} temporada {season}: {e}")
            return []
    
    async def get_odds_by_fixture(self, fixture_id: int, bookmaker_id: int = None) -> List[Dict]:
        """
        Obtener cuotas pre-match para un fixture específico
        
        Args:
            fixture_id: ID del fixture en API-FOOTBALL
            bookmaker_id: ID del bookmaker (opcional, si no se especifica devuelve todos)
        
        Returns:
            Lista de odds por bookmaker
        """
        try:
            params = {"fixture": fixture_id}
            if bookmaker_id:
                params["bookmaker"] = bookmaker_id
            
            response = await self.client.get(
                f"{self.BASE_URL}/odds", 
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("response", [])
        except Exception as e:
            logger.error(f"Error obteniendo odds para fixture {fixture_id}: {e}")
            return []
    
    async def get_odds_by_date(self, date: str) -> List[Dict]:
        """
        Obtener cuotas para todos los partidos de una fecha específica
        
        Args:
            date: Fecha en formato YYYY-MM-DD
        
        Returns:
            Lista de fixtures con odds disponibles
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/odds", 
                params={"date": date},
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"API-FOOTBALL: {len(data.get('response', []))} fixtures con odds para {date}")
            return data.get("response", [])
        except Exception as e:
            logger.error(f"Error obteniendo odds para fecha {date}: {e}")
            return []
    
    async def get_odds_by_league_season(self, league_id: int, season: int, bookmaker_id: int = None) -> List[Dict]:
        """
        Obtener cuotas para todos los partidos de una liga/temporada
        
        Args:
            league_id: ID de la liga
            season: Año de la temporada
            bookmaker_id: ID del bookmaker (opcional)
        
        Returns:
            Lista de odds (paginado, máx 10 fixtures por página)
        """
        try:
            params = {"league": league_id, "season": season}
            if bookmaker_id:
                params["bookmaker"] = bookmaker_id
            
            response = await self.client.get(
                f"{self.BASE_URL}/odds", 
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("response", [])
        except Exception as e:
            logger.error(f"Error obteniendo odds para liga {league_id}: {e}")
            return []
    
    def parse_h2h_odds(self, odds_response: List[Dict]) -> List[Dict]:
        """
        Parsear odds de Match Winner (1X2) de la respuesta de API-FOOTBALL
        
        Returns:
            Lista de dicts con formato:
            {
                'fixture_id': int,
                'home_team': str,
                'away_team': str,
                'bookmaker': str,
                'home_odds': float,
                'draw_odds': float,
                'away_odds': float,
                'update_time': datetime
            }
        """
        results = []
        
        for fixture_data in odds_response:
            fixture_info = fixture_data.get("fixture", {})
            fixture_id = fixture_info.get("id")
            
            league_info = fixture_data.get("league", {})
            
            for bookmaker_data in fixture_data.get("bookmakers", []):
                bookmaker_id = bookmaker_data.get("id")
                bookmaker_name = BOOKMAKER_ID_MAP.get(bookmaker_id, f"Unknown_{bookmaker_id}")
                
                for bet_data in bookmaker_data.get("bets", []):
                    # Match Winner es bet id=1 o name="Match Winner"
                    if bet_data.get("id") == 1 or bet_data.get("name") == "Match Winner":
                        values = bet_data.get("values", [])
                        
                        home_odds = None
                        draw_odds = None
                        away_odds = None
                        
                        for v in values:
                            val_name = v.get("value")
                            odd = v.get("odd")
                            if odd:
                                try:
                                    odd = float(odd)
                                except (ValueError, TypeError):
                                    continue
                                
                                if val_name == "Home":
                                    home_odds = odd
                                elif val_name == "Draw":
                                    draw_odds = odd
                                elif val_name == "Away":
                                    away_odds = odd
                        
                        if home_odds and draw_odds and away_odds:
                            results.append({
                                'fixture_id': fixture_id,
                                'league_id': league_info.get("id"),
                                'league_name': league_info.get("name"),
                                'bookmaker_id': bookmaker_id,
                                'bookmaker': bookmaker_name,
                                'home_odds': home_odds,
                                'draw_odds': draw_odds,
                                'away_odds': away_odds,
                            })
        
        return results
    
    def parse_totals_odds(self, odds_response: List[Dict]) -> List[Dict]:
        """
        Parsear odds de Over/Under de la respuesta de API-FOOTBALL
        
        Returns:
            Lista de dicts con formato:
            {
                'fixture_id': int,
                'bookmaker': str,
                'line': float (ej: 2.5),
                'over_odds': float,
                'under_odds': float
            }
        """
        results = []
        
        for fixture_data in odds_response:
            fixture_info = fixture_data.get("fixture", {})
            fixture_id = fixture_info.get("id")
            
            for bookmaker_data in fixture_data.get("bookmakers", []):
                bookmaker_id = bookmaker_data.get("id")
                bookmaker_name = BOOKMAKER_ID_MAP.get(bookmaker_id, f"Unknown_{bookmaker_id}")
                
                for bet_data in bookmaker_data.get("bets", []):
                    # Goals Over/Under es bet id=5 o similar
                    bet_name = bet_data.get("name", "")
                    if "Over/Under" in bet_name or bet_data.get("id") == 5:
                        values = bet_data.get("values", [])
                        
                        # Agrupar por línea
                        lines = {}
                        for v in values:
                            val_name = v.get("value", "")
                            odd = v.get("odd")
                            
                            if odd and ("Over" in val_name or "Under" in val_name):
                                try:
                                    odd = float(odd)
                                    # Extraer línea del nombre (ej: "Over 2.5" -> 2.5)
                                    parts = val_name.split()
                                    if len(parts) >= 2:
                                        line = float(parts[1])
                                        
                                        if line not in lines:
                                            lines[line] = {}
                                        
                                        if "Over" in val_name:
                                            lines[line]['over'] = odd
                                        else:
                                            lines[line]['under'] = odd
                                except (ValueError, TypeError, IndexError):
                                    continue
                        
                        for line, odds in lines.items():
                            if 'over' in odds and 'under' in odds:
                                results.append({
                                    'fixture_id': fixture_id,
                                    'bookmaker_id': bookmaker_id,
                                    'bookmaker': bookmaker_name,
                                    'line': line,
                                    'over_odds': odds['over'],
                                    'under_odds': odds['under'],
                                })
        
        return results
    
    def calculate_double_chance(self, home_odds: float, draw_odds: float, away_odds: float) -> Tuple[float, float]:
        """
        Calcular cuotas de doble oportunidad a partir de 1X2
        
        Returns:
            (odds_1x, odds_x2)
        """
        prob_1x = (1/home_odds) + (1/draw_odds)
        prob_x2 = (1/draw_odds) + (1/away_odds)
        
        odds_1x = round(1 / prob_1x, 4)
        odds_x2 = round(1 / prob_x2, 4)
        
        return odds_1x, odds_x2
