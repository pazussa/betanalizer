#!/usr/bin/env python3
"""
main6.py - Análisis histórico de odds usando THE_ODDS_API Historical

Simula ejecutar `main3.py analyze --hours-ahead 50` cada viernes
de los últimos 6 meses de 2025 (julio-diciembre).

Usa el endpoint histórico:
GET /v4/historical/sports/{sport}/odds?date={date}&markets=totals&regions=eu,us,uk,au

NOTA: Requiere plan de pago de THE_ODDS_API con acceso a historical odds.
Costo: 10 créditos por región por market por llamada (vs 1 en API normal)

Genera un Excel/CSV por cada viernes analizado.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import click
import pandas as pd
import numpy as np
from scipy import stats
from dotenv import load_dotenv
import httpx

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('historical_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Mapeo de número de mes a nombre de carpeta
MONTH_FOLDERS = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}


# Ligas de fútbol a analizar (mismas que main3.py)
SOCCER_LEAGUES = [
    # Top 5 europeas
    ("soccer_epl", "Premier League"),
    ("soccer_spain_la_liga", "La Liga"),
    ("soccer_germany_bundesliga", "Bundesliga"),
    ("soccer_italy_serie_a", "Serie A"),
    ("soccer_france_ligue_one", "Ligue 1"),
    # Segundas divisiones
    ("soccer_efl_champ", "Championship"),
    ("soccer_spain_segunda_division", "La Liga 2"),
    ("soccer_germany_bundesliga2", "Bundesliga 2"),
    ("soccer_italy_serie_b", "Serie B"),
    ("soccer_france_ligue_two", "Ligue 2"),
    # Otras europeas
    ("soccer_netherlands_eredivisie", "Eredivisie"),
    ("soccer_portugal_primeira_liga", "Liga Portugal"),
    ("soccer_belgium_first_div", "Pro League"),
    ("soccer_turkey_super_league", "Süper Lig"),
    ("soccer_greece_super_league", "Super League Greece"),
    ("soccer_austria_bundesliga", "Austrian Bundesliga"),
    ("soccer_switzerland_superleague", "Super League Switzerland"),
    ("soccer_denmark_superliga", "Superliga Denmark"),
    ("soccer_sweden_allsvenskan", "Allsvenskan"),
    ("soccer_norway_eliteserien", "Eliteserien"),
    ("soccer_poland_ekstraklasa", "Ekstraklasa"),
    ("soccer_spl", "Scottish Premiership"),
    ("soccer_england_league1", "League One"),
    ("soccer_england_league2", "League Two"),
    ("soccer_germany_liga3", "3. Liga"),
    # Competiciones UEFA
    ("soccer_uefa_champs_league", "Champions League"),
    ("soccer_uefa_europa_league", "Europa League"),
    ("soccer_uefa_europa_conference_league", "Conference League"),
    # Americas
    ("soccer_brazil_campeonato", "Brasileirão"),
    ("soccer_argentina_primera_division", "Liga Profesional"),
    ("soccer_chile_campeonato", "Primera División Chile"),
    ("soccer_mexico_ligamx", "Liga MX"),
    ("soccer_usa_mls", "MLS"),
    ("soccer_conmebol_copa_libertadores", "Copa Libertadores"),
    # Asia/Oceanía
    ("soccer_japan_j_league", "J1 League"),
    ("soccer_korea_kleague1", "K League 1"),
    ("soccer_australia_aleague", "A-League"),
]


# Bookmakers permitidos (del enum BookmakerType de main3.py)
ALLOWED_BOOKMAKERS = {
    "pinnacle", "bet365", "betfair", "unibet", "williamhill", "betsson",
    "marathonbet", "bwin", "draftkings", "fanduel", "betmgm", "bovada",
    "betway", "onexbet", "sport888", "betvictor", "ladbrokes_uk",
    "coolbet", "nordicbet", "suprabets", "tipico_de", "livescorebet_eu",
    "betonlineag", "lowvig", "mybookieag", "betanysports", "betus",
    "pointsbetus", "betrivers", "superbook", "wynnbet", "unibet_us",
    "twinspires", "sisportsbook", "espnbet", "fliff", "hardrockbet",
    "windcreek", "betparx", "matchbook", "betfair_ex_eu", "betfair_ex_uk",
    "sportsbet", "tab", "pointsbet_au", "neds", "playup", "bluebet",
    "betr_au", "unibet_eu", "livescorebet"
}


@dataclass
class TotalsRecord:
    """Registro de odds Over/Under"""
    match_id: str
    home_team: str
    away_team: str
    commence_time: str
    sport_key: str
    league_name: str
    bookmaker: str
    line: float
    over_odds: float
    under_odds: float
    last_update: str
    snapshot_date: str  # Fecha del snapshot histórico


class HistoricalOddsClient:
    """Cliente para THE_ODDS_API Historical Odds endpoint"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self.requests_remaining = None
        self.requests_used = None
    
    async def close(self):
        await self.client.aclose()
    
    async def get_historical_odds(
        self,
        sport_key: str,
        snapshot_date: datetime,
        commence_time_from: Optional[datetime] = None,
        commence_time_to: Optional[datetime] = None,
        markets: str = "totals",
        regions: str = "eu,us,uk,au"
    ) -> Tuple[Optional[Dict], str]:
        """
        Obtiene odds históricos para un deporte en una fecha específica.
        
        Args:
            sport_key: Clave del deporte (ej: soccer_epl)
            snapshot_date: Fecha del snapshot (se usa el más cercano igual o anterior)
            commence_time_from: Filtrar eventos que comienzan después de esta fecha
            commence_time_to: Filtrar eventos que comienzan antes de esta fecha
            markets: Mercados a consultar (h2h, totals, spreads)
            regions: Regiones de bookmakers
            
        Returns:
            Tuple de (datos, timestamp del snapshot)
        """
        url = f"{self.BASE_URL}/historical/sports/{sport_key}/odds"
        
        params = {
            "apiKey": self.api_key,
            "date": snapshot_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }
        
        if commence_time_from:
            params["commenceTimeFrom"] = commence_time_from.strftime("%Y-%m-%dT%H:%M:%SZ")
        if commence_time_to:
            params["commenceTimeTo"] = commence_time_to.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        try:
            response = await self.client.get(url, params=params)
            
            # Actualizar contadores de requests
            self.requests_remaining = response.headers.get("x-requests-remaining")
            self.requests_used = response.headers.get("x-requests-used")
            
            if response.status_code == 401:
                logger.error("❌ API Key inválida o sin acceso a historical odds")
                return None, ""
            
            if response.status_code == 422:
                # Fecha fuera de rango o deporte no disponible en esa fecha
                return None, ""
            
            response.raise_for_status()
            data = response.json()
            
            timestamp = data.get("timestamp", "")
            events = data.get("data", [])
            
            return events, timestamp
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                # No hay datos para esta fecha/deporte
                return None, ""
            logger.warning(f"Error HTTP {e.response.status_code} para {sport_key}: {e}")
            return None, ""
        except Exception as e:
            logger.warning(f"Error obteniendo historical odds para {sport_key}: {e}")
            return None, ""
    
    def parse_totals_from_events(self, events: List[Dict], league_name: str, snapshot_date: str) -> List[TotalsRecord]:
        """
        Parsea eventos y extrae registros de Over/Under.
        """
        records = []
        
        for event in events:
            match_id = event.get("id", "")
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            commence_time = event.get("commence_time", "")
            sport_key = event.get("sport_key", "")
            
            for bookmaker in event.get("bookmakers", []):
                bookmaker_key = bookmaker.get("key", "").lower()
                
                # Filtrar solo bookmakers permitidos
                if bookmaker_key not in ALLOWED_BOOKMAKERS:
                    continue
                
                last_update = bookmaker.get("last_update", "")
                
                for market in bookmaker.get("markets", []):
                    if market.get("key") != "totals":
                        continue
                    
                    outcomes = market.get("outcomes", [])
                    
                    # Agrupar por punto (línea)
                    lines = {}
                    for outcome in outcomes:
                        point = outcome.get("point")
                        name = outcome.get("name")
                        price = outcome.get("price")
                        
                        if point is None or price is None:
                            continue
                        
                        if point not in lines:
                            lines[point] = {}
                        lines[point][name] = price
                    
                    # Crear registros para cada línea completa
                    for line, prices in lines.items():
                        over_odds = prices.get("Over")
                        under_odds = prices.get("Under")
                        
                        if over_odds and under_odds:
                            records.append(TotalsRecord(
                                match_id=match_id,
                                home_team=home_team,
                                away_team=away_team,
                                commence_time=commence_time,
                                sport_key=sport_key,
                                league_name=league_name,
                                bookmaker=bookmaker_key,
                                line=float(line),
                                over_odds=float(over_odds),
                                under_odds=float(under_odds),
                                last_update=last_update,
                                snapshot_date=snapshot_date
                            ))
        
        return records


