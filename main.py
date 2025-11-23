#!/usr/bin/env python3
"""
Football Betting Odds Analyzer CLI
Análisis verídico de cuotas usando APIs oficiales
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.analyzer import FootballOddsAnalyzer
from src.reporter import ReportGenerator
from src.models import ValidationError


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('betting_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    🏈 Football Betting Odds Analyzer
    
    Análisis verídico de cuotas de fútbol usando APIs oficiales.
    Sin scraping - Solo fuentes autorizadas.
    """
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar que las API keys estén configuradas
    required_keys = ['THE_ODDS_API_KEY']
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        click.echo(f"❌ Error: Faltan las siguientes API keys: {', '.join(missing_keys)}")
        click.echo("💡 Configura tu archivo .env basado en .env.example")
        sys.exit(1)


@cli.command()
@click.option(
    '--min-probability', '-p',
    default=0.7,
    help='Probabilidad implícita mínima (0.0-1.0)',
    type=click.FloatRange(0.0, 1.0)
)
@click.option(
    '--min-odds', '-o',
    default=1.30,
    help='Cuota mínima requerida',
    type=click.FloatRange(1.0, 10.0)
)
@click.option(
    '--hours-ahead', '-h',
    default=168,
    help='Horas hacia adelante para buscar partidos (por defecto 168 = 7 días)',
    type=click.IntRange(1, 336)
)
@click.option(
    '--show-all/--only-compliant',
    default=True,
    help='Mostrar todos los resultados o solo los que cumplen criterios'
)
@click.option(
    '--export-csv',
    help='Exportar resultados a archivo CSV',
    type=click.Path()
)
def analyze(min_probability, min_odds, hours_ahead, show_all, export_csv):
    """
    Ejecutar análisis completo de cuotas de fútbol
    
    Obtiene partidos próximos de APIs oficiales, consulta cuotas de múltiples
    bookmakers y genera análisis detallado con probabilidades implícitas.
    """
    async def _run_analysis():
        try:
            click.echo("🔄 Iniciando análisis de cuotas...")
            
            # Inicializar analizador
            analyzer = FootballOddsAnalyzer()
            reporter = ReportGenerator()
            
            # Validar conexiones API
            click.echo("🔌 Validando conexión a The Odds API (datos 100% reales)...")
            try:
                api_status = await analyzer.validate_api_connections()
                # Obtener requests iniciales
                requests_iniciales = await analyzer.odds_client.get_remaining_requests()
            except ValidationError as e:
                click.echo(f"❌ Error: {e}")
                sys.exit(1)
            
            # Ejecutar análisis
            click.echo(f"📊 Analizando partidos próximos ({hours_ahead} horas = {hours_ahead//24} días)...")
            results = await analyzer.analyze_all_matches(
                min_probability=min_probability,
                min_odds=min_odds,
                hours_ahead=hours_ahead
            )
            
            if not results:
                click.echo("❌ No se encontraron partidos para analizar")
                # Cleanup antes de salir
                await analyzer.cleanup()
                return
            
            # Generar y mostrar reporte
            click.echo("\n" + "="*60)
            report = reporter.generate_analysis_table(results, show_all=show_all)
            click.echo(report)
            
            # Generar nombre de archivo CSV automático si no se especificó
            csv_filename = export_csv
            if not csv_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filename = f"analisis_cuotas_{timestamp}.csv"
            
            # Exportar siempre a CSV
            csv_data = reporter.export_to_csv_format(results)
            with open(csv_filename, 'w', encoding='utf-8') as f:
                f.write(csv_data)
            click.echo(f"\n💾 Resultados exportados a: {csv_filename}")
            
            # Limpiar recursos
            requests_finales = await analyzer.cleanup()
            
            # Mostrar uso de API
            if requests_iniciales and requests_finales:
                requests_usados = requests_iniciales - requests_finales
                click.echo(f"\n📊 Uso de API:")
                click.echo(f"   • Requests utilizados: {requests_usados}")
                click.echo(f"   • Requests restantes: {requests_finales}/500 (plan gratuito)")
                porcentaje_total = (500 - requests_finales) / 500 * 100
                click.echo(f"   • Quota total usada: {porcentaje_total:.1f}%")
            
            click.echo("\n✅ Análisis completado exitosamente")
            
        except ValidationError as e:
            click.echo(f"❌ Error de validación: {e}")
            # Cleanup en caso de error
            try:
                await analyzer.cleanup()
            except:
                pass
            sys.exit(1)
        except Exception as e:
            click.echo(f"💥 Error inesperado: {e}")
            logger.exception("Error en análisis")
            # Cleanup en caso de error
            try:
                await analyzer.cleanup()
            except:
                pass
            sys.exit(1)
    
    # Ejecutar función asíncrona
    asyncio.run(_run_analysis())


@cli.command()
def validate():
    """
    Validar conexiones API y configuración del sistema
    """
    async def _run_validation():
        try:
            click.echo("🔍 Validando configuración del sistema...")
            
            # Verificar API keys
            the_odds_key = os.getenv("THE_ODDS_API_KEY")
            sportradar_key = os.getenv("SPORTRADAR_API_KEY")
            
            click.echo(f"🔑 The Odds API Key: {'✅ Configurada' if the_odds_key else '❌ Falta'}")
            click.echo(f"🔑 SportRadar API Key: {'✅ Configurada' if sportradar_key else '⚠️ Opcional'}")
            
            # Validar conexiones
            analyzer = FootballOddsAnalyzer()
            api_status = await analyzer.validate_api_connections()
            
            click.echo("\n📡 Estado de APIs:")
            for api_name, status in api_status.items():
                status_icon = "✅" if status else "❌"
                click.echo(f"  {status_icon} {api_name.replace('_', ' ').title()}: {'Conectada' if status else 'Error'}")
            
            await analyzer.cleanup()
            
            if all(api_status.values()):
                click.echo("\n🎉 Sistema completamente funcional")
            else:
                click.echo("\n⚠️  Algunas APIs no están disponibles")
                
        except Exception as e:
            click.echo(f"💥 Error en validación: {e}")
            sys.exit(1)
    
    # Ejecutar función asíncrona
    asyncio.run(_run_validation())


@cli.command()
@click.option(
    '--min-probability', '-p',
    default=0.7,
    help='Probabilidad implícita mínima',
    type=click.FloatRange(0.0, 1.0)
)
@click.option(
    '--min-odds', '-o',
    default=1.30,
    help='Cuota mínima requerida',
    type=click.FloatRange(1.0, 10.0)
)
def compliance(min_probability, min_odds):
    """
    Generar reporte específico de cumplimiento de criterios
    """
    async def _run_compliance():
        try:
            click.echo("🔍 Generando reporte de cumplimiento...")
            
            analyzer = FootballOddsAnalyzer()
            reporter = ReportGenerator()
            
            # Obtener resultados
            results = await analyzer.analyze_all_matches(
                min_probability=min_probability,
                min_odds=min_odds,
                hours_ahead=168  # Una semana completa
            )
            
            if not results:
                click.echo("❌ No se encontraron partidos para analizar")
                return
            
            # Generar reporte de cumplimiento
            compliance_report = reporter.generate_compliance_report(results)
            click.echo("\n" + compliance_report)
            
            await analyzer.cleanup()
            
        except Exception as e:
            click.echo(f"💥 Error generando reporte: {e}")
            sys.exit(1)
    
    # Ejecutar función asíncrona
    asyncio.run(_run_compliance())


def main():
    """Punto de entrada principal"""
    cli()


if __name__ == '__main__':
    main()