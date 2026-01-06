# Investigación de APIs de Odds de Apuestas Deportivas

## Estado Actual - THE_ODDS_API

### Tu cuenta actual tiene:
- **Requests usados**: 4
- **Requests restantes**: 496 (de 500/mes en el plan gratuito)

### Bookmakers disponibles con THE_ODDS_API (58 casas):

| Región | Bookmakers |
|--------|------------|
| **EU** | pinnacle, marathonbet, betsson, coolbet, nordicbet, tipico_de, winamax_de, winamax_fr, parionssport_fr, pmu_fr, unibet_fr, unibet_nl, unibet_se, codere_it, onexbet, everygame, gtbets |
| **UK** | betfair_ex_uk, betfair_sb_uk, betway, sport888, coral, paddypower, skybet, smarkets, unibet_uk, virginbet, williamhill, boylesports, casumo, grosvenor, leovegas, livescorebet, ladbrokes_uk, matchbook |
| **US** | betmgm, betonlineag, betrivers, betus, bovada, draftkings, fanduel, lowvig, mybookieag |
| **AU** | betfair_ex_au, betr_au, betright, boombet, ladbrokes_au, neds, playup, pointsbetau, sportsbet, tab, tabtouch, unibet |
| **Global** | leovegas_se (SE) |

---

## APIs Alternativas Investigadas

### 1. API-FOOTBALL (Recomendada para odds adicionales)
**URL**: https://www.api-football.com/

**Características**:
- ✅ **Plan gratuito**: 100 requests/día
- ✅ Cuotas pre-match y en vivo disponibles
- ✅ +180 ligas de fútbol
- ✅ Endpoint específico de odds: `/odds` y `/odds/live`
- ✅ Bookmakers incluidos: ~15 diferentes

**Bookmakers disponibles** (complementarios a THE_ODDS_API):
- Bet365 (no disponible en THE_ODDS_API gratuito)
- Bwin (no disponible en THE_ODDS_API)
- 1xBet (aparece como "onexbet" en THE_ODDS_API)
- Unibet, Betway, William Hill (ya en THE_ODDS_API)

**Cómo obtener API Key**:
1. Ir a https://dashboard.api-football.com/register
2. Registrarse gratis
3. Obtener API Key en el dashboard

**Ejemplo de uso**:
```python
import requests

headers = {'x-apisports-key': 'TU_API_KEY'}
url = 'https://v3.football.api-sports.io/odds'
params = {'league': 39, 'season': 2024}  # Premier League 2024

response = requests.get(url, headers=headers, params=params)
```

---

### 2. BetsAPI (De pago, pero económica)
**URL**: https://betsapi.com/

**Características**:
- ❌ NO tiene plan gratuito
- 💰 Desde $10/mes (precio muy bajo)
- ✅ Acceso a casas específicas con mercados completos:
  - Bet365 API (todos los mercados)
  - Bwin API
  - Betfair (Sportsbook + Exchange)
  - SboBet
  - 1xBet
  - Betway (nuevo)
  
**Ventaja principal**: Acceso a **Bet365** completo, que es la casa con mayor cobertura y mercados más líquidos.

**Rate Limit**: 3,600 requests/hora

**Qué aporta que THE_ODDS_API no tiene**:
- Bet365 con todos los mercados
- Sbobet
- Datos históricos de odds

---

### 3. Sportradar (Enterprise - No recomendada)
**URL**: https://sportradar.com/

- ❌ Solo para empresas (licensing enterprise)
- ❌ Sin capa gratuita
- ❌ Precios no públicos (típicamente $1,000+/mes)

---

## Comparativa de Casas de Apuestas por API