def remove_vig(odds_dict: Dict[str, float]) -> Dict[str, float]:
    """Quita el margen de las cuotas y devuelve probabilidades justas."""
    if not odds_dict:
        return {}
    probs = {k: 1.0 / v for k, v in odds_dict.items() if v > 1}
    total = sum(probs.values())
    if total == 0:
        return {}
    return {k: p / total for k, p in probs.items()}


def jensen_shannon(p: List[float], q: List[float], base: float = 2.0) -> float:
    """Compute Jensen-Shannon divergence between two distributions."""
    import math
    def kl_div(a, b):
        return sum(ai * math.log(ai / bi) if ai > 0 and bi > 0 else 0 for ai, bi in zip(a, b))
    m = [(pi + qi) / 2.0 for pi, qi in zip(p, q)]
    return 0.5 * (kl_div(p, m) + kl_div(q, m))


def bookmaker_disagreement_local(bookmaker_odds_list: List[Dict[str, float]]) -> Dict:
    """
    Calcula métricas de desacuerdo entre bookmakers.
    Replica exactamente la lógica de src/disagreement.py
    """
    import math
    
    fair_list = []
    outcomes_set = set()
    for odds in bookmaker_odds_list:
        fair = remove_vig(odds)
        if fair:
            fair_list.append(fair)
            outcomes_set.update(fair.keys())
    
    n = len(fair_list)
    if n == 0:
        return {'jsd_mean': None, 'per_outcome_std': {}, 'per_outcome_mad': {}, 'n_bookmakers': 0}
    
    outcomes = sorted(outcomes_set)
    
    # Build matrix
    matrix = []
    for fair in fair_list:
        row = [fair.get(o, 0.0) for o in outcomes]
        matrix.append(row)
    
    # Mean distribution
    k = len(outcomes)
    mean_dist = [sum(row[col] for row in matrix) / n for col in range(k)]
    
    # JSD for each bookmaker vs mean
    jsds = [jensen_shannon(row, mean_dist) for row in matrix]
    
    # Per-outcome stats
    per_outcome_std = {}
    per_outcome_mad = {}
    for col_idx, o in enumerate(outcomes):
        vals = [row[col_idx] for row in matrix]
        mean_v = sum(vals) / n
        var = sum((v - mean_v) ** 2 for v in vals) / n
        per_outcome_std[o] = math.sqrt(var)
        per_outcome_mad[o] = sum(abs(v - mean_v) for v in vals) / n
    
    return {
        'jsd_mean': sum(jsds) / len(jsds) if jsds else None,
        'per_outcome_std': per_outcome_std,
        'per_outcome_mad': per_outcome_mad,
        'n_bookmakers': n,
    }


