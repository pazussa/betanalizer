#!/usr/bin/env python3
"""
Verificar resultados de partidos históricos del dataset main6.
Busca los resultados reales y calcula aciertos de Over/Under.
"""

import asyncio
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from src.apis.api_football import APIFootballClient, LEAGUE_IDS
except ImportError:
    print("⚠️ No se pudo importar APIFootballClient")
    APIFootballClient = None

import httpx

# Mapeo de nombres de ligas del CSV a IDs de API-FOOTBALL
LEAGUE_NAME_TO_ID = {
    "Premier League": 39,
    "La Liga": 140,
    "Bundesliga": 78,
    "Serie A": 135,
    "Serie B": 136,
    "Ligue 1": 61,
    "Ligue 2": 62,
    "Championship": 40,
    "League One": 41,
    "League Two": 42,
    "La Liga 2": 141,
    "Liga Portugal": 94,
    "Eredivisie": 88,
    "Süper Lig": 203,
    "Super League Switzerland": 207,
    "Superliga Denmark": 119,
    "Ekstraklasa": 106,
    "Pro League": 144,  # Bélgica
    "Liga MX": 262,
    "MLS": 253,
    "Liga Profesional": 128,  # Argentina
    "Primera División Chile": 265,
    "J1 League": 98,
    "K League 1": 292,
    "A-League": 188,
    "Scottish Premiership": 179,
}


