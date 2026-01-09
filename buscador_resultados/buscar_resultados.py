#!/usr/bin/env python3
"""
🔍 BUSCADOR DE RESULTADOS DE PARTIDOS
=====================================

Script principal para buscar resultados de partidos de fútbol
usando múltiples fuentes (web scraping de sitios públicos).

Uso:
    python buscar_resultados.py <archivo_historico.csv>
    python buscar_resultados.py historical_20250314.csv
    
Genera:
    - <archivo>_resultados.json: Resultados encontrados
    - <archivo>_no_encontrados.txt: Partidos sin resultado
    - <archivo>_con_resultados.csv: Archivo con resultados agregados
"""

import pandas as pd
import requests
import re
import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import unicodedata

# Configuración
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
TIMEOUT = 10
MAX_WORKERS = 5  # Threads paralelos para búsqueda


def normalizar_nombre(nombre: str) -> str:
    """Normaliza un nombre de equipo para comparación."""
    if not nombre:
        return ""
    nombre = nombre.lower().strip()
    # Remover acentos
    nombre = unicodedata.normalize('NFD', nombre)
    nombre = ''.join(c for c in nombre if unicodedata.category(c) != 'Mn')
    # Normalizar caracteres
    nombre = nombre.replace('ü', 'u').replace('ö', 'o').replace('ä', 'a')
    nombre = nombre.replace('ß', 'ss')
    # Remover sufijos comunes
    sufijos = ['fc', 'cf', 'sc', 'ac', 'afc', 'bc', 'fk', 'sk', 'as', 'ss', 'sv', 'vfb', 'vfl', 'tsv', 'fsv']
    for suf in sufijos:
        nombre = re.sub(rf'\b{suf}\b', '', nombre)
    nombre = re.sub(r'[^a-z0-9\s]', '', nombre)
    nombre = ' '.join(nombre.split())
    return nombre


def extraer_equipos(partido: str) -> Tuple[str, str]:
    """Extrae los nombres de los equipos de un string 'Local vs Visitante'."""
    partes = partido.split(' vs ')
    if len(partes) == 2:
        return partes[0].strip(), partes[1].strip()
    return partido, ""


def extraer_fecha_archivo(filepath: str) -> Optional[str]:
    """Extrae la fecha del nombre del archivo."""
    match = re.search(r'(\d{8})', os.path.basename(filepath))
    if match:
        fecha_str = match.group(1)
        try:
            return datetime.strptime(fecha_str, '%Y%m%d').strftime('%Y-%m-%d')
        except:
            pass
    return None


def buscar_en_flashscore(local: str, visitante: str, fecha: str) -> Optional[str]:
    """
    Busca resultado en Flashscore (placeholder - requiere implementación con Selenium).
    Por ahora retorna None.
    """
    # Flashscore requiere JavaScript, necesitaría Selenium
    return None


def buscar_en_soccerway(local: str, visitante: str, fecha: str) -> Optional[str]:
    """
    Intenta buscar en Soccerway.
    """
    try:
        # Soccerway también es complicado, requiere navegación
        return None
    except:
        return None


def calcular_total_goles(score: str) -> str:
    """Calcula el total de goles de un marcador."""
    if not score or score == "":
        return ""
    try:
        partes = score.replace('–', '-').replace('—', '-').split('-')
        return str(int(partes[0].strip()) + int(partes[1].strip()))
    except:
        return ""


def verificar_acierto(mercado: str, total_goles: str) -> str:
    """Verifica si una apuesta acertó."""
    if total_goles == "" or total_goles is None:
        return ""
    try:
        total = float(total_goles)
        tipo = mercado.split()[0]  # Over o Under
        linea = float(mercado.split()[1])
        
        if tipo == 'Over':
            return 'Sí' if total > linea else 'No'
        else:  # Under
            return 'Sí' if total < linea else 'No'
    except:
        return ""


