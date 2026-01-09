#!/usr/bin/env python3
"""
Pipeline Completo de Análisis Histórico
=======================================

Este script automatiza todo el proceso:
1. Toma un archivo histórico (historical_YYYYMMDD.csv)
2. Busca los resultados de los partidos
3. Agrega Score, Total_Goles, Acerto
4. Ejecuta el análisis de rendimiento completo

Uso:
    python pipeline_historico.py <archivo_historico.csv> [--manual-results archivo.json]
    
El archivo puede ser:
- Un CSV generado por main6.py (historical_YYYYMMDD.csv)
- Un CSV ya procesado con resultados (_con_resultados.csv)
"""

import pandas as pd
import numpy as np
import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Importar módulos locales
try:
    from analizar_rendimiento_historico import (
        cargar_datos, imprimir_reporte, guardar_reporte_csv
    )
except ImportError:
    print("Error: Se requiere analizar_rendimiento_historico.py en el mismo directorio")
    sys.exit(1)


def detectar_tipo_archivo(filepath: str) -> str:
    """Detecta si el archivo ya tiene resultados o no."""
    df = pd.read_csv(filepath)
    
    if 'Score' in df.columns and 'Acerto' in df.columns:
        # Verificar si tiene datos
        if df['Score'].notna().any() and (df['Score'] != '').any():
            return 'con_resultados'
    
    return 'sin_resultados'


def extraer_fecha_archivo(filepath: str) -> str:
    """Extrae la fecha del nombre del archivo o del contenido."""
    # Buscar patrón YYYYMMDD en el nombre
    match = re.search(r'(\d{8})', os.path.basename(filepath))
    if match:
        fecha_str = match.group(1)
        try:
            return datetime.strptime(fecha_str, '%Y%m%d').strftime('%Y-%m-%d')
        except:
            pass
    
    # Intentar desde el contenido
    df = pd.read_csv(filepath)
    if 'Fecha_Hora_Colombia' in df.columns:
        try:
            fecha_str = df['Fecha_Hora_Colombia'].iloc[0]
            return fecha_str.split()[0]
        except:
            pass
    
    return None


def cargar_resultados_json(json_path: str) -> dict:
    """Carga resultados desde un archivo JSON."""
    with open(json_path, 'r') as f:
        return json.load(f)


def normalizar_nombre(nombre: str) -> str:
    """Normaliza un nombre de equipo para comparación."""
    nombre = nombre.lower().strip()
    nombre = nombre.replace('ü', 'u').replace('ö', 'o').replace('ä', 'a')
    nombre = nombre.replace('ñ', 'n').replace('é', 'e').replace('á', 'a')
    nombre = nombre.replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    nombre = re.sub(r'[^a-z0-9\s]', '', nombre)
    nombre = ' '.join(nombre.split())
    return nombre


def buscar_resultado(partido: str, resultados: dict) -> str:
    """Busca el resultado de un partido en el diccionario."""
    # Búsqueda exacta
    if partido in resultados:
        return resultados[partido]
    
    # Búsqueda normalizada
    partido_norm = normalizar_nombre(partido)
    for key, score in resultados.items():
        if normalizar_nombre(key) == partido_norm:
            return score
    
    # Búsqueda parcial (equipos individuales)
    equipos_partido = partido_norm.split(' vs ')
    if len(equipos_partido) == 2:
        local, visitante = equipos_partido
        for key, score in resultados.items():
            key_norm = normalizar_nombre(key)
            equipos_key = key_norm.split(' vs ')
            if len(equipos_key) == 2:
                if (local in equipos_key[0] or equipos_key[0] in local) and \
                   (visitante in equipos_key[1] or equipos_key[1] in visitante):
                    return score
    
    return ""


def calcular_total_goles(score: str) -> str:
    """Calcula el total de goles de un marcador."""
    if not score or score == "":
        return ""
    try:
        partes = score.split('-')
        return str(int(partes[0]) + int(partes[1]))
    except:
        return ""


def verificar_acierto(row) -> str:
    """Verifica si una apuesta acertó."""
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


def agregar_resultados_a_df(df: pd.DataFrame, resultados: dict) -> pd.DataFrame:
    """Agrega resultados, total de goles y acierto al DataFrame."""
    df = df.copy()
    
    # Agregar Score
    df['Score'] = df['Partido'].apply(lambda x: buscar_resultado(x, resultados))
    
    # Agregar Total_Goles
    df['Total_Goles'] = df['Score'].apply(calcular_total_goles)
    
    # Agregar Acerto
    df['Acerto'] = df.apply(verificar_acierto, axis=1)
    
    return df


