"""
Analizador de cuotas de corners en vivo
"""
import logging
from typing import List, Optional
from collections import defaultdict

from models import LiveMatch, MatchCornerOdds, CornersAnalysisResult, CornerOdds
from api_client import TheOddsAPIClient


class CornersAnalyzer:
    """Analizador de mercados de corners en vivo"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_client = TheOddsAPIClient(api_key)
        self.logger = logging.getLogger(__name__)
    
    def _calculate_volatility(self, odds_list: List[float]) -> Optional[float]:
        """
        Calcula la volatilidad (desviación estándar) de una lista de cuotas
        """
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
    
    def analyze_corners_market(self, match_odds: MatchCornerOdds) -> List[CornersAnalysisResult]:
        """
        Analiza las cuotas de corners de un partido
        """
        if not match_odds.totals_odds:
            return []
        
        results = []
        
        # Agrupar cuotas por mercado (Over/Under + punto)
        markets_dict = defaultdict(list)
        for odds in match_odds.totals_odds:
            markets_dict[odds.market].append(odds)
        
        # Analizar cada mercado único
        for market_name, odds_list in markets_dict.items():
            if not odds_list:
                continue
            
            # Obtener la mejor cuota
            best = max(odds_list, key=lambda x: x.odds)
            
            # Calcular margen promedio del mercado
            avg_margin = match_odds.avg_overround_percentage
            
            # Calcular margen del bookmaker específico
            # Para esto necesitamos encontrar el par Over/Under del mismo bookmaker Y mismo punto
            bookmaker_margin = None
            
            # Determinar si es Over o Under y extraer el punto
            is_over = "over" in market_name.lower()
            point = best.point
            
            # Buscar el mercado complementario (Over <-> Under) con el mismo punto
            opposite_market = f"{'Under' if is_over else 'Over'} {point}"
            
            # Buscar la cuota del mismo bookmaker en el mercado complementario
            opposite_odds = [
                o for o in match_odds.totals_odds 
                if o.bookmaker == best.bookmaker and o.market == opposite_market
            ]
            
            if opposite_odds:
                # Calcular margen: (prob_over + prob_under - 1) * 100
                prob_current = best.implied_probability
                prob_opposite = opposite_odds[0].implied_probability
                bookmaker_margin = round((prob_current + prob_opposite - 1) * 100, 2)
            
            # Calcular promedio de cuotas para este mercado específico
            avg_odds = sum(o.odds for o in odds_list) / len(odds_list)
            
            # Calcular volatilidad
            volatility = self._calculate_volatility([o.odds for o in odds_list])
            
            result = CornersAnalysisResult(
                match=match_odds.match,
                market=market_name,
                best_odds=best.odds,
                bookmaker=best.bookmaker,
                all_odds=odds_list,  # Incluir todas las cuotas
                bookmaker_margin=bookmaker_margin,
                avg_market_margin=round(avg_margin, 2) if avg_margin else None,
                avg_market_odds=round(avg_odds, 4),
                volatility_std=volatility
            )
            
            results.append(result)
        
        return results
    
    async def analyze_all_live_matches(self) -> List[CornersAnalysisResult]:
        """
        Analiza todos los partidos en vivo y sus mercados de corners
        """
        try:
            self.logger.info("Obteniendo partidos en vivo...")
            live_matches = await self.api_client.get_live_matches()
            
            if not live_matches:
                self.logger.warning("No hay partidos en vivo")
                return []
            
            self.logger.info(f"Encontrados {len(live_matches)} partidos en vivo")
            
            all_results = []
            matches_with_corners = 0
            
            for match in live_matches:
                self.logger.info(f"Analizando {match.match_display}...")
                
                # Obtener cuotas de corners
                match_odds = await self.api_client.get_corners_odds(match)
                
                if not match_odds.totals_odds:
                    continue
                
                matches_with_corners += 1
                
                # Analizar mercados
                results = self.analyze_corners_market(match_odds)
                all_results.extend(results)
            
            self.logger.info(
                f"Análisis completado: {matches_with_corners} partidos con corners, "
                f"{len(all_results)} mercados analizados"
            )
            
            # Ordenar por Score_Final descendente
            all_results.sort(
                key=lambda x: x.final_score if x.final_score is not None else -999999,
                reverse=True
            )
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Error en análisis: {e}")
            raise
    
    async def cleanup(self):
        """Limpia recursos"""
        await self.api_client.close()
