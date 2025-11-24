"""
Punto de entrada para el análisis de mercados en vivo
"""
import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from models import MarketType
from analyzer import LiveMarketsAnalyzer
from reporter import LiveMarketsReporter


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Función principal"""
    analyzer = None
    
    try:
        print("\n🔄 Iniciando análisis de mercados de apuestas...")
        print("📅 Analizando partidos de los próximos 10 días")
        print("🔌 Conectando a The Odds API (datos 100% reales)...\n")
        
        # Crear analizador
        analyzer = LiveMarketsAnalyzer()
        
        # Verificar API
        remaining = await analyzer.api_client.get_remaining_requests()
        print(f"✅ API conectada. Requests restantes: {remaining}/500\n")
        
        if remaining < 50:
            print("⚠️  ADVERTENCIA: Quedan menos de 50 requests. Considera esperar al reset.\n")
        
        # Definir mercados a analizar
        market_types = [
            MarketType.TOTALS,    # Over/Under goles
            MarketType.BTTS,      # Ambos marcan
            MarketType.H2H_Q1     # 1X2 primer tiempo
        ]
        
        print(f"📊 Analizando {len(market_types)} mercados:")
        print("  • TOTALS (Over/Under Goles)")
        print("  • BTTS (Ambos Equipos Marcan)")
        print("  • H2H Primer Tiempo (1X2)\n")
        
        # Analizar todos los mercados
        results_by_market = await analyzer.analyze_all_markets(market_types)
        
        # Generar reportes
        reporter = LiveMarketsReporter()
        
        # Imprimir resumen en consola
        reporter.print_summary(results_by_market)
        
        # Generar CSVs
        print("\n" + "="*80)
        generated_files = reporter.generate_csvs(results_by_market)
        
        if generated_files:
            print("\n💾 Archivo CSV generado:")
            filepath = generated_files.get("combined", "")
            filename = Path(filepath).name if filepath else "N/A"
            total_count = sum(len(results) for results in results_by_market.values())
            print(f"  • {filename} ({total_count} mercados combinados)")
        else:
            print("\n❌ No se generó archivo (no hay datos)")
        
        # Obtener uso final de API
        remaining_after = await analyzer.api_client.get_remaining_requests()
        used = remaining - remaining_after
        
        print("\n📊 Uso de API:")
        print(f"   • Requests utilizados: {used}")
        print(f"   • Requests restantes: {remaining_after}/500")
        print(f"   • Quota total usada: {((500 - remaining_after) / 500 * 100):.1f}%")
        
        print("\n✅ Análisis completado exitosamente\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Análisis interrumpido por el usuario")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error durante el análisis: {e}")
        logging.exception("Error detallado:")
        sys.exit(1)
        
    finally:
        if analyzer:
            print("🔌 Conexiones cerradas correctamente")
            await analyzer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
