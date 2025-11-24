#!/usr/bin/env python3
"""
Test para verificar que Score_Final se calcula correctamente para todos los mercados
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.analyzer import FootballOddsAnalyzer
from src.reporter import ReportGenerator
from dotenv import load_dotenv

load_dotenv()


async def main():
    print("🔄 Testing Score_Final calculation for all markets...\n")
    
    analyzer = FootballOddsAnalyzer()
    
    # Validar API
    print("🔌 Validating API...")
    requests_inicial = await analyzer.odds_client.get_remaining_requests()
    print(f"✅ API OK: {requests_inicial} requests available\n")
    
    # Obtener partidos
    print("📅 Getting matches (next 240 hours)...")
    matches = await analyzer.get_upcoming_matches(hours_ahead=240)
    print(f"✅ Found {len(matches)} matches\n")
    
    if not matches:
        print("❌ No matches found")
        return
    
    # Analizar solo 2 partidos para prueba rápida
    print("🧪 TEST: Analyzing 2 matches...\n")
    
    results = []
    for i, match in enumerate(matches[:2], 1):
        print(f"{i}. {match.home_team} vs {match.away_team} ({match.league})")
        
        try:
            # Analizar doble chance
            match_odds = await analyzer.get_match_odds_data(match)
            if match_odds.odds_1x or match_odds.odds_x2:
                dc_results = analyzer.analyze_match_odds(match_odds, min_probability=0.5, min_odds=1.0)
                results.extend(dc_results)
                print(f"   ✅ Doble Chance: {len(dc_results)} markets")
            
            # Analizar mercados adicionales
            additional = await analyzer.analyze_additional_markets(match)
            if additional:
                results.extend(additional)
                # Contar por tipo
                totals = sum(1 for r in additional if r.market.value == "totals")
                btts = sum(1 for r in additional if r.market.value == "btts")
                h2h_q1 = sum(1 for r in additional if r.market.value == "h2h_q1")
                print(f"   ✅ TOTALS: {totals}, BTTS: {btts}, H2H_Q1: {h2h_q1}")
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📈 TOTAL: {len(results)} markets analyzed\n")
    
    # Verificar Score_Final
    print("🔍 Checking Score_Final calculation:\n")
    
    markets_with_score = {}
    markets_without_score = {}
    
    for result in results:
        market_type = result.market.value
        if result.final_score is not None:
            if market_type not in markets_with_score:
                markets_with_score[market_type] = 0
            markets_with_score[market_type] += 1
        else:
            if market_type not in markets_without_score:
                markets_without_score[market_type] = 0
            markets_without_score[market_type] += 1
    
    print("✅ Markets WITH Score_Final:")
    for market, count in markets_with_score.items():
        print(f"   • {market}: {count} markets")
    
    if markets_without_score:
        print("\n❌ Markets WITHOUT Score_Final:")
        for market, count in markets_without_score.items():
            print(f"   • {market}: {count} markets")
        
        # Mostrar ejemplos sin score
        print("\n📋 Example without score:")
        for result in results:
            if result.final_score is None:
                print(f"   • {result.match_display}")
                print(f"     Market: {result.market_name} ({result.market.value})")
                print(f"     bookmaker_margin: {result.bookmaker_margin}")
                print(f"     avg_market_margin: {result.avg_market_margin}")
                print(f"     margin_advantage: {result.margin_advantage}")
                print(f"     final_score: {result.final_score}")
                break
    else:
        print("\n✅ ALL markets have Score_Final calculated!")
    
    # Generar CSV
    print("\n💾 Generating CSV...")
    reporter = ReportGenerator()
    csv_path = reporter.generate_combined_csv(results, output_dir=".")
    print(f"✅ CSV generated: {csv_path}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    requests_final = await analyzer.cleanup()
    
    if requests_inicial and requests_final:
        used = requests_inicial - requests_final
        print(f"✅ Requests used: {used}")
        print(f"✅ Requests remaining: {requests_final}/500")
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(main())
