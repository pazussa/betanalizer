import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
import httpx
from ..models import (
    Match, OddsData, H2HOdds, BookmakerType, 
    MarketType, APIError
)

logger = logging.getLogger(__name__)


class OddsAPIIOClient:
    """
    Cliente para Odds-API.io
    Documentación: https://docs.odds-api.io/
    """
    
    def __init__(self):
        self.api_key = os.getenv("ODDS_API_IO_KEY")
        self.enabled = bool(self.api_key and self.api_key != "your_api_key_here")
        
        if not self.enabled:
            logger.warning("ODDS_API_IO_KEY no configurada - funcionalidad de Bwin deshabilitada")
        
        self.base_url = "https://api.odds-api.io/v3"
        self.logger = logging.getLogger(__name__)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_bwin_odds(self, match: Match) -> Tuple[List[OddsData], List[H2HOdds]]:
        """
        Obtiene cuotas de Bwin para un partido específico
        
        Args:
            match: Partido para buscar cuotas
            
        Returns:
            Tupla de (odds_data, h2h_odds) para Bwin
        """
        # Si no está habilitado, devolver vacío
        if not self.enabled:
            return [], []
        
        try:
            # Primero obtener eventos de football
            events_url = f"{self.base_url}/events"
            params = {
                'apiKey': self.api_key,
                'sport': 'football',
                'limit': 100
            }
            
            self.logger.info(f"Obteniendo eventos de Odds-API.io para buscar: {match.home_team} vs {match.away_team}")
            
            response = await self.client.get(events_url, params=params)
            response.raise_for_status()
            
            events = response.json()
            
            # Buscar el evento que corresponde a nuestro partido
            event_id = None
            for event in events:
                if self._match_teams(event, match.home_team, match.away_team):
                    event_id = event.get('id')
                    self.logger.info(f"Evento encontrado: ID {event_id}")
                    break
            
            if not event_id:
                self.logger.warning(f"No se encontró evento para {match.home_team} vs {match.away_team}")
                return [], []
            
            # Obtener cuotas para el evento específico con Bwin
            odds_url = f"{self.base_url}/odds"
            odds_params = {
                'apiKey': self.api_key,
                'eventId': event_id,
                'bookmakers': 'Bwin'
            }
            
            self.logger.info(f"Obteniendo cuotas de Bwin para evento ID {event_id}")
            
            odds_response = await self.client.get(odds_url, params=odds_params)
            odds_response.raise_for_status()
            
            odds_data_list = []
            h2h_odds_list = []
            
            odds_json = odds_response.json()
            
            # Log de bookmakers disponibles
            if 'bookmakers' in odds_json:
                available_bookmakers = list(odds_json['bookmakers'].keys())
                self.logger.info(f"Bookmakers disponibles para evento {event_id}: {available_bookmakers}")
            else:
                self.logger.warning(f"No hay bookmakers en la respuesta para evento {event_id}")
            
            # Verificar si hay bookmakers
            if 'bookmakers' in odds_json and 'Bwin' in odds_json['bookmakers']:
                bwin_markets = odds_json['bookmakers']['Bwin']
                
                # Buscar el mercado ML (1X2)
                for market in bwin_markets:
                    if market.get('name') == 'ML' and 'odds' in market and len(market['odds']) > 0:
                        odds = market['odds'][0]
                        
                        home_odds = float(odds.get('home', 0))
                        draw_odds = float(odds.get('draw', 0))
                        away_odds = float(odds.get('away', 0))
                        
                        if home_odds > 0 and draw_odds > 0 and away_odds > 0:
                            # Crear H2HOdds con timestamp
                            h2h_odds_obj = H2HOdds(
                                bookmaker=BookmakerType.BWIN,
                                home_odds=home_odds,
                                draw_odds=draw_odds,
                                away_odds=away_odds,
                                timestamp=datetime.now(timezone.utc)
                            )
                            h2h_odds_list.append(h2h_odds_obj)
                            
                            # Calcular cuotas de doble oportunidad
                            # 1X = Local o Empate
                            odds_1x = 1.0 / ((1.0 / home_odds) + (1.0 / draw_odds))
                            odds_data_list.append(OddsData(
                                bookmaker=BookmakerType.BWIN,
                                market=MarketType.DOUBLE_CHANCE_1X,
                                odds=round(odds_1x, 4),
                                timestamp=datetime.now(timezone.utc)
                            ))
                            
                            # X2 = Empate o Visitante
                            odds_x2 = 1.0 / ((1.0 / draw_odds) + (1.0 / away_odds))
                            odds_data_list.append(OddsData(
                                bookmaker=BookmakerType.BWIN,
                                market=MarketType.DOUBLE_CHANCE_X2,
                                odds=round(odds_x2, 4),
                                timestamp=datetime.now(timezone.utc)
                            ))
                            
                            self.logger.info(f"Cuotas Bwin encontradas: 1={home_odds}, X={draw_odds}, 2={away_odds}")
                            break
                
                if not odds_data_list:
                    self.logger.warning(f"Mercado Moneyline no encontrado en Bwin para evento {event_id}")
            else:
                self.logger.warning(f"Bwin no tiene cuotas disponibles para evento {event_id}")
            
            if not odds_data_list:
                self.logger.warning(f"No se encontraron cuotas de Bwin para {match.home_team} vs {match.away_team}")
            
            return odds_data_list, h2h_odds_list
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Error HTTP obteniendo cuotas de Bwin: {e.response.status_code}")
            return [], []
        except Exception as e:
            self.logger.error(f"Error obteniendo cuotas de Bwin: {e}")
            return [], []
    
    def _match_teams(self, event: Dict, home_team: str, away_team: str) -> bool:
        """
        Intenta emparejar un evento con los nombres de equipos
        
        Args:
            event: Evento de la API
            home_team: Nombre del equipo local
            away_team: Nombre del equipo visitante
            
        Returns:
            True si coincide, False en caso contrario
        """
        try:
            event_home = event.get('home', '').lower()
            event_away = event.get('away', '').lower()
            
            home_match = home_team.lower() in event_home or event_home in home_team.lower()
            away_match = away_team.lower() in event_away or event_away in away_team.lower()
            
            return home_match and away_match
        except:
            return False
    
    async def close(self):
        """Cierra la conexión HTTP"""
        await self.client.aclose()