def calculate_bdi_metrics_main3_format(df: pd.DataFrame, snapshot_date: str) -> pd.DataFrame:
    """
    Calcula métricas BDI y genera CSV en FORMATO MAIN3.
    
    Genera una fila por cada mercado (Over X.X, Under X.X) con:
    - Partido, Fecha, Mercado, Mejor_Cuota, Cuota_Promedio, BDI_jsd_fair, etc.
    - Todas_Las_Cuotas con detalle de cada bookmaker
    """
    import pytz
    
    if df.empty:
        return pd.DataFrame()
    
    tz_colombia = pytz.timezone("America/Bogota")
    results = []
    
    # Agrupar por partido + línea
    df['market_key'] = df['match_id'] + '_' + df['line'].astype(str)
    
    for market_key, group in df.groupby('market_key'):
        if len(group) < 2:
            continue
        
        first = group.iloc[0]
        partido = f"{first['home_team']} vs {first['away_team']}"
        
        # Convertir fecha a Colombia
        try:
            utc_time = datetime.fromisoformat(first['commence_time'].replace('Z', '+00:00'))
            col_time = utc_time.astimezone(tz_colombia)
            fecha_col = col_time.strftime('%Y-%m-%d %H:%M:%S')
        except:
            fecha_col = first['commence_time']
        
        line = first['line']
        league = first['league_name']
        
        # Construir lista de odds por bookmaker para BDI "fair"
        bookmaker_odds_list = []
        over_details = []
        under_details = []
        
        for _, row in group.iterrows():
            bookie = row['bookmaker']
            over_o = row['over_odds']
            under_o = row['under_odds']
            
            bookmaker_odds_list.append({
                f"Over {line}": over_o,
                f"Under {line}": under_o
            })
            over_details.append((bookie, over_o))
            under_details.append((bookie, under_o))
        
        # Calcular BDI fair (usando pares Over/Under)
        bdi_fair_res = bookmaker_disagreement_local(bookmaker_odds_list)
        bdi_jsd_fair = bdi_fair_res.get('jsd_mean')
        bdi_n_fair = bdi_fair_res.get('n_bookmakers')
        bdi_std_fair = bdi_fair_res.get('per_outcome_std', {})
        bdi_mad_fair = bdi_fair_res.get('per_outcome_mad', {})
        
        # === Generar fila para OVER ===
        over_odds_list = [o for _, o in over_details]
        best_over = max(over_details, key=lambda x: x[1])
        avg_over = np.mean(over_odds_list)
        
        # BDI raw para Over (solo con Over, usando "other" side)
        over_raw_list = []
        for bookie, o in over_details:
            p = 1.0 / o
            other = 1.0 / max(1e-9, 1.0 - p)
            over_raw_list.append({f"Over {line}": o, f"Over {line}_other": other})
        bdi_over_raw = bookmaker_disagreement_local(over_raw_list)
        
        # Volatilidad y margen
        volatility_over = np.std(over_odds_list) if len(over_odds_list) > 1 else 0
        margin_over = (1/best_over[1] + 1/min(u for _, u in under_details) - 1) * 100 if under_details else 0
        
        # Todas las cuotas formateadas
        over_all_odds = "; ".join([f"{b}:{o:.4f}" for b, o in sorted(over_details, key=lambda x: -x[1])])
        
        results.append({
            'Partido': partido,
            'Fecha_Hora_Colombia': fecha_col,
            'Mercado': f"Over {line}",
            'Mejor_Cuota': best_over[1],
            'Cuota_Promedio_Mercado': round(avg_over, 4),
            'BDI_jsd_fair': bdi_jsd_fair,
            'BDI_n_bookmakers_fair': bdi_n_fair,
            'BDI_std_p_fair': bdi_std_fair.get(f"Over {line}"),
            'BDI_mad_p_fair': bdi_mad_fair.get(f"Over {line}"),
            'BDI_jsd': bdi_over_raw.get('jsd_mean'),
            'BDI_n_bookmakers': bdi_over_raw.get('n_bookmakers'),
            'BDI_std_p': bdi_over_raw.get('per_outcome_std', {}).get(f"Over {line}"),
            'BDI_mad_p': bdi_over_raw.get('per_outcome_mad', {}).get(f"Over {line}"),
            'Mejor_Casa': best_over[0],
            'Num_Casas': len(over_details),
            'Diferencia_Cuota_Promedio': round(best_over[1] - avg_over, 4),
            'Volatilidad_Pct': round(volatility_over, 4),
            'Margen_Casa_Pct': round(margin_over, 2),
            'Liga': league,
            'Tipo_Mercado': 'Goles (Over/Under)',
            'Snapshot_Date': snapshot_date,
            'Todas_Las_Cuotas': over_all_odds
        })
        
        # === Generar fila para UNDER ===
        under_odds_list = [o for _, o in under_details]
        best_under = max(under_details, key=lambda x: x[1])
        avg_under = np.mean(under_odds_list)
        
        # BDI raw para Under
        under_raw_list = []
        for bookie, o in under_details:
            p = 1.0 / o
            other = 1.0 / max(1e-9, 1.0 - p)
            under_raw_list.append({f"Under {line}": o, f"Under {line}_other": other})
        bdi_under_raw = bookmaker_disagreement_local(under_raw_list)
        
        volatility_under = np.std(under_odds_list) if len(under_odds_list) > 1 else 0
        margin_under = (1/best_under[1] + 1/min(o for _, o in over_details) - 1) * 100 if over_details else 0
        
        under_all_odds = "; ".join([f"{b}:{o:.4f}" for b, o in sorted(under_details, key=lambda x: -x[1])])
        
        results.append({
            'Partido': partido,
            'Fecha_Hora_Colombia': fecha_col,
            'Mercado': f"Under {line}",
            'Mejor_Cuota': best_under[1],
            'Cuota_Promedio_Mercado': round(avg_under, 4),
            'BDI_jsd_fair': bdi_jsd_fair,
            'BDI_n_bookmakers_fair': bdi_n_fair,
            'BDI_std_p_fair': bdi_std_fair.get(f"Under {line}"),
            'BDI_mad_p_fair': bdi_mad_fair.get(f"Under {line}"),
            'BDI_jsd': bdi_under_raw.get('jsd_mean'),
            'BDI_n_bookmakers': bdi_under_raw.get('n_bookmakers'),
            'BDI_std_p': bdi_under_raw.get('per_outcome_std', {}).get(f"Under {line}"),
            'BDI_mad_p': bdi_under_raw.get('per_outcome_mad', {}).get(f"Under {line}"),
            'Mejor_Casa': best_under[0],
            'Num_Casas': len(under_details),
            'Diferencia_Cuota_Promedio': round(best_under[1] - avg_under, 4),
            'Volatilidad_Pct': round(volatility_under, 4),
            'Margen_Casa_Pct': round(margin_under, 2),
            'Liga': league,
            'Tipo_Mercado': 'Goles (Over/Under)',
            'Snapshot_Date': snapshot_date,
            'Todas_Las_Cuotas': under_all_odds
        })
    
    return pd.DataFrame(results)


