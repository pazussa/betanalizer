import os
import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential
from ..models import Match, OddsData, MarketType, BookmakerType, APIError, H2HOdds


class TheOddsAPIClient:
    """
    Cliente para The Odds API - Fuente oficial de cuotas deportivas
    Documentación: https://the-odds-api.com/
    """
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("THE_ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("THE_ODDS_API_KEY es requerida")
        
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "FootballBettingAnalyzer/1.0"}
        )
        
        self.logger = logging.getLogger(__name__)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get_football_matches(self, regions: str = "eu,us") -> List[Match]:
        """
        Obtiene partidos de fútbol de TODAS las ligas disponibles
        
        Args:
            regions: Regiones para obtener cuotas (eu=Europa, us=Estados Unidos)
            
        Returns:
            Lista de partidos disponibles de múltiples ligas
        """
        all_matches = []
        
        # Lista de ligas de fútbol disponibles en The Odds API
        soccer_leagues = [
            ("soccer_epl", "Premier League", "England"),
            ("soccer_spain_la_liga", "La Liga", "Spain"),
            ("soccer_germany_bundesliga", "Bundesliga", "Germany"),
            ("soccer_italy_serie_a", "Serie A", "Italy"),
            ("soccer_france_ligue_one", "Ligue 1", "France"),
            ("soccer_uefa_champs_league", "Champions League", "Europe"),
            ("soccer_uefa_europa_league", "Europa League", "Europe"),
            ("soccer_netherlands_eredivisie", "Eredivisie", "Netherlands"),
            ("soccer_portugal_primeira_liga", "Primeira Liga", "Portugal"),
            ("soccer_brazil_campeonato", "Brasileirão", "Brazil"),
            ("soccer_argentina_primera_division", "Primera División", "Argentina"),
            ("soccer_chile_primera_division", "Primera División Chile", "Chile"),
            ("soccer_colombia_primera_a", "Liga Colombia", "Colombia"),
            ("soccer_mexico_ligamx", "Liga MX", "Mexico"),
            ("soccer_usa_mls", "MLS", "USA")
        ]
        
        for sport_key, league_name, country in soccer_leagues:
            try:
                url = f"{self.BASE_URL}/sports/{sport_key}/events"
                params = {
                    "apiKey": self.api_key,
                    "regions": regions,
                    "dateFormat": "iso"
                }
                
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                league_matches = []
                
                for event in data:
                    match = Match(
                        id=event["id"],
                        home_team=event["home_team"],
                        away_team=event["away_team"],
                        league=league_name,
                        country=country,
                        kickoff_time=datetime.fromisoformat(
                            event["commence_time"].replace("Z", "+00:00")
                        ),
                        sport_key=sport_key
                    )
                    league_matches.append(match)
                
                all_matches.extend(league_matches)
                self.logger.info(f"Obtenidos {len(league_matches)} partidos de {league_name}")
                
                # Pausa pequeña entre requests para respetar rate limits
                await asyncio.sleep(0.2)
                
            except Exception as e:
                self.logger.warning(f"No se pudieron obtener partidos de {league_name}: {e}")
                continue
        
        self.logger.info(f"TOTAL: {len(all_matches)} partidos de todas las ligas")
        return all_matches
    
    async def get_match_odds(self, match_id: str, sport_key: str = "soccer_epl") -> Tuple[List[OddsData], List[H2HOdds]]:
        """
        Obtiene cuotas para un partido específico
        
        Args:
            match_id: ID del partido
            sport_key: Clave de la liga/deporte (ej: soccer_epl, soccer_spain_la_liga)
            
        Returns:
            Tupla con (lista de cuotas doble chance, lista de cuotas H2H para margen)
        """
        try:
            url = f"{self.BASE_URL}/sports/{sport_key}/events/{match_id}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,us,uk,au",
                "markets": "h2h",  # Head to head (1X2)
                "oddsFormat": "decimal",
                "dateFormat": "iso",
                "bookmakers": "betsson,pinnacle,marathonbet,codere_it,winamax_fr,winamax_de"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            all_odds = []
            h2h_odds = []
            
            # Procesar cuotas de cada bookmaker
            for bookmaker_data in data.get("bookmakers", []):
                bookmaker_name = bookmaker_data["key"]
                
                # Casas de apuestas permitidas
                restricted_bookmakers = {
                    "betsson": BookmakerType.BETSSON,
                    "pinnacle": BookmakerType.PINNACLE,
                    "marathonbet": BookmakerType.MARATHONBET,
                    "codere_it": BookmakerType.CODERE_IT,
                    "winamax_fr": BookmakerType.WINAMAX,
                    "winamax_de": BookmakerType.WINAMAX_DE
                }
                
                if bookmaker_name not in restricted_bookmakers:
                    continue
                
                bookmaker_enum = restricted_bookmakers[bookmaker_name]
                
                for market_data in bookmaker_data.get("markets", []):
                    if market_data["key"] != "h2h":
                        continue
                    
                    outcomes = market_data["outcomes"]
                    timestamp = datetime.fromisoformat(
                        market_data["last_update"].replace("Z", "+00:00")
                    )
                    
                    # Extraer cuotas para calcular doble oportunidad
                    home_odds = next(
                        (o["price"] for o in outcomes if o["name"] == data["home_team"]), 
                        None
                    )
                    draw_odds = next(
                        (o["price"] for o in outcomes if o["name"] == "Draw"), 
                        None
                    )
                    away_odds = next(
                        (o["price"] for o in outcomes if o["name"] == data["away_team"]), 
                        None
                    )
                    
                    # Guardar cuotas H2H para cálculo de margen
                    if home_odds and draw_odds and away_odds:
                        h2h_odds.append(H2HOdds(
                            bookmaker=bookmaker_enum,
                            home_odds=home_odds,
                            draw_odds=draw_odds,
                            away_odds=away_odds,
                            timestamp=timestamp
                        ))
                    
                    # Calcular cuotas de doble oportunidad
                    if home_odds and draw_odds:
                        # 1X = 1/(1/home + 1/draw)
                        prob_1x = (1/home_odds) + (1/draw_odds)
                        odds_1x = 1 / prob_1x
                        
                        all_odds.append(OddsData(
                            bookmaker=bookmaker_enum,
                            market=MarketType.DOUBLE_CHANCE_1X,
                            odds=round(odds_1x, 2),
                            timestamp=timestamp
                        ))
                    
                    if draw_odds and away_odds:
                        # X2 = 1/(1/draw + 1/away)
                        prob_x2 = (1/draw_odds) + (1/away_odds)
                        odds_x2 = 1 / prob_x2
                        
                        all_odds.append(OddsData(
                            bookmaker=bookmaker_enum,
                            market=MarketType.DOUBLE_CHANCE_X2,
                            odds=round(odds_x2, 2),
                            timestamp=timestamp
                        ))
            
            self.logger.info(f"Obtenidas {len(all_odds)} cuotas para match {match_id}")
            return all_odds, h2h_odds
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # 404 = cuotas no disponibles aún (normal para partidos futuros)
                self.logger.debug(f"Cuotas no disponibles para match {match_id} (404)")
                return [], []  # Retornar vacío, no es un error
            else:
                # Otros errores HTTP son problemáticos
                self.logger.error(f"Error HTTP {e.response.status_code} obteniendo cuotas para {match_id}")
                raise APIError(f"Error al obtener cuotas: {e}")
        except Exception as e:
            self.logger.error(f"Error procesando cuotas: {e}")
            raise APIError(f"Error procesando cuotas: {e}")
    
    async def get_remaining_requests(self) -> int:
        """Obtiene el número de requests restantes en tu quota"""
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