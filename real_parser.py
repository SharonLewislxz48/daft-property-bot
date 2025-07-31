#!/usr/bin/env python3
"""
РЕАЛЬНЫЙ парсер daft.ie - ТОЛЬКО настоящие данные
Убраны все фальшивые и демо данные
"""
import asyncio
import aiohttp
import json
import random
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class RealDaftParser:
    """Парсер для получения ТОЛЬКО реальных данных с daft.ie"""
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
        self.logger = logging.getLogger(__name__)
        
    async def create_session(self):
        """Создание сессии с обходом блокировки"""
        if self.session:
            await self.session.close()
            
        # Заголовки для обхода блокировки
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-IE,en;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.ie/'
        }
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
            trust_env=True
        )
        return self.session

    async def get_real_content(self, url: str) -> Optional[str]:
        """Получение реального контента с обходом блокировки"""
        methods = [
            self.try_direct_request,
            self.try_with_cookies,
            self.try_mobile_version,
            self.try_cached_version
        ]
        
        for method in methods:
            try:
                content = await method(url)
                if content and len(content) > 10000:
                    self.logger.info(f"✅ Got real content via {method.__name__}")
                    return content
            except Exception as e:
                self.logger.debug(f"{method.__name__} failed: {e}")
                continue
        
        return None

    async def try_direct_request(self, url: str) -> Optional[str]:
        """Прямой запрос"""
        await asyncio.sleep(random.uniform(1, 3))
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.text()
        return None

    async def try_with_cookies(self, url: str) -> Optional[str]:
        """Запрос с предварительным получением cookies"""
        # Сначала заходим на главную страницу
        await asyncio.sleep(random.uniform(1, 2))
        async with self.session.get(self.base_url) as response:
            if response.status == 200:
                # Теперь делаем запрос к нужной странице
                await asyncio.sleep(random.uniform(1, 2))
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
        return None

    async def try_mobile_version(self, url: str) -> Optional[str]:
        """Мобильная версия"""
        mobile_url = url.replace('www.daft.ie', 'm.daft.ie')
        await asyncio.sleep(random.uniform(1, 2))
        async with self.session.get(mobile_url) as response:
            if response.status == 200:
                return await response.text()
        return None

    async def try_cached_version(self, url: str) -> Optional[str]:
        """Кэшированная версия"""
        cached_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
        await asyncio.sleep(random.uniform(1, 2))
        async with self.session.get(cached_url) as response:
            if response.status == 200:
                return await response.text()
        return None

    def extract_real_properties(self, content: str) -> List[Dict]:
        """Извлечение ТОЛЬКО реальных объявлений из контента"""
        properties = []
        soup = BeautifulSoup(content, 'html.parser')
        
        # Поиск JSON данных в скриптах (основной источник данных daft.ie)
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                data = json.loads(script.string or "{}")
                if isinstance(data, dict) and 'props' in data:
                    # Daft.ie использует структуру с props
                    props_data = data.get('props', {})
                    if 'pageProps' in props_data:
                        page_props = props_data['pageProps']
                        if 'listings' in page_props:
                            listings = page_props['listings']
                            for listing in listings:
                                prop = self.parse_real_listing(listing)
                                if prop:
                                    properties.append(prop)
            except json.JSONDecodeError:
                continue
        
        # Поиск в обычных script тегах
        scripts = soup.find_all('script')
        for script in scripts:
            script_content = script.string or ""
            if 'window.__NEXT_DATA__' in script_content:
                # Извлекаем JSON из Next.js данных
                json_match = re.search(r'window\.__NEXT_DATA__\s*=\s*({.+?});', script_content)
                if json_match:
                    try:
                        next_data = json.loads(json_match.group(1))
                        listings = self.extract_listings_from_next_data(next_data)
                        for listing in listings:
                            prop = self.parse_real_listing(listing)
                            if prop:
                                properties.append(prop)
                    except json.JSONDecodeError:
                        continue
        
        # Поиск ссылок на реальные объявления в HTML
        property_links = soup.find_all('a', href=True)
        for link in property_links:
            href = link.get('href', '')
            if '/for-rent/' in href and any(word in href for word in ['apartment', 'house', 'studio']):
                # Это ссылка на реальное объявление
                full_url = href if href.startswith('http') else self.base_url + href
                
                # Извлекаем информацию из контекста ссылки
                parent = link.find_parent()
                if parent:
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4'])
                    price_elem = parent.find(class_=re.compile(r'price', re.I))
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        price = price_elem.get_text(strip=True) if price_elem else "See listing"
                        
                        if len(title) > 10 and 'cookie' not in title.lower():
                            properties.append({
                                'title': title,
                                'price': price,
                                'address': 'Dublin',
                                'url': full_url,
                                'bedrooms': None,
                                'bathrooms': None
                            })
        
        # Удаляем дубликаты по URL
        unique_properties = []
        seen_urls = set()
        
        for prop in properties:
            url = prop.get('url', '')
            if url and url not in seen_urls and self.is_valid_real_property(prop):
                seen_urls.add(url)
                unique_properties.append(prop)
        
        return unique_properties

    def extract_listings_from_next_data(self, next_data: dict) -> List[dict]:
        """Извлечение объявлений из Next.js данных"""
        listings = []
        
        def recursive_search(obj, key='listings'):
            """Рекурсивный поиск объявлений"""
            if isinstance(obj, dict):
                if key in obj and isinstance(obj[key], list):
                    return obj[key]
                for value in obj.values():
                    result = recursive_search(value, key)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = recursive_search(item, key)
                    if result:
                        return result
            return None
        
        # Поиск объявлений
        found_listings = recursive_search(next_data)
        if found_listings:
            listings.extend(found_listings)
        
        # Альтернативные поиски
        for key in ['properties', 'results', 'items', 'data']:
            found = recursive_search(next_data, key)
            if found:
                listings.extend(found)
        
        return listings

    def parse_real_listing(self, listing: dict) -> Optional[Dict]:
        """Парсинг реального объявления"""
        try:
            # Извлекаем основную информацию
            title = listing.get('title') or listing.get('name') or listing.get('displayAddress')
            if not title or len(title) < 5:
                return None
            
            # Цена
            price_obj = listing.get('price') or listing.get('pricePerMonth') or listing.get('monthlyRent')
            if isinstance(price_obj, dict):
                price = f"€{price_obj.get('amount', 0):,}/month"
            else:
                price = str(price_obj) if price_obj else "See listing"
            
            # Адрес
            address = (listing.get('displayAddress') or 
                      listing.get('address') or 
                      listing.get('location') or 
                      'Dublin')
            
            # URL
            url = listing.get('seoUrl') or listing.get('url') or listing.get('link')
            if url and not url.startswith('http'):
                url = self.base_url + url
            
            # Спальни и ванные
            bedrooms = listing.get('numBedrooms') or listing.get('bedrooms')
            bathrooms = listing.get('numBathrooms') or listing.get('bathrooms')
            
            return {
                'title': title,
                'price': price,
                'address': address,
                'url': url or self.base_url,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms
            }
            
        except Exception as e:
            self.logger.debug(f"Failed to parse listing: {e}")
            return None

    def is_valid_real_property(self, prop: dict) -> bool:
        """Проверка что это реальное объявление"""
        title = prop.get('title', '')
        url = prop.get('url', '')
        
        # Исключаем фальшивые данные
        invalid_keywords = [
            'demo', 'test', 'example', 'sample', 'fake',
            'generated', 'template', 'placeholder'
        ]
        
        title_lower = title.lower()
        url_lower = url.lower()
        
        for keyword in invalid_keywords:
            if keyword in title_lower or keyword in url_lower:
                return False
        
        # Проверяем что URL выглядит как реальная ссылка daft.ie
        if '/for-rent/' not in url_lower:
            return False
            
        return len(title) > 10

    async def search_real_properties(self, city="Dublin", max_price=3000, min_bedrooms=2) -> List[Dict]:
        """Поиск ТОЛЬКО реальных объявлений"""
        self.logger.info(f"🔍 Searching REAL properties: {city}, max €{max_price}, {min_bedrooms}+ beds")
        
        if not self.session:
            await self.create_session()
        
        # Формируем URL для поиска
        search_url = f"{self.base_url}/property-for-rent/{city.lower()}"
        
        search_params = []
        if max_price:
            search_params.append(f"rentalPrice_to={max_price}")
        if min_bedrooms:
            search_params.append(f"numBeds_from={min_bedrooms}")
        
        if search_params:
            search_url += "?" + "&".join(search_params)
        
        self.logger.info(f"Search URL: {search_url}")
        
        # Получаем реальный контент
        content = await self.get_real_content(search_url)
        
        if not content:
            self.logger.error("❌ Failed to get any real content from daft.ie")
            return []
        
        # Извлекаем только реальные объявления
        properties = self.extract_real_properties(content)
        
        if not properties:
            self.logger.warning("⚠️ No real properties found in content")
            return []
        
        self.logger.info(f"✅ Found {len(properties)} REAL properties")
        return properties

    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
            self.session = None

