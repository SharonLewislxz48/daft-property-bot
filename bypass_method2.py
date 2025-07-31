#!/usr/bin/env python3
"""
Обход блокировки - метод 2: Мобильная версия и API
"""
import asyncio
import aiohttp
import json
import random
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MobileDaftParser:
    """Парсер через мобильную версию и API endpoints"""
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.mobile_url = "https://m.daft.ie" 
        self.api_url = "https://gateway.daft.ie"
        self.session = None
    
    async def create_mobile_session(self):
        """Создание сессии под мобильное устройство"""
        if self.session:
            await self.session.close()
        
        # Мобильные User-Agent
        mobile_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Android 14; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        ]
        
        user_agent = random.choice(mobile_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            # Мобильные заголовки
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"' if 'Android' in user_agent else '"iOS"',
            'Viewport-Width': '375'
        }
        
        connector = aiohttp.TCPConnector(limit=5, ttl_dns_cache=300)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout,
            trust_env=True
        )
        
        logger.info(f"Mobile session created: {user_agent[:50]}...")
        return self.session
    
    async def try_mobile_site(self, search_params: Dict) -> Optional[str]:
        """Пробуем мобильную версию сайта"""
        try:
            session = await self.create_mobile_session()
            
            # Мобильный URL
            mobile_search_url = f"{self.mobile_url}/property-for-rent/dublin"
            if search_params:
                params = "&".join([f"{k}={v}" for k, v in search_params.items()])
                mobile_search_url += f"?{params}"
            
            logger.info(f"Trying mobile site: {mobile_search_url}")
            
            await asyncio.sleep(random.uniform(1, 3))
            
            async with session.get(mobile_search_url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"Mobile site response: {len(content)} chars")
                    
                    if 'property' in content.lower() and len(content) > 5000:
                        return content
                
                logger.warning(f"Mobile site returned: {response.status}")
                return None
                
        except Exception as e:
            logger.error(f"Mobile site error: {e}")
            return None
    
    async def try_api_endpoints(self, search_params: Dict) -> Optional[List[Dict]]:
        """Пробуем различные API endpoints"""
        session = await self.create_mobile_session()
        
        # Различные возможные API endpoints
        api_endpoints = [
            f"{self.api_url}/v1/listings",
            f"{self.api_url}/v2/search",
            f"{self.api_url}/search/properties",
            f"{self.base_url}/api/v1/search",
            f"{self.base_url}/api/properties",
            f"{self.base_url}/graphql"
        ]
        
        for endpoint in api_endpoints:
            try:
                logger.info(f"Trying API endpoint: {endpoint}")
                await asyncio.sleep(random.uniform(1, 2))
                
                # GET запрос
                params = {
                    'location': 'dublin',
                    'maxPrice': search_params.get('rentalPrice_to', 3000),
                    'minBeds': search_params.get('numBeds_from', 2),
                    'limit': 20
                }
                
                async with session.get(endpoint, params=params) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            logger.info(f"✅ API success: {endpoint}")
                            
                            if isinstance(data, dict):
                                # Ищем массивы с данными
                                for key in ['results', 'listings', 'properties', 'data']:
                                    if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                                        logger.info(f"Found {len(data[key])} items in {key}")
                                        return data[key]
                            elif isinstance(data, list) and len(data) > 0:
                                logger.info(f"Found {len(data)} items in direct array")
                                return data
                                
                        except json.JSONDecodeError:
                            logger.debug(f"Not JSON response from {endpoint}")
                    else:
                        logger.debug(f"API endpoint {endpoint}: {response.status}")
                
                # POST запрос для GraphQL
                if 'graphql' in endpoint:
                    query = {
                        "query": """
                        query SearchProperties($filters: SearchFilters!) {
                            search(filters: $filters) {
                                listings {
                                    id
                                    title
                                    price { displayValue }
                                    address
                                    seoPath
                                    bedrooms
                                    bathrooms
                                }
                            }
                        }
                        """,
                        "variables": {
                            "filters": {
                                "location": "dublin",
                                "maxPrice": search_params.get('rentalPrice_to', 3000),
                                "minBedrooms": search_params.get('numBeds_from', 2)
                            }
                        }
                    }
                    
                    async with session.post(endpoint, json=query) as response:
                        if response.status == 200:
                            try:
                                data = await response.json()
                                if 'data' in data and 'search' in data['data']:
                                    listings = data['data']['search'].get('listings', [])
                                    if listings:
                                        logger.info(f"✅ GraphQL success: {len(listings)} listings")
                                        return listings
                            except:
                                pass
                
            except Exception as e:
                logger.debug(f"API endpoint {endpoint} failed: {e}")
                continue
        
        return None
    
    async def try_rss_feeds(self) -> Optional[List[Dict]]:
        """Пробуем RSS ленты"""
        session = await self.create_mobile_session()
        
        rss_urls = [
            f"{self.base_url}/rss/rental/dublin.xml",
            f"{self.base_url}/feeds/rental.rss",
            f"{self.base_url}/rss/properties.xml"
        ]
        
        for rss_url in rss_urls:
            try:
                logger.info(f"Trying RSS: {rss_url}")
                await asyncio.sleep(random.uniform(1, 2))
                
                async with session.get(rss_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        if '<rss' in content or '<feed' in content:
                            logger.info(f"✅ RSS found: {rss_url}")
                            return self.parse_rss_content(content)
                            
            except Exception as e:
                logger.debug(f"RSS {rss_url} failed: {e}")
                continue
        
        return None
    
    def parse_rss_content(self, content: str) -> List[Dict]:
        """Парсинг RSS контента"""
        from xml.etree import ElementTree as ET
        properties = []
        
        try:
            root = ET.fromstring(content)
            
            # RSS 2.0 format
            items = root.findall('.//item')
            if not items:
                # Atom format
                items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            for item in items:
                prop = {}
                
                title = item.find('title') or item.find('.//{http://www.w3.org/2005/Atom}title')
                if title is not None:
                    prop['title'] = title.text
                
                link = item.find('link') or item.find('.//{http://www.w3.org/2005/Atom}link')
                if link is not None:
                    prop['url'] = link.text if link.text else link.get('href')
                
                description = item.find('description') or item.find('.//{http://www.w3.org/2005/Atom}summary')
                if description is not None:
                    prop['description'] = description.text
                
                if 'title' in prop and prop['title']:
                    prop['price'] = 'See listing'
                    prop['address'] = 'Dublin'
                    properties.append(prop)
            
            logger.info(f"Parsed {len(properties)} properties from RSS")
            
        except Exception as e:
            logger.error(f"RSS parsing error: {e}")
        
        return properties
    
    async def search_properties(self, city="Dublin", max_price=3000, min_bedrooms=2) -> List[Dict]:
        """Основной поиск через мобильные методы"""
        logger.info(f"🔍 Mobile/API search: {city}, max €{max_price}, {min_bedrooms}+ beds")
        
        search_params = {
            'rentalPrice_to': max_price,
            'numBeds_from': min_bedrooms
        }
        
        properties = []
        
        # Метод 1: API endpoints
        api_results = await self.try_api_endpoints(search_params)
        if api_results:
            properties.extend(self.normalize_api_results(api_results))
        
        # Метод 2: Мобильная версия
        if not properties:
            mobile_html = await self.try_mobile_site(search_params)
            if mobile_html:
                properties.extend(self.parse_mobile_html(mobile_html))
        
        # Метод 3: RSS ленты
        if not properties:
            rss_results = await self.try_rss_feeds()
            if rss_results:
                properties.extend(rss_results)
        
        logger.info(f"Total found: {len(properties)} properties")
        return properties
    
    def normalize_api_results(self, results: List[Dict]) -> List[Dict]:
        """Нормализация результатов API"""
        properties = []
        
        for item in results:
            prop = {
                'title': item.get('title') or item.get('displayAddress') or 'Property',
                'address': item.get('address') or item.get('displayAddress') or 'Dublin',
                'url': f"{self.base_url}{item.get('seoPath', '/property')}" if item.get('seoPath') else '',
                'bedrooms': item.get('bedrooms') or item.get('numBedrooms'),
                'bathrooms': item.get('bathrooms') or item.get('numBathrooms')
            }
            
            # Цена
            price = item.get('price')
            if isinstance(price, dict):
                prop['price'] = price.get('displayValue', 'Price on request')
            else:
                prop['price'] = str(price) if price else 'Price on request'
            
            properties.append(prop)
        
        return properties
    
    def parse_mobile_html(self, html: str) -> List[Dict]:
        """Парсинг мобильного HTML"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        properties = []
        
        # Мобильные селекторы
        selectors = [
            '.listing-item',
            '.property-item',
            '[data-testid*="mobile-property"]',
            '.search-result'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Mobile parsing: found {len(elements)} with {selector}")
                
                for elem in elements:
                    title_elem = elem.find(['h2', 'h3', '.title'])
                    if title_elem:
                        prop = {
                            'title': title_elem.get_text(strip=True),
                            'address': 'Dublin',
                            'price': 'See listing',
                            'url': f"{self.base_url}/property"
                        }
                        
                        link = elem.find('a', href=True)
                        if link:
                            prop['url'] = f"{self.base_url}{link['href']}" if link['href'].startswith('/') else link['href']
                        
                        properties.append(prop)
                
                if properties:
                    break
        
        return properties
    
    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()

# Тест мобильного парсера
async def test_mobile_parser():
    parser = MobileDaftParser()
    
    try:
        print("📱 Тестируем МОБИЛЬНЫЙ обход блокировки...")
        print("=" * 60)
        
        properties = await parser.search_properties("Dublin", 3000, 2)
        
        if properties:
            print(f"✅ УСПЕХ! Найдено {len(properties)} объявлений через мобильные методы:")
            print()
            
            for i, prop in enumerate(properties[:3], 1):
                print(f"   {i}. 🏠 {prop['title']}")
                print(f"      📍 {prop['address']}")
                print(f"      💰 {prop['price']}")
                if prop.get('bedrooms'):
                    print(f"      🛏️ {prop['bedrooms']} спален")
                print(f"      🔗 {prop['url'][:80]}...")
                print()
            
            return True
        else:
            print("❌ Мобильные методы не дали результатов")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await parser.close()

if __name__ == "__main__":
    success = asyncio.run(test_mobile_parser())
    
    if success:
        print("\n🎉 МЕТОД 2 УСПЕШЕН! Мобильный обход работает!")
    else:
        print("\n⚠️ Метод 2 не сработал, переходим к методу 3...")
