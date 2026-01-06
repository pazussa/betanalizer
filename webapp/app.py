#!/usr/bin/env python3
"""
Webapp de Análisis de Cuotas de Fútbol
Interfaz Streamlit para analizar cuotas usando THE_ODDS_API
Desplegable en Hugging Face Spaces (gratuito)
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict

import streamlit as st
import pandas as pd
import httpx
import numpy as np
from scipy import stats

# ========== CONFIGURACIÓN DE LOGGING ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== MODELOS ==========
class MarketType(str, Enum):
    DOUBLE_CHANCE_1X = "1X"
    DOUBLE_CHANCE_X2 = "X2"
    TOTALS = "totals"


class BookmakerType(str, Enum):
    PINNACLE = "pinnacle"
    BETFAIR = "betfair"
    BETFAIR_EX_EU = "betfair_ex_eu"
    BETFAIR_EX_UK = "betfair_ex_uk"
    UNIBET = "unibet"
    WILLIAM_HILL = "williamhill"
    BETSSON = "betsson"
    MARATHONBET = "marathonbet"
    BWIN = "bwin"
    LADBROKES = "ladbrokes"
    BETVICTOR = "betvictor"
    BETWAY = "betway"
    NORDICBET = "nordicbet"
    PADDYPOWER = "paddypower"
    SMARKETS = "smarkets"
    SPORT888 = "sport888"
    TIPICO = "tipico_de"
    CODERE_IT = "codere_it"
    BETMGM = "betmgm"
    BOVADA = "bovada"
    DRAFTKINGS = "draftkings"
    FANDUEL = "fanduel"
    # Agregar más según necesidad


# ========== CLIENTE API ==========
class TheOddsAPIClient:
    """Cliente para The Odds API"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    SOCCER_LEAGUES = [
        ("soccer_epl", "EPL", "England"),
        ("soccer_spain_la_liga", "La Liga", "Spain"),
        ("soccer_germany_bundesliga", "Bundesliga", "Germany"),
        ("soccer_italy_serie_a", "Serie A", "Italy"),
        ("soccer_france_ligue_one", "Ligue 1", "France"),
        ("soccer_efl_champ", "Championship", "England"),
        ("soccer_spain_segunda_division", "La Liga 2", "Spain"),
        ("soccer_germany_bundesliga2", "Bundesliga 2", "Germany"),
        ("soccer_italy_serie_b", "Serie B", "Italy"),
        ("soccer_france_ligue_two", "Ligue 2", "France"),
        ("soccer_netherlands_eredivisie", "Eredivisie", "Netherlands"),
        ("soccer_portugal_primeira_liga", "Primeira Liga", "Portugal"),
        ("soccer_belgium_first_div", "Belgium First Div", "Belgium"),
        ("soccer_turkey_super_league", "Super League", "Turkey"),
        ("soccer_greece_super_league", "Super League", "Greece"),
        ("soccer_austria_bundesliga", "Austrian Bundesliga", "Austria"),
        ("soccer_switzerland_superleague", "Swiss Superleague", "Switzerland"),
        ("soccer_denmark_superliga", "Superliga", "Denmark"),
        ("soccer_sweden_allsvenskan", "Allsvenskan", "Sweden"),
        ("soccer_norway_eliteserien", "Eliteserien", "Norway"),
        ("soccer_poland_ekstraklasa", "Ekstraklasa", "Poland"),
        ("soccer_spl", "Premiership", "Scotland"),
        ("soccer_england_league1", "League 1", "England"),
        ("soccer_england_league2", "League 2", "England"),
        ("soccer_uefa_champs_league", "Champions League", "Europe"),
        ("soccer_uefa_europa_league", "Europa League", "Europe"),
        ("soccer_uefa_europa_conference_league", "Conference League", "Europe"),
        ("soccer_brazil_campeonato", "Brasileirão", "Brazil"),
        ("soccer_argentina_primera_division", "Primera División", "Argentina"),
        ("soccer_mexico_ligamx", "Liga MX", "Mexico"),
        ("soccer_usa_mls", "MLS", "USA"),
        ("soccer_conmebol_copa_libertadores", "Copa Libertadores", "South America"),
        ("soccer_japan_j_league", "J League", "Japan"),
        ("soccer_korea_kleague1", "K League 1", "South Korea"),
        ("soccer_australia_aleague", "A-League", "Australia"),
    ]
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def get_remaining_requests(self) -> int:
        """Obtiene requests restantes"""
        try:
            url = f"{self.BASE_URL}/sports"
            params = {"apiKey": self.api_key}
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return int(response.headers.get("x-requests-remaining", 0))
        except Exception:
            return -1
    
    async def get_football_matches(self, progress_callback=None) -> List[Dict]:
        """Obtiene partidos de todas las ligas"""
        all_matches = []
        total = len(self.SOCCER_LEAGUES)
        
        for i, (sport_key, league_name, country) in enumerate(self.SOCCER_LEAGUES):
            try:
                url = f"{self.BASE_URL}/sports/{sport_key}/events"
                params = {
                    "apiKey": self.api_key,
                    "regions": "eu,us,uk,au",
                    "dateFormat": "iso"
                }
                
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for event in data:
                    match = {
                        "id": event["id"],
                        "home_team": event["home_team"],
                        "away_team": event["away_team"],
                        "league": league_name,
                        "country": country,
                        "kickoff_time": datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00")),
                        "sport_key": sport_key
                    }
                    all_matches.append(match)
                
                await asyncio.sleep(0.15)
                
                if progress_callback:
                    progress_callback((i + 1) / total)
                    
            except Exception as e:
                logger.warning(f"Error obteniendo {league_name}: {e}")
                continue
        
        return all_matches
    
    async def get_match_odds(self, match_id: str, sport_key: str) -> Tuple[List[Dict], List[Dict]]:
        """Obtiene cuotas H2H para un partido"""
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
                
                for market_data in bookmaker_data.get("markets", []):
                    if market_data.get("key") != "h2h":
                        continue
                    
                    outcomes = market_data.get("outcomes", [])
                    timestamp = datetime.now(timezone.utc)
                    
                    home_odds = next((o.get("price") for o in outcomes if o.get("name") == data.get("home_team")), None)
                    draw_odds = next((o.get("price") for o in outcomes if o.get("name") == "Draw"), None)
                    away_odds = next((o.get("price") for o in outcomes if o.get("name") == data.get("away_team")), None)
                    
                    if home_odds and draw_odds and away_odds:
                        h2h_odds.append({
                            "bookmaker": bookmaker_name,
                            "home_odds": float(home_odds),
                            "draw_odds": float(draw_odds),
                            "away_odds": float(away_odds)
                        })
                        
                        # Calcular doble oportunidad
                        prob_1x = (1/float(home_odds)) + (1/float(draw_odds))
                        odds_1x = 1 / prob_1x
                        all_odds.append({
                            "bookmaker": bookmaker_name,
                            "market": "1X",
                            "odds": round(odds_1x, 4)
                        })
                        
                        prob_x2 = (1/float(draw_odds)) + (1/float(away_odds))
                        odds_x2 = 1 / prob_x2
                        all_odds.append({
                            "bookmaker": bookmaker_name,
                            "market": "X2",
                            "odds": round(odds_x2, 4)
                        })
            
            return all_odds, h2h_odds
            
        except Exception as e:
            logger.warning(f"Error obteniendo cuotas para {match_id}: {e}")
            return [], []
    
    async def get_totals_odds(self, match_id: str, sport_key: str) -> List[Dict]:
        """Obtiene cuotas Over/Under para un partido"""
        try:
            url = f"{self.BASE_URL}/sports/{sport_key}/events/{match_id}/odds"
            params = {
                "apiKey": self.api_key,
                "regions": "eu,us,uk,au",
                "markets": "totals",
                "oddsFormat": "decimal",
                "dateFormat": "iso"
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            odds_list = []
            
            for bookmaker_data in data.get("bookmakers", []):
                bookmaker_name = bookmaker_data.get("key")
                
                for market_data in bookmaker_data.get("markets", []):
                    for outcome in market_data.get("outcomes", []):
                        odds_info = {
                            "bookmaker": bookmaker_name,
                            "market_name": outcome["name"],
                            "odds": float(outcome["price"]),
                            "point": outcome.get("point")
                        }
                        odds_list.append(odds_info)
            
            return odds_list
            
        except Exception:
            return []


# ========== CÁLCULO BDI ==========
def bookmaker_disagreement(bookmaker_odds_list: List[Dict]) -> Dict:
    """
    Calcula el Bookmaker Disagreement Index (BDI) basado en Jensen-Shannon Divergence
    """
    if not bookmaker_odds_list or len(bookmaker_odds_list) < 2:
        return {}
    
    # Obtener las claves de outcomes
    outcomes = list(bookmaker_odds_list[0].keys())
    n_bookmakers = len(bookmaker_odds_list)
    
    # Convertir odds a probabilidades normalizadas
    prob_matrix = []
    for bookie_odds in bookmaker_odds_list:
        probs = []
        total = 0
        for outcome in outcomes:
            odds = bookie_odds.get(outcome, 100)  # Default alto
            if odds and odds > 1:
                p = 1.0 / odds
            else:
                p = 0.01
            probs.append(p)
            total += p
        
        # Normalizar
        if total > 0:
            probs = [p / total for p in probs]
        prob_matrix.append(probs)
    
    prob_array = np.array(prob_matrix)
    
    # Calcular distribución promedio
    mean_dist = np.mean(prob_array, axis=0)
    
    # Calcular JSD
    def kl_divergence(p, q):
        """KL divergence con protección contra log(0)"""
        p = np.clip(p, 1e-10, 1)
        q = np.clip(q, 1e-10, 1)
        return np.sum(p * np.log(p / q))
    
    jsd_values = []
    for probs in prob_matrix:
        m = (np.array(probs) + mean_dist) / 2
        jsd = 0.5 * kl_divergence(probs, m) + 0.5 * kl_divergence(mean_dist, m)
        jsd_values.append(jsd)
    
    jsd_mean = np.mean(jsd_values)
    
    # Calcular std por outcome
    per_outcome_std = {}
    per_outcome_mad = {}
    for i, outcome in enumerate(outcomes):
        outcome_probs = prob_array[:, i]
        per_outcome_std[outcome] = float(np.std(outcome_probs))
        per_outcome_mad[outcome] = float(np.median(np.abs(outcome_probs - np.median(outcome_probs))))
    
    return {
        'jsd_mean': round(float(jsd_mean), 6),
        'n_bookmakers': n_bookmakers,
        'per_outcome_std': per_outcome_std,
        'per_outcome_mad': per_outcome_mad
    }


# ========== ANALIZADOR ==========
class OddsAnalyzer:
    """Analizador de cuotas simplificado"""
    
    def __init__(self, api_key: str):
        self.client = TheOddsAPIClient(api_key)
    
    async def close(self):
        await self.client.close()
    
    async def analyze(self, hours_from: int, hours_ahead: int, progress_placeholder) -> pd.DataFrame:
        """Ejecuta el análisis completo"""
        results = []
        
        # 1. Obtener partidos
        progress_placeholder.text("📡 Obteniendo partidos de todas las ligas...")
        progress_bar = st.progress(0)
        
        def update_progress(p):
            progress_bar.progress(p)
        
        all_matches = await self.client.get_football_matches(progress_callback=update_progress)
        
        # 2. Filtrar por tiempo
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(hours=hours_from)
        cutoff_time = now + timedelta(hours=hours_ahead)
        
        filtered_matches = [
            m for m in all_matches
            if start_time <= m["kickoff_time"] <= cutoff_time
        ]
        
        progress_placeholder.text(f"✅ {len(filtered_matches)} partidos encontrados en el rango de tiempo")
        
        if not filtered_matches:
            return pd.DataFrame()
        
        # 3. Analizar cada partido
        progress_placeholder.text("🔍 Analizando cuotas de cada partido...")
        total_matches = len(filtered_matches)
        
        for i, match in enumerate(filtered_matches):
            progress_bar.progress((i + 1) / total_matches)
            
            try:
                # Obtener cuotas totals
                totals_data = await self.client.get_totals_odds(match["id"], match["sport_key"])
                
                if totals_data:
                    totals_results = self._analyze_totals(match, totals_data)
                    results.extend(totals_results)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Error analizando {match['home_team']} vs {match['away_team']}: {e}")
                continue
        
        progress_bar.progress(1.0)
        
        if not results:
            return pd.DataFrame()
        
        # 4. Crear DataFrame
        df = pd.DataFrame(results)
        
        # 5. Filtrar mercados 1X y X2 (solo queremos Over/Under)
        # Ya está filtrado porque solo analizamos totals
        
        # 6. Ordenar por BDI_jsd_fair descendente
        if 'BDI_jsd_fair' in df.columns:
            df = df.sort_values('BDI_jsd_fair', ascending=False)
        
        return df
    
    def _analyze_totals(self, match: Dict, odds_data: List[Dict]) -> List[Dict]:
        """Analiza mercados Over/Under"""
        results = []
        
        # Agrupar por mercado
        markets_dict = defaultdict(list)
        for odds_info in odds_data:
            key = f"{odds_info['market_name']} {odds_info.get('point', '')}"
            markets_dict[key].append(odds_info)
        
        for market_name, odds_list in markets_dict.items():
            if len(odds_list) < 2:
                continue
            
            # Mejor cuota
            best = max(odds_list, key=lambda x: x["odds"])
            
            # Calcular BDI fair
            is_over = "Over" in market_name
            parts = market_name.split()
            point = parts[-1] if len(parts) >= 2 else None
            opposite_name = f"{'Under' if is_over else 'Over'} {point}"
            
            fair_list = []
            all_bookmakers = set(o["bookmaker"] for o in odds_list)
            
            for bookie in all_bookmakers:
                current = next((x for x in odds_data if x["bookmaker"] == bookie and f"{x['market_name']} {x.get('point')}" == market_name), None)
                opposite = next((x for x in odds_data if x["bookmaker"] == bookie and f"{x['market_name']} {x.get('point')}" == opposite_name), None)
                
                if current and opposite:
                    fair_list.append({market_name: current['odds'], opposite_name: opposite['odds']})
            
            bdi_jsd_fair = None
            bdi_n_fair = None
            
            if fair_list and len(fair_list) >= 2:
                bdi_res = bookmaker_disagreement(fair_list)
                bdi_jsd_fair = bdi_res.get('jsd_mean')
                bdi_n_fair = bdi_res.get('n_bookmakers')
            
            # Convertir kickoff a hora Colombia (UTC-5)
            kickoff_utc = match["kickoff_time"]
            kickoff_colombia = kickoff_utc - timedelta(hours=5)
            
            result = {
                "Partido": f"{match['home_team']} vs {match['away_team']}",
                "Fecha_Hora_Colombia": kickoff_colombia.strftime("%Y-%m-%d %H:%M"),
                "Mercado": market_name,
                "Mejor_Cuota": round(best["odds"], 2),
                "BDI_jsd_fair": bdi_jsd_fair,
                "BDI_n_bookmakers_fair": bdi_n_fair,
                "Liga": match["league"],
                "Pais": match["country"]
            }
            results.append(result)
        
        return results


# ========== INTERFAZ STREAMLIT ==========
def main():
    st.set_page_config(
        page_title="⚽ Análisis de Cuotas de Fútbol",
        page_icon="⚽",
        layout="wide"
    )
    
    st.title("⚽ Análisis de Cuotas de Fútbol")
    st.markdown("""
    Analiza mercados **Over/Under** de fútbol usando datos de **THE_ODDS_API**.
    
    Los resultados están ordenados por **BDI_jsd_fair** (Bookmaker Disagreement Index) de forma descendente.
    Un BDI alto indica mayor desacuerdo entre casas de apuestas, lo cual puede señalar oportunidades de valor.
    """)
    
    st.divider()
    
    # Sidebar con configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        api_key = st.text_input(
            "🔑 THE_ODDS_API_KEY",
            type="password",
            help="Pega tu API key de the-odds-api.com"
        )
        
        st.divider()
        
        hours_from = st.number_input(
            "📅 Horas desde ahora (hours-from)",
            min_value=0,
            max_value=336,
            value=0,
            help="Empezar a buscar partidos desde X horas en el futuro"
        )
        
        hours_ahead = st.number_input(
            "⏰ Horas hacia adelante (hours-ahead)",
            min_value=1,
            max_value=336,
            value=72,
            help="Buscar partidos hasta X horas en el futuro"
        )
        
        st.divider()
        
        run_button = st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True)
        
        st.divider()
        
        st.markdown("""
        ### ℹ️ Información
        - **Mercados**: Solo Over/Under (sin 1X ni X2)
        - **Ordenamiento**: BDI_jsd_fair descendente
        - **Hora**: Colombia (UTC-5)
        - **Fuente**: THE_ODDS_API (58+ bookmakers)
        """)
    
    # Área principal
    if run_button:
        if not api_key:
            st.error("❌ Por favor, ingresa tu API key de THE_ODDS_API")
            return
        
        st.info(f"🔍 Buscando partidos entre {hours_from}h y {hours_ahead}h desde ahora...")
        
        progress_placeholder = st.empty()
        
        async def run_analysis():
            analyzer = OddsAnalyzer(api_key)
            try:
                # Verificar API key
                remaining = await analyzer.client.get_remaining_requests()
                if remaining == -1:
                    st.error("❌ API key inválida o error de conexión")
                    return None
                
                st.success(f"✅ API conectada - {remaining} requests restantes")
                
                # Ejecutar análisis
                df = await analyzer.analyze(hours_from, hours_ahead, progress_placeholder)
                return df
            finally:
                await analyzer.close()
        
        # Ejecutar
        df = asyncio.run(run_analysis())
        
        if df is None:
            return
        
        if df.empty:
            st.warning("⚠️ No se encontraron resultados para los criterios especificados")
            return
        
        progress_placeholder.empty()
        
        # Mostrar resultados
        st.success(f"✅ Análisis completado - {len(df)} mercados encontrados")
        
        # Filtrar solo las columnas requeridas
        display_columns = [
            "Partido",
            "Fecha_Hora_Colombia",
            "Mercado",
            "Mejor_Cuota",
            "BDI_jsd_fair",
            "BDI_n_bookmakers_fair"
        ]
        
        df_display = df[display_columns].copy()
        
        # Formatear
        df_display["BDI_jsd_fair"] = df_display["BDI_jsd_fair"].apply(
            lambda x: f"{x:.6f}" if pd.notna(x) else "-"
        )
        df_display["BDI_n_bookmakers_fair"] = df_display["BDI_n_bookmakers_fair"].apply(
            lambda x: int(x) if pd.notna(x) else "-"
        )
        
        # Mostrar tabla
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=600
        )
        
        # Estadísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Mercados", len(df))
        with col2:
            partidos_unicos = df["Partido"].nunique()
            st.metric("Partidos Únicos", partidos_unicos)
        with col3:
            if df["BDI_jsd_fair"].notna().any():
                max_bdi = df["BDI_jsd_fair"].max()
                st.metric("Max BDI", f"{max_bdi:.6f}" if pd.notna(max_bdi) else "-")
    
    else:
        # Placeholder cuando no hay análisis
        st.info("👈 Configura los parámetros en la barra lateral y presiona **Ejecutar Análisis**")
        
        st.markdown("""
        ### 📋 Columnas del resultado:
        | Columna | Descripción |
        |---------|-------------|
        | **Partido** | Equipos local vs visitante |
        | **Fecha_Hora_Colombia** | Fecha y hora del partido (UTC-5) |
        | **Mercado** | Tipo de mercado (Over/Under X.X) |
        | **Mejor_Cuota** | La mejor cuota disponible |
        | **BDI_jsd_fair** | Índice de desacuerdo entre bookmakers (mayor = más desacuerdo) |
        | **BDI_n_bookmakers_fair** | Número de bookmakers usados para calcular BDI |
        """)


if __name__ == "__main__":
    main()
