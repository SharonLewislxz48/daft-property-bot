#!/usr/bin/env python3
"""
Продвинутый обход блокировки - метод 1
"""
import asyncio
import aiohttp
import random
import json
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedDaftParser:
    """Продвинутый парсер с обходом блокировки"""
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
        
        # Множественные User-Agent
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0 Safari/537.36"
        ]
        
        # Рефереры для имитации навигации
        self.referrers = [
            "https://www.google.com/",
            "https://www.google.ie/",
            "https://www.bing.com/",
            "https://duckduckgo.com/",
            "https://www.daft.ie/",
            ""
        ]
        
    async def create_session(self):
        """Создание сессии с продвинутыми настройками"""
        if self.session:
            await self.session.close()
            
        # Случайный User-Agent
        user_agent = random.choice(self.user_agents)
        referrer = random.choice(self.referrers)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none' if not referrer else 'cross-site',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        if referrer:
            headers['Referer'] = referrer
            
        # Создаем cookie jar для сохранения куки
        cookie_jar = aiohttp.CookieJar()
        
        connector = aiohttp.TCPConnector(
            limit=5,
            limit_per_host=2,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=45, connect=15, sock_read=30)
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout,
            cookie_jar=cookie_jar,
            trust_env=True
        )
        
        logger.info(f"Created session with User-Agent: {user_agent[:50]}...")
        return self.session
    
    async def visit_homepage_first(self):
        """Сначала посещаем главную страницу для получения куки"""
        try:
            session = await self.create_session()
            logger.info("Visiting homepage first to get cookies...")
            
            await asyncio.sleep(random.uniform(1, 3))
            
            async with session.get(self.base_url) as response:
                if response.status == 200:
                    logger.info(f"Homepage visited successfully: {response.status}")
                    # Сохраняем куки
                    cookies = session.cookie_jar.filter_cookies(self.base_url)
                    logger.info(f"Received {len(cookies)} cookies")
                    return True
                else:
                    logger.warning(f"Homepage returned: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error visiting homepage: {e}")
            return False
    
    async def fetch_with_retries(self, url: str, max_retries: int = 5) -> Optional[str]:
        """Получение страницы с множественными попытками и стратегиями"""
        
        for attempt in range(max_retries):
            try:
                # Случайная задержка между попытками
                if attempt > 0:
                    delay = random.uniform(5, 15) * (attempt + 1)
                    logger.info(f"Attempt {attempt + 1}: waiting {delay:.1f}s before retry")
                    await asyncio.sleep(delay)
                
                # Пересоздаем сессию на каждые 2 попытки
                if attempt % 2 == 0:
                    await self.create_session()
                    if attempt == 0:  # Первая попытка - посещаем главную
                        await self.visit_homepage_first()
                        await asyncio.sleep(random.uniform(2, 5))
                
                session = self.session
                
                # Добавляем случайные задержки для имитации человека
                await asyncio.sleep(random.uniform(1, 4))
                
                logger.info(f"Attempt {attempt + 1}: Fetching {url}")
                
                async with session.get(url) as response:
                    logger.info(f"Response: {response.status} | Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        # Проверяем качество контента
                        if len(content) > 10000:  # Достаточно большая страница
                            if 'daft.ie' in content and ('property' in content.lower() or 'listing' in content.lower()):
                                logger.info(f"✅ Success! Content length: {len(content)}")
                                return content
                            else:
                                logger.warning("Content seems incomplete or redirected")
                        else:
                            logger.warning(f"Content too short: {len(content)} bytes")
                    
                    elif response.status == 403:
                        logger.warning(f"Forbidden (403) - trying different approach")
                        # Меняем стратегию - новый User-Agent и больше задержка
                        await self.create_session()
                        
                    elif response.status == 429:
                        logger.warning(f"Rate limited (429) - waiting longer")
                        await asyncio.sleep(random.uniform(30, 60))
                        
                    elif response.status in [301, 302, 307, 308]:
                        redirect_url = response.headers.get('Location')
                        logger.info(f"Redirect to: {redirect_url}")
                        
                    else:
                        logger.warning(f"Unexpected status: {response.status}")
                        
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
    
    async def parse_properties_from_html(self, html: str) -> List[Dict]:
        """Парсинг объявлений из HTML с множественными стратегиями"""
        soup = BeautifulSoup(html, 'html.parser')
        properties = []
        
        logger.info("Parsing HTML for property listings...")
        
        # Стратегия 1: Поиск JSON данных в скриптах
        scripts = soup.find_all('script')
        for script in scripts:
            script_content = script.string or ""
            
            # Ищем различные JSON структуры
            json_patterns = [
                r'"listings":\s*(\[.*?\])',
                r'"properties":\s*(\[.*?\])',
                r'"searchResults":\s*\{.*?"listings":\s*(\[.*?\])',
                r'__NEXT_DATA__\s*=\s*({.*?});',
                r'window\.__APP_STATE__\s*=\s*({.*?});'
            ]
            
            for pattern in json_patterns:
                import re
                matches = re.findall(pattern, script_content, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, list) and len(data) > 0:
                            logger.info(f"Found JSON data with {len(data)} items")
                            return self.parse_json_properties(data)
                        elif isinstance(data, dict):
                            # Рекурсивно ищем массивы с объявлениями
                            found_props = self.find_properties_in_json(data)
                            if found_props:
                                return found_props
                    except:
                        continue
        
        # Стратегия 2: HTML селекторы
        selectors = [
            'div[data-testid*="property"]',
            'div[data-testid*="listing"]',
            'article[data-testid*="property"]',
            '.SearchResult',
            '.PropertyCard',
            '.ListingCard',
            '[class*="property" i][class*="card" i]',
            'div[class*="result" i]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Found {len(elements)} elements with selector: {selector}")
                
                for element in elements:
                    prop = self.parse_html_property(element)
                    if prop:
                        properties.append(prop)
                
                if properties:
                    break
        
        logger.info(f"Parsed {len(properties)} properties from HTML")
        return properties
    
    def find_properties_in_json(self, data, path="") -> Optional[List[Dict]]:
        """Рекурсивный поиск объявлений в JSON"""
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                
                if key.lower() in ['listings', 'properties', 'results', 'data'] and isinstance(value, list):
                    if len(value) > 0 and isinstance(value[0], dict):
                        logger.info(f"Found properties array at: {new_path}")
                        return self.parse_json_properties(value)
                
                result = self.find_properties_in_json(value, new_path)
                if result:
                    return result
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                result = self.find_properties_in_json(item, f"{path}[{i}]")
                if result:
                    return result
        
        return None
    
    def parse_json_properties(self, data: List[Dict]) -> List[Dict]:
        """Парсинг объявлений из JSON массива"""
        properties = []
        
        for item in data:
            if not isinstance(item, dict):
                continue
                
            prop = {}
            
            # Извлекаем поля
            prop['title'] = (
                item.get('title') or 
                item.get('displayAddress') or 
                item.get('name') or 
                'Property'
            )
            
            # Цена
            price_field = item.get('price') or item.get('rent') or item.get('monthlyRent')
            if isinstance(price_field, dict):
                prop['price'] = price_field.get('displayValue') or price_field.get('amount', 'Price on request')
            else:
                prop['price'] = str(price_field) if price_field else 'Price on request'
            
            # Адрес
            prop['address'] = (
                item.get('address') or
                item.get('displayAddress') or 
                item.get('location', {}).get('displayValue') if isinstance(item.get('location'), dict) else item.get('location') or
                'Dublin'
            )
            
            # URL
            seo_path = item.get('seoPath') or item.get('path') or item.get('url')
            if seo_path:
                prop['url'] = f"{self.base_url}{seo_path}" if seo_path.startswith('/') else seo_path
            else:
                prop['url'] = f"{self.base_url}/property/listing"
            
            # Спальни и ванные
            prop['bedrooms'] = item.get('bedrooms') or item.get('numBedrooms') or item.get('beds')
            prop['bathrooms'] = item.get('bathrooms') or item.get('numBathrooms') or item.get('baths')
            
            if prop['title'] and len(prop['title']) > 5:  # Базовая валидация
                properties.append(prop)
        
        return properties
    
    def parse_html_property(self, element) -> Optional[Dict]:
        """Парсинг одного объявления из HTML элемента"""
        try:
            # Ссылка
            link = element.find('a', href=True)
            url = ""
            if link:
                url = link['href']
                if not url.startswith('http'):
                    url = self.base_url + url
            
            # Заголовок
            title_selectors = ['h1', 'h2', 'h3', 'h4', '[data-testid*="title"]', '.title', '[class*="title" i]']
            title = ""
            for sel in title_selectors:
                elem = element.select_one(sel)
                if elem:
                    title = elem.get_text(strip=True)
                    break
            
            # Цена
            price_selectors = ['[data-testid*="price"]', '.price', '[class*="price" i]']
            price = "Price on request"
            for sel in price_selectors:
                elem = element.select_one(sel)
                if elem and ('€' in elem.get_text() or 'euro' in elem.get_text().lower()):
                    price = elem.get_text(strip=True)
                    break
            
            # Адрес
            address_selectors = ['[data-testid*="address"]', '.address', '[class*="address" i]', '[class*="location" i]']
            address = "Dublin"
            for sel in address_selectors:
                elem = element.select_one(sel)
                if elem:
                    address = elem.get_text(strip=True)
                    break
            
            if title and len(title) > 5:
                return {
                    'title': title,
                    'price': price,
                    'address': address,
                    'url': url,
                    'bedrooms': None,
                    'bathrooms': None
                }
        except Exception as e:
            logger.debug(f"Error parsing HTML property: {e}")
        
        return None
    
    async def search_properties(self, city="Dublin", max_price=3000, min_bedrooms=2) -> List[Dict]:
        """Основной метод поиска с обходом блокировки"""
        
        logger.info(f"🔍 Advanced search: {city}, max €{max_price}, {min_bedrooms}+ beds")
        
        # Формируем URL
        search_url = f"{self.base_url}/property-for-rent/{city.lower()}"
        params = []
        
        if max_price:
            params.append(f"rentalPrice_to={max_price}")
        if min_bedrooms:
            params.append(f"numBeds_from={min_bedrooms}")
        
        if params:
            search_url += "?" + "&".join(params)
        
        # Получаем страницу
        html = await self.fetch_with_retries(search_url)
        if not html:
            return []
        
        # Парсим объявления
        properties = await self.parse_properties_from_html(html)
        
        logger.info(f"Found {len(properties)} properties")
        return properties
    
    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()

# Тест продвинутого парсера
async def test_advanced_parser():
    parser = AdvancedDaftParser()
    
    try:
        print("🚀 Тестируем ПРОДВИНУТЫЙ обход блокировки...")
        print("=" * 60)
        
        properties = await parser.search_properties("Dublin", 3000, 2)
        
        if properties:
            print(f"✅ УСПЕХ! Найдено {len(properties)} РЕАЛЬНЫХ объявлений:")
            print()
            
            for i, prop in enumerate(properties[:3], 1):
                print(f"   {i}. 🏠 {prop['title']}")
                print(f"      📍 {prop['address']}")
                print(f"      💰 {prop['price']}")
                if prop['bedrooms']:
                    print(f"      🛏️ {prop['bedrooms']} спален")
                print(f"      🔗 {prop['url'][:80]}...")
                print()
            
            return True
        else:
            print("❌ Объявления не найдены")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await parser.close()

if __name__ == "__main__":
    success = asyncio.run(test_advanced_parser())
    
    if success:
        print("\n🎉 МЕТОД 1 УСПЕШЕН! Обход блокировки работает!")
    else:
        print("\n⚠️ Метод 1 не сработал, переходим к методу 2...")