def get_fridays_in_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    """Obtiene todos los viernes entre dos fechas."""
    fridays = []
    current = start_date
    
    # Ajustar al primer viernes
    days_until_friday = (4 - current.weekday()) % 7
    current = current + timedelta(days=days_until_friday)
    
    while current <= end_date:
        fridays.append(current)
        current += timedelta(days=7)
    
    return fridays


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """CLI para análisis histórico de odds con THE_ODDS_API"""
    load_dotenv(override=True)
    
    if not os.getenv('THE_ODDS_API_KEY'):
        click.echo("❌ Error: THE_ODDS_API_KEY no encontrada en .env")
        sys.exit(1)


@cli.command()
def check_access():
    """Verificar acceso a historical odds API"""
    async def _run():
        click.echo("🔍 Verificando acceso a Historical Odds API...\n")
        
        api_key = os.getenv('THE_ODDS_API_KEY')
        client = HistoricalOddsClient(api_key)
        
        # Probar con una fecha conocida (ej: 1 de diciembre 2025)
        test_date = datetime(2025, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        click.echo(f"📅 Probando snapshot para: {test_date.strftime('%Y-%m-%d %H:%M')} UTC")
        
        events, timestamp = await client.get_historical_odds(
            sport_key="soccer_epl",
            snapshot_date=test_date,
            markets="totals",
            regions="eu"  # Solo 1 región para minimizar costo
        )
        
        if events is not None:
            click.echo(f"✅ Acceso confirmado!")
            click.echo(f"   Timestamp del snapshot: {timestamp}")
            click.echo(f"   Eventos encontrados: {len(events)}")
            if client.requests_remaining:
                click.echo(f"   Requests restantes: {client.requests_remaining}")
        else:
            click.echo("❌ No se pudo acceder a historical odds")
            click.echo("   Posibles causas:")
            click.echo("   - Plan gratuito (historical requiere plan de pago)")
            click.echo("   - API key inválida")
            click.echo("   - Fecha fuera de rango disponible")
        
        await client.close()
    
    asyncio.run(_run())


@cli.command()
@click.option('--month', '-m', default=None, type=click.IntRange(1, 12),
              help='Mes específico a analizar (1-12). Si no se especifica, analiza todos los meses del período.')
@click.option('--year', '-y', default=2025, type=int,
              help='Año a analizar, default: 2025')
@click.option('--hours-ahead', '-h', default=50, type=click.IntRange(1, 168),
              help='Horas hacia adelante para filtrar partidos, default: 50')
@click.option('--output-dir', '-o', default='historical_analysis',
              help='Directorio de salida para los CSVs')
@click.option('--single-date', type=str, default=None,
              help='Analizar solo una fecha específica (formato: YYYY-MM-DD)')
@click.option('--dry-run', is_flag=True, 
              help='Solo mostrar fechas sin hacer llamadas API')
def analyze(month, year, hours_ahead, output_dir, single_date, dry_run):
    """
    Analiza odds históricos (Over/Under) para cada viernes del mes especificado.
    
    Simula ejecutar análisis de mercados totals en cada viernes.
    
    IMPORTANTE: Cada llamada a historical odds cuesta 10x más que la API normal.
    Con 4 regiones y 1 market (totals) = 40 créditos por liga por viernes.
    
    Ejemplos:
        python main6.py analyze --month 1 --year 2025   # Enero 2025
        python main6.py analyze --month 3               # Marzo 2025
        python main6.py analyze --year 2025             # Ene-Jun 2025 completo
        python main6.py analyze --start-month 7 --end-month 12 --year 2025
    """
    async def _run():
        click.echo("=" * 70)
        click.echo("📊 ANÁLISIS HISTÓRICO DE ODDS (Over/Under) - THE_ODDS_API")
        click.echo("=" * 70)
        
        # Nombres de meses en español
        MONTH_NAMES = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        
        # Determinar fechas a analizar
        if single_date:
            try:
                target_date = datetime.strptime(single_date, "%Y-%m-%d")
                target_date = target_date.replace(hour=12, minute=0, second=0, tzinfo=timezone.utc)
                fridays = [target_date]
                click.echo(f"\n📅 Analizando fecha única: {single_date}")
            except ValueError:
                click.echo(f"❌ Formato de fecha inválido: {single_date}")
                click.echo("   Usar formato: YYYY-MM-DD")
                return
        elif month:
            # Mes específico
            start_date = datetime(year, month, 1, tzinfo=timezone.utc)
            if month == 12:
                end_date = datetime(year, 12, 31, tzinfo=timezone.utc)
            else:
                end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc) - timedelta(days=1)
            
            fridays = get_fridays_in_range(start_date, end_date)
            
            click.echo(f"\n📅 Mes: {MONTH_NAMES[month]} {year}")
            click.echo(f"📅 Viernes a analizar: {len(fridays)}")
        else:
            # Período completo: Enero-Junio 2025
            start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(year, 6, 30, tzinfo=timezone.utc)
            
            fridays = get_fridays_in_range(start_date, end_date)
            
            click.echo(f"\n📅 Período: {MONTH_NAMES[1]} - {MONTH_NAMES[6]} {year}")
            click.echo(f"📅 Viernes a analizar: {len(fridays)}")
        
        click.echo(f"⏰ Hours-ahead: {hours_ahead}")
        click.echo(f"📁 Output: {output_dir}/")
        click.echo(f"🏟️  Ligas: {len(SOCCER_LEAGUES)}")
        
        # Estimar costo
        # 4 regiones * 1 market * 10 = 40 créditos por liga
        # Total por viernes = 40 * num_ligas
        cost_per_friday = 40 * len(SOCCER_LEAGUES)
        total_cost = cost_per_friday * len(fridays)
        
        click.echo(f"\n💰 Costo estimado:")
        click.echo(f"   Por viernes: ~{cost_per_friday} créditos (40 × {len(SOCCER_LEAGUES)} ligas)")
        click.echo(f"   Total: ~{total_cost} créditos")
        
        click.echo(f"\n📋 Viernes a procesar:")
        for i, friday in enumerate(fridays, 1):
            click.echo(f"   {i}. {friday.strftime('%Y-%m-%d')} ({friday.strftime('%A')})")
        
        if dry_run:
            click.echo("\n⚠️  Modo DRY-RUN: No se harán llamadas API")
            return
        
        # Confirmar
        click.echo("")
        if not click.confirm("¿Continuar con el análisis?"):
            click.echo("❌ Cancelado")
            return
        
        # Crear directorio de salida
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        api_key = os.getenv('THE_ODDS_API_KEY')
        client = HistoricalOddsClient(api_key)
        
        all_summaries = []
        
        for friday_idx, friday in enumerate(fridays, 1):
            click.echo(f"\n{'='*60}")
            click.echo(f"📅 [{friday_idx}/{len(fridays)}] Procesando {friday.strftime('%Y-%m-%d')} ({friday.strftime('%A')})")
            click.echo("="*60)
            
            # Configurar snapshot a las 12:00 UTC del viernes
            snapshot_date = friday.replace(hour=12, minute=0, second=0)
            
            # Partidos desde el viernes hasta hours_ahead después
            commence_from = snapshot_date
            commence_to = snapshot_date + timedelta(hours=hours_ahead)
            
            click.echo(f"   Snapshot: {snapshot_date.strftime('%Y-%m-%dT%H:%M:%SZ')}")
            click.echo(f"   Partidos: {commence_from.strftime('%Y-%m-%d %H:%M')} → {commence_to.strftime('%Y-%m-%d %H:%M')} UTC")
            
            all_records = []
            
            for league_key, league_name in SOCCER_LEAGUES:
                try:
                    events, timestamp = await client.get_historical_odds(
                        sport_key=league_key,
                        snapshot_date=snapshot_date,
                        commence_time_from=commence_from,
                        commence_time_to=commence_to,
                        markets="totals",
                        regions="eu,us,uk,au"
                    )
                    
                    if events:
                        records = client.parse_totals_from_events(
                            events, 
                            league_name, 
                            snapshot_date.strftime("%Y-%m-%d")
                        )
                        all_records.extend(records)
                        click.echo(f"   ✅ {league_name}: {len(events)} eventos, {len(records)} odds")
                    
                    # Pequeña pausa entre requests
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    click.echo(f"   ⚠️  {league_name}: Error - {e}")
                    continue
            
            if client.requests_remaining:
                click.echo(f"\n   📊 Requests restantes: {client.requests_remaining}")
            
            if not all_records:
                click.echo(f"   ⚠️  No se encontraron datos para este viernes")
                continue
            
            # Crear DataFrame
            df = pd.DataFrame([vars(r) for r in all_records])
            
            # Calcular métricas BDI en formato main3
            click.echo(f"   📈 Calculando métricas BDI (formato main3)...")
            snapshot_str = friday.strftime('%Y-%m-%d')
            df_analyzed = calculate_bdi_metrics_main3_format(df, snapshot_str)
            
            if df_analyzed.empty:
                click.echo(f"   ⚠️  No hay mercados con suficientes bookmakers")
                continue
            
            # Filtrar línea 2.5 (más común) - buscar en columna Mercado
            df_25 = df_analyzed[df_analyzed['Mercado'].str.contains('2.5', na=False)].copy()
            
            # Determinar carpeta del mes
            friday_month = friday.month
            month_folder = MONTH_FOLDERS.get(friday_month, str(friday_month))
            month_path = output_path / str(year) / month_folder
            month_path.mkdir(parents=True, exist_ok=True)
            
            # Guardar datos raw para reprocesamiento futuro
            raw_filename = f"raw_{friday.strftime('%Y%m%d')}.csv"
            raw_path = month_path / raw_filename
            df.to_csv(raw_path, index=False)
            click.echo(f"   💾 Raw guardado: {raw_path}")
            
            # Guardar CSV analizado (formato main3)
            csv_filename = f"historical_{friday.strftime('%Y%m%d')}.csv"
            csv_path = month_path / csv_filename
            df_analyzed.to_csv(csv_path, index=False)
            click.echo(f"   💾 Guardado: {csv_path}")
            
            # Resumen
            summary = {
                'date': friday.strftime('%Y-%m-%d'),
                'day': friday.strftime('%A'),
                'total_markets': len(df_analyzed),
                'markets_25': len(df_25),
                'unique_matches': df_analyzed['Partido'].nunique(),
                'avg_bookmakers': df_analyzed['Num_Casas'].mean().round(1),
                'avg_bdi_fair': df_analyzed['BDI_jsd_fair'].mean() if df_analyzed['BDI_jsd_fair'].notna().any() else 0,
                'max_bdi_fair': df_analyzed['BDI_jsd_fair'].max() if df_analyzed['BDI_jsd_fair'].notna().any() else 0,
            }
            all_summaries.append(summary)
            
            click.echo(f"\n   📊 Resumen:")
            click.echo(f"      Mercados totales: {summary['total_markets']}")
            click.echo(f"      Mercados línea 2.5: {summary['markets_25']}")
            click.echo(f"      Partidos únicos: {summary['unique_matches']}")
            click.echo(f"      Promedio bookmakers: {summary['avg_bookmakers']}")
            click.echo(f"      BDI_fair promedio: {summary['avg_bdi_fair']:.6f}" if summary['avg_bdi_fair'] else "      BDI_fair promedio: N/A")
            
            # Top 5 por BDI
            if not df_25.empty and df_25['BDI_jsd_fair'].notna().any():
                top5 = df_25.nlargest(5, 'BDI_jsd_fair')
                click.echo(f"\n   🔥 Top 5 mercados (línea 2.5) por BDI_fair:")
                for _, row in top5.iterrows():
                    click.echo(f"      • {row['Partido']} - {row['Mercado']}")
                    click.echo(f"        BDI: {row['BDI_jsd_fair']:.6f} | {row['Num_Casas']} casas")
        
        # Guardar resumen general
        if all_summaries:
            summary_df = pd.DataFrame(all_summaries)
            year_path = output_path / str(year)
            year_path.mkdir(parents=True, exist_ok=True)
            
            summary_path = year_path / "resumen_general.csv"
            summary_df.to_csv(summary_path, index=False)
            
            click.echo(f"\n{'='*60}")
            click.echo("📊 RESUMEN GENERAL")
            click.echo("="*60)
            click.echo(f"Viernes procesados: {len(all_summaries)}")
            click.echo(f"Total mercados: {summary_df['total_markets'].sum()}")
            click.echo(f"BDI_fair promedio global: {summary_df['avg_bdi_fair'].mean():.6f}")
            click.echo(f"\n💾 Resumen guardado: {summary_path}")
        
        await client.close()
        click.echo(f"\n✅ Análisis histórico completado")
    
    asyncio.run(_run())


