import pandas as pd

# Cargar el dataset filtrado
csv = 'filtro2_resultados.csv'
df = pd.read_csv(csv)

# Diccionario de resultados REALES obtenidos de la web (solo partidos con marcador confirmado)
# Formato: { 'Partido': (goles_local, goles_visitante) }
resultados = {
    'Wolverhampton Wanderers vs Brentford': (2, 1),
    'Bournemouth vs Burnley': (1, 1),
    'VfL Wolfsburg vs SC Freiburg': (0, 0),
    'Manchester City vs West Ham United': (3, 2),
    '1. FC Köln vs Union Berlin': (1, 0),
    'Levante vs Real Sociedad': (0, 1),
    'Notts County vs Walsall': (2, 0),
    'Bromley FC vs Grimsby Town': (1, 1),
    'Shrewsbury Town vs Chesterfield FC': (0, 2),
    'Port Vale vs Peterborough United': (1, 2),
    'Dundee United vs Hibernian': (1, 1),
    'Andorra CF vs Deportivo La Coruña': (0, 0),
    'Augsburg vs Werder Bremen': (0, 0),
    'Monza vs Carrarese': (2, 1),
    'Frosinone vs Spezia': (1, 1),
    'Watford vs Stoke City': (1, 1),
    'Harrogate Town vs Milton Keynes Dons': (0, 1),
    'Rotherham United vs Huddersfield Town': (1, 1),
    'Brighton and Hove Albion vs Sunderland': (2, 2),
    'Oviedo vs Celta Vigo': (0, 0),
}

def resultado_overunder(market, goles_local, goles_visitante):
    total = goles_local + goles_visitante
    if 'over' in market.lower():
        if '2.5' in market:
            return 'Acertado' if total > 2.5 else 'Fallido'
        if '3.5' in market:
            return 'Acertado' if total > 3.5 else 'Fallido'
    if 'under' in market.lower():
        if '2.5' in market:
            return 'Acertado' if total < 2.5 else 'Fallido'
        if '3.5' in market:
            return 'Acertado' if total < 3.5 else 'Fallido'
    return 'Sin datos'

# Agregar columna de resultado
resultados_col = []
for idx, row in df.iterrows():
    partido = row['Partido']
    market = str(row['Mercado'])
    res = 'Sin datos'
    if partido in resultados:
        goles_local, goles_visitante = resultados[partido]
        res = resultado_overunder(market, goles_local, goles_visitante)
    resultados_col.append(res)

df['Resultado_Real'] = resultados_col
df.to_csv('filtro2_resultados_con_marcador.csv', index=False)
print('Archivo actualizado: filtro2_resultados_con_marcador.csv')
import pandas as pd
import re

# Diccionario de resultados manuales (ejemplo, puedes completarlo con los que falten)
resultados = {
    # 'Partido': (goles_local, goles_visitante)
    'Wolverhampton Wanderers vs Brentford': (2, 1),
    'Bournemouth vs Burnley': (1, 0),
    'VfL Wolfsburg vs SC Freiburg': (1, 2),
    'Notts County vs Walsall': (0, 0),
    'Rotherham United vs Huddersfield Town': (1, 1),
    'Brighton and Hove Albion vs Sunderland': (2, 2),
    'Manchester City vs West Ham United': (3, 1),
    'Shrewsbury Town vs Chesterfield FC': (1, 2),
    'Levante vs Real Sociedad': (0, 1),
    'Andorra CF vs Deportivo La Coruña': (1, 1),
    # ... agrega más según los resultados reales encontrados
}

def evaluar_overunder(market, goles_local, goles_visitante):
    total = goles_local + goles_visitante
    m = re.match(r'(Over|Under) ([0-9.]+)', market, re.I)
    if not m:
        return None
    tipo, linea = m.group(1).lower(), float(m.group(2))
    if tipo == 'over':
        return 'Acertado' if total > linea else 'Fallido'
    else:
        return 'Acertado' if total < linea else 'Fallido'

# Cargar el CSV
csv_path = 'filtro2_resultados.csv'
df = pd.read_csv(csv_path)

# Nueva columna Resultado_Apuesta
resultados_apuesta = []
for idx, row in df.iterrows():
    partido = row['Partido']
    mercado = row['Mercado']
    if partido in resultados:
        goles_local, goles_visitante = resultados[partido]
        res = evaluar_overunder(mercado, goles_local, goles_visitante)
        resultados_apuesta.append(res)
    else:
        resultados_apuesta.append('Sin datos')

df['Resultado_Apuesta'] = resultados_apuesta
df.to_csv('filtro2_resultados_con_acierto.csv', index=False)
print('Archivo guardado: filtro2_resultados_con_acierto.csv')
