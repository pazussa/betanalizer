#!/usr/bin/env python3
"""
Script para buscar resultados de partidos usando API-FOOTBALL
=============================================================

Este script busca los resultados de partidos de un archivo histórico
usando la API de API-FOOTBALL.

Uso:
    python buscar_resultados_api.py <archivo_historico.csv> [--api-key TU_API_KEY]

Requisitos:
    - API Key de API-FOOTBALL (https://www.api-football.com/)
    - requests, pandas
"""

import pandas as pd
import requests
import re
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple
import time

# Tu API key de API-FOOTBALL (también puede venir de variable de entorno)
API_KEY = os.environ.get('API_FOOTBALL_KEY', '')

# Mapeo de nombres de ligas a IDs de API-FOOTBALL
LIGA_TO_API_ID = {
    'Premier League': 39,
    'La Liga': 140,
    'Bundesliga': 78,
    'Serie A': 135,
    'Ligue 1': 61,
    'Eredivisie': 88,
    'Liga Portugal': 94,
    'Championship': 40,
    'League One': 41,
    'League Two': 42,
    'Bundesliga 2': 79,
    '3. Liga': 80,
    'La Liga 2': 141,
    'Serie B': 136,
    'Ligue 2': 62,
    'MLS': 253,
    'Liga MX': 262,
    'Liga Profesional': 128,  # Argentina
    'Primera División Chile': 265,
    'Süper Lig': 203,
    'Pro League': 144,  # Bélgica
    'Ekstraklasa': 106,
    'Super League Switzerland': 207,
    'Superliga Denmark': 119,
    'K League 1': 292,
    'J1 League': 98,
    'A-League': 188,
}


def normalizar_nombre_equipo(nombre: str) -> str:
    """Normaliza el nombre de un equipo para búsqueda."""
    nombre = nombre.lower().strip()
    
    # Remover sufijos comunes
    sufijos = ['fc', 'cf', 'sc', 'ac', 'afc', 'bc', 'fk', 'sk', 'as', 'ss']
    for suf in sufijos:
        nombre = re.sub(rf'\b{suf}\b', '', nombre)
    
    # Normalizar caracteres especiales
    nombre = nombre.replace('ü', 'u').replace('ö', 'o').replace('ä', 'a')
    nombre = nombre.replace('ñ', 'n').replace('é', 'e').replace('á', 'a')
    nombre = nombre.replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    
    # Remover caracteres no alfanuméricos
    nombre = re.sub(r'[^a-z0-9\s]', '', nombre)
    nombre = ' '.join(nombre.split())
    
    return nombre


def extraer_equipos(partido: str) -> Tuple[str, str]:
    """Extrae los nombres de los equipos de un string 'Local vs Visitante'."""
    partes = partido.split(' vs ')
    if len(partes) == 2:
        return partes[0].strip(), partes[1].strip()
    return partido, ""


def buscar_fixture_api(local: str, visitante: str, fecha: str, liga_id: int = None) -> Optional[dict]:
    """
    Busca un fixture específico en API-FOOTBALL.
    
    Args:
        local: Nombre del equipo local
        visitante: Nombre del equipo visitante
        fecha: Fecha en formato YYYY-MM-DD
        liga_id: ID de la liga (opcional)
    
    Returns:
        Diccionario con el resultado o None
    """
    if not API_KEY:
        return None
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    # Buscar por fecha
    url = f'https://v3.football.api-sports.io/fixtures'
    params = {'date': fecha}
    
    if liga_id:
        params['league'] = liga_id
        params['season'] = int(fecha[:4])  # Año de la fecha
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        if 'response' not in data:
            return None
        
        local_norm = normalizar_nombre_equipo(local)
        visitante_norm = normalizar_nombre_equipo(visitante)
        
        for fixture in data['response']:
            home = normalizar_nombre_equipo(fixture['teams']['home']['name'])
            away = normalizar_nombre_equipo(fixture['teams']['away']['name'])
            
            # Verificar si coinciden los equipos
            if (local_norm in home or home in local_norm) and \
               (visitante_norm in away or away in visitante_norm):
                
                score = fixture.get('score', {}).get('fulltime', {})
                if score.get('home') is not None and score.get('away') is not None:
                    return {
                        'score': f"{score['home']}-{score['away']}",
                        'home': fixture['teams']['home']['name'],
                        'away': fixture['teams']['away']['name'],
                        'fixture_id': fixture['fixture']['id']
                    }
        
        return None
        
    except Exception as e:
        print(f"Error en API: {e}")
        return None


