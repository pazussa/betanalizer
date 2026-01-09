#!/usr/bin/env python3
"""
Busca resultados faltantes de La Liga 2
"""

import json
from pathlib import Path

# Partidos sin resultado en los archivos históricos
PARTIDOS_SIN_RESULTADO = [
    "Albacete vs Málaga",
    "Albacete vs Real Racing Club de Santander",
    "Albacete vs Zaragoza",
    "Almería vs Levante",
    "Almería vs Málaga",
    "Almería vs Oviedo",
    "Almería vs Zaragoza",
    "Burgos CF vs Deportivo La Coruña",
    "Burgos CF vs Oviedo",
    "CD Castellón vs Burgos CF",
    "CD Castellón vs SD Eibar",
    "CD Castellón vs SD Huesca",
    "CD Eldense vs Burgos CF",
    "CD Eldense vs Cádiz CF",
    "CD Eldense vs CD Mirandés",
    "CD Eldense vs Granada CF",
    "CD Mirandés vs Elche",
    "CD Mirandés vs Oviedo",
    "Córdoba vs Almería",
    "Córdoba vs Elche",
    "Córdoba vs Granada CF",
    "Córdoba vs Real Racing Club de Santander",
    "Córdoba vs Sporting Gijón",
    "Deportivo La Coruña vs Córdoba",
    "Deportivo La Coruña vs Levante",
    "Elche vs CD Castellón",
    "Elche vs SD Eibar",
    "Elche vs Tenerife",
    "FC Cartagena vs Burgos CF",
    "FC Cartagena vs CD Castellón",
    "FC Cartagena vs Málaga",
    "FC Cartagena vs Oviedo",
    "FC Cartagena vs SD Eibar",
    "Granada CF vs Burgos CF",
    "Granada CF vs CD Mirandés",
    "Granada CF vs Sporting Gijón",
    "Granada CF vs Zaragoza",
    "Levante vs Granada CF",
    "Málaga vs Deportivo La Coruña",
    "Málaga vs Levante",
    "Oviedo vs Albacete",
    "Oviedo vs Elche",
    "Oviedo vs Sporting Gijón",
    "Racing de Ferrol vs CD Castellón",
    "Racing de Ferrol vs Córdoba",
    "Racing de Ferrol vs Deportivo La Coruña",
    "Racing de Ferrol vs FC Cartagena",
    "Racing de Ferrol vs SD Eibar",
    "Real Racing Club de Santander vs Cádiz CF",
    "Real Racing Club de Santander vs Elche",
    "Real Racing Club de Santander vs Málaga",
    "Real Racing Club de Santander vs Zaragoza",
    "SD Eibar vs Albacete",
    "SD Eibar vs Almería",
    "SD Eibar vs Real Racing Club de Santander",
    "SD Huesca vs CD Mirandés",
    "SD Huesca vs FC Cartagena",
    "SD Huesca vs Racing de Ferrol",
    "Sporting Gijón vs Almería",
    "Sporting Gijón vs Burgos CF",
    "Sporting Gijón vs Elche",
    "Sporting Gijón vs Real Racing Club de Santander",
    "Sporting Gijón vs SD Eibar",
    "Tenerife vs CD Castellón",
    "Tenerife vs CD Eldense",
    "Tenerife vs Córdoba",
    "Tenerife vs Granada CF",
    "Tenerife vs SD Huesca",
    "Zaragoza vs CD Eldense",
    "Zaragoza vs Sporting Gijón",
]

# Cargar resultados existentes de los archivos JSON
buscador_path = Path("/home/asus/Escritorio/proyectos/betsanalizer/betanalizer/buscador_resultados")
resultados_existentes = {}

for json_file in buscador_path.glob("*.json"):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        resultados_existentes.update(data)

# Cargar resultados del archivo principal
with open("/home/asus/Escritorio/proyectos/betsanalizer/betanalizer/resultados_encontrados.py", 'r', encoding='utf-8') as f:
    content = f.read()
    # Extraer solo la sección RESULTADOS
    import re
    matches = re.findall(r'"([^"]+)"\s*:\s*"(\d+-\d+)"', content)
    for partido, resultado in matches:
        resultados_existentes[partido] = resultado

# Normalizar nombres para mejor coincidencia
def normalizar_nombre(nombre):
    """Normaliza nombres de equipos para mejor coincidencia"""
    normalizaciones = {
        'Real Oviedo': 'Oviedo',
        'Racing Santander': 'Real Racing Club de Santander',
        'Racing de Santander': 'Real Racing Club de Santander',
        'Racing Ferrol': 'Racing de Ferrol',
        'Racing de Ferrol': 'Racing de Ferrol',
        'Eibar': 'SD Eibar',
        'Huesca': 'SD Huesca',
        'Malaga': 'Málaga',
        'Cordoba': 'Córdoba',
        'Zaragoza': 'Real Zaragoza',
        'Real Zaragoza': 'Zaragoza',
        'Castellón': 'CD Castellón',
        'Eldense': 'CD Eldense',
        'Mirandés': 'CD Mirandés',
        'Mirandes': 'CD Mirandés',
        'Deportivo': 'Deportivo La Coruña',
        'Cartagena': 'FC Cartagena',
        'Granada': 'Granada CF',
        'Cadiz': 'Cádiz CF',
        'Cádiz': 'Cádiz CF',
        'Almeria': 'Almería',
        'Sporting Gijon': 'Sporting Gijón',
    }
    
    for old, new in normalizaciones.items():
        nombre = nombre.replace(old, new)
    return nombre

# Buscar resultados
resultados_encontrados = {}
partidos_no_encontrados = []

for partido in PARTIDOS_SIN_RESULTADO:
    encontrado = False
    partido_norm = normalizar_nombre(partido)
    
    # Buscar en resultados existentes
    for key, value in resultados_existentes.items():
        key_norm = normalizar_nombre(key)
        
        # Comparar exacto
        if key_norm == partido_norm:
            resultados_encontrados[partido] = value
            encontrado = True
            break
        
        # Comparar equipos en orden inverso
        equipos = partido_norm.split(' vs ')
        if len(equipos) == 2:
            partido_inverso = f"{equipos[1]} vs {equipos[0]}"
            if key_norm == partido_inverso:
                # Invertir resultado
                partes = value.split('-')
                if len(partes) == 2:
                    resultado_invertido = f"{partes[1]}-{partes[0]}"
                    resultados_encontrados[partido] = resultado_invertido
                    encontrado = True
                    break
    
    if not encontrado:
        partidos_no_encontrados.append(partido)

# Imprimir resultados
print("=" * 80)
print("RESULTADOS ENCONTRADOS DE LA LIGA 2:")
print("=" * 80)
for partido, resultado in sorted(resultados_encontrados.items()):
    print(f"'{partido}': '{resultado}'")

print("\n" + "=" * 80)
print(f"TOTAL ENCONTRADOS: {len(resultados_encontrados)}")
print("=" * 80)

if partidos_no_encontrados:
    print("\n" + "=" * 80)
    print("PARTIDOS NO ENCONTRADOS:")
    print("=" * 80)
    for partido in sorted(partidos_no_encontrados):
        print(f"  - {partido}")
    print(f"\nTOTAL NO ENCONTRADOS: {len(partidos_no_encontrados)}")
    print("=" * 80)