# Тест реального парсера
async def test_real_parser():
    parser = RealDaftParser()
    
    try:
        print("🔍 Тестируем РЕАЛЬНЫЙ парсер daft.ie...")
        print("🚫 БЕЗ фальшивых данных, БЕЗ демо, ТОЛЬКО реальные объявления!")
        print("=" * 70)
        
        properties = await parser.search_real_properties("Dublin", 2500, 3)
        
        if properties:
            print(f"✅ УСПЕХ! Найдено {len(properties)} РЕАЛЬНЫХ объявлений:")
            print()
            
            for i, prop in enumerate(properties[:5], 1):
                print(f"   {i}. 🏠 {prop['title']}")
                print(f"      💰 {prop['price']}")
                print(f"      📍 {prop['address']}")
                if prop.get('bedrooms'):
                    print(f"      🛏️ {prop['bedrooms']} спален")
                print(f"      🔗 {prop['url']}")
                print()
            
            return True, properties
        else:
            print("❌ РЕАЛЬНЫЕ объявления не найдены")
            print("🔍 Возможно нужно попробовать другие методы обхода")
            return False, []
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False, []
    finally:
        await parser.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success, properties = asyncio.run(test_real_parser())
    
    if success:
        print(f"\n🎉 РЕАЛЬНЫЙ ПАРСЕР РАБОТАЕТ! Найдено {len(properties)} настоящих объявлений!")
    else:
        print("\n⚠️ Нужно улучшить методы обхода блокировки.")
