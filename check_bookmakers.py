import httpx
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('THE_ODDS_API_KEY')

# Obtener partidos
response = httpx.get(f'https://api.the-odds-api.com/v4/sports/soccer_epl/events?apiKey={api_key}')
match_id = response.json()[0]['id']

# Obtener odds
odds_response = httpx.get(
    f'https://api.the-odds-api.com/v4/sports/soccer_epl/events/{match_id}/odds',
    params={'apiKey': api_key, 'regions': 'eu,us,uk,au', 'markets': 'h2h'}
)

bookmakers = sorted([b['key'] for b in odds_response.json()['bookmakers']])

# Casas solicitadas
requested = ['bwin', 'codere', 'winamax', 'betsson', 'pinnacle', 'marathonbet']

print('Verificación de casas de apuestas:')
print('=' * 50)
for casa in requested:
    # Buscar coincidencias parciales
    matches = [b for b in bookmakers if casa.lower() in b.lower()]
    if matches:
        print(f'{casa.upper()}: ✅ ENCONTRADA como {matches}')
    else:
        print(f'{casa.upper()}: ❌ NO DISPONIBLE')

print(f'\nTotal de casas disponibles: {len(bookmakers)}')