def crear_directorio_output(filepath: str) -> str:
    """Crea el directorio de salida basado en la fecha del archivo."""
    fecha = extraer_fecha_archivo(filepath)
    
    if fecha:
        try:
            dt = datetime.strptime(fecha, '%Y-%m-%d')
            year = str(dt.year)
            month = dt.strftime('%B').lower()  # marzo, abril, etc.
            
            # Traducir mes al español
            meses = {
                'january': 'enero', 'february': 'febrero', 'march': 'marzo',
                'april': 'abril', 'may': 'mayo', 'june': 'junio',
                'july': 'julio', 'august': 'agosto', 'september': 'septiembre',
                'october': 'octubre', 'november': 'noviembre', 'december': 'diciembre'
            }
            month = meses.get(month, month)
            
            base_dir = os.path.dirname(filepath)
            output_dir = os.path.join(base_dir, 'historical_analysis', year, month)
            os.makedirs(output_dir, exist_ok=True)
            return output_dir
        except:
            pass
    
    # Si no se puede determinar, usar el mismo directorio
    return os.path.dirname(filepath)


def ejecutar_pipeline(filepath: str, resultados_json: str = None):
    """
    Ejecuta el pipeline completo de análisis.
    
    Args:
        filepath: Ruta al archivo CSV histórico
        resultados_json: Ruta a un archivo JSON con resultados (opcional)
    """
    print('=' * 80)
    print('PIPELINE DE ANÁLISIS HISTÓRICO')
    print('=' * 80)
    
    # 1. Detectar tipo de archivo
    tipo = detectar_tipo_archivo(filepath)
    print(f'\n📁 Archivo: {filepath}')
    print(f'   Tipo: {tipo}')
    
    fecha = extraer_fecha_archivo(filepath)
    print(f'   Fecha: {fecha}')
    
    # 2. Si no tiene resultados, intentar agregarlos
    if tipo == 'sin_resultados':
        print('\n⚠️  El archivo no tiene resultados.')
        
        if resultados_json and os.path.exists(resultados_json):
            print(f'   Cargando resultados desde: {resultados_json}')
            resultados = cargar_resultados_json(resultados_json)
            
            df = pd.read_csv(filepath)
            df = agregar_resultados_a_df(df, resultados)
            
            # Guardar archivo con resultados
            output_dir = crear_directorio_output(filepath)
            output_file = os.path.join(output_dir, os.path.basename(filepath).replace('.csv', '_con_resultados.csv'))
            df.to_csv(output_file, index=False)
            
            print(f'   ✅ Archivo guardado: {output_file}')
            
            # Continuar con este archivo
            filepath = output_file
        else:
            print('\n❌ Para agregar resultados, proporciona un archivo JSON con --manual-results')
            print('   Formato JSON: {"Partido vs Partido": "X-X", ...}')
            print('\n   Ejemplo de uso:')
            print('   python pipeline_historico.py historical_20250307.csv --manual-results resultados.json')
            return
    
    # 3. Ejecutar análisis de rendimiento
    print('\n📊 Ejecutando análisis de rendimiento...\n')
    
    df = cargar_datos(filepath)
    
    # Verificar que hay suficientes datos
    partidos_con_resultado = df[df['Score'] != ''].shape[0]
    if partidos_con_resultado == 0:
        print('❌ No hay partidos con resultado para analizar.')
        return
    
    print(f'   Partidos con resultado: {partidos_con_resultado}')
    
    # Imprimir reporte
    imprimir_reporte(df, filepath)
    
    # Guardar CSVs
    guardar_reporte_csv(df, filepath)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pipeline completo de análisis histórico',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    # Analizar archivo que ya tiene resultados
    python pipeline_historico.py historical_analysis/2025/marzo/historical_20250307_con_resultados.csv
    
    # Agregar resultados y analizar
    python pipeline_historico.py historical_20250307.csv --manual-results resultados.json
    
Formato del archivo JSON de resultados:
{
    "Real Madrid vs Barcelona": "2-1",
    "Liverpool vs Manchester United": "3-0",
    ...
}
        """
    )
    
    parser.add_argument('archivo', help='Archivo CSV histórico a analizar')
    parser.add_argument('--manual-results', dest='resultados', 
                        help='Archivo JSON con resultados manuales')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.archivo):
        print(f'Error: No se encuentra el archivo {args.archivo}')
        sys.exit(1)
    
    ejecutar_pipeline(args.archivo, args.resultados)


if __name__ == '__main__':
    main()
