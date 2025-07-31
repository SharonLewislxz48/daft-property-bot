#!/usr/bin/env python3
"""
JSON-парсер для извлечения реальных данных из __NEXT_DATA__
"""
import asyncio
import aiohttp
import json
import random
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealDaftParser:
    """Парсер реальных данных из JSON на странице Daft.ie"""
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
    
    async def get_session(self):
        """Создание сессии с настройками"""
        if not self.session:
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        
        return self.session
    
    async def fetch_page_data(self, url: str) -> Optional[Dict]:
        """Получение и парсинг JSON данных со страницы"""
        session = await self.get_session()
        
        # Случайная задержка
        delay = random.uniform(2.0, 4.0)
        logger.info(f"Fetching {url} with delay {delay:.1f}s")
        await asyncio.sleep(delay)
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} for {url}")
                    return None
                
                html = await response.text()
                logger.info(f"Received HTML: {len(html)} characters")
                
                # Парсим HTML и ищем __NEXT_DATA__
                soup = BeautifulSoup(html, 'html.parser')
                
                # Ищем скрипт с __NEXT_DATA__
                script_tag = soup.find('script', string=lambda text: text and '__NEXT_DATA__' in text)
                
                if not script_tag:
                    logger.error("__NEXT_DATA__ not found")
                    return None
                
                # Извлекаем JSON
                script_content = script_tag.string
                match = re.search(r'__NEXT_DATA__\s*=\s*({.*?});?\s*$', script_content, re.MULTILINE | re.DOTALL)
                
                if not match:
                    logger.error("Failed to extract JSON from __NEXT_DATA__")
                    return None
                
                json_str = match.group(1)
                data = json.loads(json_str)
                
                logger.info("Successfully parsed __NEXT_DATA__")
                return data
                
        except Exception as e:
            logger.error(f"Error fetching page data: {e}")
            return None
    
    def extract_properties_from_json(self, data: Dict) -> List[Dict]:
        """Извлечение списка объявлений из JSON данных"""
        properties = []
        
        try:
            # Ищем данные в различных возможных путях
            possible_paths = [
                ['props', 'pageProps', 'searchResults', 'listings'],
                ['props', 'pageProps', 'results', 'listings'],
                ['props', 'pageProps', 'listings'],
                ['props', 'pageProps', 'searchResults'],
                ['props', 'pageProps', 'results'],
                ['props', 'pageProps', 'data', 'listings']
            ]
            
            listings_data = None
            
            for path in possible_paths:
                current = data
                try:
                    for key in path:
                        current = current[key]
                    if isinstance(current, list) and len(current) > 0:
                        listings_data = current
                        logger.info(f"Found listings at path: {' -> '.join(path)}")
                        break
                except (KeyError, TypeError):
                    continue
            
            if not listings_data:
                # Поиск в любом месте JSON
                def find_listings_recursive(obj, path=""):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            new_path = f"{path}.{key}" if path else key
                            if key in ['listings', 'properties', 'results'] and isinstance(value, list):
                                if len(value) > 0 and isinstance(value[0], dict):
                                    logger.info(f"Found potential listings at: {new_path}")
                                    return value
                            result = find_listings_recursive(value, new_path)
                            if result:
                                return result
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            result = find_listings_recursive(item, f"{path}[{i}]")
                            if result:
                                return result
                    return None
                
                listings_data = find_listings_recursive(data)
            
            if not listings_data:
                logger.error("No listings found in JSON data")
                return []
            
            logger.info(f"Processing {len(listings_data)} listings")
            
            # Обрабатываем каждое объявление
            for item in listings_data:
                if not isinstance(item, dict):
                    continue
                
                try:
                    property_data = self.parse_property_item(item)
                    if property_data:
                        properties.append(property_data)
                except Exception as e:
                    logger.debug(f"Error parsing property item: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(properties)} properties")
            
        except Exception as e:
            logger.error(f"Error extracting properties: {e}")
        
        return properties
    
    def parse_property_item(self, item: Dict) -> Optional[Dict]:
        """Парсинг одного объявления из JSON"""
        try:
            # Извлекаем основные поля (возможные варианты названий)
            title = (
                item.get('title') or 
                item.get('name') or 
                item.get('displayAddress') or 
                item.get('description', '')[:100]
            )
            
            if not title:
                return None
            
            # Цена
            price = None
            price_fields = ['price', 'monthlyRent', 'rent', 'pricePerMonth']
            for field in price_fields:
                if field in item:
                    price_data = item[field]
                    if isinstance(price_data, dict):
                        price = price_data.get('displayValue') or price_data.get('amount')
                    else:
                        price = price_data
                    break
            
            # Адрес
            address = (
                item.get('address') or
                item.get('displayAddress') or
                item.get('location', {}).get('displayValue') or
                item.get('area', '')
            )
            
            # URL
            seo_path = item.get('seoPath') or item.get('path') or item.get('url', '')
            url = f"{self.base_url}{seo_path}" if seo_path.startswith('/') else seo_path
            
            # Спальни
            bedrooms = (
                item.get('bedrooms') or
                item.get('numBedrooms') or
                item.get('beds')
            )
            
            # Ванные
            bathrooms = (
                item.get('bathrooms') or
                item.get('numBathrooms') or
                item.get('baths')
            )
            
            # Описание
            description = (
                item.get('description') or
                item.get('summary') or
                f"Property in {address}"
            )
            
            return {
                'title': str(title),
                'price': str(price) if price else 'Price on request',
                'address': str(address),
                'url': url,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'description': str(description)[:300] if description else ''
            }
            
        except Exception as e:
            logger.debug(f"Error parsing property item: {e}")
            return None
    
    async def search_properties(self, city="Dublin", max_price=3000, min_bedrooms=2) -> List[Dict]:
        """Поиск объявлений"""
        logger.info(f"Searching real properties in {city}, max price: €{max_price}, min bedrooms: {min_bedrooms}")
        
        # Формируем URL поиска
        search_url = f"{self.base_url}/property-for-rent/{city.lower()}"
        params = []
        
        if max_price:
            params.append(f"rentalPrice_to={max_price}")
        if min_bedrooms:
            params.append(f"numBeds_from={min_bedrooms}")
        
        if params:
            search_url += "?" + "&".join(params)
        
        # Получаем данные первой страницы
        data = await self.fetch_page_data(search_url)
        if not data:
            logger.error("Failed to fetch page data")
            return []
        
        # Извлекаем объявления
        properties = self.extract_properties_from_json(data)
        
        return properties
    
    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()

# Тест реального парсера
async def test_real_json_parser():
    parser = RealDaftParser()
    
    try:
        print("🌐 Тестируем извлечение РЕАЛЬНЫХ данных из JSON...")
        print("=" * 60)
        
        properties = await parser.search_properties("Dublin", 3000, 2)
        
        if properties:
            print(f"✅ УСПЕХ! Извлечено {len(properties)} РЕАЛЬНЫХ объявлений:")
            print()
            
            for i, prop in enumerate(properties[:5], 1):
                print(f"   {i}. 🏠 {prop['title']}")
                print(f"      📍 {prop['address']}")
                print(f"      💰 {prop['price']}")
                print(f"      🛏️ {prop['bedrooms']} спален" if prop['bedrooms'] else "")
                print(f"      🔗 {prop['url'][:80]}...")
                print()
            
            return True
        else:
            print("❌ Объявления не найдены в JSON данных")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await parser.close()

if __name__ == "__main__":
    success = asyncio.run(test_real_json_parser())
    if success:
        print("\n🎉 JSON парсер работает! Получаем реальные данные с Daft.ie!")
    else:
        print("\n⚠️ JSON парсер не смог извлечь данные.")
