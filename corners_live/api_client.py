"""
Cliente para The Odds API - Mercados de Corners en vivo
"""
import os
import logging
from typing import List, Optional
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv

from models import LiveMatch, CornerOdds, BookmakerType, MatchCornerOdds

load_dotenv()


class TheOddsAPIClient:
    """Cliente para interactuar con The Odds API"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("THE_ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("THE_ODDS_API_KEY no está configurada")
        
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = logging.getLogger(__name__)
    
    async def get_live_matches(self) -> List[LiveMatch]:
        """
        Obtiene todos los partidos de fútbol actualmente en vivo o próximos a comenzar
        """
        try:
            # Ligas principales de fútbol
            leagues = [
                "soccer_epl",  # Premier League
                "soccer_spain_la_liga",  # La Liga
                "soccer_germany_bundesliga",  # Bundesliga
                "soccer_italy_serie_a",  # Serie A
                "soccer_france_ligue_one",  # Ligue 1
                "soccer_uefa_champs_league",  # Champions League
                "soccer_uefa_europa_league",  # Europa League
                "soccer_netherlands_eredivisie",  # Eredivisie
                "soccer_portugal_primeira_liga",  # Primeira Liga
                "soccer_brazil_campeonato",  # Brasileirão
                "soccer_argentina_primera_division",  # Primera División
                "soccer_mexico_ligamx",  # Liga MX
                "soccer_usa_mls",  # MLS
            ]
            
            all_matches = []
            now = datetime.now(timezone.utc)
            
            for league in leagues:
                try:
                    url = f"{self.BASE_URL}/sports/{league}/events"
                    params = {
                        "apiKey": self.api_key,
                        "regions": "eu,us",
                        "dateFormat": "iso"
                    }
                    
                    response = await self.client.get(url, params=params)
                    response.raise_for_status()
                    
                    events = response.json()
                    
                    for event in events:
                        commence_time = datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00"))
                        
                        # Considerar en vivo si comenzó hace menos de 3 horas
                        # (duración típica de un partido + tiempo extra)
                        time_diff = (now - commence_time).total_seconds() / 3600
                        
                        if -0.5 <= time_diff <= 3:  # Desde 30 min antes hasta 3 horas después
                            match = LiveMatch(
                                id=event["id"],
                                sport_key=event["sport_key"],
                                sport_title=event["sport_title"],
                                commence_time=commence_time,
                                home_team=event["home_team"],
                                away_team=event["away_team"]
                            )
                            
                            # Marcar como en vivo si ya comenzó
                            if time_diff >= 0:
                                match.is_live = True
                            
                            all_matches.append(match)
                    
                    live_count = len([m for m in all_matches if m.sport_key == league and m.is_live])
                    if live_count > 0:
                        self.logger.info(f"Liga {league}: {live_count} en vivo")
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        self.logger.warning(f"Liga {league} no disponible")
                    else:
                        raise
            
            self.logger.info(f"TOTAL: {len(all_matches)} partidos (en vivo o próximos)")
            return all_matches
            
        except Exception as e:
            self.logger.error(f"Error obteniendo partidos en vivo: {e}")
            return []
    
    async def get_corners_odds(self, match: LiveMatch) -> MatchCornerOdds:
        """
        Obtiene las cuotas de corners para un partido específico
        """
        try:
            url = f"{self.BASE_URL}/sports/{match.sport_key}/events/{match.id}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,us,uk,au",
                "markets": "totals",  # Mercado de corners totales
                "oddsFormat": "decimal",
                "dateFormat": "iso",
                # Mismas 6 casas que el proyecto principal
                "bookmakers": "betsson,pinnacle,marathonbet,codere_it,winamax_fr,winamax_de"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("bookmakers"):
                self.logger.warning(f"No hay cuotas de corners para {match.match_display}")
                return MatchCornerOdds(match=match)
            
            corner_odds = []
            
            for bookmaker_data in data["bookmakers"]:
                bookmaker_key = bookmaker_data["key"]
                
                try:
                    bookmaker = BookmakerType(bookmaker_key)
                except ValueError:
                    continue
                
                for market in bookmaker_data.get("markets", []):
                    if market["key"] != "totals":
                        continue
                    
                    for outcome in market.get("outcomes", []):
                        # Verificar si es un mercado de corners (point debería existir)
                        point = outcome.get("point")
                        if point is None:
                            continue
                        
                        # Nombre del outcome: "Over" o "Under"
                        name = outcome["name"]
                        market_name = f"{name} {point}"
                        
                        odds = CornerOdds(
                            bookmaker=bookmaker,
                            market=market_name,
                            odds=outcome["price"],
                            point=point
                        )
                        corner_odds.append(odds)
            
            self.logger.info(f"Obtenidas {len(corner_odds)} cuotas de corners para {match.match_display}")
            
            return MatchCornerOdds(
                match=match,
                totals_odds=corner_odds
            )
            
        except Exception as e:
            self.logger.error(f"Error obteniendo cuotas de corners para {match.match_display}: {e}")
            return MatchCornerOdds(match=match)
    
    async def get_remaining_requests(self) -> int:
        """Obtiene el número de requests restantes"""
        try:
            url = f"{self.BASE_URL}/sports"
            params = {"apiKey": self.api_key}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            remaining = int(response.headers.get("x-requests-remaining", 0))
            self.logger.info(f"Requests restantes: {remaining}")
            return remaining
            
        except Exception as e:
            self.logger.warning(f"No se pudo obtener quota restante: {e}")
            return 0
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
