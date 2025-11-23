"""
Demo del Football Betting Odds Analyzer
Ejecutar este script para probar el sistema con datos simulados
"""

import asyncio
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from datetime import datetime, timezone, timedelta

# Imports absolutos para evitar problemas de relative imports
import src.models as models
import src.reporter as reporter


def create_demo_data():
    """Crear datos de demostración para testing"""
    
    # Crear partidos de ejemplo
    matches = [
        models.Match(
            id="demo_1",
            home_team="Manchester United",
            away_team="Liverpool", 
            league="Premier League",
            country="England",
            kickoff_time=datetime.now(timezone.utc) + timedelta(hours=24),
            sport_key="soccer_epl"
        ),
        models.Match(
            id="demo_2",
            home_team="Barcelona",
            away_team="Real Madrid",
            league="La Liga", 
            country="Spain",
            kickoff_time=datetime.now(timezone.utc) + timedelta(hours=36),
            sport_key="soccer_laliga"
        ),
        models.Match(
            id="demo_3",
            home_team="Bayern Munich", 
            away_team="Dortmund",
            league="Bundesliga",
            country="Germany", 
            kickoff_time=datetime.now(timezone.utc) + timedelta(hours=48),
            sport_key="soccer_bundesliga"
        )
    ]
    
    # Crear cuotas de ejemplo que cumplan criterios
    timestamp = datetime.now(timezone.utc)
    
    results = [
        # Man United vs Liverpool - 1X cumple criterios
        models.AnalysisResult(
            match=matches[0],
            market=models.MarketType.DOUBLE_CHANCE_1X,
            best_odds=1.45,  # Probabilidad implícita ~69% - NO cumple
            implied_probability=0.690,
            bookmaker=models.BookmakerType.PINNACLE,
            meets_criteria=False,
            min_prob_threshold=0.7,
            min_odds_threshold=1.30
        ),
        
        # Man United vs Liverpool - X2 cumple criterios  
        models.AnalysisResult(
            match=matches[0],
            market=models.MarketType.DOUBLE_CHANCE_X2,
            best_odds=1.35,  # Probabilidad implícita ~74% - SÍ cumple
            implied_probability=0.741,
            bookmaker=models.BookmakerType.BET365,
            meets_criteria=True,
            min_prob_threshold=0.7,
            min_odds_threshold=1.30
        ),
        
        # Barcelona vs Real Madrid - 1X SÍ cumple
        models.AnalysisResult(
            match=matches[1],
            market=models.MarketType.DOUBLE_CHANCE_1X,
            best_odds=1.38,  # Probabilidad implícita ~72% - SÍ cumple
            implied_probability=0.725,
            bookmaker=models.BookmakerType.UNIBET,
            meets_criteria=True,
            min_prob_threshold=0.7,
            min_odds_threshold=1.30
        ),
        
        # Barcelona vs Real Madrid - X2 NO cumple
        models.AnalysisResult(
            match=matches[1],
            market=models.MarketType.DOUBLE_CHANCE_X2,
            best_odds=1.28,  # Cuota muy baja - NO cumple
            implied_probability=0.781,
            bookmaker=models.BookmakerType.WILLIAM_HILL,
            meets_criteria=False,
            min_prob_threshold=0.7,
            min_odds_threshold=1.30
        ),
        
        # Bayern vs Dortmund - 1X NO cumple
        models.AnalysisResult(
            match=matches[2],
            market=models.MarketType.DOUBLE_CHANCE_1X,
            best_odds=1.65,  # Probabilidad baja ~60% - NO cumple
            implied_probability=0.606,
            bookmaker=models.BookmakerType.PINNACLE,
            meets_criteria=False,
            min_prob_threshold=0.7,
            min_odds_threshold=1.30
        ),
        
        # Bayern vs Dortmund - X2 SÍ cumple 
        models.AnalysisResult(
            match=matches[2],
            market=models.MarketType.DOUBLE_CHANCE_X2,
            best_odds=1.42,  # Probabilidad ~70% - SÍ cumple
            implied_probability=0.704,
            bookmaker=models.BookmakerType.BETFAIR,
            meets_criteria=True,
            min_prob_threshold=0.7,
            min_odds_threshold=1.30
        )
    ]
    
    return results


def main():
    """Ejecutar demo del sistema"""
    print("🏈 Football Betting Odds Analyzer - DEMO")
    print("=" * 50)
    print("📊 Ejecutando con datos simulados verídicos...")
    print("🔗 En producción: datos de APIs oficiales\n")
    
    # Crear datos de demostración
    demo_results = create_demo_data()
    
    # Generar reportes
    report_generator = reporter.ReportGenerator()
    
    # Tabla completa
    print("📋 REPORTE COMPLETO:")
    print("-" * 30)
    complete_report = report_generator.generate_analysis_table(demo_results, show_all=True)
    print(complete_report)
    print("\n")
    
    # Reporte de cumplimiento
    print("🎯 REPORTE DE CUMPLIMIENTO:")
    print("-" * 35)
    compliance_report = report_generator.generate_compliance_report(demo_results)
    print(compliance_report)
    print("\n")
    
    # Estadísticas
    print("📈 ESTADÍSTICAS:")
    print("-" * 20)
    stats = report_generator.generate_summary_stats(demo_results)
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"{key.replace('_', ' ').title()}:")
            for subkey, subvalue in value.items():
                print(f"  • {subkey.replace('_', ' ').title()}: {subvalue}")
        else:
            print(f"• {key.replace('_', ' ').title()}: {value}")
    
    print("\n" + "="*60)
    print("✅ Demo completado exitosamente")
    print("💡 Para usar datos reales, configura tus API keys en .env")
    print("🚀 Ejecuta: python main.py analyze")


if __name__ == '__main__':
    main()