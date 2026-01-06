#!/usr/bin/env python3
"""
main3.py - Análisis con múltiples APIs de Odds

Combina:
- THE_ODDS_API: 58 bookmakers (Pinnacle, Betfair, DraftKings, etc.)
- API-FOOTBALL: Bookmakers adicionales (Bet365, Bwin, SBO/Sbobet, etc.)

Run: `python main3.py analyze` para análisis completo con todas las fuentes
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

import click
import pandas as pd
from dotenv import load_dotenv

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.analyzer import FootballOddsAnalyzer
from src.reporter import ReportGenerator
from src.models import ValidationError, BookmakerType, OddsData, H2HOdds, MarketType
from src.apis.the_odds_api import TheOddsAPIClient
from src.apis.api_football import APIFootballClient, BOOKMAKER_ID_MAP, LEAGUE_IDS

import httpx


# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('betting_analysis_multi_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Mapeo de nombres de API-FOOTBALL a BookmakerType (los que coinciden)
API_FOOTBALL_TO_BOOKMAKER_TYPE = {
    "Bet365": "bet365",
    "Bwin": "bwin", 
    "Pinnacle": "pinnacle",
    "Betfair": "betfair",
    "William Hill": "williamhill",
    "Marathonbet": "marathonbet",
    "1xBet": "onexbet",
    "Unibet": "unibet",
    "Betway": "betway",
    "Betsson": "betsson",
    "NordicBet": "nordicbet",
    "888Sport": "sport888",
    "Tipico": "tipico_de",
    "Bovada": "bovada",
    "Ladbrokes": "ladbrokes",
    # Casas adicionales de API-FOOTBALL (no en THE_ODDS_API)
    "SBO": "sbo",           # Sbobet - Casa asiática
    "Dafabet": "dafabet",
    "BetFred": "betfred",
    "188Bet": "188bet",
    "10Bet": "10bet",
    "Betano": "betano",
    "Superbet": "superbet",
}


class MultiAPIBookmakerType:
    """
    Clase para manejar bookmakers de múltiples APIs
    Algunos bookmakers no están en el enum BookmakerType original
    """
    # Bookmakers exclusivos de API-FOOTBALL
    EXTRA_BOOKMAKERS = {
        "bet365", "bwin", "sbo", "dafabet", "betfred", 
        "188bet", "10bet", "betano", "superbet"
    }
    
    @staticmethod
    def is_valid(bookmaker_key: str) -> bool:
        """Verifica si el bookmaker es válido (en enum o en extras)"""
        try:
            BookmakerType(bookmaker_key)
            return True
        except ValueError:
            return bookmaker_key in MultiAPIBookmakerType.EXTRA_BOOKMAKERS


class AllBookmakersTheOddsAPIClient(TheOddsAPIClient):
    """
    Cliente THE_ODDS_API que procesa TODOS los bookmakers disponibles
    """

    async def get_match_odds(self, match_id: str, sport_key: str = "soccer_epl"):
        """Obtiene cuotas para un partido específico e intenta incluir todas las casas"""
        try:
            url = f"{self.BASE_URL}/sports/{sport_key}/events/{match_id}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,us,uk,au",
                "markets": "h2h",
                "oddsFormat": "decimal",
                "dateFormat": "iso"
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            all_odds = []
            h2h_odds = []

            for bookmaker_data in data.get("bookmakers", []):
                bookmaker_name = bookmaker_data.get("key")
                try:
                    bookmaker_enum = BookmakerType(bookmaker_name)
                except Exception:
                    continue

                for market_data in bookmaker_data.get("markets", []):
                    if market_data.get("key") != "h2h":
                        continue

                    outcomes = market_data.get("outcomes", [])
                    timestamp = datetime.fromisoformat(market_data.get("last_update").replace("Z", "+00:00")) if market_data.get("last_update") else datetime.now(timezone.utc)

                    home_odds = next((o.get("price") for o in outcomes if o.get("name") == data.get("home_team")), None)
                    draw_odds = next((o.get("price") for o in outcomes if o.get("name") == "Draw"), None)
                    away_odds = next((o.get("price") for o in outcomes if o.get("name") == data.get("away_team")), None)

                    if home_odds and draw_odds and away_odds:
                        try:
                            h2h_odds.append(H2HOdds(
                                bookmaker=bookmaker_enum,
                                home_odds=float(home_odds),
                                draw_odds=float(draw_odds),
                                away_odds=float(away_odds),
                                timestamp=timestamp
                            ))
                        except Exception:
                            continue

                    try:
                        if home_odds and draw_odds:
                            prob_1x = (1/float(home_odds)) + (1/float(draw_odds))
                            odds_1x = 1 / prob_1x
                            all_odds.append(OddsData(bookmaker=bookmaker_enum, market="1X", odds=round(odds_1x, 4), timestamp=timestamp))
                        if draw_odds and away_odds:
                            prob_x2 = (1/float(draw_odds)) + (1/float(away_odds))
                            odds_x2 = 1 / prob_x2
                            all_odds.append(OddsData(bookmaker=bookmaker_enum, market="X2", odds=round(odds_x2, 4), timestamp=timestamp))
                    except Exception:
                        continue

            return all_odds, h2h_odds

        except Exception as e:
            logger.warning(f"Error obteniendo cuotas (all bookies) para match {match_id}: {e}")
            return [], []

    async def get_market_odds(self, match_id: str, sport_key: str = "soccer_epl", market: str = "totals"):
        """Obtener cuotas para un mercado específico"""
        try:
            url = f"{self.BASE_URL}/sports/{sport_key}/events/{match_id}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,us,uk,au",
                "markets": market,
                "oddsFormat": "decimal",
                "dateFormat": "iso",
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            odds_list = []

            for bookmaker_data in data.get("bookmakers", []):
                bookmaker_name = bookmaker_data.get("key")
                try:
                    bookmaker_enum = BookmakerType(bookmaker_name)
                except Exception:
                    continue

                for market_data in bookmaker_data.get("markets", []):
                    timestamp = None
                    if market_data.get("last_update"):
                        try:
                            timestamp = datetime.fromisoformat(market_data.get("last_update").replace("Z", "+00:00"))
                        except Exception:
                            timestamp = datetime.now(timezone.utc)

                    for outcome in market_data.get("outcomes", []):
                        odds_info = {
                            "bookmaker": bookmaker_enum,
                            "market_name": outcome.get("name"),
                            "odds": float(outcome.get("price")) if outcome.get("price") is not None else None,
                            "point": outcome.get("point"),
                            "timestamp": timestamp
                        }
                        odds_list.append(odds_info)

            return odds_list

        except Exception as e:
            logger.warning(f"Error obteniendo cuotas de mercado para match {match_id}, market {market}: {e}")
            return []


class MultiAPIAnalyzer:
    """
    Analizador que combina datos de múltiples APIs de odds
    """
    
    def __init__(self):
        self.odds_api_client = AllBookmakersTheOddsAPIClient()
        self.api_football_client = None
        
        # Inicializar API-FOOTBALL si la key está disponible
        api_football_key = os.getenv("API_FOOTBALL_KEY")
        if api_football_key:
            self.api_football_client = APIFootballClient(api_football_key)
            logger.info("✅ API-FOOTBALL inicializado")
        else:
            logger.warning("⚠️ API_FOOTBALL_KEY no encontrada - usando solo THE_ODDS_API")
    
    async def cleanup(self):
        """Cerrar conexiones"""
        await self.odds_api_client.close()
        if self.api_football_client:
            await self.api_football_client.close()
    
    async def validate_connections(self):
        """Validar conexiones a todas las APIs"""
        # Validar THE_ODDS_API - obtener requests restantes
        try:
            remaining = await self.odds_api_client.get_remaining_requests()
            logger.info(f"✅ THE_ODDS_API conectado - {remaining} requests restantes")
        except Exception as e:
            logger.warning(f"⚠️ THE_ODDS_API: error verificando estado: {e}")
        
        # Validar API-FOOTBALL
        if self.api_football_client:
            status = await self.api_football_client.get_status()
            if status:
                requests_info = status.get("requests", {})
                logger.info(f"✅ API-FOOTBALL conectado - {requests_info.get('current', 0)}/{requests_info.get('limit_day', 100)} requests hoy")
            else:
                logger.warning("⚠️ API-FOOTBALL: no se pudo verificar estado")
    
    async def get_api_football_odds_for_today(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Obtener odds de API-FOOTBALL para partidos de hoy y mañana
        usando el endpoint por fecha (más eficiente y disponible en plan gratuito)
        
        Returns:
            Tuple de (h2h_odds, totals_odds)
        """
        if not self.api_football_client:
            return [], []
        
        all_h2h_odds = []
        all_totals_odds = []
        
        # Obtener odds de las próximas 72 horas
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        for date in [today, tomorrow, day_after]:
            try:
                # Usar el endpoint por fecha que SÍ funciona en plan gratuito
                odds_data = await self.api_football_client.get_odds_by_date(date)
                
                if odds_data:
                    # Parsear H2H (1X2 / Doble oportunidad)
                    h2h_odds = self.api_football_client.parse_h2h_odds(odds_data)
                    all_h2h_odds.extend(h2h_odds)
                    
                    # Parsear Totals (Over/Under)
                    totals_odds = self.api_football_client.parse_totals_odds(odds_data)
                    all_totals_odds.extend(totals_odds)
                    
                    logger.info(f"  📊 {date}: {len(h2h_odds)} H2H, {len(totals_odds)} Over/Under")
                
                # Pequeña pausa para no saturar
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.warning(f"Error obteniendo odds de API-FOOTBALL para {date}: {e}")
                continue
        
        return all_h2h_odds, all_totals_odds
    
    async def compare_odds_sources(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Comparar odds entre THE_ODDS_API y API-FOOTBALL
        
        Returns:
            Tuple de (DataFrame H2H, DataFrame Totals)
        """
        logger.info("🔄 Obteniendo odds de API-FOOTBALL...")
        h2h_odds, totals_odds = await self.get_api_football_odds_for_today()
        
        h2h_df = pd.DataFrame()
        totals_df = pd.DataFrame()
        
        # Procesar H2H
        if h2h_odds:
            h2h_df = pd.DataFrame(h2h_odds)
            
            # Calcular doble oportunidad
            h2h_df['odds_1x'] = h2h_df.apply(
                lambda row: round(1 / ((1/row['home_odds']) + (1/row['draw_odds'])), 4), 
                axis=1
            )
            h2h_df['odds_x2'] = h2h_df.apply(
                lambda row: round(1 / ((1/row['draw_odds']) + (1/row['away_odds'])), 4), 
                axis=1
            )
            
            # Calcular probabilidades implícitas
            h2h_df['prob_1x'] = (1 / h2h_df['odds_1x'] * 100).round(2)
            h2h_df['prob_x2'] = (1 / h2h_df['odds_x2'] * 100).round(2)
        
        # Procesar Totals
        if totals_odds:
            totals_df = pd.DataFrame(totals_odds)
            
            # Calcular probabilidades implícitas
            totals_df['prob_over'] = (1 / totals_df['over_odds'] * 100).round(2)
            totals_df['prob_under'] = (1 / totals_df['under_odds'] * 100).round(2)
            
            # Calcular margen
            totals_df['margin'] = ((1/totals_df['over_odds'] + 1/totals_df['under_odds'] - 1) * 100).round(2)
        
        if h2h_odds:
            logger.info(f"  ✅ {len(h2h_df)} cuotas H2H de API-FOOTBALL")
        if totals_odds:
            logger.info(f"  ✅ {len(totals_df)} cuotas Over/Under de API-FOOTBALL")
        
        if h2h_df.empty and totals_df.empty:
            logger.warning("No se encontraron odds en API-FOOTBALL")
        
        return h2h_df, totals_df


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """CLI para análisis multi-API de cuotas de apuestas"""
    load_dotenv(override=True)
    
    # Validar API keys
    if not os.getenv('THE_ODDS_API_KEY'):
        click.echo("❌ Error: THE_ODDS_API_KEY no encontrada en .env")
        sys.exit(1)


@cli.command()
def status():
    """Verificar estado de todas las APIs"""
    async def _run():
        click.echo("🔍 Verificando estado de las APIs...\n")
        
        # THE_ODDS_API
        click.echo("📡 THE_ODDS_API:")
        try:
            client = TheOddsAPIClient()
            # Hacer una petición simple para verificar
            sports = await client.client.get(
                f"{client.BASE_URL}/sports",
                params={"apiKey": client.api_key}
            )
            sports.raise_for_status()
            click.echo("  ✅ Conexión OK")
            await client.close()
        except Exception as e:
            click.echo(f"  ❌ Error: {e}")
        
        # API-FOOTBALL
        click.echo("\n📡 API-FOOTBALL:")
        api_key = os.getenv("API_FOOTBALL_KEY")
        if api_key:
            try:
                client = APIFootballClient(api_key)
                status = await client.get_status()
                if status:
                    requests = status.get("requests", {})
                    subscription = status.get("subscription", {})
                    click.echo(f"  ✅ Conexión OK")
                    click.echo(f"  📊 Plan: {subscription.get('plan', 'Unknown')}")
                    click.echo(f"  📊 Requests: {requests.get('current', 0)}/{requests.get('limit_day', 100)} hoy")
                await client.close()
            except Exception as e:
                click.echo(f"  ❌ Error: {e}")
        else:
            click.echo("  ⚠️ API_FOOTBALL_KEY no configurada")
        
        click.echo("\n✅ Verificación completada")
    
    asyncio.run(_run())


@cli.command()
def bookmakers():
    """Listar bookmakers disponibles en cada API"""
    async def _run():
        click.echo("📚 Bookmakers disponibles:\n")
        
        # THE_ODDS_API bookmakers
        click.echo("═══ THE_ODDS_API ═══")
        click.echo("(58 bookmakers en plan gratuito, incluyendo:)")
        the_odds_api_top = [
            "pinnacle", "betfair", "williamhill", "unibet", "betway",
            "draftkings", "fanduel", "betmgm", "marathonbet", "betsson"
        ]
        for bm in the_odds_api_top:
            click.echo(f"  • {bm}")
        click.echo("  ... y 48 más")
        
        # API-FOOTBALL bookmakers
        click.echo("\n═══ API-FOOTBALL ═══")
        api_key = os.getenv("API_FOOTBALL_KEY")
        if api_key:
            try:
                client = APIFootballClient(api_key)
                bookmakers = await client.get_bookmakers()
                click.echo(f"({len(bookmakers)} bookmakers disponibles)")
                
                # Destacar los exclusivos
                exclusive = ["Bet365", "Bwin", "SBO", "Dafabet", "BetFred", "188Bet"]
                click.echo("\n⭐ Exclusivos (no en THE_ODDS_API gratis):")
                for bm in bookmakers:
                    if bm['name'] in exclusive:
                        click.echo(f"  • {bm['name']} (id: {bm['id']})")
                
                click.echo("\n📋 Todos:")
                for bm in bookmakers:
                    marker = "⭐" if bm['name'] in exclusive else "  "
                    click.echo(f"  {marker} {bm['name']}")
                
                await client.close()
            except Exception as e:
                click.echo(f"  ❌ Error: {e}")
        else:
            click.echo("  ⚠️ API_FOOTBALL_KEY no configurada")
    
    asyncio.run(_run())


@cli.command()
@click.option('--min-probability', '-p', default=0.7, type=click.FloatRange(0.0, 1.0))
@click.option('--min-odds', '-o', default=1.30, type=click.FloatRange(1.0, 10.0))
@click.option('--hours-ahead', '-h', default=72, type=click.IntRange(1, 336))
@click.option('--hours-from', default=0, type=click.IntRange(0, 336))
@click.option('--show-all/--only-compliant', default=True)
@click.option('--only-totals/--all-markets', default=False, help='Incluir solo mercado Over/Under')
@click.option('--export-csv', type=click.Path(), help='Exportar a CSV')
@click.option('--include-api-football/--no-api-football', default=True, help='Incluir datos de API-FOOTBALL')
def analyze(min_probability, min_odds, hours_ahead, hours_from, show_all, only_totals, export_csv, include_api_football):
    """
    Análisis completo combinando THE_ODDS_API + API-FOOTBALL
    
    Obtiene cuotas de ~70+ bookmakers incluyendo:
    - THE_ODDS_API: Pinnacle, Betfair, DraftKings, FanDuel, etc.
    - API-FOOTBALL: Bet365, Bwin, Sbobet (SBO), etc.
    """
    async def _run():
        click.echo("🚀 Iniciando análisis MULTI-API...")
        click.echo(f"   • THE_ODDS_API: 58 bookmakers")
        
        if include_api_football and os.getenv("API_FOOTBALL_KEY"):
            click.echo(f"   • API-FOOTBALL: +34 bookmakers (Bet365, Bwin, SBO)")
        
        click.echo("")
        
        # Inicializar analizador principal (THE_ODDS_API)
        analyzer = FootballOddsAnalyzer()
        analyzer.odds_client = AllBookmakersTheOddsAPIClient()
        reporter = ReportGenerator()
        
        try:
            await analyzer.validate_api_connections()
        except ValidationError as e:
            click.echo(f"❌ Error validando APIs: {e}")
            sys.exit(1)
        
        # Obtener resultados de THE_ODDS_API
        click.echo("📡 Obteniendo datos de THE_ODDS_API...")
        results = await analyzer.analyze_all_matches(
            min_probability=min_probability,
            min_odds=min_odds,
            hours_ahead=hours_ahead,
            hours_from=hours_from,
            only_totals=only_totals,
        )
        
        click.echo(f"   ✅ {len(results) if results else 0} mercados encontrados")
        
        # Obtener datos adicionales de API-FOOTBALL
        api_football_h2h_df = None
        api_football_totals_df = None
        if include_api_football and os.getenv("API_FOOTBALL_KEY"):
            click.echo("\n📡 Obteniendo datos de API-FOOTBALL (Bet365, Bwin, SBO)...")
            
            multi_analyzer = MultiAPIAnalyzer()
            try:
                await multi_analyzer.validate_connections()
                api_football_h2h_df, api_football_totals_df = await multi_analyzer.compare_odds_sources()
                
                # Resumen H2H
                if api_football_h2h_df is not None and not api_football_h2h_df.empty:
                    click.echo(f"\n   📊 Doble Oportunidad (1X/X2): {len(api_football_h2h_df)} cuotas")
                    for bm in api_football_h2h_df['bookmaker'].unique():
                        count = len(api_football_h2h_df[api_football_h2h_df['bookmaker'] == bm])
                        is_exclusive = bm in ["Bet365", "Bwin", "SBO", "Dafabet"]
                        marker = "⭐" if is_exclusive else "  "
                        click.echo(f"     {marker} {bm}: {count}")
                
                # Resumen Totals
                if api_football_totals_df is not None and not api_football_totals_df.empty:
                    click.echo(f"\n   📊 Over/Under: {len(api_football_totals_df)} cuotas")
                    for bm in api_football_totals_df['bookmaker'].unique():
                        count = len(api_football_totals_df[api_football_totals_df['bookmaker'] == bm])
                        is_exclusive = bm in ["Bet365", "Bwin", "SBO", "Dafabet"]
                        marker = "⭐" if is_exclusive else "  "
                        click.echo(f"     {marker} {bm}: {count}")
                
                if (api_football_h2h_df is None or api_football_h2h_df.empty) and \
                   (api_football_totals_df is None or api_football_totals_df.empty):
                    click.echo("   ⚠️ No se encontraron datos en API-FOOTBALL")
                
                await multi_analyzer.cleanup()
            except Exception as e:
                click.echo(f"   ⚠️ Error con API-FOOTBALL: {e}")
        
        has_api_football = (api_football_h2h_df is not None and not api_football_h2h_df.empty) or \
                          (api_football_totals_df is not None and not api_football_totals_df.empty)
        
        if not results and not has_api_football:
            click.echo("\n❌ No se encontraron resultados en ninguna fuente")
            await analyzer.cleanup()
            return
        
        # Si solo totals
        if only_totals and results:
            results = [r for r in results if r.market == MarketType.TOTALS]
        
        # Generar CSV combinado
        if results:
            csv_path = reporter.generate_combined_csv(results, output_dir='.')
            click.echo(f"\n💾 CSV THE_ODDS_API: {csv_path}")
        
        # Guardar datos de API-FOOTBALL
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar H2H de API-FOOTBALL
        if api_football_h2h_df is not None and not api_football_h2h_df.empty:
            h2h_csv = f"api_football_h2h_{timestamp}.csv"
            api_football_h2h_df.to_csv(h2h_csv, index=False)
            click.echo(f"💾 CSV API-FOOTBALL H2H: {h2h_csv}")
        
        # Guardar Totals de API-FOOTBALL
        if api_football_totals_df is not None and not api_football_totals_df.empty:
            totals_csv = f"api_football_totals_{timestamp}.csv"
            api_football_totals_df.to_csv(totals_csv, index=False)
            click.echo(f"💾 CSV API-FOOTBALL Over/Under: {totals_csv}")
            
            # Mostrar mejores Over/Under de Bet365/SBO
            click.echo("\n" + "="*60)
            click.echo("⭐ MEJORES OVER/UNDER DE API-FOOTBALL (Bet365, SBO)")
            click.echo("="*60)
            
            # Filtrar línea 2.5 con alta probabilidad
            exclusive_bm = ["Bet365", "SBO"]
            line_25 = api_football_totals_df[api_football_totals_df['line'] == 2.5].copy()
            
            for bm in exclusive_bm:
                bm_data = line_25[line_25['bookmaker'] == bm]
                if not bm_data.empty:
                    click.echo(f"\n📊 {bm} - Over/Under 2.5:")
                    # High prob over (>70%)
                    high_over = bm_data[bm_data['prob_over'] >= 70]
                    if not high_over.empty:
                        click.echo(f"   🔥 Over 2.5 con prob ≥70%: {len(high_over)}")
                        for _, row in high_over.head(3).iterrows():
                            click.echo(f"      Over: {row['over_odds']:.2f} ({row['prob_over']:.1f}%)")
                    
                    # High prob under (>70%)
                    high_under = bm_data[bm_data['prob_under'] >= 70]
                    if not high_under.empty:
                        click.echo(f"   🔥 Under 2.5 con prob ≥70%: {len(high_under)}")
                        for _, row in high_under.head(3).iterrows():
                            click.echo(f"      Under: {row['under_odds']:.2f} ({row['prob_under']:.1f}%)")
        
        # Mostrar mejores oportunidades H2H de API-FOOTBALL
        if api_football_h2h_df is not None and not api_football_h2h_df.empty:
            click.echo("\n" + "="*60)
            click.echo("⭐ MEJORES 1X/X2 DE API-FOOTBALL (Bet365, SBO)")
            click.echo("="*60)
            
            # Filtrar por prob_1x > 70% o prob_x2 > 70%
            high_prob = api_football_h2h_df[
                (api_football_h2h_df['prob_1x'] >= min_probability * 100) | 
                (api_football_h2h_df['prob_x2'] >= min_probability * 100)
            ].copy()
            
            if not high_prob.empty:
                exclusive_bm = ["Bet365", "SBO"]
                for bm in exclusive_bm:
                    bm_data = high_prob[high_prob['bookmaker'] == bm]
                    if not bm_data.empty:
                        click.echo(f"\n📊 {bm}:")
                        for _, row in bm_data.head(5).iterrows():
                            click.echo(f"   Liga: {row['league_name']}")
                            click.echo(f"   1X: {row['odds_1x']} ({row['prob_1x']}%) | X2: {row['odds_x2']} ({row['prob_x2']}%)")
            else:
                click.echo("No hay oportunidades H2H que cumplan los criterios mínimos")
        
        await analyzer.cleanup()
        click.echo("\n✅ Análisis completado")
    
    asyncio.run(_run())


@cli.command()
def test_api_football():
    """Prueba rápida de API-FOOTBALL"""
    async def _run():
        click.echo("🧪 Probando API-FOOTBALL...\n")
        
        api_key = os.getenv("API_FOOTBALL_KEY")
        if not api_key:
            click.echo("❌ API_FOOTBALL_KEY no encontrada en .env")
            return
        
        client = APIFootballClient(api_key)
        
        # 1. Verificar estado
        click.echo("1️⃣ Estado de la cuenta:")
        status = await client.get_status()
        if status:
            click.echo(f"   ✅ Plan: {status.get('subscription', {}).get('plan')}")
            click.echo(f"   ✅ Requests: {status.get('requests', {}).get('current')}/{status.get('requests', {}).get('limit_day')}")
        
        # 2. Listar bookmakers
        click.echo("\n2️⃣ Bookmakers disponibles:")
        bookmakers = await client.get_bookmakers()
        exclusive = ["Bet365", "Bwin", "SBO"]
        for bm in bookmakers:
            if bm['name'] in exclusive:
                click.echo(f"   ⭐ {bm['name']} (id: {bm['id']}) - EXCLUSIVO")
        
        # 3. Obtener odds de muestra (Premier League)
        click.echo("\n3️⃣ Odds de muestra (Premier League 2024):")
        try:
            odds = await client.get_odds_by_league_season(league_id=39, season=2024)
            if odds:
                parsed = client.parse_h2h_odds(odds[:3])  # Solo primeros 3
                for o in parsed[:10]:
                    click.echo(f"   • {o['bookmaker']}: 1={o['home_odds']}, X={o['draw_odds']}, 2={o['away_odds']}")
            else:
                click.echo("   ⚠️ No hay odds disponibles (puede que no haya partidos próximos)")
        except Exception as e:
            click.echo(f"   ⚠️ Error: {e}")
        
        await client.close()
        click.echo("\n✅ Prueba completada")
    
    asyncio.run(_run())


def main():
    cli()


if __name__ == '__main__':
    main()
