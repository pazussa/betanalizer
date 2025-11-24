#!/usr/bin/env python3
"""
Script para verificar todas las ligas de fútbol disponibles en The Odds API
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def check_available_leagues():
    api_key = os.getenv("THE_ODDS_API_KEY")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Obtener todos los deportes disponibles
        url = "https://api.the-odds-api.com/v4/sports"
        params = {"apiKey": api_key}
        
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        sports = response.json()
        
        # Filtrar solo ligas de fútbol
        soccer_leagues = [
            sport for sport in sports 
            if sport["key"].startswith("soccer_") and sport["active"]
        ]
        
        print(f"\n🏆 LIGAS DE FÚTBOL DISPONIBLES: {len(soccer_leagues)}\n")
        print("=" * 80)
        
        for league in sorted(soccer_leagues, key=lambda x: x["title"]):
            print(f"Key: {league['key']:<45} | {league['title']}")
        
        print("\n" + "=" * 80)
        print(f"\nTotal: {len(soccer_leagues)} ligas activas")
        
        # Mostrar requests restantes
        remaining = int(response.headers.get("x-requests-remaining", 0))
        print(f"Requests restantes: {remaining}/500")

if __name__ == "__main__":
    asyncio.run(check_available_leagues())
