#!/usr/bin/env python3
"""
🚀 PROCESAR MÚLTIPLES FECHAS
============================

Procesa múltiples archivos históricos de una vez.

Uso:
    python procesar_multiples.py archivo1.csv archivo2.csv archivo3.csv
    python procesar_multiples.py ../historical_analysis/2025/marzo/*.csv
"""

import sys
import os
import glob
from buscar_resultados import procesar_archivo, cargar_resultados_existentes
from analizar_rendimiento import cargar_datos, imprimir_reporte
import json


def main():
    if len(sys.argv) < 2:
        print("Uso: python procesar_multiples.py <archivo1.csv> [archivo2.csv] ...")
        print("\nEjemplo:")
        print("  python procesar_multiples.py ../historical_analysis/2025/marzo/historical_2025031*.csv")
        sys.exit(1)
    
    # Expandir globs y obtener archivos
    archivos = []
    for arg in sys.argv[1:]:
        if '*' in arg:
            archivos.extend(glob.glob(arg))
        else:
            archivos.append(arg)
    
    # Filtrar solo CSV que no sean ya "_con_resultados"
    archivos = [a for a in archivos if a.endswith('.csv') and '_con_resultados' not in a]
    
    if not archivos:
        print("No se encontraron archivos para procesar")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"🚀 PROCESAMIENTO MÚLTIPLE")
    print(f"{'='*70}")
    print(f"Archivos a procesar: {len(archivos)}")
    for a in archivos:
        print(f"  - {os.path.basename(a)}")
    
    # Cargar todos los resultados existentes
    print(f"\n📂 Cargando base de resultados...")
    resultados_base = cargar_resultados_existentes('.')
    
    # También cargar de la carpeta padre
    resultados_padre = cargar_resultados_existentes('..')
    resultados_base.update(resultados_padre)
    
    print(f"   Total resultados en base: {len(resultados_base)}")
    
    # Procesar cada archivo
    resultados_globales = []
    
    for filepath in archivos:
        if not os.path.exists(filepath):
            print(f"\n⚠️  No existe: {filepath}")
            continue
        
        stats = procesar_archivo(filepath, resultados_base)
        resultados_globales.append(stats)
        
        # Agregar nuevos resultados a la base para los siguientes archivos
        if stats['encontrados'] > 0:
            json_path = filepath.replace('.csv', '_resultados.json')
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    nuevos = json.load(f)
                    resultados_base.update(nuevos)
    
    # Resumen global
    print(f"\n{'='*70}")
    print(f"📊 RESUMEN GLOBAL")
    print(f"{'='*70}")
    
    total_encontrados = sum(r['encontrados'] for r in resultados_globales)
    total_no_encontrados = sum(r['no_encontrados'] for r in resultados_globales)
    total_partidos = sum(r['total'] for r in resultados_globales)
    
    print(f"   Archivos procesados: {len(resultados_globales)}")
    print(f"   Partidos encontrados: {total_encontrados}/{total_partidos} ({100*total_encontrados/total_partidos:.1f}%)")
    print(f"   Partidos faltantes: {total_no_encontrados}")
    
    # Listar partidos faltantes
    if total_no_encontrados > 0:
        print(f"\n⚠️  PARTIDOS NO ENCONTRADOS:")
        print("-" * 60)
        for stats in resultados_globales:
            if stats['partidos_faltantes']:
                print(f"\n{os.path.basename(stats['archivo'])}:")
                for partido, liga in stats['partidos_faltantes'][:10]:  # Mostrar max 10
                    print(f"   - {partido} ({liga})")
                if len(stats['partidos_faltantes']) > 10:
                    print(f"   ... y {len(stats['partidos_faltantes']) - 10} más")
    
    # Análisis de rendimiento para archivos con resultados
    print(f"\n{'='*70}")
    print(f"📈 ANÁLISIS DE RENDIMIENTO")
    print(f"{'='*70}")
    
    for stats in resultados_globales:
        if stats['output_csv'] and os.path.exists(stats['output_csv']):
            print(f"\n{'='*70}")
            df = cargar_datos(stats['output_csv'])
            if len(df) > 0:
                imprimir_reporte(df, stats['output_csv'])


if __name__ == '__main__':
    main()
