"""
Tests para el analizador de cuotas de fútbol
"""

import pytest
import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.models import Match, OddsData, MarketType, BookmakerType
from src.analyzer import FootballOddsAnalyzer


# Configurar pytest para funciones async
pytestmark = pytest.mark.asyncio


class TestFootballOddsAnalyzer:
    """Tests para el analizador principal"""
    
    @pytest.fixture
    def sample_match(self):
        """Partido de ejemplo para tests"""
        return Match(
            id="test_match_1",
            home_team="Manchester United",
            away_team="Liverpool",
            league="Premier League",
            country="England",
            kickoff_time=datetime.now(timezone.utc),
            sport_key="soccer_epl"
        )
    
    @pytest.fixture
    def sample_odds(self):
        """Cuotas de ejemplo para tests"""
        return [
            OddsData(
                bookmaker=BookmakerType.PINNACLE,
                market=MarketType.DOUBLE_CHANCE_1X,
                odds=1.45,
                timestamp=datetime.now(timezone.utc)
            ),
            OddsData(
                bookmaker=BookmakerType.BET365,
                market=MarketType.DOUBLE_CHANCE_X2,
                odds=1.85,
                timestamp=datetime.now(timezone.utc)
            )
        ]
    
    def test_implied_probability_calculation(self, sample_odds):
        """Test del cálculo de probabilidad implícita"""
        odds_1x = sample_odds[0]
        expected_prob = 1.0 / 1.45
        assert abs(odds_1x.implied_probability - expected_prob) < 0.001
    
    @patch.dict(os.environ, {"THE_ODDS_API_KEY": "test_key", "SPORTRADAR_API_KEY": "test_key"})
    @patch('src.apis.the_odds_api.TheOddsAPIClient')
    @patch('src.apis.sportradar_api.SportRadarAPIClient')
    async def test_analyzer_initialization(self, mock_sportradar, mock_odds_api):
        """Test de inicialización del analizador"""
        analyzer = FootballOddsAnalyzer()
        assert analyzer.min_probability == 0.7
        assert analyzer.min_odds == 1.30
        assert analyzer.odds_client is not None
        assert analyzer.schedule_client is not None
    
    @patch.dict(os.environ, {"THE_ODDS_API_KEY": "test_key", "SPORTRADAR_API_KEY": "test_key"})
    @patch('src.apis.the_odds_api.TheOddsAPIClient')
    @patch('src.apis.sportradar_api.SportRadarAPIClient')
    def test_remove_duplicate_matches(self, mock_sportradar, mock_odds_api):
        """Test de eliminación de partidos duplicados"""
        analyzer = FootballOddsAnalyzer()
        
        # Crear partidos duplicados
        match1 = Match(
            id="1", home_team="Team A", away_team="Team B",
            league="Test League", country="Test",
            kickoff_time=datetime(2025, 11, 22, 15, 0, tzinfo=timezone.utc),
            sport_key="test"
        )
        match2 = Match(
            id="2", home_team="Team A", away_team="Team B", 
            league="Test League", country="Test",
            kickoff_time=datetime(2025, 11, 22, 15, 30, tzinfo=timezone.utc),  # Misma hora redondeada
            sport_key="test"
        )
        match3 = Match(
            id="3", home_team="Team C", away_team="Team D",
            league="Test League", country="Test", 
            kickoff_time=datetime(2025, 11, 22, 16, 0, tzinfo=timezone.utc),
            sport_key="test"
        )
        
        matches = [match1, match2, match3]
        unique_matches = analyzer._remove_duplicate_matches(matches)
        
        # Debe eliminar el duplicado
        assert len(unique_matches) == 2
        assert any(m.home_team == "Team C" for m in unique_matches)


class TestValidation:
    """Tests de validación de datos"""
    
    def test_odds_validation_positive(self):
        """Test que las cuotas deben ser positivas"""
        with pytest.raises(ValueError):
            OddsData(
                bookmaker=BookmakerType.PINNACLE,
                market=MarketType.DOUBLE_CHANCE_1X,
                odds=0.5,  # Cuota inválida
                timestamp=datetime.now(timezone.utc)
            )
    
    def test_match_string_representation(self):
        """Test de representación string de partidos"""
        match = Match(
            id="test",
            home_team="Barcelona", 
            away_team="Real Madrid",
            league="La Liga",
            country="Spain",
            kickoff_time=datetime.now(timezone.utc),
            sport_key="soccer"
        )
        
        assert str(match) == "Barcelona vs Real Madrid"


if __name__ == '__main__':
    # Ejecutar tests
    pytest.main([__file__, '-v'])