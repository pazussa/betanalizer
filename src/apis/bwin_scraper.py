import asyncio
import logging
from typing import Optional, Dict
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
import re


class BwinScraper:
    """
    Scraper para obtener cuotas de Bwin mediante búsqueda en Google
    
    ADVERTENCIA: Este método viola los TOS de Google y Bwin.
    Úsalo bajo tu propio riesgo.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.browser = None
        self.context = None
        self.page = None
        
    async def initialize(self):
        """Inicializa el navegador Playwright"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            self.page = await self.context.new_page()
            self.logger.info("Navegador Playwright inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando Playwright: {e}")
            raise
    
    async def search_bwin_odds(self, home_team: str, away_team: str) -> Optional[Dict[str, float]]:
        """
        Busca las cuotas de Bwin directamente en su sitio web
        
        Args:
            home_team: Nombre del equipo local
            away_team: Nombre del equipo visitante
            
        Returns:
            Dict con cuotas {'home': float, 'draw': float, 'away': float} o None si falla
        """
        if not self.page:
            await self.initialize()
        
        try:
            self.logger.info(f"Buscando cuotas de Bwin para: {home_team} vs {away_team}")
            
            # Navegar a Bwin con el popup de búsqueda
            bwin_url = "https://www.bwin.co/es/sports?popup=betfinder"
            await self.page.goto(bwin_url, wait_until='domcontentloaded', timeout=30000)
            
            # Esperar a que cargue la página
            await asyncio.sleep(3)
            
            # Buscar el cuadro de búsqueda (puede tener varios selectores posibles)
            search_selectors = [
                'input[placeholder*="Busca"]',
                'input[type="search"]',
                'input[class*="search"]',
                '.search-input',
                '#search-input'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = await self.page.wait_for_selector(selector, timeout=5000)
                    if search_box:
                        self.logger.info(f"Cuadro de búsqueda encontrado con selector: {selector}")
                        break
                except:
                    continue
            
            if not search_box:
                self.logger.error("No se encontró el cuadro de búsqueda")
                return None
            
            # Buscar por el equipo local primero
            await search_box.fill(home_team)
            await asyncio.sleep(2)
            
            # Buscar el elemento específico ds-list-item y hacer clic
            result_selectors = [
                'ds-list-item.ds-list-item-interactive',
                '.ds-list-item.ds-list-item-interactive',
                'ds-list-item[class*="interactive"]',
                '.ds-list-tile-title'
            ]
            
            clicked = False
            for selector in result_selectors:
                try:
                    # Esperar a que aparezcan resultados
                    await self.page.wait_for_selector(selector, timeout=3000)
                    # Hacer clic en el primer resultado
                    await self.page.click(selector)
                    clicked = True
                    self.logger.info(f"Clic en resultado con selector: {selector}")
                    break
                except:
                    continue
            
            if not clicked:
                self.logger.warning(f"No se encontraron resultados para {home_team}")
                return None
            
            # Esperar a que carguen las cuotas
            await asyncio.sleep(3)
            
            # Intentar extraer las cuotas del partido
            # Buscar elementos con las cuotas (formato común: 1 X 2)
            odds_selectors = [
                'button[class*="odd"]',
                'span[class*="odd"]',
                'div[class*="odd"]',
                '[data-odd-value]'
            ]
            
            odds_elements = []
            for selector in odds_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if len(elements) >= 3:
                        odds_elements = elements
                        self.logger.info(f"Cuotas encontradas con selector: {selector}")
                        break
                except:
                    continue
            
            if len(odds_elements) < 3:
                self.logger.warning("No se encontraron suficientes elementos de cuotas")
                return None
            
            # Extraer valores de cuotas
            home_odds = None
            draw_odds = None
            away_odds = None
            
            for i, elem in enumerate(odds_elements[:3]):
                try:
                    # Intentar obtener el valor de diferentes formas
                    text = await elem.inner_text()
                    odds_match = re.search(r'(\d+\.\d+)', text)
                    if odds_match:
                        value = float(odds_match.group(1))
                        if i == 0:
                            home_odds = value
                        elif i == 1:
                            draw_odds = value
                        elif i == 2:
                            away_odds = value
                except:
                    continue
            
            if home_odds and draw_odds and away_odds:
                self.logger.info(f"Cuotas encontradas: {home_odds} / {draw_odds} / {away_odds}")
                return {
                    'home': home_odds,
                    'draw': draw_odds,
                    'away': away_odds
                }
            
            self.logger.warning(f"No se pudieron extraer las cuotas para {home_team} vs {away_team}")
            return None
            
        except PlaywrightTimeout:
            self.logger.error(f"Timeout buscando cuotas para {home_team} vs {away_team}")
            return None
        except Exception as e:
            self.logger.error(f"Error scraping Bwin: {e}")
            return None
    
    async def close(self):
        """Cierra el navegador"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            self.logger.info("Navegador cerrado")
        except Exception as e:
            self.logger.error(f"Error cerrando navegador: {e}")
