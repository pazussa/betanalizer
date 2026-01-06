#!/usr/bin/env python3
"""
Webapp de Análisis de Cuotas de Fútbol
Interfaz Streamlit para analizar cuotas usando THE_ODDS_API + API-FOOTBALL
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

# ========== CONFIGURACIÓN DE LOGGING ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== API KEYS ==========
# API-FOOTBALL key (estática, nunca cambia)
API_FOOTBALL_KEY = "beea0d8f9ab22740c465933f98a87170"

# THE_ODDS_API keys disponibles
THE_ODDS_API_KEYS = [
    "71bf811f7d188e95e23785f793b94185",
    "2172cf43249121d14f0f851c037d6ad6",
    "a4f8886d0f51a44abf623af42327f6da",
    "4a717f7542e3c4362ddf8f8b59c03754",
    "2c141cbd97634510a0edb715acb37e4c",
    "2b9a248f5870d1f1e19b85bae7c6b313",
    "30e5f3c7f8d38475175d6b3e920ebb6c",
    "1375f6f4aef4a8a0994207f08d2a7490",
    "2855ea30b14dd550f95fab246178baec",
    "ae6dc3a151fae15a337fc4d363d726fd",
]


# ========== MODELOS ==========
class MarketType(str, Enum):
    DOUBLE_CHANCE_1X = "1X"
    DOUBLE_CHANCE_X2 = "X2"
    TOTALS = "totals"


# ========== CLIENTE THE ODDS API ==========
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
                            "point": outcome.get("point"),
                            "source": "THE_ODDS_API"
                        }
                        odds_list.append(odds_info)
            
            return odds_list
            
        except Exception:
            return []


# ========== CLIENTE API-FOOTBALL ==========
class APIFootballClient:
    """Cliente para API-FOOTBALL (Bet365, Bwin, SBO)"""
    
    BASE_URL = "https://v3.football.api-sports.io"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": "v3.football.api-sports.io"
            }
        )
    
    async def close(self):
        await self.client.aclose()
    
    async def get_status(self) -> Optional[Dict]:
        """Verifica estado de la API"""
        try:
            response = await self.client.get(f"{self.BASE_URL}/status")
            response.raise_for_status()
            data = response.json()
            return data.get("response", {})
        except Exception:
            return None
    
    async def get_odds_by_date(self, date: str) -> List[Dict]:
        """Obtiene odds por fecha (YYYY-MM-DD)"""
        try:
            url = f"{self.BASE_URL}/odds"
            params = {
                "date": date,
                "bookmaker": "6",  # Bwin
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get("response", [])
        except Exception as e:
            logger.warning(f"Error obteniendo odds de API-FOOTBALL para {date}: {e}")
            return []
    
    def parse_totals_odds(self, odds_data: List[Dict]) -> List[Dict]:
        """Parsea odds de Over/Under de API-FOOTBALL"""
        results = []
        
        for fixture_data in odds_data:
            fixture = fixture_data.get("fixture", {})
            league = fixture_data.get("league", {})
            
            fixture_id = fixture.get("id")
            fixture_date = fixture.get("date", "")
            
            # Info del partido (necesitamos obtenerla de otro endpoint o fixture)
            home_team = fixture_data.get("teams", {}).get("home", {}).get("name", "Home")
            away_team = fixture_data.get("teams", {}).get("away", {}).get("name", "Away")
            
            for bookmaker_data in fixture_data.get("bookmakers", []):
                bookmaker_name = bookmaker_data.get("name", "Unknown")
                
                for bet in bookmaker_data.get("bets", []):
                    bet_name = bet.get("name", "")
                    
                    # Solo Over/Under
                    if "Over/Under" in bet_name or "Goals" in bet_name:
                        for value in bet.get("values", []):
                            val = value.get("value", "")
                            odd = value.get("odd")
                            
                            if odd:
                                # Parsear Over/Under
                                if "Over" in str(val) or "Under" in str(val):
                                    parts = str(val).split()
                                    market_type = parts[0] if parts else val
                                    point = parts[1] if len(parts) > 1 else ""
                                    
                                    results.append({
                                        "fixture_id": fixture_id,
                                        "home_team": home_team,
                                        "away_team": away_team,
                                        "league": league.get("name", ""),
                                        "country": league.get("country", ""),
                                        "kickoff_time": fixture_date,
                                        "bookmaker": bookmaker_name,
                                        "market_name": market_type,
                                        "point": point,
                                        "odds": float(odd),
                                        "source": "API-FOOTBALL"
                                    })
        
        return results


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
            odds = bookie_odds.get(outcome, 100)
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
        p = np.clip(p, 1e-10, 1)
        q = np.clip(q, 1e-10, 1)
        return np.sum(p * np.log(p / q))
    
    jsd_values = []
    for probs in prob_matrix:
        m = (np.array(probs) + mean_dist) / 2
        jsd = 0.5 * kl_divergence(probs, m) + 0.5 * kl_divergence(mean_dist, m)
        jsd_values.append(jsd)
    
    jsd_mean = np.mean(jsd_values)
    
    return {
        'jsd_mean': round(float(jsd_mean), 6),
        'n_bookmakers': n_bookmakers
    }


# ========== ANALIZADOR ==========
class OddsAnalyzer:
    """Analizador de cuotas combinando THE_ODDS_API + API-FOOTBALL"""
    
    def __init__(self, the_odds_api_key: str, api_football_key: str):
        self.odds_client = TheOddsAPIClient(the_odds_api_key)
        self.api_football_client = APIFootballClient(api_football_key)
    
    async def close(self):
        await self.odds_client.close()
        await self.api_football_client.close()
    
    async def analyze(self, hours_from: int, hours_ahead: int, progress_placeholder) -> pd.DataFrame:
        """Ejecuta el análisis completo"""
        results = []
        
        # 1. Obtener partidos de THE_ODDS_API
        progress_placeholder.text("📡 Obteniendo partidos de THE_ODDS_API (35 ligas)...")
        progress_bar = st.progress(0)
        
        def update_progress(p):
            progress_bar.progress(p)
        
        all_matches = await self.odds_client.get_football_matches(progress_callback=update_progress)
        
        # 2. Filtrar por tiempo
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(hours=hours_from)
        cutoff_time = now + timedelta(hours=hours_ahead)
        
        filtered_matches = [
            m for m in all_matches
            if start_time <= m["kickoff_time"] <= cutoff_time
        ]
        
        progress_placeholder.text(f"✅ {len(filtered_matches)} partidos de THE_ODDS_API en el rango")
        
        # 3. Obtener datos de API-FOOTBALL
        progress_placeholder.text("📡 Obteniendo datos de API-FOOTBALL (Bet365, Bwin, SBO)...")
        
        api_football_totals = []
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        for date in [today, tomorrow, day_after]:
            try:
                odds_data = await self.api_football_client.get_odds_by_date(date)
                if odds_data:
                    totals = self.api_football_client.parse_totals_odds(odds_data)
                    api_football_totals.extend(totals)
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.warning(f"Error API-FOOTBALL {date}: {e}")
        
        if api_football_totals:
            progress_placeholder.text(f"✅ {len(api_football_totals)} cuotas de API-FOOTBALL")
        
        # 4. Analizar cada partido de THE_ODDS_API
        progress_placeholder.text("🔍 Analizando cuotas Over/Under...")
        total_matches = len(filtered_matches)
        
        for i, match in enumerate(filtered_matches):
            progress_bar.progress((i + 1) / total_matches)
            
            try:
                # Obtener cuotas totals de THE_ODDS_API
                totals_data = await self.odds_client.get_totals_odds(match["id"], match["sport_key"])
                
                if totals_data:
                    totals_results = self._analyze_totals(match, totals_data)
                    results.extend(totals_results)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Error analizando {match['home_team']} vs {match['away_team']}: {e}")
                continue
        
        # 5. Agregar resultados de API-FOOTBALL
        for totals_info in api_football_totals:
            try:
                kickoff_str = totals_info.get("kickoff_time", "")
                if kickoff_str:
                    kickoff_utc = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
                    kickoff_colombia = kickoff_utc - timedelta(hours=5)
                else:
                    kickoff_colombia = datetime.now()
                
                market_name = f"{totals_info['market_name']} {totals_info['point']}"
                
                result = {
                    "Partido": f"{totals_info['home_team']} vs {totals_info['away_team']}",
                    "Fecha_Hora_Colombia": kickoff_colombia.strftime("%Y-%m-%d %H:%M"),
                    "Mercado": market_name,
                    "Mejor_Cuota": round(totals_info["odds"], 2),
                    "BDI_jsd_fair": None,  # No calculamos BDI para API-FOOTBALL individual
                    "BDI_n_bookmakers_fair": 1,
                    "Liga": totals_info.get("league", ""),
                    "Pais": totals_info.get("country", ""),
                    "Fuente": "API-FOOTBALL ⭐"
                }
                results.append(result)
            except Exception:
                continue
        
        progress_bar.progress(1.0)
        
        if not results:
            return pd.DataFrame()
        
        # 6. Crear DataFrame
        df = pd.DataFrame(results)
        
        # 7. Ordenar por BDI_jsd_fair descendente (None al final)
        if 'BDI_jsd_fair' in df.columns:
            df = df.sort_values('BDI_jsd_fair', ascending=False, na_position='last')
        
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
                "Pais": match["country"],
                "Fuente": "THE_ODDS_API"
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
    Analiza mercados **Over/Under** de fútbol usando **THE_ODDS_API** + **API-FOOTBALL**.
    
    - **THE_ODDS_API**: 58+ bookmakers (Pinnacle, Betfair, DraftKings, etc.)
    - **API-FOOTBALL**: Bet365, Bwin, SBO (Sbobet) ⭐
    
    Resultados ordenados por **BDI_jsd_fair** (mayor = más desacuerdo entre casas).
    """)
    
    st.divider()
    
    # Sidebar con configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Selector de API key
        st.subheader("🔑 THE_ODDS_API Key")
        
        # Opción 1: Seleccionar de la lista
        selected_key = st.selectbox(
            "Seleccionar key disponible:",
            options=THE_ODDS_API_KEYS,
            format_func=lambda x: f"...{x[-8:]}"  # Mostrar solo últimos 8 caracteres
        )
        
        # Opción 2: Pegar una nueva key
        st.markdown("---")
        st.markdown("**O pegar una nueva key:**")
        custom_key = st.text_input(
            "Nueva API key",
            type="password",
            placeholder="Pega aquí una nueva key..."
        )
        
        # Usar la key personalizada si se proporcionó
        api_key = custom_key if custom_key else selected_key
        
        st.divider()
        
        # Parámetros de búsqueda
        st.subheader("📅 Rango de tiempo")
        
        hours_from = st.number_input(
            "Desde (horas)",
            min_value=0,
            max_value=336,
            value=0,
            help="Empezar a buscar partidos desde X horas en el futuro"
        )
        
        hours_ahead = st.number_input(
            "Hasta (horas)",
            min_value=1,
            max_value=336,
            value=72,
            help="Buscar partidos hasta X horas en el futuro"
        )
        
        st.divider()
        
        run_button = st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True)
        
        st.divider()
        
        # Info
        st.markdown("""
        ### ℹ️ Info
        - **Mercados**: Solo Over/Under
        - **Hora**: Colombia (UTC-5)
        - **API-FOOTBALL**: Key fija ✅
        
        ### 📊 Fuentes
        - THE_ODDS_API: 58 bookmakers
        - API-FOOTBALL: Bet365, Bwin, SBO
        """)
    
    # Área principal
    if run_button:
        if not api_key:
            st.error("❌ Por favor, selecciona o ingresa una API key")
            return
        
        st.info(f"🔍 Buscando partidos entre {hours_from}h y {hours_ahead}h desde ahora...")
        
        progress_placeholder = st.empty()
        
        async def run_analysis():
            analyzer = OddsAnalyzer(api_key, API_FOOTBALL_KEY)
            try:
                # Verificar API keys
                col1, col2 = st.columns(2)
                
                with col1:
                    remaining = await analyzer.odds_client.get_remaining_requests()
                    if remaining == -1:
                        st.error("❌ THE_ODDS_API key inválida")
                        return None
                    st.success(f"✅ THE_ODDS_API: {remaining} requests")
                
                with col2:
                    status = await analyzer.api_football_client.get_status()
                    if status:
                        requests = status.get("requests", {})
                        st.success(f"✅ API-FOOTBALL: {requests.get('current', 0)}/{requests.get('limit_day', 100)}")
                    else:
                        st.warning("⚠️ API-FOOTBALL: sin verificar")
                
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
            st.warning("⚠️ No se encontraron resultados")
            return
        
        progress_placeholder.empty()
        
        # Mostrar resultados
        st.success(f"✅ Análisis completado - {len(df)} mercados encontrados")
        
        # Columnas a mostrar
        display_columns = [
            "Partido",
            "Fecha_Hora_Colombia",
            "Mercado",
            "Mejor_Cuota",
            "BDI_jsd_fair",
            "BDI_n_bookmakers_fair"
        ]
        
        # Verificar que existan las columnas
        available_columns = [c for c in display_columns if c in df.columns]
        df_display = df[available_columns].copy()
        
        # Formatear
        if "BDI_jsd_fair" in df_display.columns:
            df_display["BDI_jsd_fair"] = df_display["BDI_jsd_fair"].apply(
                lambda x: f"{x:.6f}" if pd.notna(x) else "-"
            )
        if "BDI_n_bookmakers_fair" in df_display.columns:
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
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Mercados", len(df))
        with col2:
            partidos_unicos = df["Partido"].nunique()
            st.metric("Partidos Únicos", partidos_unicos)
        with col3:
            if "BDI_jsd_fair" in df.columns and df["BDI_jsd_fair"].notna().any():
                max_bdi = df["BDI_jsd_fair"].max()
                st.metric("Max BDI", f"{max_bdi:.6f}" if pd.notna(max_bdi) else "-")
            else:
                st.metric("Max BDI", "-")
        with col4:
            if "Fuente" in df.columns:
                api_football_count = len(df[df["Fuente"].str.contains("API-FOOTBALL", na=False)])
                st.metric("API-FOOTBALL ⭐", api_football_count)
    
    else:
        # Placeholder
        st.info("👈 Configura los parámetros en la barra lateral y presiona **Ejecutar Análisis**")
        
        st.markdown("""
        ### 📋 Columnas del resultado
        
        | Columna | Descripción |
        |---------|-------------|
        | **Partido** | Equipos local vs visitante |
        | **Fecha_Hora_Colombia** | Fecha y hora (UTC-5) |
        | **Mercado** | Over/Under X.X |
        | **Mejor_Cuota** | Mejor cuota disponible |
        | **BDI_jsd_fair** | Índice de desacuerdo (mayor = más oportunidad) |
        | **BDI_n_bookmakers_fair** | Número de bookmakers |
        
        ### 🔑 Keys disponibles
        
        Se incluyen **10 keys** de THE_ODDS_API. Si alguna se agota, selecciona otra del menú.
        
        También puedes pegar una nueva key si tienes más.
        """)


if __name__ == "__main__":
    main()
