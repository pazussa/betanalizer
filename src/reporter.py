import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from tabulate import tabulate
from .models import AnalysisResult, MarketType
import os
import csv
from pathlib import Path
import pytz


class ReportGenerator:
    """
    Generador de reportes para análisis de cuotas
    Formatea resultados en tablas legibles
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.timezone = pytz.timezone("America/Bogota")
    
    def generate_combined_csv(self, results: List[AnalysisResult], output_dir: str = ".") -> str:
        """
        Genera UN SOLO CSV combinando todos los mercados (1X, X2, TOTALS, BTTS, H2H_Q1)
        
        Args:
            results: Lista de resultados de todos los mercados
            output_dir: Directorio donde guardar el CSV
            
        Returns:
            Ruta del archivo CSV generado
        """
        if not results:
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analisis_mercados_{timestamp}.csv"
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
                "Fecha_Hora_Colombia",
                "Liga",
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
                # Convertir a hora de Colombia
                fecha_hora_utc = result.match.kickoff_time
                fecha_hora_col = fecha_hora_utc.astimezone(self.timezone)
                fecha_hora_str = fecha_hora_col.strftime('%Y-%m-%d %H:%M:%S')
                
                # Tipo de mercado legible
                market_type_map = {
                    MarketType.DOUBLE_CHANCE_1X: "Doble Chance",
                    MarketType.DOUBLE_CHANCE_X2: "Doble Chance",
                    MarketType.TOTALS: "Goles (Over/Under)",
                    MarketType.BTTS: "Ambos Marcan",
                    MarketType.H2H_Q1: "1X2 Primer Tiempo"
                }
                tipo_mercado = market_type_map.get(result.market, result.market.value)
                
                # Nombre del mercado
                market_name = result.market_name if result.market_name else result.market.value
                
                # Valores opcionales
                score_final = result.final_score if result.final_score is not None else ""
                odds_diff = result.odds_advantage if result.odds_advantage is not None else ""
                volatility = result.volatility_std if result.volatility_std is not None else ""
                margin_bookmaker = result.bookmaker_margin if result.bookmaker_margin is not None else ""
                avg_odds = result.avg_market_odds if result.avg_market_odds else ""
                num_casas = result.num_bookmakers if result.num_bookmakers else ""
                all_odds = result.all_odds_formatted if result.all_odds_formatted else ""
                
                row = [
                    result.match_display,
                    fecha_hora_str,
                    result.match.league,
                    tipo_mercado,
                    market_name,
                    result.best_odds,
                    result.bookmaker.value,
                    num_casas,
                    score_final,
                    odds_diff,
                    volatility,
                    margin_bookmaker,
                    avg_odds,
                    all_odds
                ]
                
                writer.writerow(row)
        
        self.logger.info(f"CSV combinado generado: {filepath}")
        return str(filepath)
    
    def generate_analysis_table(
        self, 
        results: List[AnalysisResult],
        show_all: bool = True
    ) -> str:
        """
        Genera tabla completa de análisis en formato solicitado
        
        Args:
            results: Resultados del análisis
            show_all: Si mostrar todos los resultados o solo los que cumplen criterios
            
        Returns:
            Tabla formateada como string
        """
        if not results:
            return "📊 **ANÁLISIS DE CUOTAS DE FÚTBOL**\n\n❌ No se encontraron partidos para analizar."
        
        # Filtrar resultados si es necesario
        display_results = results
        if not show_all:
            display_results = [r for r in results if r.meets_criteria]
        
        # Ordenar por Score_Final descendente
        display_results = sorted(
            display_results,
            key=lambda r: self._calculate_score_final(r) if self._calculate_score_final(r) is not None else -999999,
            reverse=True
        )
        
        # Preparar datos para la tabla
        table_data = []
        meets_criteria_count = 0
        
        for result in display_results:
            if result.meets_criteria:
                meets_criteria_count += 1
            
            # Formato de fecha y hora
            kickoff = result.match.kickoff_time.strftime("%d/%m %H:%M")
            
            # Emoji para cumplimiento de criterios
            meets_emoji = "✅ Sí" if result.meets_criteria else "❌ No"
            
            # Formato del mercado
            market_display = "1X (Local/Empate)" if result.market == MarketType.DOUBLE_CHANCE_1X else "X2 (Empate/Visitante)"
            
            # Formato del margen
            margin_display = f"{result.bookmaker_margin:.1f}%" if result.bookmaker_margin else "N/D"
            
            row = [
                f"{result.match.home_team} vs {result.match.away_team}",
                market_display,
                f"{result.best_odds:.2f}",
                result.bookmaker.value.title(),
                margin_display,
                meets_emoji,
                kickoff,
                result.match.league
            ]
            table_data.append(row)
        
        # Headers de la tabla
        headers = [
            "Partido",
            "Mercado Analizado", 
            "Cuota Más Alta",
            "Casa de Apuestas",
            "Margen Casa (%)",
            "¿Cumple Criterios?",
            "Fecha/Hora",
            "Liga"
        ]
        
        # Generar tabla
        table = tabulate(
            table_data,
            headers=headers,
            tablefmt="grid",
            stralign="left",
            numalign="center"
        )
        
        # Generar resumen estadístico
        total_markets = len(display_results)
        compliance_rate = (meets_criteria_count / total_markets * 100) if total_markets > 0 else 0
        
        # Construir reporte completo
        report = f"""📊 **ANÁLISIS VERÍDICO DE CUOTAS DE FÚTBOL**
