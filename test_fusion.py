#!/usr/bin/env python3
"""
Script de prueba para el sistema fusionado
"""

import asyncio
import logging
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.analyzer import FootballOddsAnalyzer
from src.reporter import ReportGenerator
from src.models import MarketType
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_fusion():
    """Prueba del sistema fusionado"""
    try:
        print("\n🔄 Iniciando prueba del sistema fusionado...")
        print("📅 Analizando partidos de los próximos 10 días\n")
        
        # Cargar .env
        load_dotenv()
        
        # Inicializar
        analyzer = FootballOddsAnalyzer()
        reporter = ReportGenerator()
        
        # Validar API
        print("🔌 Validando API...")
        await analyzer.validate_api_connections()
        
        # Obtener partidos (limitado para prueba)
        print("📊 Obteniendo partidos...")
        matches = await analyzer.get_upcoming_matches(hours_ahead=240)  # 10 días
        print(f"✅ Encontrados {len(matches)} partidos\n")
        
        if not matches:
            print("❌ No hay partidos disponibles")
            return
        
        # Analizar solo los primeros 3 partidos para prueba rápida
        test_matches = matches[:3]
        print(f"🧪 PRUEBA: Analizando {len(test_matches)} partidos...\n")
        
        all_results = []
        
        for i, match in enumerate(test_matches, 1):
            print(f"{i}. {match.home_team} vs {match.away_team} ({match.league})")
            
            try:
                # Analizar doble chance
                match_odds = await analyzer.get_match_odds_data(match)
                if match_odds.odds_1x or match_odds.odds_x2:
                    dc_results = analyzer.analyze_match_odds(match_odds)
                    all_results.extend(dc_results)
                    print(f"   ✅ Doble Chance: {len(dc_results)} mercados")
                
                # Analizar mercados adicionales
                additional = await analyzer.analyze_additional_markets(match)
                if additional:
                    all_results.extend(additional)
                    
                    # Contar por tipo
                    totals = sum(1 for r in additional if r.market == MarketType.TOTALS)
                    btts = sum(1 for r in additional if r.market == MarketType.BTTS)
                    h2h_q1 = sum(1 for r in additional if r.market == MarketType.H2H_Q1)
                    
                    print(f"   ✅ TOTALS: {totals}, BTTS: {btts}, H2H_Q1: {h2h_q1}")
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
        
        print(f"\n📈 TOTAL: {len(all_results)} mercados analizados")
        
        # Generar CSV combinado
        if all_results:
            print("\n💾 Generando CSV combinado...")
            csv_path = reporter.generate_combined_csv(all_results, output_dir=".")
            print(f"✅ CSV generado: {csv_path}")
            
            # Estadísticas por mercado
            from collections import defaultdict
            by_market = defaultdict(int)
            for r in all_results:
                by_market[r.market] += 1
            
            print("\n📊 Distribución por mercado:")
            for market, count in by_market.items():
                print(f"   • {market.value}: {count} mercados")
        
        # Cleanup
        print("\n🧹 Limpiando recursos...")
        await analyzer.cleanup()
        
        print("\n✅ Prueba completada exitosamente!")
        
    except Exception as e:
        logger.exception("Error en prueba")
        print(f"\n💥 Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_fusion())