@cli.command()
@click.argument('csv_files', nargs=-1, type=click.Path(exists=True))
@click.option('--output', '-o', default='consolidated_analysis.csv',
              help='Archivo CSV de salida consolidado')
def consolidate(csv_files, output):
    """
    Consolida múltiples CSVs históricos en uno solo.
    
    Ejemplo:
        python main6.py consolidate historical_analysis/*.csv -o all_fridays.csv
    """
    if not csv_files:
        click.echo("❌ No se especificaron archivos CSV")
        return
    
    click.echo(f"📁 Consolidando {len(csv_files)} archivos...")
    
    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dfs.append(df)
            click.echo(f"   ✅ {csv_file}: {len(df)} filas")
        except Exception as e:
            click.echo(f"   ⚠️  {csv_file}: Error - {e}")
    
    if not dfs:
        click.echo("❌ No se pudo leer ningún archivo")
        return
    
    consolidated = pd.concat(dfs, ignore_index=True)
    consolidated.to_csv(output, index=False)
    
    click.echo(f"\n💾 Consolidado guardado: {output}")
    click.echo(f"   Total filas: {len(consolidated)}")
    if 'Snapshot_Date' in consolidated.columns:
        click.echo(f"   Fechas únicas: {consolidated['Snapshot_Date'].nunique()}")