def cargar_resultados_existentes(directorio: str = None) -> Dict[str, str]:
    """Carga todos los resultados existentes de archivos JSON previos."""
    resultados = {}
    
    # Buscar en el directorio actual y padre
    dirs_buscar = ['.', '..', directorio] if directorio else ['.', '..']
    
    for dir_path in dirs_buscar:
        if not dir_path or not os.path.exists(dir_path):
            continue
        for archivo in os.listdir(dir_path):
            if archivo.endswith('_resultados.json') or archivo == 'resultados_marzo_2025.json':
                try:
                    with open(os.path.join(dir_path, archivo), 'r') as f:
                        data = json.load(f)
                        resultados.update(data)
                        print(f"  📂 Cargados {len(data)} resultados de {archivo}")
                except:
                    pass
    
    return resultados


def buscar_resultado_en_cache(partido: str, cache: Dict[str, str]) -> Optional[str]:
    """Busca un resultado en el cache de resultados existentes."""
    # Búsqueda exacta
    if partido in cache:
        return cache[partido]
    
    # Búsqueda normalizada
    partido_norm = normalizar_nombre(partido)
    for key, score in cache.items():
        if normalizar_nombre(key) == partido_norm:
            return score
    
    # Búsqueda parcial (equipos individuales)
    equipos_partido = partido_norm.split(' vs ')
    if len(equipos_partido) == 2:
        local, visitante = equipos_partido
        for key, score in cache.items():
            key_norm = normalizar_nombre(key)
            if ' vs ' in key_norm:
                equipos_key = key_norm.split(' vs ')
                if len(equipos_key) == 2:
                    # Coincidencia parcial en ambos equipos
                    match_local = (local in equipos_key[0] or equipos_key[0] in local or 
                                   any(p in equipos_key[0] for p in local.split() if len(p) > 3))
                    match_visit = (visitante in equipos_key[1] or equipos_key[1] in visitante or
                                   any(p in equipos_key[1] for p in visitante.split() if len(p) > 3))
                    if match_local and match_visit:
                        return score
    
    return None


def buscar_resultados_archivo(filepath: str, resultados_manual: Dict[str, str] = None) -> Tuple[Dict, List]:
    """
    Busca resultados para todos los partidos en un archivo CSV.
    
    Args:
        filepath: Ruta al archivo CSV con datos históricos
        resultados_manual: Diccionario adicional con resultados manuales
        
    Returns:
        Tuple de (resultados_encontrados, partidos_no_encontrados)
    """
    # Cargar datos
    df = pd.read_csv(filepath)
    
    # Obtener partidos únicos
    if 'Liga' in df.columns:
        partidos_unicos = df[['Partido', 'Liga']].drop_duplicates()
    else:
        partidos_unicos = df[['Partido']].drop_duplicates()
        partidos_unicos['Liga'] = 'Desconocida'
    
    fecha = extraer_fecha_archivo(filepath)
    
    print(f"\n{'='*60}")
    print(f"📁 Archivo: {os.path.basename(filepath)}")
    print(f"📅 Fecha: {fecha}")
    print(f"⚽ Partidos únicos: {len(partidos_unicos)}")
    print(f"{'='*60}")
    
    # Cargar cache de resultados existentes
    print("\n🔍 Cargando resultados existentes...")
    cache = cargar_resultados_existentes(os.path.dirname(filepath))
    
    # Agregar resultados manuales al cache
    if resultados_manual:
        cache.update(resultados_manual)
        print(f"  📂 Agregados {len(resultados_manual)} resultados manuales")
    
    print(f"  📊 Total en cache: {len(cache)} resultados")
    
    resultados = {}
    no_encontrados = []
    
    print("\n🔎 Buscando resultados...")
    
    for _, row in partidos_unicos.iterrows():
        partido = row['Partido']
        liga = row.get('Liga', 'Desconocida')
        
        # Buscar en cache
        score = buscar_resultado_en_cache(partido, cache)
        
        if score:
            resultados[partido] = score
            print(f"  ✅ {partido}: {score}")
        else:
            no_encontrados.append((partido, liga))
            print(f"  ❌ {partido}")
    
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN:")
    print(f"   ✅ Encontrados: {len(resultados)}/{len(partidos_unicos)}")
    print(f"   ❌ No encontrados: {len(no_encontrados)}")
    print(f"{'='*60}")
    
    return resultados, no_encontrados


