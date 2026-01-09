#!/usr/bin/env python3
"""
Script para reconstruir registros con columna Bookmaker
en los datasets historical_con_resultados.

Los registros con datos en la columna Bookmaker provienen de una fuente diferente
y no fueron procesados por main3.py. Este script los reconstruye para que tengan
todas las columnas completas, y luego elimina la columna Bookmaker.

Columnas a completar:
- Mejor_Casa: Se toma del valor de Bookmaker
- Num_Casas: 1 (solo hay una casa de apuestas)
- Todas_Las_Cuotas: "{Bookmaker}:{Mejor_Cuota}"
- Diferencia_Cuota_Promedio: 0 (Mejor_Cuota = Cuota_Promedio_Mercado)
- Volatilidad_Pct: 0 (con una sola cuota no hay volatilidad)
- Margen_Casa_Pct: Se calcula si es posible emparejar Over/Under
- BDI_*: NaN (no se pueden calcular con una sola casa de apuestas)
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import shutil
from datetime import datetime


def reconstruir_registro(row: pd.Series, df: pd.DataFrame) -> pd.Series:
    """
    Reconstruye un registro con Bookmaker para que tenga todas las columnas completas.
    
    Args:
        row: Fila con Bookmaker que necesita ser reconstruida
        df: DataFrame completo para buscar pares Over/Under
        
    Returns:
        Fila reconstruida con todas las columnas
    """
    row_copy = row.copy()
    
    # Mejor_Casa = Bookmaker
    row_copy['Mejor_Casa'] = row_copy['Bookmaker']
    
    # Num_Casas = 1
    row_copy['Num_Casas'] = 1
    
    # Formatear Todas_Las_Cuotas
    mejor_cuota = row_copy['Mejor_Cuota']
    bookmaker = row_copy['Bookmaker']
    row_copy['Todas_Las_Cuotas'] = f"{bookmaker}:{mejor_cuota:.4f}" if pd.notna(mejor_cuota) else ""
    
    # Diferencia_Cuota_Promedio = 0 (ya que solo hay una cuota)
    row_copy['Diferencia_Cuota_Promedio'] = 0.0
    
    # Volatilidad_Pct = 0 (sin dispersión con una sola cuota)
    row_copy['Volatilidad_Pct'] = 0.0
    
    # Calcular Margen_Casa_Pct si podemos encontrar el par Over/Under
    mercado = row_copy['Mercado']
    margen = None
    
    if 'Over' in str(mercado) or 'Under' in str(mercado):
        # Extraer la línea del mercado (ej: "Over 2.5" -> 2.5)
        parts = str(mercado).split()
        if len(parts) >= 2:
            tipo = parts[0]  # Over o Under
            linea = parts[1] if len(parts) > 1 else ""
            
            # Buscar el par complementario del mismo partido, bookmaker y línea
            tipo_opuesto = 'Under' if tipo == 'Over' else 'Over'
            mercado_opuesto = f"{tipo_opuesto} {linea}"
            
            # Buscar en el mismo DataFrame
            par = df[(df['Partido'] == row_copy['Partido']) &
                    (df['Mercado'] == mercado_opuesto) &
                    (df['Bookmaker'] == row_copy['Bookmaker'])]
            
            if not par.empty:
                cuota_actual = float(row_copy['Mejor_Cuota'])
                cuota_opuesta = float(par.iloc[0]['Mejor_Cuota'])
                
                if cuota_actual > 1 and cuota_opuesta > 1:
                    prob_actual = 1 / cuota_actual
                    prob_opuesta = 1 / cuota_opuesta
                    margen = round((prob_actual + prob_opuesta - 1) * 100, 2)
    
    row_copy['Margen_Casa_Pct'] = margen if margen is not None else np.nan
    
    # BDIs no se pueden calcular con una sola casa de apuestas
    # Los dejamos como NaN (ya están así)
    
    return row_copy


def procesar_archivo(filepath: str, backup_dir: str) -> dict:
    """
    Procesa un archivo CSV reconstruyendo los registros con Bookmaker.
    
    Args:
        filepath: Ruta al archivo CSV
        backup_dir: Directorio para guardar backup
        
    Returns:
        Diccionario con estadísticas del procesamiento
    """
    filename = os.path.basename(filepath)
    print(f"\n{'='*60}")
    print(f"Procesando: {filename}")
    print('='*60)
    
    # Leer archivo
    df = pd.read_csv(filepath)
    
    # Verificar si tiene columna Bookmaker
    if 'Bookmaker' not in df.columns:
        print(f"  ⚠️  El archivo no tiene columna 'Bookmaker', se omite.")
        return {'archivo': filename, 'procesados': 0, 'total': len(df), 'omitido': True}
    
    # Identificar registros con Bookmaker
    mask_con_bookmaker = df['Bookmaker'].notna() & (df['Bookmaker'] != '')
    registros_con_bm = df[mask_con_bookmaker].copy()
    registros_sin_bm = df[~mask_con_bookmaker].copy()
    
    n_con_bm = len(registros_con_bm)
    n_sin_bm = len(registros_sin_bm)
    
    print(f"  📊 Total registros: {len(df)}")
    print(f"  📊 Con Bookmaker (a reconstruir): {n_con_bm}")
    print(f"  📊 Sin Bookmaker (completos): {n_sin_bm}")
    
    if n_con_bm == 0:
        print(f"  ✅ No hay registros que reconstruir.")
        # Aún así eliminar la columna Bookmaker
        df = df.drop(columns=['Bookmaker'])
        df.to_csv(filepath, index=False)
        print(f"  ✅ Columna 'Bookmaker' eliminada.")
        return {'archivo': filename, 'procesados': 0, 'total': len(df), 'omitido': False}
    
    # Crear backup antes de modificar
    backup_path = os.path.join(backup_dir, filename)
    shutil.copy2(filepath, backup_path)
    print(f"  💾 Backup creado: {backup_path}")
    
    # Reconstruir registros con Bookmaker
    print(f"  🔄 Reconstruyendo {n_con_bm} registros...")
    
    margenes_calculados = 0
    for idx in registros_con_bm.index:
        row_reconstruida = reconstruir_registro(df.loc[idx], df)
        df.loc[idx] = row_reconstruida
        if pd.notna(row_reconstruida['Margen_Casa_Pct']):
            margenes_calculados += 1
    
    print(f"  📈 Márgenes calculados: {margenes_calculados}/{n_con_bm}")
    
    # Eliminar columna Bookmaker
    df = df.drop(columns=['Bookmaker'])
    
    # Guardar archivo procesado
    df.to_csv(filepath, index=False)
    print(f"  ✅ Archivo guardado (columna 'Bookmaker' eliminada)")
    
    # Verificación
    df_verificacion = pd.read_csv(filepath)
    print(f"\n  🔍 Verificación:")
    print(f"     - Columnas: {len(df_verificacion.columns)}")
    print(f"     - 'Bookmaker' en columnas: {'Bookmaker' in df_verificacion.columns}")
    print(f"     - Registros con Mejor_Casa: {df_verificacion['Mejor_Casa'].notna().sum()}/{len(df_verificacion)}")
    print(f"     - Registros con Num_Casas: {df_verificacion['Num_Casas'].notna().sum()}/{len(df_verificacion)}")
    
    return {
        'archivo': filename,
        'procesados': n_con_bm,
        'total': len(df),
        'margenes_calculados': margenes_calculados,
        'omitido': False
    }


def main():
    """Función principal que procesa todos los archivos."""
    # Directorio de datos
    data_dir = Path("historical_con_resultados")
    
    # Crear directorio de backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = data_dir / f"backup_reconstruccion_{timestamp}"
    backup_dir.mkdir(exist_ok=True)
    
    print(f"="*70)
    print(f"RECONSTRUCCIÓN DE REGISTROS CON BOOKMAKER")
    print(f"="*70)
    print(f"Directorio de datos: {data_dir}")
    print(f"Directorio de backup: {backup_dir}")
    
    # Obtener archivos CSV (excluyendo subcarpetas)
    archivos = [f for f in data_dir.glob("*.csv") if f.is_file()]
    archivos.sort()
    
    print(f"\nArchivos encontrados: {len(archivos)}")
    
    # Procesar cada archivo
    estadisticas = []
    for filepath in archivos:
        stats = procesar_archivo(str(filepath), str(backup_dir))
        estadisticas.append(stats)
    
    # Resumen final
    print(f"\n{'='*70}")
    print("RESUMEN FINAL")
    print(f"{'='*70}")
    
    total_procesados = sum(s['procesados'] for s in estadisticas if not s.get('omitido', False))
    total_archivos = len([s for s in estadisticas if not s.get('omitido', False)])
    
    print(f"\n📊 Archivos procesados: {total_archivos}/{len(archivos)}")
    print(f"📊 Registros reconstruidos: {total_procesados}")
    
    print(f"\nDetalle por archivo:")
    for s in estadisticas:
        if s.get('omitido', False):
            print(f"  ⚠️  {s['archivo']}: OMITIDO (sin columna Bookmaker)")
        else:
            print(f"  ✅ {s['archivo']}: {s['procesados']} reconstruidos de {s['total']} total")
    
    print(f"\n✅ Proceso completado. Backups en: {backup_dir}")


if __name__ == "__main__":
    main()
