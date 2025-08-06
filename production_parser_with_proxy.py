#!/usr/bin/env python3
"""
Парсер с поддержкой бесплатных прокси для обхода блокировок
"""

import asyncio
import aiohttp
import re
import json
import logging
import random
from typing import List, Dict, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DaftParserWithProxy:
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
        self.free_proxies = [
            # Бесплатные HTTP прокси (обновляются автоматически)
            "http://proxy-list.download/api/v1/get?type=http",
            "http://free-proxy-list.net/",
            "http://www.proxy-list.download/HTTP",
        ]
        
        # Статические бесплатные прокси для тестирования
        self.test_proxies = [
            "http://103.149.162.194:80",
            "http://185.162.235.164:80", 
            "http://103.145.45.10:55443",
            "http://103.156.17.71:8080",
            "http://139.255.25.106:8080",
        ]

    async def get_free_proxies(self) -> List[str]:
        """Получаем список бесплатных прокси"""
        proxies = []
        
        # Добавляем тестовые прокси
        proxies.extend(self.test_proxies)
        
        try:
            # Пытаемся получить свежие прокси из API
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
                    timeout=10
                ) as response:
                    if response.status == 200:
                        proxy_text = await response.text()
                        for line in proxy_text.strip().split('\n'):
                            if ':' in line:
                                proxies.append(f"http://{line.strip()}")
        except Exception as e:
            logger.warning(f"Не удалось получить свежие прокси: {e}")
        
        return proxies[:20]  # Ограничиваем до 20 прокси

    async def test_proxy(self, proxy_url: str) -> bool:
        """Тестируем работоспособность прокси"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.get(
                    "https://httpbin.org/ip",
                    proxy=proxy_url,
                    headers=self._get_headers()
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Прокси {proxy_url} работает. IP: {result.get('origin')}")
                        return True
        except Exception as e:
            logger.debug(f"Прокси {proxy_url} не работает: {e}")
        
        return False

    async def test_daft_access(self, proxy_url: Optional[str] = None) -> bool:
        """Тестируем доступ к daft.ie через прокси"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=15)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                kwargs = {
                    "headers": self._get_headers(),
                    "allow_redirects": True
                }
                
                if proxy_url:
                    kwargs["proxy"] = proxy_url
                
                async with session.get(f"{self.base_url}/", **kwargs) as response:
                    logger.info(f"Тест daft.ie {'с прокси ' + proxy_url if proxy_url else 'без прокси'}: {response.status}")
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Ошибка доступа к daft.ie: {e}")
        
        return False

    def _get_headers(self):
        """Генерируем реалистичные заголовки"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        ]
        
        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }

    async def search_properties(self, bedrooms: int = 2, max_price: int = 2500, location: str = "dublin-city") -> List[Dict]:
        """Поиск недвижимости с использованием прокси при необходимости"""
        
        # Сначала пробуем без прокси
        logger.info("Пробуем доступ к daft.ie без прокси...")
        if await self.test_daft_access():
            logger.info("✅ Доступ без прокси работает!")
            return await self._search_with_proxy(None, bedrooms, max_price, location)
        
        # Если прямой доступ заблокирован, пробуем прокси
        logger.info("❌ Прямой доступ заблокирован. Ищем рабочие прокси...")
        
        proxies = await self.get_free_proxies()
        logger.info(f"Найдено {len(proxies)} прокси для тестирования")
        
        for i, proxy in enumerate(proxies, 1):
            logger.info(f"Тестируем прокси {i}/{len(proxies)}: {proxy}")
            
            # Тестируем прокси
            if not await self.test_proxy(proxy):
                continue
            
            # Тестируем доступ к daft.ie через этот прокси
            if await self.test_daft_access(proxy):
                logger.info(f"✅ Рабочий прокси найден: {proxy}")
                return await self._search_with_proxy(proxy, bedrooms, max_price, location)
        
        logger.error("❌ Ни один прокси не работает")
        return []

    async def _search_with_proxy(self, proxy_url: Optional[str], bedrooms: int, max_price: int, location: str) -> List[Dict]:
        """Выполняем поиск с указанным прокси (или без него)"""
        search_url = f"{self.base_url}/property-for-rent/{location}?numBeds={bedrooms}&maxPrice={max_price}"
        
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                kwargs = {
                    "headers": self._get_headers(),
                    "allow_redirects": True
                }
                
                if proxy_url:
                    kwargs["proxy"] = proxy_url
                
                logger.info(f"Запрос к: {search_url}")
                async with session.get(search_url, **kwargs) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка HTTP: {response.status}")
                        return []
                    
                    html = await response.text()
                    return self._extract_properties_from_html(html)
                    
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []

    def _extract_properties_from_html(self, html: str) -> List[Dict]:
        """Извлекаем данные о недвижимости из HTML"""
        properties = []
        
        try:
            # Пытаемся найти JSON данные в скрипте
            json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group(1))
                properties = self._extract_from_json(json_data)
                
            if properties:
                logger.info(f"✅ Найдено {len(properties)} объектов через JSON")
                return properties
            
            # Если JSON не найден, пробуем парсить HTML
            logger.info("JSON не найден, пробуем HTML парсинг...")
            properties = self._extract_from_html_regex(html)
            
        except Exception as e:
            logger.error(f"Ошибка извлечения данных: {e}")
        
        return properties

    def _extract_from_json(self, json_data: dict) -> List[Dict]:
        """Извлекаем данные из JSON структуры"""
        properties = []
        
        try:
            # Ищем данные о недвижимости в JSON
            props_data = json_data.get('props', {}).get('pageProps', {})
            
            # Разные возможные пути к данным
            listings = (
                props_data.get('listings', []) or
                props_data.get('searchResults', {}).get('listings', []) or
                props_data.get('properties', [])
            )
            
            for item in listings:
                prop = {
                    'title': item.get('title', 'Без названия'),
                    'price': item.get('price', 'Цена не указана'),
                    'location': item.get('location', 'Местоположение не указано'),
                    'bedrooms': item.get('bedrooms', 'Не указано'),
                    'url': f"https://www.daft.ie{item.get('seoPath', '')}" if item.get('seoPath') else None
                }
                properties.append(prop)
                
        except Exception as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
        
        return properties

    def _extract_from_html_regex(self, html: str) -> List[Dict]:
        """Резервный метод извлечения через регулярные выражения"""
        properties = []
        
        # Здесь можно добавить HTML парсинг как fallback
        logger.info("HTML парсинг пока не реализован")
        
        return properties

async def main():
    """Тестирование парсера с прокси"""
    parser = DaftParserWithProxy()
    
    print("🔍 Тестируем парсер с поддержкой прокси...")
    
    # Тестируем поиск
    properties = await parser.search_properties(
        bedrooms=2,
        max_price=2500,
        location="dublin-city"
    )
    
    if properties:
        print(f"\n✅ Найдено {len(properties)} объектов:")
        for i, prop in enumerate(properties[:5], 1):
            print(f"\n{i}. {prop['title']}")
            print(f"   Цена: {prop['price']}")
            print(f"   Местоположение: {prop['location']}")
            print(f"   Спальни: {prop['bedrooms']}")
            if prop['url']:
                print(f"   URL: {prop['url']}")
    else:
        print("❌ Объекты не найдены")

if __name__ == "__main__":
    asyncio.run(main())
