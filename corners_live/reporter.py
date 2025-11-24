"""
Generador de reportes CSV para análisis de corners
"""
import csv
from datetime import datetime
from typing import List
from pathlib import Path
import pytz

from models import CornersAnalysisResult


class CornersReporter:
    """Generador de reportes para análisis de corners"""
    
    def __init__(self, timezone: str = "America/Bogota"):
        self.timezone = pytz.timezone(timezone)
    
    def generate_csv(self, results: List[CornersAnalysisResult], output_dir: str = ".") -> str:
        """
        Genera un CSV con los resultados del análisis
        
        Returns:
            Ruta del archivo generado
        """
        if not results:
            raise ValueError("No hay resultados para exportar")
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"corners_live_{timestamp}.csv"
        filepath = Path(output_dir) / filename
        
        # Ordenar por Score_Final descendente
        sorted_results = sorted(
            results,
            key=lambda x: x.final_score if x.final_score is not None else -999999,
            reverse=True
        )
        
        # Escribir CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Headers
            headers = [
                "Partido",
                "Estado",
                "Score_Final",
                "Diferencia_Cuota_Promedio",
                "Mercado",
                "Mejor_Cuota",
                "Mejor_Casa",
                "Num_Casas",  # Cantidad de casas que ofrecen el mercado
                "Volatilidad_Pct",
                "Margen_Casa_Pct",
                "Cuota_Promedio_Mercado",
                "Todas_Las_Cuotas"
            ]
            writer.writerow(headers)
            
            # Rows
            for result in sorted_results:
                # Calcular valores
                score_final = result.final_score if result.final_score is not None else ""
                odds_diff = result.odds_advantage if result.odds_advantage is not None else ""
                volatility = result.volatility_std if result.volatility_std is not None else ""
                margin_bookmaker = result.bookmaker_margin if result.bookmaker_margin is not None else ""
                avg_odds = result.avg_market_odds if result.avg_market_odds else ""
                
                # Estado del partido
                estado = "🔴 EN VIVO" if result.match.is_live else "⏰ Próximo"
                
                # Formatear todas las cuotas: "casa1:cuota1; casa2:cuota2; ..."
                all_odds_str = "; ".join([
                    f"{odds.bookmaker.value}:{odds.odds}"
                    for odds in sorted(result.all_odds, key=lambda x: x.odds, reverse=True)
                ])
                
                # Contar número de casas
                num_casas = len(result.all_odds)
                
                row = [
                    result.match.match_display,
                    estado,
                    score_final,
                    odds_diff,
                    result.market,
                    result.best_odds,
                    result.bookmaker.value,
                    num_casas,  # Cantidad de casas
                    volatility,
                    margin_bookmaker,
                    avg_odds,
                    all_odds_str  # Todas las cuotas formateadas
                ]
                
                writer.writerow(row)
        
        return str(filepath)
    
    def print_summary(self, results: List[CornersAnalysisResult]):
        """
        Imprime un resumen de los resultados en consola
        """
        if not results:
            print("\n❌ No se encontraron partidos en vivo con mercados de corners")
            return
        
        # Contar partidos únicos
        unique_matches = len(set(r.match.id for r in results))
        
        # Ordenar por Score_Final
        sorted_results = sorted(
            results,
            key=lambda x: x.final_score if x.final_score is not None else -999999,
            reverse=True
        )
        
        print("\n" + "="*80)
        print("🏟️  ANÁLISIS DE CORNERS EN VIVO")
        print("🔗 Fuente: The Odds API (datos 100% reales)")
        print("="*80)
        
        print(f"\n📊 RESUMEN:")
        print(f"  • Partidos en vivo analizados: {unique_matches}")
        print(f"  • Mercados de corners encontrados: {len(results)}")
        
        print(f"\n🏆 TOP 10 OPORTUNIDADES (por Score_Final):")
        print("-" * 80)
        
        for i, result in enumerate(sorted_results[:10], 1):
            estado = "🔴 VIVO" if result.match.is_live else "⏰"
            score = f"{result.final_score:.4f}" if result.final_score is not None else "N/A"
            
            print(f"\n#{i} - {result.match.match_display} {estado}")
            print(f"    Mercado: {result.market}")
            print(f"    Cuota: {result.best_odds} ({result.bookmaker.value})")
            print(f"    Score_Final: {score}")
            print(f"    Volatilidad: {result.volatility_std}%" if result.volatility_std else "    Volatilidad: N/A")
        
        print("\n" + "="*80)
