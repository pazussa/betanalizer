#!/usr/bin/env python3
"""
Variant of the CLI that tries to include all possible bookmakers when analyzing.
Run: `python main2.py analyze` to perform the analysis including all bookmakers
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
from src.models import ValidationError, BookmakerType, OddsData, H2HOdds, MarketType
from src.apis.the_odds_api import TheOddsAPIClient

import httpx
from datetime import timezone


# Logging igual que main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('betting_analysis_allbookies.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AllBookmakersTheOddsAPIClient(TheOddsAPIClient):
    """
    Cliente similar a TheOddsAPIClient pero intenta procesar TODOS los bookmakers
    que aparecen en la respuesta (siempre que el nombre pueda mapearse a BookmakerType).
    """

    async def get_match_odds(self, match_id: str, sport_key: str = "soccer_epl"):
        """
        Obtiene cuotas para un partido específico e intenta incluir todas las casas
        """
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
                # Try mapping to BookmakerType enum; if not possible, skip (to keep types consistent)
                try:
                    bookmaker_enum = BookmakerType(bookmaker_name)
                except Exception:
                    # skip unknown bookmaker keys (safe fallback)
                    continue

                for market_data in bookmaker_data.get("markets", []):
                    if market_data.get("key") != "h2h":
                        continue

                    outcomes = market_data.get("outcomes", [])
                    timestamp = datetime.fromisoformat(market_data.get("last_update").replace("Z", "+00:00")) if market_data.get("last_update") else datetime.now(timezone.utc)

                    # Extract H2H prices using outcome names
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

                    # Build double-chance odds (1X, X2) if possible
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
        """
        Obtener cuotas para un mercado específico sin filtrar por bookmakers.
        Devuelve lista de dicts similares a TheOddsAPIClient.get_market_odds
        pero intentando incluir todas las casas retornadas por la API (mapeando
        aquellas que coincidan con `BookmakerType`).
        """
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
                # attempt to map to enum; if fails, skip to keep types consistent
                try:
                    bookmaker_enum = BookmakerType(bookmaker_name)
                except Exception:
                    # skip unmapped bookmakers to avoid breaking models
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
            logger.warning(f"Error obteniendo cuotas de mercado (all bookies) para match {match_id}, market {market}: {e}")
            return []


@click.group()
@click.version_option(version='1.0.0')
def cli():
    load_dotenv()
    # Require THE_ODDS_API_KEY as in main.py
    required_keys = ['THE_ODDS_API_KEY']
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    if missing_keys:
        click.echo(f"❌ Error: Faltan las siguientes API keys: {', '.join(missing_keys)}")
        sys.exit(1)


@cli.command()
@click.option('--min-probability', '-p', default=0.7, type=click.FloatRange(0.0, 1.0))
@click.option('--min-odds', '-o', default=1.30, type=click.FloatRange(1.0, 10.0))
@click.option('--hours-ahead', '-h', default=72, type=click.IntRange(1, 336))
@click.option('--hours-from', default=0, type=click.IntRange(0, 336))
@click.option('--show-all/--only-compliant', default=True)
@click.option('--only-totals/--all-markets', default=False, help='Si se indica, incluir solo el mercado Over/Under (TOTALS)')
@click.option('--export-csv', type=click.Path(), help='Exportar resultados a archivo CSV')
def analyze(min_probability, min_odds, hours_ahead, hours_from, show_all, only_totals, export_csv):
    """Run analysis but include all bookmakers where possible."""
    async def _run():
        click.echo("🔄 Iniciando análisis (ALL BOOKMAKERS)...")
        analyzer = FootballOddsAnalyzer()
        # Replace default odds client with the all-bookmakers variant
        analyzer.odds_client = AllBookmakersTheOddsAPIClient()
        reporter = ReportGenerator()

        try:
            await analyzer.validate_api_connections()
        except ValidationError as e:
            click.echo(f"❌ Error: {e}")
            sys.exit(1)

        results = await analyzer.analyze_all_matches(
            min_probability=min_probability,
            min_odds=min_odds,
            hours_ahead=hours_ahead,
            hours_from=hours_from,
            only_totals=only_totals,
        )

        if not results:
            click.echo("No se encontraron resultados")
            await analyzer.cleanup()
            return

        # Si el usuario pidió solo TOTALS (Over/Under), filtrar resultados
        if only_totals:
            click.echo("🔎 Filtrando resultados: sólo mercado TOTALS (Over/Under)")
            results = [r for r in results if r.market == MarketType.TOTALS]
            if not results:
                click.echo("No se encontraron mercados TOTALS en el rango solicitado.")
                await analyzer.cleanup()
                return

        csv_path = reporter.generate_combined_csv(results, output_dir='.')
        click.echo(f"💾 CSV generado: {csv_path} (incluye todas las casas mapeables)")

        await analyzer.cleanup()

    asyncio.run(_run())


def main():
    cli()


if __name__ == '__main__':
    main()