@cli.command()
@click.option('--year', '-y', default=2025, type=int, help='Año a estimar')
def estimate_cost(year):
    """Estimar costo de créditos por mes para Enero-Junio"""
    click.echo("💰 ESTIMACIÓN DE COSTOS - Historical Odds API (Over/Under)")
    click.echo("=" * 60)
    
    MONTH_NAMES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 
        4: "Abril", 5: "Mayo", 6: "Junio"
    }
    
    click.echo(f"\n📅 Período: Enero - Junio {year}")
    click.echo(f"🏟️  Ligas: {len(SOCCER_LEAGUES)}")
    click.echo(f"📊 Market: totals (Over/Under) únicamente")
    
    # Costo: 10 créditos × 4 regiones × 1 market = 40 por liga
    cost_per_league = 10 * 4 * 1
    cost_per_friday = cost_per_league * len(SOCCER_LEAGUES)
    
    click.echo(f"\n💳 Fórmula:")
    click.echo(f"   Por liga: 10 × 4 regiones × 1 market = {cost_per_league} créditos")
    click.echo(f"   Por viernes: {cost_per_league} × {len(SOCCER_LEAGUES)} ligas = {cost_per_friday} créditos")
    
    click.echo(f"\n" + "="*60)
    click.echo(f"{'Mes':<12} {'Viernes':>10} {'Costo':>15} {'Comando':>20}")
    click.echo("="*60)
    
    total_fridays = 0
    total_cost = 0
    
    for m in range(1, 7):
        start = datetime(year, m, 1)
        if m == 12:
            end = datetime(year, 12, 31)
        else:
            end = datetime(year, m + 1, 1) - timedelta(days=1)
        
        fridays = get_fridays_in_range(start, end)
        month_cost = cost_per_friday * len(fridays)
        total_fridays += len(fridays)
        total_cost += month_cost
        
        cmd = f"--month {m}"
        click.echo(f"{MONTH_NAMES[m]:<12} {len(fridays):>10} {month_cost:>12,} cr  {cmd:>20}")
    
    click.echo("="*60)
    click.echo(f"{'TOTAL':<12} {total_fridays:>10} {total_cost:>12,} cr")
    
    click.echo(f"\n📊 Planes THE_ODDS_API (referencia):")
    click.echo(f"   Free: 500 créditos/mes")
    click.echo(f"   Starter: 10,000 créditos/mes ($19/mes)")
    click.echo(f"   Pro: 50,000 créditos/mes ($79/mes)")
    
    click.echo(f"\n💡 Recomendación:")
    avg_month_cost = total_cost // 6
    if avg_month_cost <= 500:
        click.echo(f"   ✅ Plan Free suficiente (~{avg_month_cost} cr/mes promedio)")
    elif avg_month_cost <= 10000:
        click.echo(f"   ⚠️  Plan Starter recomendado (~{avg_month_cost} cr/mes promedio)")
    else:
        click.echo(f"   ⚠️  Plan Pro recomendado (~{avg_month_cost} cr/mes promedio)")
    
    click.echo(f"\n📝 Ejemplo de uso:")
    click.echo(f"   python main6.py analyze --month 1 --year {year}   # Solo Enero")
    click.echo(f"   python main6.py analyze --month 3 --year {year}   # Solo Marzo")
    click.echo(f"   python main6.py analyze --year {year}             # Ene-Jun completo")