def buscar_resultados_archivo(filepath: str, output_path: str = None, api_key: str = None):
    """
    Busca resultados para todos los partidos en un archivo CSV.
    
    Args:
        filepath: Ruta al archivo CSV con datos históricos
        output_path: Ruta para guardar el archivo con resultados (opcional)
        api_key: API key de API-FOOTBALL (opcional, usa variable de entorno si no se proporciona)
    """
    global API_KEY
    if api_key:
        API_KEY = api_key
    
    # Cargar datos
    df = pd.read_csv(filepath)
    
    # Obtener partidos únicos
    partidos_unicos = df[['Partido', 'Liga']].drop_duplicates()
    
    # Extraer fecha del nombre del archivo o de la columna
    if 'Fecha_Hora_Colombia' in df.columns:
        # Intentar extraer fecha de la primera fila
        try:
            fecha_str = df['Fecha_Hora_Colombia'].iloc[0]
            # Parsear fecha (formato esperado: "2025-03-07 ...")
            fecha = fecha_str.split()[0]
        except:
            fecha = None
    else:
        fecha = None
    
    print(f"Archivo: {filepath}")
    print(f"Partidos únicos: {len(partidos_unicos)}")
    print(f"Fecha detectada: {fecha}")
    print("-" * 50)
    
    resultados = {}
    encontrados = 0
    no_encontrados = []
    
    for _, row in partidos_unicos.iterrows():
        partido = row['Partido']
        liga = row['Liga']
        local, visitante = extraer_equipos(partido)
        
        if not local or not visitante:
            continue
        
        # Obtener ID de liga si está mapeada
        liga_id = LIGA_TO_API_ID.get(liga)
        
        # Buscar en la API
        if API_KEY and fecha:
            # Buscar en la fecha y días cercanos
            for delta in [0, 1, -1]:
                try:
                    fecha_busqueda = (datetime.strptime(fecha, '%Y-%m-%d') + timedelta(days=delta)).strftime('%Y-%m-%d')
                    resultado = buscar_fixture_api(local, visitante, fecha_busqueda, liga_id)
                    if resultado:
                        resultados[partido] = resultado['score']
                        encontrados += 1
                        print(f"✅ {partido}: {resultado['score']}")
                        break
                except:
                    pass
            else:
                no_encontrados.append((partido, liga))
                print(f"❌ {partido}")
            
            # Rate limiting
            time.sleep(0.5)
        else:
            no_encontrados.append((partido, liga))
    
    print("-" * 50)
    print(f"Encontrados: {encontrados}/{len(partidos_unicos)}")
    print(f"No encontrados: {len(no_encontrados)}")
    
    # Guardar resultados parciales
    if resultados:
        resultados_file = filepath.replace('.csv', '_resultados_api.json')
        with open(resultados_file, 'w') as f:
            json.dump(resultados, f, indent=2)
        print(f"\nResultados guardados en: {resultados_file}")
    
    # Guardar lista de no encontrados
    if no_encontrados:
        no_encontrados_file = filepath.replace('.csv', '_no_encontrados.txt')
        with open(no_encontrados_file, 'w') as f:
            for partido, liga in no_encontrados:
                f.write(f"{partido} | {liga}\n")
        print(f"No encontrados guardados en: {no_encontrados_file}")
    
    return resultados, no_encontrados


def agregar_resultados_a_csv(filepath: str, resultados: dict, output_path: str = None):
    """
    Agrega los resultados encontrados al archivo CSV.
    
    Args:
        filepath: Ruta al archivo CSV original
        resultados: Diccionario {partido: score}
        output_path: Ruta de salida (opcional)
    """
    df = pd.read_csv(filepath)
    
    def obtener_score(partido):
        # Buscar exactamente
        if partido in resultados:
            return resultados[partido]
        # Buscar normalizado
        for key, score in resultados.items():
            if normalizar_nombre_equipo(partido) == normalizar_nombre_equipo(key):
                return score
        return ""
    
    def calcular_total_goles(score):
        if not score or score == "":
            return ""
        try:
            partes = score.split('-')
            return int(partes[0]) + int(partes[1])
        except:
            return ""
    
    def verificar_acierto(row):
        if row['Total_Goles'] == "" or pd.isna(row['Total_Goles']):
            return ""
        
        try:
            total = float(row['Total_Goles'])
            mercado = row['Mercado']
            tipo = mercado.split()[0]  # Over o Under
            linea = float(mercado.split()[1])
            
            if tipo == 'Over':
                return 'Sí' if total > linea else 'No'
            else:  # Under
                return 'Sí' if total < linea else 'No'
        except:
            return ""
    
    # Agregar columnas
    df['Score'] = df['Partido'].apply(obtener_score)
    df['Total_Goles'] = df['Score'].apply(calcular_total_goles)
    df['Acerto'] = df.apply(verificar_acierto, axis=1)
    
    # Guardar
    if output_path is None:
        output_path = filepath.replace('.csv', '_con_resultados.csv')
    
    df.to_csv(output_path, index=False)
    
    # Estadísticas
    con_resultado = df[df['Score'] != ''].shape[0]
    total = df.shape[0]
    print(f"\nArchivo guardado: {output_path}")
    print(f"Filas con resultado: {con_resultado}/{total}")
    
    return df


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Buscar resultados de partidos usando API-FOOTBALL')
    parser.add_argument('archivo', help='Archivo CSV con datos históricos')
    parser.add_argument('--api-key', help='API key de API-FOOTBALL')
    parser.add_argument('--output', help='Archivo de salida (opcional)')
    parser.add_argument('--solo-buscar', action='store_true', help='Solo buscar, no agregar al CSV')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.archivo):
        print(f"Error: No se encuentra el archivo {args.archivo}")
        sys.exit(1)
    
    # Buscar resultados
    resultados, no_encontrados = buscar_resultados_archivo(
        args.archivo, 
        api_key=args.api_key
    )
    
    # Agregar al CSV si se encontraron resultados
    if resultados and not args.solo_buscar:
        agregar_resultados_a_csv(args.archivo, resultados, args.output)


if __name__ == '__main__':
    main()
