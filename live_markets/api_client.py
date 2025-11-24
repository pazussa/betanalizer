"""
Cliente API para The Odds API - Múltiples mercados en vivo
"""
import os
import httpx
import logging
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from models import LiveMatch, MatchMarketOdds, MarketOdds, BookmakerType, MarketType


class TheOddsAPIClient:
    """Cliente para The Odds API"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("THE_ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("THE_ODDS_API_KEY es requerida")
        
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "LiveMarketsAnalyzer/1.0"}
        )
        
        self.logger = logging.getLogger(__name__)
    
    async def get_remaining_requests(self) -> int:
        """Obtiene requests restantes del API"""
        try:
            url = f"{self.BASE_URL}/sports"
            params = {"apiKey": self.api_key}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            remaining = int(response.headers.get("x-requests-remaining", 0))
            self.logger.info(f"Requests restantes: {remaining}")
            return remaining
            
        except Exception as e:
            self.logger.error(f"Error obteniendo requests restantes: {e}")
            return 0
    
    async def get_live_matches(self) -> List[LiveMatch]:
        """Obtiene todos los partidos de fútbol actualmente en vivo o próximos a comenzar"""
        try:
            leagues = [
                "soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga",
                "soccer_italy_serie_a", "soccer_france_ligue_one",
                "soccer_uefa_champs_league", "soccer_uefa_europa_league",
                "soccer_netherlands_eredivisie", "soccer_portugal_primeira_liga",
                "soccer_brazil_campeonato", "soccer_argentina_primera_division",
                "soccer_chile_primera_division", "soccer_colombia_primera_a",
                "soccer_mexico_ligamx", "soccer_usa_mls"
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
                        time_diff = (now - commence_time).total_seconds() / 3600
                        
                        # Incluir todos los partidos de los próximos 10 días (240 horas)
                        if time_diff <= 240:
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
                    upcoming_count = len([m for m in all_matches if m.sport_key == league and not m.is_live])
                    if live_count > 0 or upcoming_count > 0:
                        self.logger.info(f"Liga {league}: {live_count} en vivo, {upcoming_count} próximos")
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        self.logger.warning(f"Liga {league} no disponible")
                    else:
                        raise
            
            self.logger.info(f"TOTAL: {len(all_matches)} partidos ({len([m for m in all_matches if m.is_live])} en vivo, {len([m for m in all_matches if not m.is_live])} próximos)")
            return all_matches
            
        except Exception as e:
            self.logger.error(f"Error obteniendo partidos en vivo: {e}")
            return []
    
    async def get_market_odds(self, match: LiveMatch, market_type: MarketType) -> MatchMarketOdds:
        """Obtiene las cuotas de un mercado específico para un partido"""
        try:
            url = f"{self.BASE_URL}/sports/{match.sport_key}/events/{match.id}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,us,uk,au",
                "markets": market_type.value,
                "oddsFormat": "decimal",
                "dateFormat": "iso",
                "bookmakers": "betsson,pinnacle,marathonbet,codere_it,winamax_fr,winamax_de"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            odds_list = []
            
            if "bookmakers" in data:
                for bookmaker_data in data["bookmakers"]:
                    bookmaker_key = bookmaker_data["key"]
                    
                    try:
                        bookmaker_enum = BookmakerType(bookmaker_key)
                    except ValueError:
                        continue
                    
                    for market_data in bookmaker_data.get("markets", []):
                        if market_data["key"] != market_type.value:
                            continue
                        
                        for outcome in market_data.get("outcomes", []):
                            market_odds = MarketOdds(
                                bookmaker=bookmaker_enum,
                                market_name=outcome["name"],
                                odds=outcome["price"],
                                point=outcome.get("point")
                            )
                            odds_list.append(market_odds)
            
            self.logger.info(f"Obtenidas {len(odds_list)} cuotas de {market_type.value} para {match.match_display}")
            
            return MatchMarketOdds(
                match=match,
                market_type=market_type,
                odds_list=odds_list
            )
            
        except Exception as e:
            self.logger.error(f"Error obteniendo cuotas de {market_type.value} para {match.match_display}: {e}")
            return MatchMarketOdds(match=match, market_type=market_type, odds_list=[])
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
