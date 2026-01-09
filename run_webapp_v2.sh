#!/bin/bash
# Script para iniciar la webapp v2 con las 3 APIs

echo "🚀 Iniciando Webapp de Análisis Triple-API..."
echo ""
echo "📡 APIs integradas:"
echo "   • THE ODDS API: ~58 bookmakers"
echo "   • API-FOOTBALL: ~34 bookmakers"  
echo "   • SPORTS GAME ODDS: ~80+ bookmakers"
echo ""
echo "🌐 La webapp se abrirá en tu navegador"
echo "   URL: http://localhost:8501"
echo ""
echo "⏹️  Para detener: Ctrl+C"
echo ""

cd webapp
streamlit run app_v2.py
