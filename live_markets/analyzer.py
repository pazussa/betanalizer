"""
Analizador de mercados en vivo
"""
import logging
from typing import List, Optional
from collections import defaultdict

from models import LiveMatch, MatchMarketOdds, MarketAnalysisResult, MarketOdds, MarketType
from api_client import TheOddsAPIClient


class LiveMarketsAnalyzer:
    """Analizador de mercados en vivo"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_client = TheOddsAPIClient(api_key)
        self.logger = logging.getLogger(__name__)
    
    def _calculate_volatility(self, odds_list: List[float]) -> Optional[float]:
        """Calcula la volatilidad (desviación estándar) de una lista de cuotas"""
        if not odds_list or len(odds_list) < 2:
            return None
        
        try:
            mean = sum(odds_list) / len(odds_list)
            variance = sum((x - mean) ** 2 for x in odds_list) / len(odds_list)
            std_dev = variance ** 0.5
            volatility_pct = (std_dev / mean) * 100 if mean > 0 else 0
            return round(volatility_pct, 2)
        except Exception as e:
            self.logger.warning(f"Error calculando volatilidad: {e}")
            return None
    
    def analyze_market(self, match_odds: MatchMarketOdds) -> List[MarketAnalysisResult]:
        """Analiza las cuotas de un mercado de un partido"""
        if not match_odds.odds_list:
            return []
        
        results = []
        
        # Agrupar cuotas por mercado específico
        markets_dict = defaultdict(list)
        for odds in match_odds.odds_list:
            # Para totals: agrupar por "Over X.X" o "Under X.X"
            # Para btts: agrupar por "Yes" o "No"
            # Para h2h_q1: agrupar por equipo
            key = f"{odds.market_name}"
            if odds.point is not None:
                key = f"{odds.market_name} {odds.point}"
            markets_dict[key].append(odds)
        
        # Analizar cada mercado único
        for market_name, odds_list in markets_dict.items():
            if not odds_list:
                continue
            
            # Obtener la mejor cuota
            best = max(odds_list, key=lambda x: x.odds)
            
            # Calcular margen promedio del mercado
            avg_margin = match_odds.avg_overround_percentage
            
            # Calcular margen del bookmaker específico
            bookmaker_margin = None
            
            # Buscar el par complementario
            if match_odds.market_type == MarketType.TOTALS:
                # Para totals: buscar Over/Under del mismo punto
                is_over = "Over" in market_name
                point = best.point
                opposite_name = f"{'Under' if is_over else 'Over'} {point}"
                
                opposite_odds = [
                    o for o in match_odds.odds_list
                    if o.bookmaker == best.bookmaker and f"{o.market_name} {o.point}" == opposite_name
                ]
                
                if opposite_odds:
                    prob_current = best.implied_probability
                    prob_opposite = opposite_odds[0].implied_probability
                    bookmaker_margin = round((prob_current + prob_opposite - 1) * 100, 2)
            
            elif match_odds.market_type == MarketType.BTTS:
                # Para BTTS: buscar Yes/No
                opposite_name = "No" if market_name == "Yes" else "Yes"
                
                opposite_odds = [
                    o for o in match_odds.odds_list
                    if o.bookmaker == best.bookmaker and o.market_name == opposite_name
                ]
                
                if opposite_odds:
                    prob_current = best.implied_probability
                    prob_opposite = opposite_odds[0].implied_probability
                    bookmaker_margin = round((prob_current + prob_opposite - 1) * 100, 2)
            
            elif match_odds.market_type == MarketType.H2H_Q1:
                # Para H2H Q1: buscar las 3 opciones (Home, Draw, Away)
                bookmaker_odds = [
                    o for o in match_odds.odds_list
                    if o.bookmaker == best.bookmaker
                ]
                
                if len(bookmaker_odds) >= 3:
                    probs = [o.implied_probability for o in bookmaker_odds[:3]]
                    bookmaker_margin = round((sum(probs) - 1) * 100, 2)
            
            # Calcular promedio de cuotas para este mercado específico
            avg_odds = sum(o.odds for o in odds_list) / len(odds_list)
            
            # Calcular volatilidad
            volatility = self._calculate_volatility([o.odds for o in odds_list])
            
            result = MarketAnalysisResult(
                match=match_odds.match,
                market_type=match_odds.market_type,
                market_name=market_name,
                best_odds=best.odds,
                bookmaker=best.bookmaker,
                all_odds=odds_list,
                bookmaker_margin=bookmaker_margin,
                avg_market_margin=round(avg_margin, 2) if avg_margin else None,
                avg_market_odds=round(avg_odds, 4),
                volatility_std=volatility
            )
            
            results.append(result)
        
        return results
    
    async def analyze_all_markets(self, market_types: List[MarketType]) -> dict:
        """Analiza todos los mercados especificados para todos los partidos disponibles"""
        try:
            self.logger.info("Obteniendo partidos...")
            live_matches = await self.api_client.get_live_matches()
            
            if not live_matches:
                self.logger.warning("No hay partidos disponibles")
                return {market_type: [] for market_type in market_types}
            
            self.logger.info(f"Encontrados {len(live_matches)} partidos disponibles")
            
            # Resultados por tipo de mercado
            results_by_market = {market_type: [] for market_type in market_types}
            
            for match in live_matches:
                self.logger.info(f"Analizando {match.match_display}...")
                
                for market_type in market_types:
                    # Obtener cuotas del mercado
                    match_odds = await self.api_client.get_market_odds(match, market_type)
                    
                    if not match_odds.odds_list:
                        continue
                    
                    # Analizar mercado
                    results = self.analyze_market(match_odds)
                    results_by_market[market_type].extend(results)
            
            # Ordenar resultados por Score_Final
            for market_type in market_types:
                results_by_market[market_type].sort(
                    key=lambda x: x.final_score if x.final_score is not None else -999999,
                    reverse=True
                )
            
            # Log resumen
            for market_type, results in results_by_market.items():
                unique_matches = len(set(r.match.id for r in results))
                self.logger.info(
                    f"{market_type.value}: {unique_matches} partidos, {len(results)} mercados analizados"
                )
            
            return results_by_market
            
        except Exception as e:
            self.logger.error(f"Error en análisis: {e}")
            raise
    
    async def cleanup(self):
        """Limpia recursos"""
        await self.api_client.close()
