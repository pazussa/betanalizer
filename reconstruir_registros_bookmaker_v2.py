#!/usr/bin/env python3
"""
Script para reconstruir CORRECTAMENTE los registros con columna Bookmaker.

Los registros con Bookmaker son MÚLTIPLES filas por partido/mercado, 
cada una con un bookmaker diferente. Deben AGRUPARSE en un solo registro
con todas las cuotas combinadas.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
from scipy.stats import entropy
from collections import defaultdict


def calculate_jsd(probs_list):
    """Calcular Jensen-Shannon Divergence promedio entre distribuciones de probabilidad."""
    if len(probs_list) < 2:
        return 0.0
    
    # Convertir a array numpy
    probs = np.array(probs_list)
    
    # Promedio de todas las distribuciones
    m = np.mean(probs, axis=0)
    
    # Calcular JSD
    jsd_values = []
    for p in probs:
        # KL divergence de p respecto a m
        kl = entropy(p, m)
        if not np.isnan(kl) and not np.isinf(kl):
            jsd_values.append(kl)
    
    if jsd_values:
        return np.mean(jsd_values)
    return 0.0


def reconstruir_grupo(grupo: pd.DataFrame) -> dict:
    """
    Reconstruye un grupo de registros (mismo partido/mercado) en un solo registro.
    
    Args:
        grupo: DataFrame con múltiples filas del mismo partido/mercado
        
    Returns:
        Diccionario con el registro reconstruido
    """
    # Datos base (tomar del primer registro)
    first = grupo.iloc[0]
    
    # Obtener todas las cuotas por bookmaker
    cuotas = []
    for _, row in grupo.iterrows():
        bookmaker = row['Bookmaker']
        cuota = row['Mejor_Cuota']
        if pd.notna(bookmaker) and pd.notna(cuota) and cuota > 1:
            cuotas.append((bookmaker, float(cuota)))
    
    # Ordenar por cuota descendente
    cuotas.sort(key=lambda x: x[1], reverse=True)
    
    # Calcular estadísticas
    odds_values = [c[1] for c in cuotas]
    n_casas = len(cuotas)
    
    if n_casas == 0:
        return None
    
    mejor_cuota = max(odds_values)
    mejor_casa = cuotas[0][0]  # El primero después de ordenar
    cuota_promedio = np.mean(odds_values)
    
    # Diferencia entre mejor cuota y promedio
    diferencia = round(mejor_cuota - cuota_promedio, 4)
    
    # Volatilidad (desviación estándar)
    volatilidad = round(np.std(odds_values), 4) if n_casas > 1 else 0.0
    
    # Formatear todas las cuotas
    todas_cuotas = "; ".join([f"{bm}:{cuota:.4f}" for bm, cuota in cuotas])
    
    # Calcular margen si podemos encontrar el par Over/Under
    margen = None
    mercado = first['Mercado']
    
    # Buscar el complementario en el mismo grupo de datos original
    # (esto se hará después en el procesamiento principal)
    
    # Calcular BDI (no-fair) - aproximación binaria
    bdi_jsd = 0.0
    bdi_std_p = 0.0
    bdi_mad_p = 0.0
    
    if n_casas > 1:
        # Convertir cuotas a probabilidades implícitas
        probs = [1.0 / o for o in odds_values]
        
        # STD y MAD de probabilidades
        bdi_std_p = round(np.std(probs), 10)
        bdi_mad_p = round(np.mean(np.abs(probs - np.mean(probs))), 10)
        
        # JSD (aproximación binaria: selección vs complemento)
        prob_pairs = []
        for p in probs:
            # Par binario: [p, 1-p]
            prob_pairs.append([p, 1 - p])
        
        bdi_jsd = round(calculate_jsd(prob_pairs), 10)
    
    return {
        'Partido': first['Partido'],
        'Fecha_Hora_Colombia': first['Fecha_Hora_Colombia'],
        'Mercado': first['Mercado'],
        'Mejor_Cuota': round(mejor_cuota, 4),
        'Cuota_Promedio_Mercado': round(cuota_promedio, 4),
        'BDI_jsd_fair': bdi_jsd,  # Usamos el mismo para fair por ahora
        'BDI_n_bookmakers_fair': n_casas,
        'BDI_std_p_fair': bdi_std_p,
        'BDI_mad_p_fair': bdi_mad_p,
        'BDI_jsd': bdi_jsd,
        'BDI_n_bookmakers': n_casas,
        'BDI_std_p': bdi_std_p,
        'BDI_mad_p': bdi_mad_p,
        'Mejor_Casa': mejor_casa,
        'Num_Casas': n_casas,
        'Diferencia_Cuota_Promedio': diferencia,
        'Volatilidad_Pct': volatilidad,
        'Margen_Casa_Pct': None,  # Se calculará después
        'Liga': first['Liga'],
        'Tipo_Mercado': first['Tipo_Mercado'],
        'Snapshot_Date': first['Snapshot_Date'],
        'Todas_Las_Cuotas': todas_cuotas,
        'Score': first['Score'],
        'Total_Goles': first['Total_Goles'],
        'Acerto': first['Acerto'],
        '_cuotas_dict': {bm: c for bm, c in cuotas}  # Para calcular margen después
    }


def calcular_margen(registro: dict, todos_registros: list) -> float:
    """
    Calcula el margen del bookmaker emparejando Over/Under.
    """
    mercado = registro['Mercado']
    partido = registro['Partido']
    mejor_casa = registro['Mejor_Casa']
    cuotas_dict = registro.get('_cuotas_dict', {})
    
    if 'Over' not in mercado and 'Under' not in mercado:
        return None
    
    # Extraer tipo y línea
    parts = mercado.split()
    if len(parts) < 2:
        return None
    
    tipo = parts[0]
    linea = ' '.join(parts[1:])
    
    tipo_opuesto = 'Under' if tipo == 'Over' else 'Over'
    mercado_opuesto = f"{tipo_opuesto} {linea}"
    
    # Buscar el registro opuesto
    for otro in todos_registros:
        if otro['Partido'] == partido and otro['Mercado'] == mercado_opuesto:
            otras_cuotas = otro.get('_cuotas_dict', {})
            
            # Buscar la misma casa en ambos
            if mejor_casa in cuotas_dict and mejor_casa in otras_cuotas:
                cuota_actual = cuotas_dict[mejor_casa]
                cuota_opuesta = otras_cuotas[mejor_casa]
                
                prob_actual = 1 / cuota_actual
                prob_opuesta = 1 / cuota_opuesta
                margen = round((prob_actual + prob_opuesta - 1) * 100, 2)
                return margen
    
    return None


def procesar_archivo(filepath: str, backup_dir: str) -> dict:
    """
    Procesa un archivo CSV reconstruyendo los registros con Bookmaker.
    """
    filename = os.path.basename(filepath)
    print(f"\n{'='*60}")
    print(f"Procesando: {filename}")
    print('='*60)
    
    # Leer del backup original
    backup_path = os.path.join(backup_dir, filename)
    if os.path.exists(backup_path):
        df = pd.read_csv(backup_path)
        print(f"  📂 Leyendo desde backup original")
    else:
        df = pd.read_csv(filepath)
        print(f"  📂 Leyendo desde archivo actual")
    
    # Verificar si tiene columna Bookmaker
    if 'Bookmaker' not in df.columns:
        print(f"  ⚠️  El archivo no tiene columna 'Bookmaker', se omite.")
        return {'archivo': filename, 'procesados': 0, 'grupos': 0, 'omitido': True}
    
    # Separar registros
    mask_con_bm = df['Bookmaker'].notna() & (df['Bookmaker'] != '')
    registros_con_bm = df[mask_con_bm].copy()
    registros_sin_bm = df[~mask_con_bm].copy()
    
    n_con_bm = len(registros_con_bm)
    n_sin_bm = len(registros_sin_bm)
    
    print(f"  📊 Total registros originales: {len(df)}")
    print(f"  📊 Con Bookmaker (filas a agrupar): {n_con_bm}")
    print(f"  📊 Sin Bookmaker (ya completos): {n_sin_bm}")
    
    if n_con_bm == 0:
        # Solo eliminar columna Bookmaker
        df = df.drop(columns=['Bookmaker'])
        df.to_csv(filepath, index=False)
        print(f"  ✅ Solo se eliminó columna 'Bookmaker'")
        return {'archivo': filename, 'procesados': 0, 'grupos': 0, 'omitido': False}
    
    # Agrupar por Partido y Mercado
    grupos = registros_con_bm.groupby(['Partido', 'Mercado'])
    n_grupos = len(grupos)
    print(f"  📊 Grupos únicos (Partido+Mercado): {n_grupos}")
    
    # Reconstruir cada grupo
    registros_reconstruidos = []
    for (partido, mercado), grupo in grupos:
        registro = reconstruir_grupo(grupo)
        if registro:
            registros_reconstruidos.append(registro)
    
    print(f"  🔄 Registros reconstruidos: {len(registros_reconstruidos)}")
    
    # Calcular márgenes
    margenes_calculados = 0
    for reg in registros_reconstruidos:
        margen = calcular_margen(reg, registros_reconstruidos)
        reg['Margen_Casa_Pct'] = margen
        if margen is not None:
            margenes_calculados += 1
        # Eliminar campo temporal
        if '_cuotas_dict' in reg:
            del reg['_cuotas_dict']
    
    print(f"  📈 Márgenes calculados: {margenes_calculados}/{len(registros_reconstruidos)}")
    
    # Crear DataFrame con registros reconstruidos
    df_reconstruidos = pd.DataFrame(registros_reconstruidos)
    
    # Eliminar columna Bookmaker de registros sin bookmaker
    registros_sin_bm = registros_sin_bm.drop(columns=['Bookmaker'])
    
    # Combinar
    df_final = pd.concat([registros_sin_bm, df_reconstruidos], ignore_index=True)
    
    # Ordenar columnas para que coincidan
    columnas_orden = [
        'Partido', 'Fecha_Hora_Colombia', 'Mercado', 'Mejor_Cuota',
        'Cuota_Promedio_Mercado', 'BDI_jsd_fair', 'BDI_n_bookmakers_fair',
        'BDI_std_p_fair', 'BDI_mad_p_fair', 'BDI_jsd', 'BDI_n_bookmakers',
        'BDI_std_p', 'BDI_mad_p', 'Mejor_Casa', 'Num_Casas',
        'Diferencia_Cuota_Promedio', 'Volatilidad_Pct', 'Margen_Casa_Pct',
        'Liga', 'Tipo_Mercado', 'Snapshot_Date', 'Todas_Las_Cuotas',
        'Score', 'Total_Goles', 'Acerto'
    ]
    df_final = df_final[columnas_orden]
    
    # Guardar
    df_final.to_csv(filepath, index=False)
    
    print(f"  ✅ Archivo guardado: {len(df_final)} registros (antes: {len(df)})")
    
    # Verificación
    df_check = pd.read_csv(filepath)
    print(f"\n  🔍 Verificación:")
    print(f"     - Columnas: {len(df_check.columns)}")
    print(f"     - 'Bookmaker' en columnas: {'Bookmaker' in df_check.columns}")
    
    # Verificar un registro reconstruido
    if len(registros_reconstruidos) > 0:
        ejemplo = df_check[df_check['Num_Casas'] > 1].iloc[0] if len(df_check[df_check['Num_Casas'] > 1]) > 0 else None
        if ejemplo is not None:
            print(f"     - Ejemplo reconstruido:")
            print(f"       Partido: {ejemplo['Partido']}")
            print(f"       Mercado: {ejemplo['Mercado']}")
            print(f"       Num_Casas: {ejemplo['Num_Casas']}")
            print(f"       Todas_Las_Cuotas: {ejemplo['Todas_Las_Cuotas'][:80]}...")
    
    return {
        'archivo': filename,
        'procesados': n_con_bm,
        'grupos': n_grupos,
        'registros_finales': len(df_final),
        'omitido': False
    }


def main():
    """Función principal."""
    data_dir = Path("historical_con_resultados")
    
    # Buscar el backup más reciente
    backups = list(data_dir.glob("backup_reconstruccion_*"))
    if not backups:
        print("❌ No se encontró backup. Ejecuta primero el script anterior.")
        return
    
    backup_dir = sorted(backups)[-1]  # El más reciente
    
    print(f"="*70)
    print(f"RECONSTRUCCIÓN CORRECTA DE REGISTROS CON BOOKMAKER")
    print(f"="*70)
    print(f"Directorio de datos: {data_dir}")
    print(f"Usando backup: {backup_dir}")
    
    # Obtener archivos CSV
    archivos = [f for f in data_dir.glob("*.csv") if f.is_file() and 'backup' not in str(f)]
    archivos.sort()
    
    print(f"\nArchivos a procesar: {len(archivos)}")
    
    # Procesar cada archivo
    estadisticas = []
    for filepath in archivos:
        stats = procesar_archivo(str(filepath), str(backup_dir))
        estadisticas.append(stats)
    
    # Resumen final
    print(f"\n{'='*70}")
    print("RESUMEN FINAL")
    print(f"{'='*70}")
    
    total_filas = sum(s.get('procesados', 0) for s in estadisticas if not s.get('omitido', False))
    total_grupos = sum(s.get('grupos', 0) for s in estadisticas if not s.get('omitido', False))
    
    print(f"\n📊 Filas con Bookmaker procesadas: {total_filas}")
    print(f"📊 Grupos reconstruidos: {total_grupos}")
    
    print(f"\nDetalle por archivo:")
    for s in estadisticas:
        if s.get('omitido', False):
            print(f"  ⚠️  {s['archivo']}: OMITIDO")
        else:
            print(f"  ✅ {s['archivo']}: {s.get('grupos', 0)} grupos de {s.get('procesados', 0)} filas")
    
    print(f"\n✅ Proceso completado")


if __name__ == "__main__":
    main()