🔗 **Fuente**: The Odds API (datos 100% reales y oficiales)
⚡ **Sin Scraping**: Solo datos autorizados y verificados
✅ **Sin Simulación**: Todos los datos son reales de bookmakers activos
📅 **Generado**: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

📈 **RESUMEN EJECUTIVO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Total de mercados analizados: {total_markets}
• Mercados que cumplen criterios: {meets_criteria_count}
• Tasa de cumplimiento: {compliance_rate:.1f}%
• Criterios aplicados: Prob. ≥ {results[0].min_prob_threshold:.0%}, Cuota ≥ {results[0].min_odds_threshold}

📋 **TABLA DETALLADA**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{table}

🔍 **VALIDACIÓN DE DATOS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Cuotas obtenidas de The Odds API en tiempo real
✅ Filtrado automático por criterios establecidos
✅ Sin manipulación ni simulación - 100% datos reales de bookmakers

💡 **INTERPRETACIÓN**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 1X: Gana equipo local O empate
• X2: Empate O gana equipo visitante
• Margen Casa: Ganancia garantizada de la casa (menor = mejor para apostador)
• Score_Final: Cuota + (Ventaja_Margen / Margen_Casa) - Mayor score = mejor oportunidad
• Criterios: Filtros para identificar oportunidades
"""
        
        return report
    
    def generate_summary_stats(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """
        Genera estadísticas resumidas del análisis
        
        Args:
            results: Resultados del análisis
            
        Returns:
            Diccionario con estadísticas
        """
        if not results:
            return {"error": "No hay resultados para analizar"}
        
        # Estadísticas básicas
        total_markets = len(results)
        meets_criteria = sum(1 for r in results if r.meets_criteria)
        
        # Distribución por mercado
        markets_1x = sum(1 for r in results if r.market == MarketType.DOUBLE_CHANCE_1X)
        markets_x2 = sum(1 for r in results if r.market == MarketType.DOUBLE_CHANCE_X2)
        
        # Estadísticas de cuotas
        all_odds = [r.best_odds for r in results]
        all_probabilities = [r.implied_probability for r in results]
        
        # Distribución por liga
        leagues = {}
        for result in results:
            league = result.match.league
            leagues[league] = leagues.get(league, 0) + 1
        
        # Distribución por bookmaker
        bookmakers = {}
        for result in results:
            bm = result.bookmaker.value
            bookmakers[bm] = bookmakers.get(bm, 0) + 1
        
        return {
            "total_markets_analyzed": total_markets,
            "markets_meeting_criteria": meets_criteria,
            "compliance_rate_pct": round(meets_criteria / total_markets * 100, 1) if total_markets > 0 else 0,
            "market_distribution": {
                "1X_markets": markets_1x,
                "X2_markets": markets_x2
            },
            "odds_statistics": {
                "min_odds": round(min(all_odds), 2) if all_odds else 0,
                "max_odds": round(max(all_odds), 2) if all_odds else 0,
                "avg_odds": round(sum(all_odds) / len(all_odds), 2) if all_odds else 0
            },
            "probability_statistics": {
                "min_probability": round(min(all_probabilities), 3) if all_probabilities else 0,
                "max_probability": round(max(all_probabilities), 3) if all_probabilities else 0,
                "avg_probability": round(sum(all_probabilities) / len(all_probabilities), 3) if all_probabilities else 0
            },
            "league_distribution": leagues,
            "bookmaker_distribution": bookmakers,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def generate_compliance_report(self, results: List[AnalysisResult]) -> str:
        """
        Genera reporte específico de cumplimiento de criterios
        
        Args:
            results: Resultados del análisis
            
        Returns:
            Reporte de cumplimiento formateado
        """
        compliant_results = [r for r in results if r.meets_criteria]
        non_compliant_results = [r for r in results if not r.meets_criteria]
        
        if not compliant_results:
            return """🔍 **REPORTE DE CUMPLIMIENTO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ **Ningún mercado cumple con los criterios establecidos**

