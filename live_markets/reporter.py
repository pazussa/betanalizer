"""
Generador de reportes CSV para análisis de mercados en vivo
"""
import csv
from datetime import datetime
from typing import List, Dict
from pathlib import Path
import pytz

from models import MarketAnalysisResult, MarketType


class LiveMarketsReporter:
    """Generador de reportes para mercados en vivo"""
    
    def __init__(self, timezone: str = "America/Bogota"):
        self.timezone = pytz.timezone(timezone)
    
    def generate_csvs(self, results_by_market: Dict[MarketType, List[MarketAnalysisResult]], 
                      output_dir: str = ".") -> Dict[str, str]:
        """
        Genera UN SOLO CSV combinando todos los mercados
        
        Returns:
            Diccionario con filepath
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Combinar todos los resultados
        all_results = []
        for market_type, results in results_by_market.items():
            all_results.extend(results)
        
        if not all_results:
            return {}
        
        filename = f"analisis_mercados_{timestamp}.csv"
        filepath = Path(output_dir) / filename
        
        # Ordenar por Score_Final descendente
        sorted_results = sorted(
            all_results,
            key=lambda x: x.final_score if x.final_score is not None else -999999,
            reverse=True
        )
        
        # Escribir CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Headers - agregamos "Tipo_Mercado" para identificar
            headers = [
                "Partido",
                "Fecha_Hora_Colombia",
                "Estado",
                "Tipo_Mercado",
                "Mercado",
                "Mejor_Cuota",
                "Mejor_Casa",
                "Num_Casas",
                "Score_Final",
                "Diferencia_Cuota_Promedio",
                "Volatilidad_Pct",
                "Margen_Casa_Pct",
                "Cuota_Promedio_Mercado",
                "Todas_Las_Cuotas"
            ]
            writer.writerow(headers)
            
            # Rows
            for result in sorted_results:
                score_final = result.final_score if result.final_score is not None else ""
                odds_diff = result.odds_advantage if result.odds_advantage is not None else ""
                volatility = result.volatility_std if result.volatility_std is not None else ""
                margin_bookmaker = result.bookmaker_margin if result.bookmaker_margin is not None else ""
                avg_odds = result.avg_market_odds if result.avg_market_odds else ""
                
                estado = "🔴 EN VIVO" if result.match.is_live else "⏰ Próximo"
                
                # Tipo de mercado legible
                tipo_mercado = {
                    MarketType.TOTALS: "Goles (Over/Under)",
                    MarketType.BTTS: "Ambos Marcan",
                    MarketType.H2H_Q1: "1X2 Primer Tiempo"
                }.get(result.market_type, result.market_type.value)
                
                # Formatear todas las cuotas
                all_odds_str = "; ".join([
                    f"{odds.bookmaker.value}:{odds.odds}"
                    for odds in sorted(result.all_odds, key=lambda x: x.odds, reverse=True)
                ])
                
                num_casas = len(result.all_odds)
                
                row = [
                    result.match.match_display,
                    result.match.commence_time_colombia,
                    estado,
                    tipo_mercado,
                    result.market_name,
                    result.best_odds,
                    result.bookmaker.value,
                    num_casas,
                    score_final,
                    odds_diff,
                    volatility,
                    margin_bookmaker,
                    avg_odds,
                    all_odds_str
                ]
                
                writer.writerow(row)
        
        return {"combined": str(filepath)}
    
    def print_summary(self, results_by_market: Dict[MarketType, List[MarketAnalysisResult]]):
        """Imprime un resumen de los resultados en consola"""
        
        market_titles = {
            MarketType.TOTALS: "TOTALS (Over/Under Goles)",
            MarketType.BTTS: "BTTS (Ambos Equipos Marcan)",
            MarketType.H2H_Q1: "H2H Primer Tiempo (1X2)"
        }
        
        print("\n" + "="*80)
        print("🏟️  ANÁLISIS DE MERCADOS DE APUESTAS")
        print("🔗 Fuente: The Odds API (datos 100% reales)")
        print("🕐 Zona horaria: Colombia (America/Bogota)")
        print("="*80)
        
        for market_type, results in results_by_market.items():
            if not results:
                continue
            
            unique_matches = len(set(r.match.id for r in results))
            
            print(f"\n📊 {market_titles.get(market_type, market_type.value)}:")
            print(f"  • Partidos analizados: {unique_matches}")
            print(f"  • Mercados encontrados: {len(results)}")
            
            print(f"\n🏆 TOP 5 OPORTUNIDADES (por Score_Final):")
            print("-" * 80)
            
            sorted_results = sorted(
                results,
                key=lambda x: x.final_score if x.final_score is not None else -999999,
                reverse=True
            )
            
            for i, result in enumerate(sorted_results[:5], 1):
                estado = "🔴 VIVO" if result.match.is_live else "⏰"
                volatility_str = f"{result.volatility_std}%" if result.volatility_std else "N/A"
                score_str = f"{result.final_score:.4f}" if result.final_score else "N/A"
                
                print(f"\n#{i} - {result.match.match_display} {estado}")
                print(f"    Mercado: {result.market_name}")
                print(f"    Cuota: {result.best_odds} ({result.bookmaker.value})")
                print(f"    Score_Final: {score_str}")
                print(f"    Volatilidad: {volatility_str}")
