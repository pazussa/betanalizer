"""
Modelos de datos para el análisis de mercados en vivo
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel
import pytz


class BookmakerType(str, Enum):
    """Casas de apuestas - exactamente las mismas 6 del proyecto principal"""
    BETSSON = "betsson"
    PINNACLE = "pinnacle"
    MARATHONBET = "marathonbet"
    CODERE_IT = "codere_it"
    WINAMAX_FR = "winamax_fr"
    WINAMAX_DE = "winamax_de"


class MarketType(str, Enum):
    """Tipos de mercados analizados"""
    TOTALS = "totals"  # Over/Under goles
    BTTS = "btts"  # Both Teams To Score
    H2H_Q1 = "h2h_q1"  # 1X2 primer tiempo


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
    
    @property
    def commence_time_colombia(self) -> str:
        """Hora de inicio en zona horaria de Colombia"""
        colombia_tz = pytz.timezone('America/Bogota')
        local_time = self.commence_time.astimezone(colombia_tz)
        return local_time.strftime('%Y-%m-%d %H:%M:%S')


class MarketOdds(BaseModel):
    """Cuota de un mercado"""
    bookmaker: BookmakerType
    market_name: str  # "Over 2.5", "Yes", "Home", etc.
    odds: float
    point: Optional[float] = None  # Para totals (2.5, 3.5, etc.)
    
    @property
    def implied_probability(self) -> float:
        """Probabilidad implícita de la cuota"""
        return 1 / self.odds if self.odds > 0 else 0


class MatchMarketOdds(BaseModel):
    """Todas las cuotas de un mercado para un partido"""
    match: LiveMatch
    market_type: MarketType
    odds_list: List[MarketOdds] = []
    
    @property
    def avg_overround_percentage(self) -> float:
        """Calcula el margen promedio del mercado"""
        if not self.odds_list:
            return 0
        
        # Agrupar por bookmaker y calcular su overround
        bookmaker_overrounds = {}
        for odds in self.odds_list:
            if odds.bookmaker not in bookmaker_overrounds:
                bookmaker_overrounds[odds.bookmaker] = []
            bookmaker_overrounds[odds.bookmaker].append(odds.implied_probability)
        
        # Calcular overround por bookmaker
        overrounds = []
        for bookmaker, probs in bookmaker_overrounds.items():
            # Para mercados con 2 opciones (Over/Under, Yes/No)
            if len(probs) >= 2:
                overround = (sum(probs[:2]) - 1) * 100
                overrounds.append(overround)
            # Para mercados con 3 opciones (1X2)
            elif len(probs) >= 3:
                overround = (sum(probs[:3]) - 1) * 100
                overrounds.append(overround)
        
        return sum(overrounds) / len(overrounds) if overrounds else 0


class MarketAnalysisResult(BaseModel):
    """Resultado del análisis de un mercado"""
    match: LiveMatch
    market_type: MarketType
    market_name: str  # "Over 2.5", "Yes", "Home", etc.
    best_odds: float
    bookmaker: BookmakerType
    all_odds: List[MarketOdds] = []
    bookmaker_margin: Optional[float] = None
    avg_market_margin: Optional[float] = None
    avg_market_odds: Optional[float] = None
    volatility_std: Optional[float] = None
    
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
