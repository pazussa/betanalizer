"""
Script principal para análisis de corners en vivo
"""
import asyncio
import logging
import sys
from pathlib import Path

from analyzer import CornersAnalyzer
from reporter import CornersReporter


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    """Función principal"""
    print("\n🔄 Iniciando análisis de corners en vivo...")
    print("🔌 Conectando a The Odds API (datos 100% reales)...\n")
    
    analyzer = None
    
    try:
        # Inicializar analizador
        analyzer = CornersAnalyzer()
        
        # Verificar quota de API
        remaining = await analyzer.api_client.get_remaining_requests()
        print(f"✅ API conectada. Requests restantes: {remaining}/500\n")
        
        # Analizar todos los partidos en vivo
        print("📊 Analizando partidos en vivo con mercados de corners...")
        results = await analyzer.analyze_all_live_matches()
        
        if not results:
            print("\n❌ No se encontraron partidos en vivo con mercados de corners")
            return
        
        # Generar reporte
        reporter = CornersReporter()
        
        # Mostrar resumen en consola
        reporter.print_summary(results)
        
        # Exportar a CSV
        csv_path = reporter.generate_csv(results)
        print(f"\n💾 Resultados exportados a: {csv_path}")
        
        # Mostrar uso de API
        final_remaining = await analyzer.api_client.get_remaining_requests()
        used = remaining - final_remaining
        print(f"\n📊 Uso de API:")
        print(f"   • Requests utilizados: {used}")
        print(f"   • Requests restantes: {final_remaining}/500")
        print(f"   • Quota total usada: {((500 - final_remaining) / 500 * 100):.1f}%")
        
        print("\n✅ Análisis completado exitosamente\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Análisis interrumpido por el usuario")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error durante el análisis: {e}")
        logging.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
        
    finally:
        if analyzer:
            await analyzer.cleanup()
            print("🔌 Conexiones cerradas correctamente\n")


if __name__ == "__main__":
    asyncio.run(main())
