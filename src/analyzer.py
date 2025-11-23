import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
from .models import (
    Match, MatchOdds, OddsData, AnalysisResult, 
    MarketType, ValidationError
)
from .apis.the_odds_api import TheOddsAPIClient
from .apis.odds_api_io import OddsAPIIOClient


class FootballOddsAnalyzer:
    """
    Motor principal de análisis de cuotas de fútbol
    Garantiza datos verídicos mediante APIs oficiales
    """
    
    def __init__(self):
        self.odds_client = TheOddsAPIClient()
        self.bwin_client = OddsAPIIOClient()
        self.logger = logging.getLogger(__name__)
        
        # Configuración por defecto
        self.min_probability = 0.7
        self.min_odds = 1.30
    
    async def get_upcoming_matches(self, hours_ahead: int = 168) -> List[Match]:
        """
        Obtiene partidos próximos de múltiples fuentes oficiales
        
        Args:
            hours_ahead: Horas hacia adelante para buscar partidos (por defecto 168 = 7 días)
            
        Returns:
            Lista combinada de partidos de todas las fuentes
        """
        try:
            # Obtener partidos SOLO de The Odds API (datos 100% reales)
            all_matches = await self.odds_client.get_football_matches()
            
            # Filtrar partidos por tiempo
            cutoff_time = datetime.now(timezone.utc) + timedelta(hours=hours_ahead)
            upcoming_matches = [
                match for match in all_matches
                if match.kickoff_time <= cutoff_time and 
                   match.kickoff_time > datetime.now(timezone.utc)
            ]
            
            self.logger.info(f"Encontrados {len(upcoming_matches)} partidos reales en {hours_ahead} horas")
            return upcoming_matches
            
        except Exception as e:
            self.logger.error(f"Error obteniendo partidos de The Odds API: {e}")
            raise ValidationError(f"No se pudieron obtener partidos: {e}")
    
    async def get_match_odds_data(self, match: Match) -> MatchOdds:
        """
        Obtiene cuotas completas para un partido específico
        
        Args:
            match: Partido para obtener cuotas
            
        Returns:
            Cuotas organizadas por mercado
        """
        try:
            # Obtener cuotas del proveedor principal con sport_key correcto
            sport_key = getattr(match, 'sport_key', 'soccer_epl')  # Usar sport_key del match
            odds_data, h2h_odds = await self.odds_client.get_match_odds(match.id, sport_key)
            
            # Intentar obtener cuotas de Bwin desde Odds-API.io
            try:
                bwin_odds_data, bwin_h2h_odds = await self.bwin_client.get_bwin_odds(match)
                
                if bwin_odds_data:
                    odds_data.extend(bwin_odds_data)
                    h2h_odds.extend(bwin_h2h_odds)
                    self.logger.info(f"Cuotas de Bwin agregadas para {match.home_team} vs {match.away_team}")
                    
            except Exception as bwin_error:
                self.logger.warning(f"Error obteniendo cuotas de Bwin: {bwin_error}")
            
            # Organizar por mercado
            odds_1x = [odds for odds in odds_data if odds.market == MarketType.DOUBLE_CHANCE_1X]
            odds_x2 = [odds for odds in odds_data if odds.market == MarketType.DOUBLE_CHANCE_X2]
            
            match_odds = MatchOdds(
                match=match,
                odds_1x=odds_1x,
                odds_x2=odds_x2,
                odds_h2h=h2h_odds
            )
            
            self.logger.debug(f"Obtenidas cuotas para {match}: 1X={len(odds_1x)}, X2={len(odds_x2)}, H2H={len(h2h_odds)}")
            return match_odds
            
        except Exception as e:
            self.logger.warning(f"No se pudieron obtener cuotas para {match}: {e}")
            # Devolver estructura vacía en caso de error
            return MatchOdds(match=match, odds_1x=[], odds_x2=[], odds_h2h=[])
    
    def analyze_match_odds(
        self, 
        match_odds: MatchOdds,
        min_probability: Optional[float] = None,
        min_odds: Optional[float] = None
    ) -> List[AnalysisResult]:
        """
        Analiza las cuotas de un partido aplicando criterios de filtrado
        
        Args:
            match_odds: Cuotas del partido
            min_probability: Probabilidad mínima requerida
            min_odds: Cuota mínima requerida
            
        Returns:
            Lista de resultados de análisis
        """
        min_prob = min_probability or self.min_probability
        min_odds_threshold = min_odds or self.min_odds
        
        results = []
        
        # Calcular margen promedio del mercado H2H (base para todos los mercados derivados)
        avg_margin = match_odds.avg_overround_percentage if match_odds.odds_h2h else None
        
        # Analizar mercado 1X
        best_1x = match_odds.best_1x_odds
        if best_1x:
            implied_prob = best_1x.implied_probability
            # Calcular sin filtros booleanos - rankear por Score_Final
            meets_criteria = True  # Siempre True, el ranking se hace por score
            
            # Encontrar el margen del bookmaker específico que ofrece la mejor cuota 1X
            bookmaker_margin = None
            if match_odds.odds_h2h:
                bookmaker_h2h = next(
                    (h for h in match_odds.odds_h2h if h.bookmaker == best_1x.bookmaker),
                    None
                )
                if bookmaker_h2h:
                    bookmaker_margin = round(bookmaker_h2h.overround_percentage, 2)
            
            result = AnalysisResult(
                match=match_odds.match,
                market=MarketType.DOUBLE_CHANCE_1X,
                best_odds=best_1x.odds,
                implied_probability=round(implied_prob, 3),
                bookmaker=best_1x.bookmaker,
                meets_criteria=meets_criteria,
                min_prob_threshold=min_prob,
                min_odds_threshold=min_odds_threshold,
                bookmaker_margin=bookmaker_margin,
                avg_market_margin=round(avg_margin, 2) if avg_margin else None,
                avg_market_odds=round(match_odds.avg_1x_odds, 4) if match_odds.avg_1x_odds > 0 else None,
                match_odds=match_odds
            )
            results.append(result)
        
        # Analizar mercado X2
        best_x2 = match_odds.best_x2_odds
        if best_x2:
            implied_prob = best_x2.implied_probability
            # Calcular sin filtros booleanos - rankear por Score_Final
            meets_criteria = True  # Siempre True, el ranking se hace por score
            
            # Encontrar el margen del bookmaker específico que ofrece la mejor cuota X2
            bookmaker_margin = None
            if match_odds.odds_h2h:
                bookmaker_h2h = next(
                    (h for h in match_odds.odds_h2h if h.bookmaker == best_x2.bookmaker),
                    None
                )
                if bookmaker_h2h:
                    bookmaker_margin = round(bookmaker_h2h.overround_percentage, 2)
            
            result = AnalysisResult(
                match=match_odds.match,
                market=MarketType.DOUBLE_CHANCE_X2,
                best_odds=best_x2.odds,
                implied_probability=round(implied_prob, 3),
                bookmaker=best_x2.bookmaker,
                meets_criteria=meets_criteria,
                min_prob_threshold=min_prob,
                min_odds_threshold=min_odds_threshold,
                bookmaker_margin=bookmaker_margin,
                avg_market_margin=round(avg_margin, 2) if avg_margin else None,
                avg_market_odds=round(match_odds.avg_x2_odds, 4) if match_odds.avg_x2_odds > 0 else None,
                match_odds=match_odds
            )
            results.append(result)
        
        return results
    
    async def analyze_all_matches(
        self,
        min_probability: float = 0.7,
        min_odds: float = 1.30,
        hours_ahead: int = 168,
        prioritize_near_matches: bool = True
    ) -> List[AnalysisResult]:
        """
        Realiza análisis completo de todos los partidos disponibles
        
        Args:
            min_probability: Probabilidad implícita mínima
            min_odds: Cuota mínima
            hours_ahead: Horas hacia adelante para buscar partidos (por defecto 168 = 7 días)
            prioritize_near_matches: Si True, prioriza partidos cercanos (próximas 72h) donde hay más probabilidad de cuotas
            
        Returns:
            Lista completa de análisis ordenada por partido
        """
        try:
            self.logger.info("Iniciando análisis completo de partidos")
            
            # 1. Obtener partidos próximos
            matches = await self.get_upcoming_matches(hours_ahead)
            if not matches:
                self.logger.warning("No se encontraron partidos para analizar")
                return []
            
            # 2. Priorizar partidos cercanos (optimización para reducir 404s)
            if prioritize_near_matches:
                now = datetime.now(timezone.utc)
                priority_cutoff = now + timedelta(hours=72)  # Próximas 72 horas
                
                # Separar en partidos cercanos y lejanos
                near_matches = [m for m in matches if m.kickoff_time <= priority_cutoff]
                far_matches = [m for m in matches if m.kickoff_time > priority_cutoff]
                
                # Ordenar cercanos por tiempo (más cercanos primero)
                near_matches.sort(key=lambda m: m.kickoff_time)
                
                self.logger.info(f"Priorizando {len(near_matches)} partidos cercanos (<72h), {len(far_matches)} lejanos")
                matches = near_matches + far_matches  # Procesar cercanos primero
            
            # 3. Obtener cuotas para cada partido
            all_results = []
            successful_odds = 0
            no_odds_available = 0
            
            for i, match in enumerate(matches, 1):
                try:
                    match_odds = await self.get_match_odds_data(match)
                    
                    # Si hay cuotas disponibles, analizar
                    if match_odds.odds_1x or match_odds.odds_x2:
                        match_results = self.analyze_match_odds(
                            match_odds, min_probability, min_odds
                        )
                        all_results.extend(match_results)
                        successful_odds += 1
                    else:
                        no_odds_available += 1
                    
                    # Log progreso cada 10 partidos
                    if i % 10 == 0:
                        self.logger.info(f"Progreso: {i}/{len(matches)} partidos - {successful_odds} con cuotas, {no_odds_available} sin cuotas")
                    
                    # Rate limiting - pausa pequeña entre requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Error analizando {match}: {e}")
                    continue
            
            # Resumen final
            self.logger.info(
                f"Análisis completado: {successful_odds} partidos con cuotas, "
                f"{no_odds_available} sin cuotas disponibles, "
                f"{len(all_results)} mercados analizados"
            )
            
            # 4. Ordenar resultados
            all_results.sort(key=lambda x: (
                x.match.kickoff_time,
                x.match.home_team,
                x.market.value
            ))
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Error en análisis completo: {e}")
            raise ValidationError(f"Error en análisis: {e}")
    
    async def validate_api_connections(self) -> Dict[str, bool]:
        """
        Valida que todas las conexiones API estén funcionando
        
        Returns:
            Estado de cada API
        """
        status = {}
        
        # Validar The Odds API (UNICA fuente de datos reales)
        try:
            remaining = await self.odds_client.get_remaining_requests()
            status["the_odds_api"] = remaining > 0
            self.logger.info(f"The Odds API: OK (requests restantes: {remaining})")
        except Exception as e:
            status["the_odds_api"] = False
            self.logger.error(f"The Odds API: ERROR - {e}")
            raise ValidationError("The Odds API no está disponible. No se puede continuar sin datos reales.")
        
        return status
    
    async def cleanup(self):
        """Cierra conexiones y limpia recursos"""
        try:
            # Obtener requests restantes antes de cerrar
            remaining = await self.odds_client.get_remaining_requests()
            await self.odds_client.close()
            await self.bwin_client.close()
            
            self.logger.info("Conexiones cerradas correctamente")
            return remaining
        except Exception as e:
            self.logger.error(f"Error cerrando conexiones: {e}")
            return None