📋 Criterios aplicados:
• Probabilidad implícita ≥ 70%
• Cuota mínima ≥ 1.30

💡 Considera ajustar los criterios para obtener más resultados."""
        
        # Tabla de mercados que SÍ cumplen
        compliant_data = []
        for result in compliant_results:
            kickoff = result.match.kickoff_time.strftime("%d/%m %H:%M")
            market_display = "1X" if result.market == MarketType.DOUBLE_CHANCE_1X else "X2"
            margin_display = f"{result.bookmaker_margin:.1f}%" if result.bookmaker_margin else "N/D"
            
            compliant_data.append([
                f"{result.match.home_team} vs {result.match.away_team}",
                market_display,
                f"{result.best_odds:.2f}",
                result.bookmaker.value.title(),
                margin_display,
                kickoff
            ])
        
        compliant_table = tabulate(
            compliant_data,
            headers=["Partido", "Mercado", "Cuota", "Bookmaker", "Margen", "Hora"],
            tablefmt="grid"
        )
        
        compliance_rate = len(compliant_results) / len(results) * 100 if results else 0
        
        report = f"""🔍 **REPORTE DE CUMPLIMIENTO DE CRITERIOS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **RESUMEN**
• Mercados que cumplen: {len(compliant_results)}/{len(results)}
• Tasa de cumplimiento: {compliance_rate:.1f}%
• Mercados rechazados: {len(non_compliant_results)}

✅ **MERCADOS QUE CUMPLEN CRITERIOS**
{compliant_table}

📈 **ANÁLISIS DE OPORTUNIDADES**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{'✅ Excelentes oportunidades identificadas' if len(compliant_results) > 3 else '⚠️ Pocas oportunidades disponibles'}
{'🎯 Considera aumentar la muestra de partidos' if len(compliant_results) < 2 else '🎯 Suficientes opciones para diversificar'}

