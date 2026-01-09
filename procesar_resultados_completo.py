#!/usr/bin/env python3
"""
Procesar todos los archivos históricos y agregar resultados.
Genera archivos _con_resultados.csv para todos los meses.
"""

import pandas as pd
import json
import glob
import os
import unicodedata
from pathlib import Path

def normalizar_nombre(nombre: str) -> str:
    """Normaliza un nombre de equipo para comparación."""
    if not nombre:
        return ""
    nombre = nombre.lower().strip()
    nombre = unicodedata.normalize('NFD', nombre)
    nombre = ''.join(c for c in nombre if unicodedata.category(c) != 'Mn')
    nombre = nombre.replace('ü', 'u').replace('ö', 'o').replace('ä', 'a').replace('ß', 'ss')
    # Remover sufijos comunes
    import re
    sufijos = ['fc', 'cf', 'sc', 'ac', 'afc', 'bc', 'fk', 'sk', 'as', 'ss', 'sv', 'vfb', 'vfl', 'tsv', 'fsv']
    for suf in sufijos:
        nombre = re.sub(rf'\b{suf}\b', '', nombre)
    nombre = re.sub(r'[^a-z0-9\s]', '', nombre)
    nombre = ' '.join(nombre.split())
    return nombre

def cargar_resultados():
    """Carga todos los resultados de archivos JSON."""
    resultados = {}
    
    # Buscar en varios directorios
    patterns = [
        'buscador_resultados/*.json',
        'historical_analysis/2025/*/*.json',
        '*.json'
    ]
    
    for pattern in patterns:
        for f in glob.glob(pattern):
            if 'resultados' in f.lower():
                try:
                    with open(f, 'r') as file:
                        data = json.load(file)
                        resultados.update(data)
                except Exception as e:
                    print(f"  Error cargando {f}: {e}")
    
    return resultados

def buscar_resultado(partido: str, cache: dict) -> str:
    """Busca un resultado en el cache con múltiples estrategias."""
    # Búsqueda exacta
    if partido in cache:
        return cache[partido]
    
    # Búsqueda normalizada
    partido_norm = normalizar_nombre(partido)
    for key, score in cache.items():
        if normalizar_nombre(key) == partido_norm:
            return score
    
    # Búsqueda parcial por equipos
    if ' vs ' in partido:
        equipos = partido.split(' vs ')
        if len(equipos) == 2:
            local, visitante = equipos[0].strip(), equipos[1].strip()
            local_norm = normalizar_nombre(local)
            visit_norm = normalizar_nombre(visitante)
            
            for key, score in cache.items():
                if ' vs ' in key:
                    key_equipos = key.split(' vs ')
                    if len(key_equipos) == 2:
                        key_local = normalizar_nombre(key_equipos[0])
                        key_visit = normalizar_nombre(key_equipos[1])
                        
                        # Match parcial
                        if ((local_norm in key_local or key_local in local_norm) and
                            (visit_norm in key_visit or key_visit in visit_norm)):
                            return score
    
    return None

def calcular_total_goles(score: str) -> str:
    """Calcula el total de goles de un marcador."""
    if not score:
        return ""
    try:
        score = score.replace('–', '-').replace('—', '-')
        partes = score.split('-')
        if len(partes) == 2:
            return str(int(partes[0].strip()) + int(partes[1].strip()))
    except:
        pass
    return ""

def verificar_acierto(mercado: str, total_goles: str) -> str:
    """Verifica si una apuesta acertó."""
    if not total_goles:
        return ""
    try:
        total = float(total_goles)
        partes = mercado.split()
        if len(partes) >= 2:
            tipo = partes[0]  # Over o Under
            linea = float(partes[1])
            
            if tipo == 'Over':
                return 'Sí' if total > linea else 'No'
            elif tipo == 'Under':
                return 'Sí' if total < linea else 'No'
    except:
        pass
    return ""

def procesar_archivo(filepath: str, cache: dict) -> tuple:
    """Procesa un archivo CSV y agrega resultados."""
    df = pd.read_csv(filepath)
    
    # Agregar columnas si no existen
    if 'Score' not in df.columns:
        df['Score'] = ""
    if 'Total_Goles' not in df.columns:
        df['Total_Goles'] = ""
    if 'Acerto' not in df.columns:
        df['Acerto'] = ""
    
    partidos_procesados = 0
    partidos_encontrados = 0
    partidos_no_encontrados = []
    
    for idx, row in df.iterrows():
        partido = row['Partido']
        score_actual = row.get('Score', '')
        
        # Si ya tiene score válido, saltar
        if pd.notna(score_actual) and score_actual not in ['', 'Sin datos']:
            continue
        
        partidos_procesados += 1
        score = buscar_resultado(partido, cache)
        
        if score:
            df.at[idx, 'Score'] = score
            total = calcular_total_goles(score)
            df.at[idx, 'Total_Goles'] = total
            df.at[idx, 'Acerto'] = verificar_acierto(row['Mercado'], total)
            partidos_encontrados += 1
        else:
            partidos_no_encontrados.append(partido)
    
    return df, partidos_encontrados, list(set(partidos_no_encontrados))

def main():
    print("=" * 60)
    print("PROCESADOR DE RESULTADOS COMPLETO")
    print("=" * 60)
    
    # Cargar cache de resultados
    print("\n📂 Cargando resultados existentes...")
    cache = cargar_resultados()
    print(f"   Total resultados en cache: {len(cache)}")
    
    # Procesar todos los archivos
    todos_no_encontrados = {}
    
    for mes in ['enero', 'febrero', 'marzo']:
        print(f"\n{'='*60}")
        print(f"📅 Procesando {mes.upper()} 2025")
        print("="*60)
        
        archivos = sorted(glob.glob(f'historical_analysis/2025/{mes}/historical_*.csv'))
        archivos = [f for f in archivos if 'raw' not in f and 'con_resultados' not in f]
        
        for filepath in archivos:
            nombre = os.path.basename(filepath)
            print(f"\n📁 {nombre}")
            
            df, encontrados, no_encontrados = procesar_archivo(filepath, cache)
            
            # Guardar archivo con resultados
            output_path = filepath.replace('.csv', '_con_resultados.csv')
            df.to_csv(output_path, index=False)
            
            # Estadísticas
            total = len(df)
            con_score = df['Score'].apply(lambda x: pd.notna(x) and x not in ['', 'Sin datos']).sum()
            pct = 100 * con_score / total if total > 0 else 0
            
            print(f"   ✅ Encontrados: {encontrados} nuevos")
            print(f"   📊 Cobertura: {con_score}/{total} ({pct:.1f}%)")
            print(f"   💾 Guardado: {os.path.basename(output_path)}")
            
            if no_encontrados:
                for p in no_encontrados[:5]:
                    todos_no_encontrados[p] = mes
                if len(no_encontrados) > 5:
                    print(f"   ❌ Faltantes: {len(no_encontrados)} partidos")
    
    # Guardar lista de partidos no encontrados
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print("="*60)
    print(f"Total partidos sin resultado: {len(todos_no_encontrados)}")
    
    # Guardar para búsqueda posterior
    with open('partidos_sin_resultado.txt', 'w') as f:
        for partido, mes in sorted(todos_no_encontrados.items()):
            f.write(f"{mes}|{partido}\n")
    
    print(f"Lista guardada en: partidos_sin_resultado.txt")

if __name__ == "__main__":
    main()