def agregar_resultados_a_csv(filepath: str, resultados: Dict[str, str]) -> str:
    """
    Agrega los resultados encontrados al archivo CSV.
    
    Returns:
        Ruta del archivo de salida
    """
    df = pd.read_csv(filepath)
    
    def obtener_score(partido):
        return buscar_resultado_en_cache(partido, resultados) or ""
    
    # Agregar columnas
    df['Score'] = df['Partido'].apply(obtener_score)
    df['Total_Goles'] = df['Score'].apply(calcular_total_goles)
    df['Acerto'] = df.apply(lambda r: verificar_acierto(r['Mercado'], r['Total_Goles']), axis=1)
    
    # Guardar
    output_path = filepath.replace('.csv', '_con_resultados.csv')
    df.to_csv(output_path, index=False)
    
    # Estadísticas
    con_resultado = (df['Score'] != '').sum()
    total = len(df)
    
    print(f"\n💾 Archivo guardado: {output_path}")
    print(f"   Filas con resultado: {con_resultado}/{total} ({100*con_resultado/total:.1f}%)")
    
    return output_path


def guardar_resultados_json(filepath: str, resultados: Dict[str, str]):
    """Guarda los resultados en un archivo JSON."""
    output_path = filepath.replace('.csv', '_resultados.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"📄 Resultados JSON: {output_path}")
    return output_path


def guardar_no_encontrados(filepath: str, no_encontrados: List[Tuple[str, str]]):
    """Guarda la lista de partidos no encontrados."""
    if not no_encontrados:
        return
    
    output_path = filepath.replace('.csv', '_no_encontrados.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Partidos no encontrados - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"# Total: {len(no_encontrados)}\n\n")
        for partido, liga in no_encontrados:
            f.write(f"{partido} | {liga}\n")
    print(f"📄 No encontrados: {output_path}")
    return output_path


def procesar_archivo(filepath: str, resultados_extra: Dict[str, str] = None) -> dict:
    """
    Procesa un archivo histórico completo.
    
    Returns:
        Diccionario con estadísticas del procesamiento
    """
    # Buscar resultados
    resultados, no_encontrados = buscar_resultados_archivo(filepath, resultados_extra)
    
    # Guardar resultados JSON
    if resultados:
        guardar_resultados_json(filepath, resultados)
    
    # Guardar no encontrados
    if no_encontrados:
        guardar_no_encontrados(filepath, no_encontrados)
    
    # Agregar al CSV
    if resultados:
        output_csv = agregar_resultados_a_csv(filepath, resultados)
    else:
        output_csv = None
    
    return {
        'archivo': filepath,
        'encontrados': len(resultados),
        'no_encontrados': len(no_encontrados),
        'total': len(resultados) + len(no_encontrados),
        'output_csv': output_csv,
        'partidos_faltantes': no_encontrados
    }


def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("Uso: python buscar_resultados.py <archivo_historico.csv>")
        print("\nEjemplo:")
        print("  python buscar_resultados.py ../historical_analysis/2025/marzo/historical_20250314.csv")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    if not os.path.exists(filepath):
        print(f"Error: No se encuentra el archivo {filepath}")
        sys.exit(1)
    
    # Verificar si hay un JSON de resultados extra como segundo argumento
    resultados_extra = None
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        with open(sys.argv[2], 'r') as f:
            resultados_extra = json.load(f)
        print(f"📂 Cargados {len(resultados_extra)} resultados extra de {sys.argv[2]}")
    
    # Procesar archivo
    stats = procesar_archivo(filepath, resultados_extra)
    
    # Resumen final
    print(f"\n{'='*60}")
    print(f"✅ PROCESAMIENTO COMPLETADO")
    print(f"{'='*60}")
    print(f"   Encontrados: {stats['encontrados']}/{stats['total']}")
    
    if stats['no_encontrados'] > 0:
        print(f"\n⚠️  Faltan {stats['no_encontrados']} partidos por encontrar.")
        print("   Puedes agregar los resultados manualmente al archivo JSON")
        print("   y volver a ejecutar el script.")


if __name__ == '__main__':
    main()
