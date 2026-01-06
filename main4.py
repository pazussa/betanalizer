#!/usr/bin/env python3
"""
main4.py - Análisis BDI para NFL (THE_ODDS_API)

Aplica el mismo procedimiento de análisis de main3.py pero para NFL y otros deportes.
El BDI (Bookmaker Disagreement Index) mide la divergencia entre las cuotas
de diferentes casas de apuestas usando Jensen-Shannon divergence.

Run: `python main4.py analyze` para análisis completo
     `python main4.py sports` para ver deportes disponibles
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
from dotenv import load_dotenv
import httpx
import pytz

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.models import BookmakerType
from src.disagreement import bookmaker_disagreement, remove_vig

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('betting_analysis_nba.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Deportes disponibles en THE_ODDS_API con mercados h2h (pertinentes para BDI)
AVAILABLE_SPORTS = {
    # Basketball (SIN EMPATE - ideal para BDI binario)
    "basketball_nba": {"name": "NBA", "group": "Basketball", "has_draw": False},
    "basketball_euroleague": {"name": "Euroleague", "group": "Basketball", "has_draw": False},
    "basketball_ncaab": {"name": "NCAAB", "group": "Basketball", "has_draw": False},
    "basketball_wnba": {"name": "WNBA", "group": "Basketball", "has_draw": False},
    "basketball_nbl": {"name": "NBL Australia", "group": "Basketball", "has_draw": False},
    
    # American Football (SIN EMPATE generalmente)
    "americanfootball_nfl": {"name": "NFL", "group": "American Football", "has_draw": False},
    "americanfootball_ncaaf": {"name": "NCAAF", "group": "American Football", "has_draw": False},
    
    # Ice Hockey
    "icehockey_nhl": {"name": "NHL", "group": "Ice Hockey", "has_draw": True},
    "icehockey_sweden_hockey_league": {"name": "SHL", "group": "Ice Hockey", "has_draw": True},
    
    # Baseball
    "baseball_mlb": {"name": "MLB", "group": "Baseball", "has_draw": False},
    
    # Tennis (solo 2 outcomes)
    "tennis_atp_aus_open_singles": {"name": "ATP Australian Open", "group": "Tennis", "has_draw": False},
    "tennis_wta_aus_open_singles": {"name": "WTA Australian Open", "group": "Tennis", "has_draw": False},
    
    # MMA
    "mma_mixed_martial_arts": {"name": "MMA", "group": "MMA", "has_draw": True},
    
    # Rugby
    "rugbyleague_nrl": {"name": "NRL", "group": "Rugby League", "has_draw": True},
}


@dataclass
class SportMatch:
    """Representa un partido/evento de cualquier deporte"""
    id: str
    sport_key: str
    sport_title: str
    home_team: str
    away_team: str
    commence_time: datetime
    bookmakers_data: List[Dict] = None
    
    def __post_init__(self):
        if self.bookmakers_data is None:
            self.bookmakers_data = []


@dataclass
class MatchAnalysisResult:
    """Resultado del análisis de un partido"""
    match: SportMatch
    market: str  # 'h2h', 'totals', 'spreads'
    market_name: str  # e.g., 'Moneyline', 'Over 220.5'
    best_odds: float
    best_bookmaker: str
    avg_odds: float
    n_bookmakers: int
    BDI_jsd_fair: Optional[float]
    BDI_n_bookmakers_fair: Optional[int]
    BDI_std_p_fair: Optional[float]
    BDI_mad_p_fair: Optional[float]
    all_odds: Dict[str, float]  # bookmaker -> odds
    implied_prob: float
    volatility_pct: float


class TheOddsAPISportClient:
    """
    Cliente para THE_ODDS_API para cualquier deporte
    """
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self):
        self.api_key = os.getenv("THE_ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("THE_ODDS_API_KEY no encontrada en .env")
        self.client = httpx.AsyncClient(timeout=60.0)
        self.remaining_requests = None
    
    async def close(self):
        await self.client.aclose()
    
    async def get_sports(self) -> List[Dict]:
        """Obtener lista de deportes disponibles"""
        url = f"{self.BASE_URL}/sports"
        params = {"apiKey": self.api_key}
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        self._update_remaining(response)
        return response.json()
    
    def _update_remaining(self, response):
        """Actualizar requests restantes"""
        if 'x-requests-remaining' in response.headers:
            self.remaining_requests = int(response.headers['x-requests-remaining'])
    
    async def get_events_with_odds(
        self, 
        sport_key: str,
        markets: str = "h2h",
        regions: str = "eu,us,uk,au"
    ) -> List[SportMatch]:
        """
        Obtener eventos con sus cuotas para un deporte específico
        
        Args:
            sport_key: Key del deporte (e.g., 'basketball_nba')
            markets: Mercados a obtener ('h2h', 'totals', 'spreads')
            regions: Regiones de bookmakers
        
        Returns:
            Lista de SportMatch con bookmakers_data poblado
        """
        url = f"{self.BASE_URL}/sports/{sport_key}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            self._update_remaining(response)
            data = response.json()
            
            matches = []
            for event in data:
                commence = datetime.fromisoformat(
                    event.get("commence_time", "").replace("Z", "+00:00")
                )
                
                match = SportMatch(
                    id=event.get("id"),
                    sport_key=event.get("sport_key"),
                    sport_title=event.get("sport_title"),
                    home_team=event.get("home_team"),
                    away_team=event.get("away_team"),
                    commence_time=commence,
                    bookmakers_data=event.get("bookmakers", [])
                )
                matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error obteniendo eventos para {sport_key}: {e}")
            return []


class SportBDIAnalyzer:
    """
    Analizador BDI para cualquier deporte de THE_ODDS_API
    """
    
    def __init__(self, sport_key: str = "americanfootball_nfl"):
        self.sport_key = sport_key
        self.sport_info = AVAILABLE_SPORTS.get(sport_key, {
            "name": sport_key,
            "group": "Unknown",
            "has_draw": False
        })
        self.client = TheOddsAPISportClient()
        self.timezone = pytz.timezone("America/Bogota")
    
    async def cleanup(self):
        await self.client.close()
    
    async def analyze_h2h_market(
        self,
        hours_ahead: int = 72,
        hours_from: int = 0
    ) -> List[MatchAnalysisResult]:
        """
        Analizar mercado H2H (Moneyline) con cálculo de BDI
        
        Para deportes sin empate (NBA, NFL, etc.), analiza Home vs Away.
        Para deportes con empate (NHL, Soccer), también considera el empate.
        """
        logger.info(f"📊 Analizando {self.sport_info['name']} - Mercado H2H...")
        
        # Obtener eventos con odds
        matches = await self.client.get_events_with_odds(
            self.sport_key, 
            markets="h2h"
        )
        
        if not matches:
            logger.warning(f"No se encontraron partidos para {self.sport_key}")
            return []
        
        # Filtrar por tiempo
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(hours=hours_from)
        end_time = now + timedelta(hours=hours_ahead)
        
        matches = [
            m for m in matches
            if start_time <= m.commence_time <= end_time
        ]
        
        logger.info(f"  📅 {len(matches)} partidos en las próximas {hours_ahead}h")
        
        results = []
        
        for match in matches:
            # Extraer odds por bookmaker para cada outcome
            home_odds = {}
            away_odds = {}
            draw_odds = {} if self.sport_info['has_draw'] else None
            
            for bm_data in match.bookmakers_data:
                bm_key = bm_data.get("key")
                
                for market_data in bm_data.get("markets", []):
                    if market_data.get("key") != "h2h":
                        continue
                    
                    outcomes = market_data.get("outcomes", [])
                    for outcome in outcomes:
                        name = outcome.get("name")
                        price = outcome.get("price")
                        
                        if name == match.home_team:
                            home_odds[bm_key] = price
                        elif name == match.away_team:
                            away_odds[bm_key] = price
                        elif name == "Draw" and draw_odds is not None:
                            draw_odds[bm_key] = price
            
            # Análisis para Home win
            if home_odds:
                result = self._analyze_outcome(
                    match=match,
                    outcome_name=f"Home ({match.home_team})",
                    main_odds=home_odds,
                    opponent_odds=away_odds,
                    draw_odds=draw_odds
                )
                if result:
                    results.append(result)
            
            # Análisis para Away win
            if away_odds:
                result = self._analyze_outcome(
                    match=match,
                    outcome_name=f"Away ({match.away_team})",
                    main_odds=away_odds,
                    opponent_odds=home_odds,
                    draw_odds=draw_odds
                )
                if result:
                    results.append(result)
        
        # Ordenar por BDI_jsd_fair descendente (mayor disagreement = más interesante)
        results.sort(
            key=lambda x: x.BDI_jsd_fair if x.BDI_jsd_fair is not None else -1,
            reverse=True
        )
        
        return results
    
    async def analyze_totals_market(
        self,
        hours_ahead: int = 72,
        hours_from: int = 0
    ) -> List[MatchAnalysisResult]:
        """
        Analizar mercado Totals (Over/Under) con cálculo de BDI
        """
        logger.info(f"📊 Analizando {self.sport_info['name']} - Mercado Totals...")
        
        matches = await self.client.get_events_with_odds(
            self.sport_key,
            markets="totals"
        )
        
        if not matches:
            logger.warning(f"No se encontraron partidos para {self.sport_key}")
            return []
        
        # Filtrar por tiempo
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(hours=hours_from)
        end_time = now + timedelta(hours=hours_ahead)
        
        matches = [
            m for m in matches
            if start_time <= m.commence_time <= end_time
        ]
        
        logger.info(f"  📅 {len(matches)} partidos con totals")
        
        results = []
        
        for match in matches:
            # Agrupar por línea (point)
            lines = {}  # {point: {"Over": {bm: odds}, "Under": {bm: odds}}}
            
            for bm_data in match.bookmakers_data:
                bm_key = bm_data.get("key")
                
                for market_data in bm_data.get("markets", []):
                    if market_data.get("key") != "totals":
                        continue
                    
                    for outcome in market_data.get("outcomes", []):
                        name = outcome.get("name")  # "Over" o "Under"
                        point = outcome.get("point")
                        price = outcome.get("price")
                        
                        if point is None:
                            continue
                        
                        if point not in lines:
                            lines[point] = {"Over": {}, "Under": {}}
                        
                        if name in ["Over", "Under"]:
                            lines[point][name][bm_key] = price
            
            # Analizar cada línea
            for point, data in lines.items():
                over_odds = data.get("Over", {})
                under_odds = data.get("Under", {})
                
                # Análisis Over
                if over_odds and under_odds:
                    result = self._analyze_outcome(
                        match=match,
                        outcome_name=f"Over {point}",
                        main_odds=over_odds,
                        opponent_odds=under_odds,
                        draw_odds=None,
                        market="totals"
                    )
                    if result:
                        results.append(result)
                    
                    # Análisis Under
                    result = self._analyze_outcome(
                        match=match,
                        outcome_name=f"Under {point}",
                        main_odds=under_odds,
                        opponent_odds=over_odds,
                        draw_odds=None,
                        market="totals"
                    )
                    if result:
                        results.append(result)
        
        # Ordenar por BDI_jsd_fair descendente
        results.sort(
            key=lambda x: x.BDI_jsd_fair if x.BDI_jsd_fair is not None else -1,
            reverse=True
        )
        
        return results
    
    def _analyze_outcome(
        self,
        match: SportMatch,
        outcome_name: str,
        main_odds: Dict[str, float],
        opponent_odds: Dict[str, float],
        draw_odds: Optional[Dict[str, float]] = None,
        market: str = "h2h"
    ) -> Optional[MatchAnalysisResult]:
        """
        Analizar un outcome específico calculando BDI fair
        
        El BDI se calcula usando las probabilidades fair (sin vig)
        de todos los bookmakers que tienen cuotas para AMBOS lados.
        """
        if not main_odds:
            return None
        
        # Encontrar bookmakers que tienen ambos lados (para calcular fair odds)
        common_bookmakers = set(main_odds.keys()) & set(opponent_odds.keys())
        if draw_odds:
            common_bookmakers &= set(draw_odds.keys())
        
        if len(common_bookmakers) < 2:
            # Necesitamos al menos 2 bookmakers para calcular BDI
            return None
        
        # Construir lista de odds por bookmaker para BDI
        bookmaker_odds_list = []
        for bm in common_bookmakers:
            if draw_odds:
                odds_dict = {
                    "main": main_odds[bm],
                    "opponent": opponent_odds[bm],
                    "draw": draw_odds[bm]
                }
            else:
                odds_dict = {
                    "main": main_odds[bm],
                    "opponent": opponent_odds[bm]
                }
            bookmaker_odds_list.append(odds_dict)
        
        # Calcular BDI usando fair probabilities
        bdi_result = bookmaker_disagreement(bookmaker_odds_list)
        
        # Extraer std y mad promedio de los diccionarios
        std_dict = bdi_result.get('per_outcome_std', {})
        mad_dict = bdi_result.get('per_outcome_mad', {})
        
        # Calcular promedio de los std/mad por outcome
        bdi_std_p_fair = None
        bdi_mad_p_fair = None
        if std_dict:
            bdi_std_p_fair = sum(std_dict.values()) / len(std_dict)
        if mad_dict:
            bdi_mad_p_fair = sum(mad_dict.values()) / len(mad_dict)
        
        # Estadísticas de las cuotas
        odds_values = list(main_odds.values())
        best_odds = max(odds_values)
        avg_odds = sum(odds_values) / len(odds_values)
        best_bookmaker = max(main_odds.keys(), key=lambda k: main_odds[k])
        
        # Volatilidad
        if len(odds_values) > 1:
            import statistics
            volatility = (statistics.stdev(odds_values) / avg_odds) * 100
        else:
            volatility = 0.0
        
        # Probabilidad implícita promedio
        implied_prob = (1 / avg_odds) * 100
        
        return MatchAnalysisResult(
            match=match,
            market=market,
            market_name=outcome_name,
            best_odds=best_odds,
            best_bookmaker=best_bookmaker,
            avg_odds=avg_odds,
            n_bookmakers=len(main_odds),
            BDI_jsd_fair=bdi_result.get('jsd_mean'),
            BDI_n_bookmakers_fair=bdi_result.get('n_bookmakers'),
            BDI_std_p_fair=bdi_std_p_fair,
            BDI_mad_p_fair=bdi_mad_p_fair,
            all_odds=main_odds,
            implied_prob=implied_prob,
            volatility_pct=volatility
        )


def results_to_dataframe(results: List[MatchAnalysisResult], tz_name: str = "America/Bogota") -> pd.DataFrame:
    """Convertir resultados a DataFrame con el mismo formato que main3.py"""
    tz = pytz.timezone(tz_name)
    
    rows = []
    for r in results:
        fecha_local = r.match.commence_time.astimezone(tz)
        
        # Formatear cuotas
        all_odds_str = "; ".join([f"{k}:{v:.2f}" for k, v in sorted(r.all_odds.items())])
        
        rows.append({
            "Partido": f"{r.match.home_team} vs {r.match.away_team}",
            "Fecha_Hora_Colombia": fecha_local.strftime('%Y-%m-%d %H:%M:%S'),
            "Mercado": r.market_name,
            "Mejor_Cuota": r.best_odds,
            "Cuota_Promedio_Mercado": round(r.avg_odds, 4),
            "BDI_jsd_fair": round(r.BDI_jsd_fair, 6) if r.BDI_jsd_fair else None,
            "BDI_n_bookmakers_fair": r.BDI_n_bookmakers_fair,
            "BDI_std_p_fair": round(r.BDI_std_p_fair, 6) if r.BDI_std_p_fair else None,
            "BDI_mad_p_fair": round(r.BDI_mad_p_fair, 6) if r.BDI_mad_p_fair else None,
            "Mejor_Casa": r.best_bookmaker,
            "Num_Casas": r.n_bookmakers,
            "Prob_Implicita_Pct": round(r.implied_prob, 2),
            "Volatilidad_Pct": round(r.volatility_pct, 2),
            "Deporte": r.match.sport_title,
            "Tipo_Mercado": r.market,
            "Todas_Las_Cuotas": all_odds_str
        })
    
    df = pd.DataFrame(rows)
    
    # Ordenar por BDI_jsd_fair descendente
    if not df.empty and 'BDI_jsd_fair' in df.columns:
        df = df.sort_values('BDI_jsd_fair', ascending=False, na_position='last')
    
    return df


# ============== CLI ==============

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """CLI para análisis BDI de deportes (THE_ODDS_API)"""
    load_dotenv(override=True)
    
    if not os.getenv('THE_ODDS_API_KEY'):
        click.echo("❌ Error: THE_ODDS_API_KEY no encontrada en .env")
        sys.exit(1)


@cli.command()
def sports():
    """Listar deportes disponibles y su pertinencia para análisis BDI"""
    click.echo("🏆 DEPORTES DISPONIBLES PARA ANÁLISIS BDI\n")
    click.echo("=" * 70)
    
    # Agrupar por categoría
    groups = {}
    for key, info in AVAILABLE_SPORTS.items():
        group = info['group']
        if group not in groups:
            groups[group] = []
        groups[group].append((key, info))
    
    for group, sports in groups.items():
        click.echo(f"\n📌 {group}")
        click.echo("-" * 40)
        for key, info in sports:
            has_draw = "⚠️ Con empate" if info['has_draw'] else "✅ Sin empate"
            click.echo(f"  {info['name']:25} | {key:35} | {has_draw}")
    
    click.echo("\n" + "=" * 70)
    click.echo("\n💡 DEPORTES MÁS PERTINENTES PARA BDI:")
    click.echo("   1. 🏀 basketball_nba - Alta liquidez, sin empate, en temporada")
    click.echo("   2. 🏈 americanfootball_nfl - Playoffs en enero, sin empate")
    click.echo("   3. 🏒 icehockey_nhl - Alta liquidez (tiene empate en tiempo regular)")
    click.echo("   4. 🎾 Tennis - Sin empate, pero eventos esporádicos")
    
    click.echo("\n⚠️ El BDI funciona mejor con deportes SIN empate (distribución binaria)")
    click.echo("   Para deportes con empate, el cálculo usa 3 outcomes.")


@cli.command()
@click.option('--sport', '-s', default='americanfootball_nfl', help='Sport key a analizar')
@click.option('--hours-ahead', '-h', default=72, type=click.IntRange(1, 336))
@click.option('--hours-from', default=0, type=click.IntRange(0, 336))
@click.option('--market', '-m', default='h2h', type=click.Choice(['h2h', 'totals', 'all']))
@click.option('--export-csv/--no-csv', default=True, help='Exportar a CSV')
@click.option('--top', '-n', default=50, type=int, help='Mostrar top N resultados')
def analyze(sport, hours_ahead, hours_from, market, export_csv, top):
    """
    Análisis BDI para un deporte específico
    
    Por defecto analiza NBA. Usa --sport para cambiar.
    
    Ejemplos:
        python main4.py analyze --sport basketball_nba
        python main4.py analyze --sport americanfootball_nfl --market all
        python main4.py analyze --sport icehockey_nhl -h 168
    """
    async def _run():
        sport_info = AVAILABLE_SPORTS.get(sport, {"name": sport, "group": "Unknown"})
        
        click.echo(f"🚀 Análisis BDI para {sport_info['name']} ({sport})")
        click.echo(f"   📅 Rango: {hours_from}h a {hours_ahead}h desde ahora")
        click.echo(f"   📊 Mercado: {market}")
        click.echo("")
        
        analyzer = SportBDIAnalyzer(sport_key=sport)
        
        all_results = []
        
        try:
            if market in ['h2h', 'all']:
                h2h_results = await analyzer.analyze_h2h_market(
                    hours_ahead=hours_ahead,
                    hours_from=hours_from
                )
                all_results.extend(h2h_results)
                click.echo(f"   ✅ H2H: {len(h2h_results)} outcomes analizados")
            
            if market in ['totals', 'all']:
                totals_results = await analyzer.analyze_totals_market(
                    hours_ahead=hours_ahead,
                    hours_from=hours_from
                )
                all_results.extend(totals_results)
                click.echo(f"   ✅ Totals: {len(totals_results)} outcomes analizados")
            
            await analyzer.cleanup()
            
        except Exception as e:
            click.echo(f"❌ Error: {e}")
            await analyzer.cleanup()
            return
        
        if not all_results:
            click.echo("\n⚠️ No se encontraron resultados para analizar")
            click.echo("   Posibles causas:")
            click.echo("   - El deporte no tiene eventos en el rango de tiempo")
            click.echo("   - No hay suficientes bookmakers con cuotas")
            return
        
        # Convertir a DataFrame
        df = results_to_dataframe(all_results)
        
        # Guardar CSV
        if export_csv:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"bdi_analysis_{sport}_{timestamp}.csv"
            df.to_csv(csv_filename, index=False)
            click.echo(f"\n💾 CSV guardado: {csv_filename}")
        
        # Mostrar resumen
        click.echo("\n" + "=" * 80)
        click.echo(f"📊 TOP {min(top, len(df))} RESULTADOS ORDENADOS POR BDI_jsd_fair")
        click.echo("=" * 80)
        
        # Mostrar tabla resumida
        display_df = df.head(top)[[
            'Partido', 
            'Mercado', 
            'Mejor_Cuota', 
            'BDI_jsd_fair',
            'BDI_n_bookmakers_fair',
            'Num_Casas',
            'Volatilidad_Pct',
            'Prob_Implicita_Pct'
        ]].copy()
        
        # Formatear para display
        display_df['BDI_jsd_fair'] = display_df['BDI_jsd_fair'].apply(
            lambda x: f"{x:.6f}" if pd.notna(x) else "N/A"
        )
        
        click.echo(display_df.to_string(index=False))
        
        # Estadísticas
        click.echo("\n" + "=" * 80)
        click.echo("📈 ESTADÍSTICAS DEL BDI")
        click.echo("=" * 80)
        
        bdi_values = df['BDI_jsd_fair'].dropna()
        if len(bdi_values) > 0:
            click.echo(f"   Total outcomes analizados: {len(df)}")
            click.echo(f"   Con BDI calculado: {len(bdi_values)}")
            click.echo(f"   BDI promedio: {bdi_values.mean():.6f}")
            click.echo(f"   BDI mediana: {bdi_values.median():.6f}")
            click.echo(f"   BDI máximo: {bdi_values.max():.6f}")
            click.echo(f"   BDI mínimo: {bdi_values.min():.6f}")
        
        # Requests restantes
        if analyzer.client.remaining_requests is not None:
            click.echo(f"\n📡 THE_ODDS_API requests restantes: {analyzer.client.remaining_requests}")
        
        click.echo("\n✅ Análisis completado")
    
    asyncio.run(_run())


@cli.command()
def status():
    """Verificar estado de THE_ODDS_API y deportes en temporada"""
    async def _run():
        click.echo("🔍 Verificando estado de THE_ODDS_API...\n")
        
        client = TheOddsAPISportClient()
        
        try:
            sports = await client.get_sports()
            
            click.echo(f"✅ API conectada - {client.remaining_requests} requests restantes\n")
            click.echo("🏆 DEPORTES ACTIVOS (con eventos próximos):")
            click.echo("-" * 50)
            
            active_count = 0
            for sport in sports:
                if sport.get('active', False):
                    key = sport.get('key')
                    title = sport.get('title')
                    group = sport.get('group')
                    
                    # Marcar si está en nuestra lista de pertinentes
                    marker = "⭐" if key in AVAILABLE_SPORTS else "  "
                    click.echo(f"{marker} {title:30} | {key}")
                    active_count += 1
            
            click.echo(f"\n📊 Total deportes activos: {active_count}")
            click.echo("⭐ = Pertinente para análisis BDI")
            
            await client.close()
            
        except Exception as e:
            click.echo(f"❌ Error: {e}")
            await client.close()
    
    asyncio.run(_run())


@cli.command()
@click.option('--sport', '-s', default='americanfootball_nfl')
def quick(sport):
    """Análisis rápido mostrando solo BDI_jsd_fair (como main3.py)"""
    async def _run():
        click.echo(f"⚡ Análisis rápido de {sport}...\n")
        
        analyzer = SportBDIAnalyzer(sport_key=sport)
        
        try:
            results = await analyzer.analyze_h2h_market(hours_ahead=72)
            await analyzer.cleanup()
        except Exception as e:
            click.echo(f"❌ Error: {e}")
            await analyzer.cleanup()
            return
        
        if not results:
            click.echo("⚠️ No hay resultados")
            return
        
        df = results_to_dataframe(results)
        
        # Mostrar columnas clave
        click.echo(df[['Partido', 'Mercado', 'Mejor_Cuota', 'BDI_jsd_fair', 'Num_Casas']].head(30).to_string(index=False))
    
    asyncio.run(_run())


def main():
    cli()


if __name__ == '__main__':
    main()
