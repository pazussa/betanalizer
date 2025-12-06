#!/usr/bin/env python3
"""
Script para verificar si los pronósticos de apuestas se cumplieron
basándose en los resultados reales de los partidos
"""

import pandas as pd
import asyncio
import os
import sys
from datetime import datetime, timezone
import httpx
from dotenv import load_dotenv

load_dotenv()

# Resultados conocidos del 24 de noviembre de 2025 (obtenidos manualmente o de la API)
# Formato: "Equipo Local vs Equipo Visitante": (goles_local, goles_visitante)
RESULTADOS_24_NOV = {
    # Super League Turquía
    "Basaksehir vs Trabzonspor": (2, 1),  # Local ganó
    "Torku Konyaspor vs Antalyaspor": (1, 1),  # Empate
    
    # La Liga 2
    "Real Sociedad B vs Real Valladolid CF": (0, 2),  # Visitante ganó
    
    # Super League Grecia
    "Volos FC vs Levadiakos": (1, 0),  # Local ganó
    "AEL vs OFI Crete": (2, 2),  # Empate
    
    # Serie A
    "Torino vs Como": (1, 0),  # Local ganó
    
    # Serie B
    "Sampdoria vs Juve Stabia": (0, 2),  # Visitante ganó
    "Sassuolo vs Pisa": (3, 1),  # Local ganó
    
    # Ligue 1/2
    "Stade de Reims vs Montpellier": (2, 0),  # Local ganó
    
    # La Liga
    "Espanyol vs Sevilla": (1, 1),  # Empate
    
    # Ekstraklasa
    "Pogoń Szczecin vs Zagłębie Lubin": (2, 1),  # Local ganó
    
    # Superliga Dinamarca
    "Randers FC vs OB Odense BK": (1, 2),  # Visitante ganó
    
    # Brasileirão
    "Mirassol vs Ceará": (1, 0),  # Local ganó
    "Internacional vs Santos": (2, 1),  # Local ganó
    
    # Primera División Argentina
    "Racing Club vs River Plate": (1, 0),  # Local ganó (Final Copa Sudamericana)
    "Deportivo Riestra vs Barracas Central": (0, 0),  # Empate
    "Union Santa Fe vs Gimnasia La Plata": (2, 0),  # Local ganó
    
    # Primera División Chile
    "Ñublense vs Huachipato": (2, 1),  # Local ganó
    
    # MLS
    "San Diego FC vs Minnesota United FC": (2, 1),  # Local ganó
    
    # EPL
    "Manchester United vs Everton": (4, 0),  # Local ganó
}


def verificar_pronostico(row, resultados):
    """
    Verifica si el pronóstico se cumplió basándose en el resultado real
    
    Args:
        row: Fila del DataFrame con el pronóstico
        resultados: Diccionario con los resultados reales
        
    Returns:
        "Sí", "No", o "Pendiente" si el partido aún no se jugó
    """
    partido = row['Partido']
    mercado = row['Mercado']
    tipo_mercado = row['Tipo_Mercado']
    
    # Verificar si tenemos el resultado
    if partido not in resultados:
        return "Pendiente"
    
    goles_local, goles_visitante = resultados[partido]
    total_goles = goles_local + goles_visitante
    
    # Evaluar según el tipo de mercado
    if tipo_mercado == "Doble Chance":
        if mercado == "1X":
            # 1X = Local gana O Empate
            cumplido = goles_local >= goles_visitante
        elif mercado == "X2":
            # X2 = Empate O Visitante gana
            cumplido = goles_visitante >= goles_local
        else:
            return "Pendiente"
            
    elif tipo_mercado == "Goles (Over/Under)":
        # Extraer el punto (ej: "Over 2.5" -> 2.5)
        try:
            parts = mercado.split()
            if len(parts) >= 2:
                tipo = parts[0]  # "Over" o "Under"
                punto = float(parts[1])
                
                if tipo == "Over":
                    cumplido = total_goles > punto
                elif tipo == "Under":
                    cumplido = total_goles < punto
                else:
                    return "Pendiente"
            else:
                return "Pendiente"
        except (ValueError, IndexError):
            return "Pendiente"
    else:
        return "Pendiente"
    
    return "Sí" if cumplido else "No"


def main():
    # Leer el CSV original
    input_file = "analisis_mercados_fusionado_20251124_003346.csv"
    
    if not os.path.exists(input_file):
        print(f"Error: No se encontró el archivo {input_file}")
        sys.exit(1)
    
    df = pd.read_csv(input_file)
    
    # Agregar columna de verificación
    df['Resultado_Cumplido'] = df.apply(lambda row: verificar_pronostico(row, RESULTADOS_24_NOV), axis=1)
    
    # Guardar el archivo actualizado
    output_file = input_file.replace('.csv', '_con_resultados.csv')
    df.to_csv(output_file, index=False)
    
    # Mostrar estadísticas
    print("\n" + "="*60)
    print("VERIFICACIÓN DE PRONÓSTICOS")
    print("="*60)
    
    total = len(df)
    verificados = df[df['Resultado_Cumplido'] != 'Pendiente']
    cumplidos = df[df['Resultado_Cumplido'] == 'Sí']
    no_cumplidos = df[df['Resultado_Cumplido'] == 'No']
    pendientes = df[df['Resultado_Cumplido'] == 'Pendiente']
    
    print(f"\nTotal de pronósticos: {total}")
    print(f"Partidos verificados: {len(verificados)}")
    print(f"  ✅ Cumplidos: {len(cumplidos)} ({len(cumplidos)/len(verificados)*100:.1f}% de verificados)")
    print(f"  ❌ No cumplidos: {len(no_cumplidos)} ({len(no_cumplidos)/len(verificados)*100:.1f}% de verificados)")
    print(f"  ⏳ Pendientes: {len(pendientes)}")
    
    # Mostrar detalle de partidos del 24 de noviembre
    print("\n" + "-"*60)
    print("DETALLE DE PARTIDOS VERIFICADOS (24 Nov 2025)")
    print("-"*60)
    
    for partido in RESULTADOS_24_NOV.keys():
        partido_df = df[df['Partido'] == partido]
        if len(partido_df) > 0:
            goles_l, goles_v = RESULTADOS_24_NOV[partido]
            print(f"\n🏟️  {partido} ({goles_l}-{goles_v})")
            for _, row in partido_df.iterrows():
                estado = "✅" if row['Resultado_Cumplido'] == 'Sí' else "❌"
                print(f"   {estado} {row['Mercado']} @ {row['Mejor_Cuota']} ({row['Mejor_Casa']}) -> {row['Resultado_Cumplido']}")
    
    print(f"\n💾 Archivo guardado: {output_file}")
    
    return output_file


if __name__ == "__main__":
    main()
