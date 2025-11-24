"""
Modelos de datos para el análisis de corners en vivo
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel


class BookmakerType(str, Enum):
    """Casas de apuestas - exactamente las mismas 6 del proyecto principal"""
    BETSSON = "betsson"
    PINNACLE = "pinnacle"
    MARATHONBET = "marathonbet"
    CODERE_IT = "codere_it"
    WINAMAX_FR = "winamax_fr"
    WINAMAX_DE = "winamax_de"


class CornerMarketType(str, Enum):
    """Tipos de mercados de corners"""
    TOTALS = "totals"  # Over/Under total corners
    TEAM_TOTALS = "team_totals"  # Over/Under corners por equipo
    ALTERNATE_TOTALS = "alternate_totals"  # Líneas alternativas


class LiveMatch(BaseModel):
    """Información de un partido en vivo"""
    id: str
    sport_key: str
    sport_title: str
    commence_time: datetime
    home_team: str
    away_team: str
    is_live: bool = False
    
    @property
    def match_display(self) -> str:
        """Formato para mostrar el partido"""
        return f"{self.home_team} vs {self.away_team}"


class CornerOdds(BaseModel):
    """Cuota de un mercado de corners"""
    bookmaker: BookmakerType
    market: str  # e.g., "Over 9.5", "Under 10.5"
    odds: float
    point: float  # La línea de corners (9.5, 10.5, etc.)
    
    @property
    def implied_probability(self) -> float:
        """Probabilidad implícita de la cuota"""
        return 1 / self.odds if self.odds > 0 else 0


class MatchCornerOdds(BaseModel):
    """Todas las cuotas de corners para un partido"""
    match: LiveMatch
    totals_odds: List[CornerOdds] = []  # Over/Under totales
    
    @property
    def avg_overround_percentage(self) -> float:
        """Calcula el margen promedio del mercado"""
        if not self.totals_odds:
            return 0
        
        # Agrupar por bookmaker y calcular su overround
        bookmaker_overrounds = {}
        for odds in self.totals_odds:
            if odds.bookmaker not in bookmaker_overrounds:
                bookmaker_overrounds[odds.bookmaker] = []
            bookmaker_overrounds[odds.bookmaker].append(odds.implied_probability)
        
        # Calcular overround por bookmaker (suma de prob implícitas - 1) * 100
        overrounds = []
        for bookmaker, probs in bookmaker_overrounds.items():
            # Para un par Over/Under, el overround es la suma - 1
            if len(probs) >= 2:
                overround = (sum(probs[:2]) - 1) * 100
                overrounds.append(overround)
        
        return sum(overrounds) / len(overrounds) if overrounds else 0
    
    def get_best_odds(self, market_filter: str) -> Optional[CornerOdds]:
        """Obtiene la mejor cuota para un mercado específico (e.g., 'Over', 'Under')"""
        filtered = [o for o in self.totals_odds if market_filter.lower() in o.market.lower()]
        return max(filtered, key=lambda x: x.odds) if filtered else None
    
    def get_avg_odds(self, market_filter: str) -> float:
        """Promedio de cuotas para un mercado específico"""
        filtered = [o for o in self.totals_odds if market_filter.lower() in o.market.lower()]
        return sum(o.odds for o in filtered) / len(filtered) if filtered else 0


class CornersAnalysisResult(BaseModel):
    """Resultado del análisis de un mercado de corners"""
    match: LiveMatch
    market: str  # "Over 9.5", "Under 10.5", etc.
    best_odds: float
    bookmaker: BookmakerType
    all_odds: List[CornerOdds] = []  # Todas las cuotas de este mercado
    bookmaker_margin: Optional[float] = None  # Margen de la casa (%)
    avg_market_margin: Optional[float] = None  # Margen promedio del mercado (%)
    avg_market_odds: Optional[float] = None  # Promedio de cuotas del mercado
    volatility_std: Optional[float] = None  # Volatilidad (desviación estándar) %
    
    @property
    def margin_advantage(self) -> Optional[float]:
        """Ventaja de margen: promedio - casa"""
        if self.bookmaker_margin is not None and self.avg_market_margin is not None:
            return round(self.avg_market_margin - self.bookmaker_margin, 2)
        return None
    
    @property
    def odds_advantage(self) -> Optional[float]:
        """Diferencia entre mejor cuota y promedio"""
        if self.best_odds is not None and self.avg_market_odds is not None and self.avg_market_odds > 0:
            return round(self.best_odds - self.avg_market_odds, 4)
        return None
    
    @property
    def final_score(self) -> Optional[float]:
        """Score_Final: Ventaja_Margen / Margen_Casa"""
        if self.margin_advantage is not None and self.bookmaker_margin is not None and self.bookmaker_margin > 0:
            return round(self.margin_advantage / self.bookmaker_margin, 4)
        return None