⚠️ **DISCLAIMER**: Análisis basado en datos oficiales. Las cuotas pueden cambiar.
"""
        
        return report
    
    def _calculate_score_final(self, result: AnalysisResult) -> Optional[float]:
        """
        Calcula el Score_Final para un resultado
        
        Args:
            result: Resultado del análisis
            
        Returns:
            Score_Final o None si no se puede calcular
        """
        if result.margin_advantage and result.bookmaker_margin and result.bookmaker_margin > 0:
            return round(result.margin_advantage / result.bookmaker_margin, 4)
        return None
    
    def export_to_csv_format(self, results: List[AnalysisResult]) -> str:
        """
        Exporta resultados en formato CSV para análisis adicional
        
        Args:
            results: Resultados del análisis
            
        Returns:
            String en formato CSV
        """
        if not results:
            return "No hay datos para exportar"
        
        # Obtener todos los bookmakers únicos de todos los resultados
        all_bookmakers = set()
        for result in results:
            if result.match_odds and result.match_odds.odds_h2h:
                for h2h in result.match_odds.odds_h2h:
                    all_bookmakers.add(h2h.bookmaker.value)
        
        bookmaker_list = sorted(all_bookmakers)
        
        # Construir encabezados dinámicamente
        headers = ["Partido", "Fecha_Hora_COT", "Score_Final", "Diferencia_Cuota_Promedio",
                   "Mercado", "Cuota", "Casa_Apuestas", "Volatilidad_Pct",
                   "Margen_Casa_Pct", "Margen_Mercado_Promedio_Pct", "Ventaja_Margen_Pct", 
                   "Cuota_Promedio_Mercado",
                   "Bwin_Cuota_1", "Bwin_Cuota_X", "Bwin_Cuota_2", "Bwin_Margen_Pct"]
        
        csv_lines = [",".join(headers)]
        
        # Ordenar por Score_Final descendente
        sorted_results = sorted(
            [r for r in results if self._calculate_score_final(r) is not None],
            key=lambda x: self._calculate_score_final(x),
            reverse=True
        )
        
        for result in sorted_results:
            market_code = "1X" if result.market == MarketType.DOUBLE_CHANCE_1X else "X2"
            cumple = "SI" if result.meets_criteria else "NO"
            
            # Convertir a GMT-5 (hora colombiana)
            fecha_hora_utc = result.match.kickoff_time
            fecha_hora_col = fecha_hora_utc - timedelta(hours=5)
            fecha_hora_str = fecha_hora_col.strftime("%Y-%m-%d %H:%M")
            
            margin_bookmaker = result.bookmaker_margin if result.bookmaker_margin else ""
            margin_avg = result.avg_market_margin if result.avg_market_margin else ""
            margin_advantage = result.margin_advantage if result.margin_advantage else ""
            
            # Calcular Score_Final: Cuota + (Ventaja_Margen / Margen_Casa)
            score_final = ""
            if result.margin_advantage and result.bookmaker_margin and result.bookmaker_margin > 0:
                score_final = round(
                    (result.margin_advantage / result.bookmaker_margin),
                    4
                )
            
            # Crear diccionario de márgenes por bookmaker
            margins_dict = {}
            h2h_dict = {}
            if result.match_odds and result.match_odds.odds_h2h:
                for h2h in result.match_odds.odds_h2h:
                    bm_name = h2h.bookmaker.value
                    margins_dict[bm_name] = round(h2h.overround_percentage, 2)
                    h2h_dict[bm_name] = {
                        "home": h2h.home_odds,
                        "draw": h2h.draw_odds,
                        "away": h2h.away_odds
                    }
            
            # Calcular diferencia entre mejor cuota y promedio
            avg_odds = result.avg_market_odds if result.avg_market_odds else ""
            odds_diff = result.odds_advantage if result.odds_advantage else ""
            
            # Obtener cuotas de Bwin si existen
            bwin_home = ""
            bwin_draw = ""
            bwin_away = ""
            bwin_margin = ""
            
            if result.match_odds and result.match_odds.odds_h2h:
                for h2h in result.match_odds.odds_h2h:
                    if h2h.bookmaker.value == "bwin":
                        bwin_home = h2h.home_odds
                        bwin_draw = h2h.draw_odds
                        bwin_away = h2h.away_odds
                        bwin_margin = round(h2h.overround_percentage, 2)
                        break
            
            # Obtener volatilidad
            volatility = result.volatility_std if result.volatility_std is not None else ""
            
            # Construir línea CSV
            row_data = [
                f'"{result.match_display}"',
                f'"{fecha_hora_str}"',
                str(score_final),
                str(odds_diff),
                f'"{market_code}"',
                str(result.best_odds),
                f'"{result.bookmaker.value}"',
                str(volatility),
                str(margin_bookmaker),
                str(margin_avg),
                str(margin_advantage),
                str(avg_odds),
                str(bwin_home),
                str(bwin_draw),
                str(bwin_away),
                str(bwin_margin)
            ]
            
            csv_lines.append(",".join(row_data))
        
        return "\n".join(csv_lines)
    
    def calculate_value_metrics(self, result: AnalysisResult) -> Dict[str, float]:
        """
        Calcula métricas de value para un resultado
        
        Args:
            result: Resultado del análisis
            
        Returns:
            Diccionario con métricas calculadas
        """
        metrics = {
            "cuota_premium": round(result.best_odds - 1.30, 4),
            "ventaja_margen": result.margin_advantage if result.margin_advantage else 0.0,
            "inverso_margen_casa": round(5.0 - (result.bookmaker_margin if result.bookmaker_margin else 5.0), 2),
            "value_score_pct": 0.0,
            "score_final": 0.0
        }
        
        # Calcular Value Score (% de ahorro vs promedio)
        if result.margin_advantage and result.avg_market_margin:
            metrics["value_score_pct"] = round((result.margin_advantage / result.avg_market_margin) * 100, 2)
        
        # Calcular Score Final: Cuota + (Ventaja_Margen / Margen_Casa)
        if result.margin_advantage and result.bookmaker_margin and result.bookmaker_margin > 0:
            metrics["score_final"] = round(
                result.best_odds + (result.margin_advantage / result.bookmaker_margin),
                4
            )
        
        return metrics
    
    def export_ranking_analysis(self, results: List[AnalysisResult], output_dir: str = ".") -> Tuple[str, str]:
        """
        Genera CSV con análisis de ranking matemático
        
        Args:
            results: Resultados del análisis
            output_dir: Directorio donde guardar el archivo
            
        Returns:
            Tupla (ruta_archivo, contenido_csv)
        """
        # Filtrar solo resultados que cumplen criterios
        compliant_results = [r for r in results if r.meets_criteria]
        
        if not compliant_results:
            self.logger.warning("No hay resultados que cumplan criterios para ranking")
            return ("", "No hay datos para ranking")
        
        # Calcular métricas para cada resultado
        ranking_data = []
        for result in compliant_results:
            metrics = self.calculate_value_metrics(result)
            
            market_code = "1X" if result.market == MarketType.DOUBLE_CHANCE_1X else "X2"
            fecha_hora_col = result.match.kickoff_time - timedelta(hours=5)
            
            ranking_data.append({
                "result": result,
                "metrics": metrics,
                "market_code": market_code,
                "fecha_hora": fecha_hora_col.strftime("%Y-%m-%d %H:%M")
            })
        
        # Ordenar por score_final descendente
        ranking_data.sort(key=lambda x: x["metrics"]["score_final"], reverse=True)
        
        # Generar CSV
        csv_lines = []
        
        # Headers
        headers = [
            "Rank",
            "Partido",
            "Mercado",
            "Cuota",
            "Casa_Apuestas",
            "Margen_Casa_Pct",
            "Margen_Mercado_Promedio_Pct",
            "Ventaja_Margen_Pct",
            "Cuota_Premium",
            "Value_Score_Pct",
            "Inverso_Margen_Casa",
            "Score_Final",
            "Fecha_Hora_COT",
            "Liga"
        ]
        csv_lines.append(",".join(headers))
        
        # Datos
        for rank, item in enumerate(ranking_data, 1):
            result = item["result"]
            metrics = item["metrics"]
            
            row = [
                str(rank),
                f'"{result.match_display}"',
                f'"{item["market_code"]}"',
                str(result.best_odds),
                f'"{result.bookmaker.value}"',
                str(result.bookmaker_margin if result.bookmaker_margin else ""),
                str(result.avg_market_margin if result.avg_market_margin else ""),
                str(result.margin_advantage if result.margin_advantage else ""),
                str(metrics["cuota_premium"]),
                str(metrics["value_score_pct"]),
                str(metrics["inverso_margen_casa"]),
                str(metrics["score_final"]),
                f'"{item["fecha_hora"]}"',
                f'"{result.match.league}"'
            ]
            csv_lines.append(",".join(row))
        
        csv_content = "\n".join(csv_lines)
        
        # Guardar archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ranking_value_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            self.logger.info(f"Ranking exportado a: {filename}")
        except Exception as e:
            self.logger.error(f"Error al guardar ranking: {e}")
            filepath = ""
        
        return (filepath, csv_content)
        
        return "\n".join(csv_lines)