| Casa de Apuestas | THE_ODDS_API (Gratis) | API-FOOTBALL (Gratis) | BetsAPI ($10/mes) |
|------------------|:---------------------:|:---------------------:|:-----------------:|
| **Pinnacle** | ✅ | ❌ | ❌ |
| **Bet365** | ❌ (Solo AU pago) | ✅ | ✅ (Completo) |
| **Bwin** | ❌ | ✅ | ✅ |
| **Betfair Exchange** | ✅ | ✅ | ✅ |
| **1xBet** | ✅ | ✅ | ✅ |
| **William Hill** | ✅ | ✅ | ✅ |
| **Betsson** | ✅ | ❌ | ✅ |
| **Marathon** | ✅ | ❌ | ❌ |
| **Unibet** | ✅ | ✅ | ❌ |
| **SboBet** | ❌ | ❌ | ✅ |
| **Draftkings** | ✅ | ❌ | ❌ |
| **FanDuel** | ✅ | ❌ | ❌ |

---

## Plan de Acción Recomendado

### Opción 1: Gratis (Recomendada para empezar)
1. **Mantener THE_ODDS_API** como fuente principal (500 requests/mes)
2. **Agregar API-FOOTBALL** como fuente complementaria (100 requests/día = 3,000/mes)

**Casas adicionales que ganarías**:
- Bet365 ⭐ (muy importante - casa más líquida)
- Bwin

### Opción 2: Con inversión mínima ($10/mes)
1. Mantener THE_ODDS_API
2. Agregar **BetsAPI** ($10/mes)

**Casas adicionales que ganarías**:
- Bet365 completo con todos los mercados
- SboBet (casa asiática muy importante para arbitraje)
- Datos históricos

---

## Implementación para API-FOOTBALL

Para integrar API-FOOTBALL en tu proyecto `main2.py`, necesitarías:

### 1. Crear archivo de configuración `.env`:
```dotenv
THE_ODDS_API_KEY=92342011a4d3e5f20e043bdc7259adab
API_FOOTBALL_KEY=TU_KEY_AQUI
```

### 2. Crear nuevo cliente API (src/apis/api_football.py):

```python
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Optional

class APIFootballClient:
    BASE_URL = "https://v3.football.api-sports.io"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"x-apisports-key": api_key}
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
    
    async def get_odds(self, fixture_id: int) -> List[Dict]:
        """Obtiene cuotas pre-match para un fixture específico"""
        url = f"{self.BASE_URL}/odds"
        params = {"fixture": fixture_id}
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return data.get("response", [])
    
    async def get_fixtures_by_date(self, date: str, league_id: int = None) -> List[Dict]:
        """Obtiene partidos por fecha (formato: YYYY-MM-DD)"""
        url = f"{self.BASE_URL}/fixtures"
        params = {"date": date}
        if league_id:
            params["league"] = league_id
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return data.get("response", [])
    
    async def get_bookmakers(self) -> List[Dict]:
        """Lista bookmakers disponibles"""
        url = f"{self.BASE_URL}/odds/bookmakers"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json().get("response", [])
```

---

## Próximos Pasos

1. **Regístrate en API-FOOTBALL**: https://dashboard.api-football.com/register (gratis)
2. **Obtén tu API Key** del dashboard
3. **Ejecuta el siguiente comando** para probar la conexión:

```bash
curl --request GET \
    --url 'https://v3.football.api-sports.io/status' \
    --header 'x-apisports-key: TU_API_KEY'
```

4. **Actualiza el archivo `.env`** con la nueva key
5. **Te creo el cliente de integración** cuando tengas la key

---

## Resumen

| API | Costo | Requests | Casas Únicas |
|-----|-------|----------|--------------|
| THE_ODDS_API | Gratis | 500/mes | Pinnacle, Marathon, DraftKings, FanDuel, casas AU |
| API-FOOTBALL | Gratis | 3,000/mes | Bet365, Bwin |
| BetsAPI | $10/mes | 3,600/hora | SboBet, Bet365 completo |

**Mi recomendación**: Empieza con API-FOOTBALL (gratis) para añadir Bet365 y Bwin que son casas muy importantes para el análisis de valor.
