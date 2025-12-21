import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
from tqdm import tqdm
from .models import (
    Match, MatchOdds, OddsData, AnalysisResult, 
    MarketType, ValidationError
)
from .apis.the_odds_api import TheOddsAPIClient
from .apis.odds_api_io import OddsAPIIOClient
from .disagreement import bookmaker_disagreement


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
    
    async def get_upcoming_matches(self, hours_ahead: int = 168, hours_from: int = 0) -> List[Match]:
        """
        Obtiene partidos próximos de múltiples fuentes oficiales
        
        Args:
            hours_ahead: Horas hacia adelante para buscar partidos (por defecto 168 = 7 días)
            hours_from: Horas desde ahora para comenzar a buscar (por defecto 0)
            
        Returns:
            Lista combinada de partidos de todas las fuentes
        """
        try:
            # Obtener partidos SOLO de The Odds API (datos 100% reales)
            all_matches = await self.odds_client.get_football_matches()
            
            # Filtrar partidos por tiempo
            now = datetime.now(timezone.utc)
            start_time = now + timedelta(hours=hours_from)
            cutoff_time = now + timedelta(hours=hours_ahead)
            
            upcoming_matches = [
                match for match in all_matches
                if start_time <= match.kickoff_time <= cutoff_time
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
    
    async def analyze_additional_markets(self, match: Match) -> List[AnalysisResult]:
        """
        Analiza los mercados adicionales (TOTALS) para un partido
        
        Args:
            match: Partido para analizar
            
        Returns:
            Lista de resultados de análisis para mercados adicionales
        """
        results = []
        sport_key = getattr(match, 'sport_key', 'soccer_epl')
        
        # Analizar TOTALS (Over/Under)
        try:
            totals_data = await self.odds_client.get_market_odds(match.id, sport_key, "totals")
            totals_results = self._analyze_grouped_market(match, totals_data, MarketType.TOTALS)
            results.extend(totals_results)
        except Exception as e:
            self.logger.warning(f"Error analizando TOTALS para {match}: {e}")
        
        return results
    
    def _analyze_grouped_market(self, match: Match, odds_data: List[Dict], market_type: MarketType) -> List[AnalysisResult]:
        """
        Analiza cuotas agrupadas por mercado específico (ej: Over 2.5, Under 2.5, Yes, No, etc.)
        
        Args:
            match: Partido
            odds_data: Datos de cuotas
            market_type: Tipo de mercado
            
        Returns:
            Lista de resultados
        """
        if not odds_data:
            return []
        
        results = []
        
        # Agrupar por market_name y point
        from collections import defaultdict
        markets_dict = defaultdict(list)
        
        for odds_info in odds_data:
            key = odds_info["market_name"]
            if odds_info.get("point"):
                key = f"{odds_info['market_name']} {odds_info['point']}"
            markets_dict[key].append(odds_info)
        
        # Analizar cada mercado único
        for market_name, odds_list in markets_dict.items():
            if not odds_list or len(odds_list) <= 1:
                continue
            
            # Filtrar mercados con menos de 2 casas de apuestas
            bookmakers_count = len(set(o["bookmaker"] for o in odds_list))
            if bookmakers_count < 2:
                continue
            
            # Obtener la mejor cuota
            best = max(odds_list, key=lambda x: x["odds"])
            
            # Calcular promedio de cuotas
            avg_odds = sum(o["odds"] for o in odds_list) / len(odds_list) if odds_list else 0
            
            # Calcular volatilidad
            volatility = self._calculate_volatility([o["odds"] for o in odds_list])
            
            # Calcular margen del bookmaker y promedio del mercado
            bookmaker_margin = None
            avg_market_margin = None
            
            # Buscar el par complementario para calcular margen (solo para TOTALS)
            if market_type == MarketType.TOTALS:
                # Para totals: buscar Over/Under del mismo punto
                is_over = "Over" in market_name
                point = best.get("point")
                opposite_name = f"{'Under' if is_over else 'Over'} {point}"
                
                opposite_odds = [o for o in odds_data 
                               if o["bookmaker"] == best["bookmaker"] 
                               and f"{o['market_name']} {o.get('point')}" == opposite_name]
                
                if opposite_odds:
                    prob_current = 1 / best["odds"]
                    prob_opposite = 1 / opposite_odds[0]["odds"]
                    bookmaker_margin = round((prob_current + prob_opposite - 1) * 100, 2)
                
                # Calcular margen promedio de todas las casas
                all_bookmakers = set(o["bookmaker"] for o in odds_list)
                margins = []
                for bookie in all_bookmakers:
                    current_odds_bookie = [o for o in odds_data 
                                          if o["bookmaker"] == bookie 
                                          and f"{o['market_name']} {o.get('point')}" == market_name]
                    opposite_odds_bookie = [o for o in odds_data 
                                           if o["bookmaker"] == bookie 
                                           and f"{o['market_name']} {o.get('point')}" == opposite_name]
                    
                    if current_odds_bookie and opposite_odds_bookie:
                        prob_c = 1 / current_odds_bookie[0]["odds"]
                        prob_o = 1 / opposite_odds_bookie[0]["odds"]
                        margin = (prob_c + prob_o - 1) * 100
                        margins.append(margin)
                
                if margins:
                    avg_market_margin = round(sum(margins) / len(margins), 2)
            
            elif market_type == MarketType.BTTS:
                # Para BTTS: buscar Yes/No
                opposite_name = "No" if market_name == "Yes" else "Yes"
                
                opposite_odds = [o for o in odds_data 
                               if o["bookmaker"] == best["bookmaker"] 
                               and o["market_name"] == opposite_name]
                
                if opposite_odds:
                    prob_current = 1 / best["odds"]
                    prob_opposite = 1 / opposite_odds[0]["odds"]
                    bookmaker_margin = round((prob_current + prob_opposite - 1) * 100, 2)
                
                # Calcular margen promedio de todas las casas
                all_bookmakers = set(o["bookmaker"] for o in odds_list)
                margins = []
                for bookie in all_bookmakers:
                    current_odds_bookie = [o for o in odds_data 
                                          if o["bookmaker"] == bookie 
                                          and o["market_name"] == market_name]
                    opposite_odds_bookie = [o for o in odds_data 
                                           if o["bookmaker"] == bookie 
                                           and o["market_name"] == opposite_name]
                    
                    if current_odds_bookie and opposite_odds_bookie:
                        prob_c = 1 / current_odds_bookie[0]["odds"]
                        prob_o = 1 / opposite_odds_bookie[0]["odds"]
                        margin = (prob_c + prob_o - 1) * 100
                        margins.append(margin)
                
                if margins:
                    avg_market_margin = round(sum(margins) / len(margins), 2)
            
            # Formatear todas las cuotas
            all_odds_formatted = "; ".join([
                f"{o['bookmaker'].value}:{o['odds']}" 
                for o in sorted(odds_list, key=lambda x: x["odds"], reverse=True)
            ])
            # Calcular BDI (no-fair) usando la aproximación binaria (selección vs complemento)
            sel_label = market_name
            try:
                bookmaker_odds_list = []
                for o in odds_list:
                    odds_val = o.get("odds")
                    if not odds_val or odds_val <= 1:
                        continue
                    p = 1.0 / float(odds_val)
                    other_odds = 1.0 / max(1e-9, 1.0 - p)
                    bookmaker_odds_list.append({sel_label: odds_val, f"{sel_label}_other": other_odds})
                bdi_res = bookmaker_disagreement(bookmaker_odds_list) if bookmaker_odds_list else {}
                bdi_jsd = bdi_res.get('jsd_mean')
                bdi_n = bdi_res.get('n_bookmakers')
                per_std = bdi_res.get('per_outcome_std', {})
                per_mad = bdi_res.get('per_outcome_mad', {})
                bdi_std_p = per_std.get(sel_label)
                bdi_mad_p = per_mad.get(sel_label)
            except Exception:
                bdi_jsd = None
                bdi_n = None
                bdi_std_p = None
                bdi_mad_p = None

            # Calcular BDI "fair" emparejando Over/Under (solo si existe lado opuesto)
            bdi_jsd_fair = None
            bdi_n_fair = None
            bdi_std_p_fair = None
            bdi_mad_p_fair = None
            try:
                # Sólo tiene sentido para mercados binarios como TOTALS o BTTS
                if market_type == MarketType.TOTALS or market_type == MarketType.BTTS:
                    is_over = "Over" in market_name
                    # construir nombre opuesto (ej: 'Under 2.5')
                    parts = market_name.split()
                    point = parts[-1] if len(parts) >= 2 else None
                    opposite_name = f"{'Under' if is_over else 'Over'} {point}"

                    # agrupar por bookie y tomar pares completos
                    all_bookmakers = set(o["bookmaker"] for o in odds_list)
                    fair_list = []
                    for bookie in all_bookmakers:
                        current = next((x for x in odds_data if x["bookmaker"] == bookie and f"{x['market_name']} {x.get('point')}" == market_name), None)
                        opposite = next((x for x in odds_data if x["bookmaker"] == bookie and f"{x['market_name']} {x.get('point')}" == opposite_name), None)
                        if current and opposite:
                            fair_list.append({market_name: current['odds'], opposite_name: opposite['odds']})
                    if fair_list:
                        fair_res = bookmaker_disagreement(fair_list)
                        bdi_jsd_fair = fair_res.get('jsd_mean')
                        bdi_n_fair = fair_res.get('n_bookmakers')
                        per_std_f = fair_res.get('per_outcome_std', {})
                        per_mad_f = fair_res.get('per_outcome_mad', {})
                        bdi_std_p_fair = per_std_f.get(market_name)
                        bdi_mad_p_fair = per_mad_f.get(market_name)
            except Exception:
                pass

            # Crear resultado
            result = AnalysisResult(
                match=match,
                market=market_type,
                market_name=market_name,
                best_odds=best["odds"],
                implied_probability=round(1 / best["odds"], 3),
                bookmaker=best["bookmaker"],
                meets_criteria=True,  # Siempre True, ordenar por score
                min_prob_threshold=self.min_probability,
                min_odds_threshold=self.min_odds,
                bookmaker_margin=bookmaker_margin,
                avg_market_margin=avg_market_margin,
                avg_market_odds=round(avg_odds, 4) if avg_odds > 0 else None,
                volatility_std=volatility,
                num_bookmakers=len(odds_list),
                all_odds_formatted=all_odds_formatted
                ,BDI_jsd=bdi_jsd, BDI_n_bookmakers=bdi_n, BDI_std_p=bdi_std_p, BDI_mad_p=bdi_mad_p
                ,BDI_jsd_fair=bdi_jsd_fair, BDI_n_bookmakers_fair=bdi_n_fair, BDI_std_p_fair=bdi_std_p_fair, BDI_mad_p_fair=bdi_mad_p_fair
            )
            
            results.append(result)
        
        return results
    
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
        if best_1x and len(match_odds.odds_1x) > 1:  # Filtrar si solo hay 1 casa
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
            
            # Calcular volatilidad (desviación estándar) de las cuotas 1X
            volatility = self._calculate_volatility([odds.odds for odds in match_odds.odds_1x])
            
            # Formatear todas las cuotas 1X
            all_odds_formatted = "; ".join([
                f"{odds.bookmaker.value}:{odds.odds}"
                for odds in sorted(match_odds.odds_1x, key=lambda x: x.odds, reverse=True)
            ])
            # Calcular BDI (no-fair) para 1X
            try:
                sel_label = "1X"
                bookmaker_odds_list = []
                for od in match_odds.odds_1x:
                    odds_val = od.odds
                    if not odds_val or odds_val <= 1:
                        continue
                    p = 1.0 / float(odds_val)
                    other_odds = 1.0 / max(1e-9, 1.0 - p)
                    bookmaker_odds_list.append({sel_label: odds_val, f"{sel_label}_other": other_odds})
                bdi_res = bookmaker_disagreement(bookmaker_odds_list) if bookmaker_odds_list else {}
                bdi_jsd = bdi_res.get('jsd_mean')
                bdi_n = bdi_res.get('n_bookmakers')
                per_std = bdi_res.get('per_outcome_std', {})
                per_mad = bdi_res.get('per_outcome_mad', {})
                bdi_std_p = per_std.get(sel_label)
                bdi_mad_p = per_mad.get(sel_label)
            except Exception:
                bdi_jsd = None
                bdi_n = None
                bdi_std_p = None
                bdi_mad_p = None
            
            result = AnalysisResult(
                match=match_odds.match,
                market=MarketType.DOUBLE_CHANCE_1X,
                market_name="1X",
                best_odds=best_1x.odds,
                implied_probability=round(implied_prob, 3),
                bookmaker=best_1x.bookmaker,
                meets_criteria=meets_criteria,
                min_prob_threshold=min_prob,
                min_odds_threshold=min_odds_threshold,
                bookmaker_margin=bookmaker_margin,
                avg_market_margin=round(avg_margin, 2) if avg_margin else None,
                avg_market_odds=round(match_odds.avg_1x_odds, 4) if match_odds.avg_1x_odds > 0 else None,
                volatility_std=volatility,
                num_bookmakers=len(match_odds.odds_1x),
                all_odds_formatted=all_odds_formatted,
                match_odds=match_odds
                ,BDI_jsd=bdi_jsd, BDI_n_bookmakers=bdi_n, BDI_std_p=bdi_std_p, BDI_mad_p=bdi_mad_p
                ,BDI_jsd_fair=None, BDI_n_bookmakers_fair=None, BDI_std_p_fair=None, BDI_mad_p_fair=None
            )
            results.append(result)
        
        # Analizar mercado X2
        best_x2 = match_odds.best_x2_odds
        if best_x2 and len(match_odds.odds_x2) > 1:  # Filtrar si solo hay 1 casa
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
            
            # Calcular volatilidad (desviación estándar) de las cuotas X2
            volatility = self._calculate_volatility([odds.odds for odds in match_odds.odds_x2])
            
            # Formatear todas las cuotas X2
            all_odds_formatted = "; ".join([
                f"{odds.bookmaker.value}:{odds.odds}"
                for odds in sorted(match_odds.odds_x2, key=lambda x: x.odds, reverse=True)
            ])
            # Calcular BDI (no-fair) para X2
            try:
                sel_label = "X2"
                bookmaker_odds_list = []
                for od in match_odds.odds_x2:
                    odds_val = od.odds
                    if not odds_val or odds_val <= 1:
                        continue
                    p = 1.0 / float(odds_val)
                    other_odds = 1.0 / max(1e-9, 1.0 - p)
                    bookmaker_odds_list.append({sel_label: odds_val, f"{sel_label}_other": other_odds})
                bdi_res = bookmaker_disagreement(bookmaker_odds_list) if bookmaker_odds_list else {}
                bdi_jsd = bdi_res.get('jsd_mean')
                bdi_n = bdi_res.get('n_bookmakers')
                per_std = bdi_res.get('per_outcome_std', {})
                per_mad = bdi_res.get('per_outcome_mad', {})
                bdi_std_p = per_std.get(sel_label)
                bdi_mad_p = per_mad.get(sel_label)
            except Exception:
                bdi_jsd = None
                bdi_n = None
                bdi_std_p = None
                bdi_mad_p = None
            
            result = AnalysisResult(
                match=match_odds.match,
                market=MarketType.DOUBLE_CHANCE_X2,
                market_name="X2",
                best_odds=best_x2.odds,
                implied_probability=round(implied_prob, 3),
                bookmaker=best_x2.bookmaker,
                meets_criteria=meets_criteria,
                min_prob_threshold=min_prob,
                min_odds_threshold=min_odds_threshold,
                bookmaker_margin=bookmaker_margin,
                avg_market_margin=round(avg_margin, 2) if avg_margin else None,
                avg_market_odds=round(match_odds.avg_x2_odds, 4) if match_odds.avg_x2_odds > 0 else None,
                volatility_std=volatility,
                num_bookmakers=len(match_odds.odds_x2),
                all_odds_formatted=all_odds_formatted,
                match_odds=match_odds
                ,BDI_jsd=bdi_jsd, BDI_n_bookmakers=bdi_n, BDI_std_p=bdi_std_p, BDI_mad_p=bdi_mad_p
                ,BDI_jsd_fair=None, BDI_n_bookmakers_fair=None, BDI_std_p_fair=None, BDI_mad_p_fair=None
            )
            results.append(result)
        
        return results
    
    async def analyze_all_matches(
        self,
        min_probability: float = 0.7,
        min_odds: float = 1.30,
        hours_ahead: int = 168,
        hours_from: int = 0,
        prioritize_near_matches: bool = True,
        only_totals: bool = False,
    ) -> List[AnalysisResult]:
        """
        Realiza análisis completo de todos los partidos disponibles
        
        Args:
            min_probability: Probabilidad implícita mínima
            min_odds: Cuota mínima
            hours_ahead: Horas hacia adelante para buscar partidos (por defecto 168 = 7 días)
            hours_from: Horas desde ahora para comenzar a buscar (por defecto 0)
            prioritize_near_matches: Si True, prioriza partidos cercanos (próximas 72h) donde hay más probabilidad de cuotas
            
        Returns:
            Lista completa de análisis ordenada por partido
        """
        try:
            self.logger.info("Iniciando análisis completo de partidos")
            
            # 1. Obtener partidos próximos
            matches = await self.get_upcoming_matches(hours_ahead, hours_from)
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
            
            # Obtener requests iniciales para la barra de progreso
            try:
                initial_requests = await self.odds_client.get_remaining_requests()
                max_quota = 500
            except:
                initial_requests = 500
                max_quota = 500
            
            # Barra de progreso basada en requests API consumidos (sin ncols para que se adapte)
            pbar = tqdm(total=max_quota, desc="Progreso API", unit="req",
                       initial=max_quota - initial_requests,
                       bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} requests [{elapsed}]",
                       leave=True, position=0, dynamic_ncols=True)
            
            last_remaining = initial_requests
            
            for i, match in enumerate(matches, 1):
                try:
                    # Si solo pedimos TOTALS, evitamos solicitar H2H y mercados asociados
                    if only_totals:
                        # Solo analizar mercados adicionales (totals)
                        additional_results = await self.analyze_additional_markets(match)
                        if additional_results:
                            all_results.extend(additional_results)
                            successful_odds += 1
                        else:
                            no_odds_available += 1
                    else:
                        # Analizar mercado doble chance (1X, X2)
                        match_odds = await self.get_match_odds_data(match)

                        # Si hay cuotas disponibles, analizar
                        if match_odds.odds_1x or match_odds.odds_x2:
                            match_results = self.analyze_match_odds(
                                match_odds, min_probability, min_odds
                            )
                            all_results.extend(match_results)
                            successful_odds += 1

                        # Analizar mercados adicionales (TOTALS, BTTS, H2H_Q1)
                        additional_results = await self.analyze_additional_markets(match)
                        if additional_results:
                            all_results.extend(additional_results)
                            if not (match_odds.odds_1x or match_odds.odds_x2):
                                successful_odds += 1

                        if not (match_odds.odds_1x or match_odds.odds_x2) and not additional_results:
                            no_odds_available += 1
                    
                    # Actualizar barra con requests consumidos cada 3 partidos
                    if i % 3 == 0:
                        try:
                            current_remaining = await self.odds_client.get_remaining_requests()
                            consumed = last_remaining - current_remaining
                            if consumed > 0:
                                pbar.update(consumed)
                                last_remaining = current_remaining
                        except:
                            pass
                    
                    # Rate limiting - pausa pequeña entre requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Error analizando {match}: {e}")
                    continue
            
            # Actualización final
            try:
                final_remaining = await self.odds_client.get_remaining_requests()
                final_consumed = last_remaining - final_remaining
                if final_consumed > 0:
                    pbar.update(final_consumed)
            except:
                pass
            
            pbar.close()
            
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
    
    def _calculate_volatility(self, odds_list: List[float]) -> Optional[float]:
        """
        Calcula la volatilidad (desviación estándar) de una lista de cuotas
        
        Args:
            odds_list: Lista de cuotas del mismo mercado de diferentes casas
            
        Returns:
            Desviación estándar en porcentaje (None si no hay suficientes datos)
        """
        if not odds_list or len(odds_list) < 2:
            return None
        
        try:
            # Calcular promedio
            mean = sum(odds_list) / len(odds_list)
            
            # Calcular varianza
            variance = sum((x - mean) ** 2 for x in odds_list) / len(odds_list)
            
            # Calcular desviación estándar
            std_dev = variance ** 0.5
            
            # Convertir a porcentaje relativo al promedio
            volatility_pct = (std_dev / mean) * 100 if mean > 0 else 0
            
            return round(volatility_pct, 2)
            
        except Exception as e:
            self.logger.warning(f"Error calculando volatilidad: {e}")
            return None
    
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