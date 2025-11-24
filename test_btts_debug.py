#!/usr/bin/env python3
"""
Test de depuración para verificar por qué BTTS no aparece en el dataset
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.analyzer import FootballOddsAnalyzer
from src.models import MarketType
from dotenv import load_dotenv
import logging

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

load_dotenv()


async def main():
    print("🔍 DEBUG: Analizando por qué BTTS no aparece\n")
    
    analyzer = FootballOddsAnalyzer()
    
    # Validar API
    print("🔌 Validando API...")
    requests_inicial = await analyzer.odds_client.get_remaining_requests()
    print(f"✅ API OK: {requests_inicial} requests disponibles\n")
    
    # Obtener partidos
    print("📅 Obteniendo partidos...")
    matches = await analyzer.get_upcoming_matches(hours_ahead=240)
    print(f"✅ Encontrados {len(matches)} partidos\n")
    
    if not matches:
        print("❌ No hay partidos")
        return
    
    # Probar 3 partidos
    print("🧪 Probando 3 partidos para ver datos de BTTS:\n")
    
    for i, match in enumerate(matches[:3], 1):
        print(f"\n{'='*80}")
        print(f"PARTIDO {i}: {match.home_team} vs {match.away_team}")
        print(f"Liga: {match.league}")
        print(f"ID: {match.id}")
        print(f"Sport Key: {match.sport_key}")
        print(f"{'='*80}\n")
        
        try:
            # Llamar directamente a get_market_odds para BTTS
            print("📡 Llamando a API para mercado BTTS...")
            btts_raw = await analyzer.odds_client.get_market_odds(
                match.id, 
                match.sport_key, 
                "btts"
            )
            
            print(f"📊 Respuesta API - Total de cuotas recibidas: {len(btts_raw)}")
            
            if not btts_raw:
                print("❌ No se recibieron cuotas BTTS de la API\n")
                continue
            
            # Mostrar datos crudos
            print("\n📋 Datos crudos recibidos:")
            for idx, odds in enumerate(btts_raw[:6], 1):  # Mostrar primeras 6
                print(f"  {idx}. {odds['bookmaker'].value}: {odds['market_name']} = {odds['odds']}")
            
            # Agrupar por mercado
            market_names = set(o["market_name"] for o in btts_raw)
            print(f"\n🎯 Mercados únicos encontrados: {market_names}")
            
            # Contar casas por mercado
            for market_name in market_names:
                odds_for_market = [o for o in btts_raw if o["market_name"] == market_name]
                bookmakers = set(o["bookmaker"].value for o in odds_for_market)
                print(f"   • {market_name}: {len(bookmakers)} casas - {bookmakers}")
            
            # Ahora analizar con el método del analyzer
            print("\n🔬 Analizando con _analyze_grouped_market...")
            btts_results = analyzer._analyze_grouped_market(match, btts_raw, MarketType.BTTS)
            
            print(f"✅ Resultados generados: {len(btts_results)}")
            
            if btts_results:
                for result in btts_results:
                    print(f"\n   📌 Mercado: {result.market_name}")
                    print(f"      Cuota: {result.best_odds} ({result.bookmaker.value})")
                    print(f"      Num casas: {result.num_bookmakers}")
                    print(f"      Margen casa: {result.bookmaker_margin}")
                    print(f"      Margen promedio: {result.avg_market_margin}")
                    print(f"      Ventaja margen: {result.margin_advantage}")
                    print(f"      Score_Final: {result.final_score}")
            else:
                print("❌ No se generaron resultados de análisis")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Cleanup
    print("\n\n🧹 Limpiando...")
    requests_final = await analyzer.cleanup()
    
    if requests_inicial and requests_final:
        usado = requests_inicial - requests_final
        print(f"✅ Requests usados: {usado}")
        print(f"✅ Requests restantes: {requests_final}/500")
    
    print("\n✅ Test completado!")


if __name__ == "__main__":
    asyncio.run(main())
