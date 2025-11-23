from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MarketType(str, Enum):
    """Tipos de mercados de apuestas"""
    DOUBLE_CHANCE_1X = "1X"
    DOUBLE_CHANCE_X2 = "X2"
    MATCH_WINNER_1 = "1"
    MATCH_WINNER_X = "X"
    MATCH_WINNER_2 = "2"


class BookmakerType(str, Enum):
    """Casas de apuestas soportadas - expandido para incluir todas las disponibles en The Odds API"""
    # Principales europeas
    PINNACLE = "pinnacle"
    BET365 = "bet365"
    BETFAIR = "betfair"
    BETFAIR_EX_EU = "betfair_ex_eu"
    BETFAIR_EX_UK = "betfair_ex_uk"
    BETFAIR_EX_AU = "betfair_ex_au"
    UNIBET = "unibet"
    UNIBET_UK = "unibet_uk"
    UNIBET_NL = "unibet_nl"
    UNIBET_SE = "unibet_se"
    WILLIAM_HILL = "williamhill"
    BETSSON = "betsson"
    MARATHONBET = "marathonbet"
    BWIN = "bwin"
    LADBROKES = "ladbrokes"
    LADBROKES_UK = "ladbrokes_uk"
    CORAL = "coral"
    BETCLIC = "betclic_fr"
    BETVICTOR = "betvictor"
    BETWAY = "betway"
    CASUMO = "casumo"
    COOLBET = "coolbet"
    GROSVENOR = "grosvenor"
    LEOVEGAS = "leovegas"
    LEOVEGAS_SE = "leovegas_se"
    NORDICBET = "nordicbet"
    PADDYPOWER = "paddypower"
    SKYBET = "skybet"
    SMARKETS = "smarkets"
    SPORT888 = "sport888"
    TIPICO = "tipico_de"
    VIRGINBET = "virginbet"
    WINAMAX = "winamax_fr"
    WINAMAX_DE = "winamax_de"
    CODERE_IT = "codere_it"
    
    # Americanas
    BETMGM = "betmgm"
    BOVADA = "bovada"
    DRAFTKINGS = "draftkings"
    FANDUEL = "fanduel"
    MYBOOKIE = "mybookieag"
    
    # Australianas
    TAB = "tab"
    TABTOUCH = "tabtouch"
    POINTSBET = "pointsbetau"


class Match(BaseModel):
    """Modelo de datos para un partido de fútbol"""
    id: str
    home_team: str
    away_team: str
    league: str
    country: str
    kickoff_time: datetime
    sport_key: str = "soccer"
    
    def __str__(self) -> str:
        return f"{self.home_team} vs {self.away_team}"


class OddsData(BaseModel):
    """Modelo de datos para cuotas de un mercado específico"""
    bookmaker: BookmakerType
    market: MarketType
    odds: float = Field(gt=1.0, description="Cuota debe ser mayor a 1.0")
    timestamp: datetime
    
    @property
    def implied_probability(self) -> float:
        """Calcula la probabilidad implícita de la cuota"""
        return 1.0 / self.odds


class H2HOdds(BaseModel):
    """Cuotas H2H (Home-Draw-Away) para cálculo de margen"""
    bookmaker: BookmakerType
    home_odds: float
    draw_odds: float
    away_odds: float
    timestamp: datetime
    
    @property
    def overround(self) -> float:
        """Calcula el margen/overround de la casa de apuestas"""
        return (1/self.home_odds + 1/self.draw_odds + 1/self.away_odds) - 1.0
    
    @property
    def overround_percentage(self) -> float:
        """Retorna el margen como porcentaje"""
        return self.overround * 100


class MatchOdds(BaseModel):
    """Cuotas completas para un partido"""
    match: Match
    odds_1x: List[OddsData] = []
    odds_x2: List[OddsData] = []
    odds_h2h: List[H2HOdds] = []  # Cuotas H2H para cálculo de margen
    
    @property
    def best_1x_odds(self) -> Optional[OddsData]:
        """Obtiene la mejor cuota para 1X"""
        if not self.odds_1x:
            return None
        return max(self.odds_1x, key=lambda x: x.odds)
    
    @property
    def best_x2_odds(self) -> Optional[OddsData]:
        """Obtiene la mejor cuota para X2"""
        if not self.odds_x2:
            return None
        return max(self.odds_x2, key=lambda x: x.odds)
    
    @property
    def avg_1x_odds(self) -> float:
        """Calcula el promedio de cuotas para 1X"""
        if not self.odds_1x:
            return 0.0
        return sum(odd.odds for odd in self.odds_1x) / len(self.odds_1x)
    
    @property
    def avg_x2_odds(self) -> float:
        """Calcula el promedio de cuotas para X2"""
        if not self.odds_x2:
            return 0.0
        return sum(odd.odds for odd in self.odds_x2) / len(self.odds_x2)
    
    @property
    def best_overround(self) -> Optional[H2HOdds]:
        """Obtiene el bookmaker con el menor margen (mejor para apostador)"""
        if not self.odds_h2h:
            return None
        return min(self.odds_h2h, key=lambda x: x.overround)
    
    @property
    def avg_overround_percentage(self) -> float:
        """Calcula el margen promedio de todas las casas"""
        if not self.odds_h2h:
            return 0.0
        return sum(h.overround_percentage for h in self.odds_h2h) / len(self.odds_h2h)


class AnalysisResult(BaseModel):
    """Resultado del análisis de un partido"""
    match: Match
    market: MarketType
    best_odds: float
    implied_probability: float
    bookmaker: BookmakerType
    meets_criteria: bool
    min_prob_threshold: float
    min_odds_threshold: float
    bookmaker_margin: Optional[float] = None  # Margen de la casa de apuestas (%)
    avg_market_margin: Optional[float] = None  # Margen promedio del mercado (%)
    avg_market_odds: Optional[float] = None  # Promedio de cuotas del mercado
    volatility_std: Optional[float] = None  # Volatilidad (desviación estándar) de las cuotas del mercado (%)
    match_odds: Optional['MatchOdds'] = None  # Todas las cuotas del partido
    
    @property
    def match_display(self) -> str:
        """Formato para mostrar el partido"""
        return f"{self.match.home_team} vs {self.match.away_team}"
    
    @property
    def margin_advantage(self) -> Optional[float]:
        """Calcula la ventaja de margen (promedio - casa). Positivo = tu casa es mejor"""
        if self.bookmaker_margin is not None and self.avg_market_margin is not None:
            return round(self.avg_market_margin - self.bookmaker_margin, 2)
        return None
    
    @property
    def odds_advantage(self) -> Optional[float]:
        """Calcula la diferencia entre la mejor cuota y el promedio del mercado"""
        if self.best_odds is not None and self.avg_market_odds is not None and self.avg_market_odds > 0:
            return round(self.best_odds - self.avg_market_odds, 4)
        return None
    
    @property
    def final_score(self) -> Optional[float]:
        """Calcula el Score_Final: Ventaja_Margen / Margen_Casa"""
        if self.margin_advantage is not None and self.bookmaker_margin is not None and self.bookmaker_margin > 0:
            return round(self.margin_advantage / self.bookmaker_margin, 4)
        return None


class APIError(Exception):
    """Excepción para errores de API"""
    pass


class ValidationError(Exception):
    """Excepción para errores de validación"""
    pass


# Actualizar forward references
AnalysisResult.model_rebuild()