async def buscar_resultado_api_football(
    client: httpx.AsyncClient,
    api_key: str,
    home_team: str,
    away_team: str,
    fecha: str,
    league_id: Optional[int] = None
) -> Optional[Dict]:
    """Busca resultado de un partido en API-FOOTBALL"""
    
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": api_key
    }
    
    params = {
        "date": fecha,
        "status": "FT"  # Solo partidos finalizados
    }
    
    if league_id:
        params["league"] = league_id
        params["season"] = 2024 if int(fecha[:4]) == 2025 and int(fecha[5:7]) <= 6 else 2025
    
    try:
        response = await client.get(
            "https://v3.football.api-sports.io/fixtures",
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        fixtures = data.get("response", [])
        
        # Buscar coincidencia por nombres de equipos
        for fixture in fixtures:
            home = fixture.get("teams", {}).get("home", {}).get("name", "")
            away = fixture.get("teams", {}).get("away", {}).get("name", "")
            
            # Normalizar nombres
            home_norm = home.lower().replace("fc", "").replace("cf", "").strip()
            away_norm = away.lower().replace("fc", "").replace("cf", "").strip()
            
            home_team_norm = home_team.lower().replace("fc", "").replace("cf", "").strip()
            away_team_norm = away_team.lower().replace("fc", "").replace("cf", "").strip()
            
            # Verificar coincidencia (parcial)
            if (home_team_norm[:6] in home_norm or home_norm[:6] in home_team_norm) and \
               (away_team_norm[:6] in away_norm or away_norm[:6] in away_team_norm):
                
                goals = fixture.get("goals", {})
                home_goals = goals.get("home")
                away_goals = goals.get("away")
                
                if home_goals is not None and away_goals is not None:
                    return {
                        "home_team": home,
                        "away_team": away,
                        "home_goals": home_goals,
                        "away_goals": away_goals,
                        "total_goals": home_goals + away_goals,
                        "score": f"{home_goals}-{away_goals}",
                        "fixture_id": fixture.get("fixture", {}).get("id")
                    }
        
        return None
        
    except Exception as e:
        print(f"Error buscando {home_team} vs {away_team}: {e}")
        return None


def extraer_linea(mercado: str) -> float:
    """Extrae la línea numérica del mercado (ej: 'Over 2.5' -> 2.5)"""
    match = re.search(r'(\d+\.?\d*)', mercado)
    if match:
        return float(match.group(1))
    return 2.5  # default


def verificar_acierto(mercado: str, total_goles: int) -> bool:
    """Verifica si el mercado acertó dado el total de goles"""
    linea = extraer_linea(mercado)
    
    if "Over" in mercado:
        return total_goles > linea
    elif "Under" in mercado:
        return total_goles < linea
    
    return False


async def main():
    # Cargar dataset
    csv_path = "historical_analysis/2025/marzo/historical_20250307.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ No se encontró: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    print(f"📊 Cargado: {len(df)} filas del CSV")
    
    # Obtener partidos únicos
    partidos_unicos = df[['Partido', 'Fecha_Hora_Colombia', 'Liga']].drop_duplicates()
    print(f"⚽ Partidos únicos: {len(partidos_unicos)}")
    
    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        print("❌ API_FOOTBALL_KEY no encontrada en .env")
        print("   Intentando buscar resultados via web...")
        # Alternativa: usar scraping o otra fuente
        return
    
    print(f"\n🔍 Buscando resultados en API-FOOTBALL...")
    
    resultados = {}
    encontrados = 0
    no_encontrados = 0
    
    async with httpx.AsyncClient() as client:
        for idx, row in partidos_unicos.iterrows():
            partido = row['Partido']
            fecha_str = row['Fecha_Hora_Colombia'][:10]
            liga = row['Liga']
            
            # Separar equipos
            if ' vs ' in partido:
                home, away = partido.split(' vs ')
            else:
                continue
            
            league_id = LEAGUE_NAME_TO_ID.get(liga)
            
            resultado = await buscar_resultado_api_football(
                client, api_key, home, away, fecha_str, league_id
            )
            
            if resultado:
                resultados[partido] = resultado
                encontrados += 1
                print(f"✅ {partido}: {resultado['score']} ({resultado['total_goals']} goles)")
            else:
                no_encontrados += 1
                # Intentar día siguiente (por diferencia horaria)
                fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                fecha_alt = (fecha_dt + timedelta(days=1)).strftime("%Y-%m-%d")
                
                resultado = await buscar_resultado_api_football(
                    client, api_key, home, away, fecha_alt, league_id
                )
                
                if resultado:
                    resultados[partido] = resultado
                    encontrados += 1
                    no_encontrados -= 1
                    print(f"✅ {partido}: {resultado['score']} ({resultado['total_goals']} goles) [fecha ajustada]")
                else:
                    print(f"❌ {partido} - No encontrado")
            
            # Pausa para no saturar API
            await asyncio.sleep(0.3)
            
            # Mostrar progreso cada 20 partidos
            if (encontrados + no_encontrados) % 20 == 0:
                print(f"   ... procesados {encontrados + no_encontrados}/{len(partidos_unicos)}")
    
    print(f"\n📊 RESULTADOS DE BÚSQUEDA:")
    print(f"   Encontrados: {encontrados}")
    print(f"   No encontrados: {no_encontrados}")
    
    if not resultados:
        print("❌ No se encontraron resultados")
        return
    
    # Agregar resultados al dataframe
    df['Total_Goles'] = df['Partido'].map(lambda p: resultados.get(p, {}).get('total_goals'))
    df['Score'] = df['Partido'].map(lambda p: resultados.get(p, {}).get('score'))
    df['Acerto'] = df.apply(
        lambda row: verificar_acierto(row['Mercado'], row['Total_Goles']) 
        if pd.notna(row['Total_Goles']) else None,
        axis=1
    )
    
    # Filtrar solo los que tienen resultado
    df_con_resultado = df[df['Total_Goles'].notna()].copy()
    
    print(f"\n📊 ANÁLISIS DE ACIERTOS:")
    print(f"   Mercados con resultado: {len(df_con_resultado)}")
    
    if len(df_con_resultado) > 0:
        aciertos = df_con_resultado['Acerto'].sum()
        total = len(df_con_resultado)
        pct = (aciertos / total * 100) if total > 0 else 0
        
        print(f"   Aciertos: {aciertos}")
        print(f"   Fallos: {total - aciertos}")
        print(f"   Tasa de acierto: {pct:.1f}%")
        
        # Por tipo de mercado
        print(f"\n📊 POR TIPO DE MERCADO:")
        for tipo in ['Over', 'Under']:
            df_tipo = df_con_resultado[df_con_resultado['Mercado'].str.contains(tipo)]
            if len(df_tipo) > 0:
                aciertos_tipo = df_tipo['Acerto'].sum()
                total_tipo = len(df_tipo)
                pct_tipo = (aciertos_tipo / total_tipo * 100) if total_tipo > 0 else 0
                print(f"   {tipo}: {aciertos_tipo}/{total_tipo} ({pct_tipo:.1f}%)")
        
        # Por línea
        print(f"\n📊 POR LÍNEA:")
        df_con_resultado['Linea'] = df_con_resultado['Mercado'].apply(extraer_linea)
        for linea in sorted(df_con_resultado['Linea'].unique()):
            df_linea = df_con_resultado[df_con_resultado['Linea'] == linea]
            if len(df_linea) > 0:
                aciertos_linea = df_linea['Acerto'].sum()
                total_linea = len(df_linea)
                pct_linea = (aciertos_linea / total_linea * 100) if total_linea > 0 else 0
                print(f"   Línea {linea}: {aciertos_linea}/{total_linea} ({pct_linea:.1f}%)")
        
        # Top mercados que más acertaron (alta cuota + acierto)
        print(f"\n🔥 TOP 10 MEJORES ACIERTOS (por cuota):")
        df_aciertos = df_con_resultado[df_con_resultado['Acerto'] == True].sort_values('Mejor_Cuota', ascending=False)
        for _, row in df_aciertos.head(10).iterrows():
            print(f"   • {row['Partido']}")
            print(f"     {row['Mercado']} @ {row['Mejor_Cuota']:.2f} → Score: {row['Score']} ✅")
        
        # Guardar resultados
        output_file = csv_path.replace('.csv', '_con_resultados.csv')
        df.to_csv(output_file, index=False)
        print(f"\n💾 Guardado: {output_file}")
    
    # Resumen por liga
    print(f"\n📊 POR LIGA:")
    for liga in df_con_resultado['Liga'].unique():
        df_liga = df_con_resultado[df_con_resultado['Liga'] == liga]
        if len(df_liga) > 0:
            aciertos_liga = df_liga['Acerto'].sum()
            total_liga = len(df_liga)
            pct_liga = (aciertos_liga / total_liga * 100) if total_liga > 0 else 0
            print(f"   {liga}: {aciertos_liga}/{total_liga} ({pct_liga:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