@cli.command()
@click.argument('raw_dir', type=click.Path(exists=True))
@click.option('--output-suffix', '-s', default='_reprocessed',
              help='Sufijo para archivos reprocesados')
def reprocess(raw_dir, output_suffix):
    """
    Reprocesa archivos raw_*.csv sin hacer llamadas API.
    
    Útil cuando se cambió la lógica de cálculo de BDI o el formato de salida.
    
    Ejemplo:
        python main6.py reprocess historical_analysis/2025/enero/
    """
    from pathlib import Path
    
    raw_path = Path(raw_dir)
    raw_files = list(raw_path.glob("raw_*.csv"))
    
    if not raw_files:
        click.echo(f"❌ No se encontraron archivos raw_*.csv en {raw_dir}")
        return
    
    click.echo(f"📁 Encontrados {len(raw_files)} archivos raw")
    
    for raw_file in sorted(raw_files):
        click.echo(f"\n📄 Procesando: {raw_file.name}")
        
        try:
            df = pd.read_csv(raw_file)
            
            # Extraer fecha del nombre del archivo
            date_str = raw_file.stem.replace('raw_', '')
            snapshot_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            click.echo(f"   📈 Calculando métricas BDI...")
            df_analyzed = calculate_bdi_metrics_main3_format(df, snapshot_str)
            
            if df_analyzed.empty:
                click.echo(f"   ⚠️  No hay mercados con suficientes datos")
                continue
            
            # Guardar con nuevo formato
            output_name = f"historical_{date_str}{output_suffix}.csv"
            output_path = raw_file.parent / output_name
            df_analyzed.to_csv(output_path, index=False)
            
            click.echo(f"   ✅ Guardado: {output_name}")
            click.echo(f"      Mercados: {len(df_analyzed)}")
            click.echo(f"      Partidos únicos: {df_analyzed['Partido'].nunique()}")
            
        except Exception as e:
            click.echo(f"   ❌ Error: {e}")
    
    click.echo(f"\n✅ Reprocesamiento completado")


def main():
    cli()


if __name__ == '__main__':
    main()
