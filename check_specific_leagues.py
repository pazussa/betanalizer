#!/usr/bin/env python3
"""
Verificar si hay partidos disponibles en ligas específicas
"""

import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def check_league(sport_key: str, league_name: str):
    """Verificar partidos disponibles en una liga específica"""
    api_key = os.getenv("THE_ODDS_API_KEY")
    
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events"
    params = {
        "apiKey": api_key,
        "regions": "eu,us,uk,au",
        "dateFormat": "iso"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            print(f"\n{league_name} ({sport_key}):")
            print(f"  Partidos disponibles: {len(data)}")
            
            if len(data) > 0:
                print(f"  Primeros partidos:")
                for event in data[:3]:
                    print(f"    - {event['home_team']} vs {event['away_team']} ({event['commence_time']})")
            
        except Exception as e:
            print(f"\n{league_name} ({sport_key}): ERROR - {e}")

async def main():
    print("🔍 Verificando ligas específicas...\n")
    
    leagues = [
        ("soccer_sweden_allsvenskan", "Allsvenskan (Suecia)"),
        ("soccer_turkey_super_league", "Super League (Turquía)"),
        ("soccer_chile_campeonato", "Primera División (Chile)")
    ]
    
    for sport_key, league_name in leagues:
        await check_league(sport_key, league_name)
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
