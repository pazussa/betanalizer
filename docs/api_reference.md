# Documentación del API

## Endpoints Principales

### The Odds API

**Base URL**: `https://api.the-odds-api.com/v4`

#### Obtener Deportes Disponibles
```http
GET /sports?apiKey={API_KEY}
```

#### Obtener Partidos de Fútbol
```http
GET /sports/soccer_epl/events?apiKey={API_KEY}&regions=eu,us&dateFormat=iso
```

#### Obtener Cuotas de un Partido
```http
GET /sports/soccer_epl/events/{event_id}/odds?apiKey={API_KEY}&regions=eu,us&markets=h2h&oddsFormat=decimal
```

### SportRadar API

**Base URL**: `https://api.sportradar.com/soccer/trial/v4/en`

#### Obtener Programación de Torneo
```http
GET /tournaments/{tournament_id}/schedule.json?api_key={API_KEY}
```

**Torneos Populares**:
- Premier League: `sr:tournament:17`
- Champions League: `sr:tournament:7`
- La Liga: `sr:tournament:8`

## Códigos de Respuesta

- `200`: Éxito
- `401`: API key inválida
- `403`: Quota excedida
- `404`: Recurso no encontrado
- `429`: Rate limit excedido

## Rate Limits

- **The Odds API**: 500 requests/mes (plan gratuito)
- **SportRadar**: 1000 requests/mes (plan trial)

## Ejemplos de Respuesta

### Partidos (The Odds API)
```json
[
  {
    "id": "event_id_123",
    "sport_key": "soccer_epl",
    "home_team": "Manchester United",
    "away_team": "Liverpool",
    "commence_time": "2025-11-22T15:00:00Z"
  }
]
```

### Cuotas (The Odds API)
```json
{
  "id": "event_id_123",
  "home_team": "Manchester United", 
  "away_team": "Liverpool",
  "bookmakers": [
    {
      "key": "pinnacle",
      "title": "Pinnacle",
      "markets": [
        {
          "key": "h2h",
          "last_update": "2025-11-21T10:30:00Z",
          "outcomes": [
            {"name": "Manchester United", "price": 2.10},
            {"name": "Draw", "price": 3.40},
            {"name": "Liverpool", "price": 3.20}
          ]
        }
      ]
    }
  ]
}
```