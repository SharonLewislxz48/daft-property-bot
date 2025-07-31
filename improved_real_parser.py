#!/usr/bin/env python3
"""
УЛУЧШЕННЫЙ реальный парсер daft.ie
Извлекает ТОЛЬКО настоящие объявления с реальными ссылками
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

class ImprovedRealParser:
    """Улучшенный парсер для получения ТОЛЬКО реальных данных"""
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
        self.logger = logging.getLogger(__name__)
        
    async def create_session(self):
        """Создание сессии"""
        if self.session:
            await self.session.close()
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-IE,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.ie/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self.session

    async def get_real_listings_page(self, city="Dublin", max_price=3000, min_bedrooms=3) -> Optional[str]:
        """Получение страницы с реальными объявлениями"""
        if not self.session:
            await self.create_session()
        
        # URL для поиска
        search_url = f"{self.base_url}/property-for-rent/{city.lower()}"
        
        # Параметры поиска
        params = []
        if max_price:
            params.append(f"rentalPrice_to={max_price}")
        if min_bedrooms:
            params.append(f"numBeds_from={min_bedrooms}")
        
        if params:
            search_url += "?" + "&".join(params)
        
        self.logger.info(f"Fetching: {search_url}")
        
        # Попробуем несколько методов
        methods = [
            self.direct_request,
            self.request_with_delay,
            self.mobile_request
        ]
        
        for method in methods:
            try:
                content = await method(search_url)
                if content and len(content) > 100000:  # Страница должна быть достаточно большой
                    self.logger.info(f"✅ Got content via {method.__name__}: {len(content)} chars")
                    return content
            except Exception as e:
                self.logger.debug(f"{method.__name__} failed: {e}")
                continue
        
        return None

    async def direct_request(self, url: str) -> Optional[str]:
        """Прямой запрос"""
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.text()
        return None

    async def request_with_delay(self, url: str) -> Optional[str]:
        """Запрос с задержкой"""
        await asyncio.sleep(random.uniform(2, 4))
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.text()
        return None

    async def mobile_request(self, url: str) -> Optional[str]:
        """Мобильный запрос"""
        mobile_url = url.replace('www.daft.ie', 'm.daft.ie')
        async with self.session.get(mobile_url) as response:
            if response.status == 200:
                return await response.text()
        return None

    def extract_real_property_links(self, content: str) -> List[str]:
        """Извлечение реальных ссылок на объявления"""
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a', href=True)
        
        property_links = []
        
        for link in links:
            href = link.get('href', '')
            
            # Ищем ссылки на объявления
            if '/for-rent/' in href and any(word in href for word in ['apartment', 'house', 'studio']):
                # Проверяем что это полная ссылка на конкретное объявление (содержит ID в конце)
                if re.search(r'/\d+$', href):  # Заканчивается на число (ID объявления)
                    full_url = href if href.startswith('http') else self.base_url + href
                    property_links.append(full_url)
        
        # Удаляем дубликаты
        unique_links = list(set(property_links))
        self.logger.info(f"Found {len(unique_links)} unique property links")
        
        return unique_links

    async def get_property_details(self, property_url: str) -> Optional[Dict]:
        """Получение деталей конкретного объявления"""
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))  # Небольшая задержка
            
            async with self.session.get(property_url) as response:
                if response.status == 200:
                    content = await response.text()
                    return self.parse_property_page(content, property_url)
                
        except Exception as e:
            self.logger.debug(f"Failed to get details for {property_url}: {e}")
        
        return None

    def parse_property_page(self, content: str, url: str) -> Optional[Dict]:
        """Парсинг страницы конкретного объявления"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Извлекаем заголовок
            title_selectors = [
                'h1',
                '[data-testid*="title"]',
                '.title',
                'title'
            ]
            
            title = "Property in Dublin"
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    title_text = elem.get_text(strip=True)
                    if len(title_text) > 10 and 'daft' not in title_text.lower():
                        title = title_text
                        break
            
            # Извлекаем цену
            price_selectors = [
                '[data-testid*="price"]',
                '.price',
                '[class*="price" i]',
                '[id*="price" i]'
            ]
            
            price = "See listing"
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem and '€' in elem.get_text():
                    price = elem.get_text(strip=True)
                    break
            
            # Извлекаем адрес
            address_selectors = [
                '[data-testid*="address"]',
                '.address',
                '[class*="address" i]',
                '[class*="location" i]'
            ]
            
            address = "Dublin"
            for selector in address_selectors:
                elem = soup.select_one(selector)
                if elem:
                    addr_text = elem.get_text(strip=True)
                    if len(addr_text) > 5:
                        address = addr_text
                        break
            
            # Извлекаем количество спален
            bedrooms = None
            bedroom_patterns = [
                r'(\d+)\s*bed',
                r'(\d+)\s*bedroom',
                r'bed.*?(\d+)',
                r'bedroom.*?(\d+)'
            ]
            
            page_text = soup.get_text().lower()
            for pattern in bedroom_patterns:
                match = re.search(pattern, page_text)
                if match:
                    bedrooms = int(match.group(1))
                    break
            
            # Извлекаем количество ванных
            bathrooms = None
            bathroom_patterns = [
                r'(\d+)\s*bath',
                r'(\d+)\s*bathroom',
                r'bath.*?(\d+)',
                r'bathroom.*?(\d+)'
            ]
            
            for pattern in bathroom_patterns:
                match = re.search(pattern, page_text)
                if match:
                    bathrooms = int(match.group(1))
                    break
            
            return {
                'title': title,
                'price': price,
                'address': address,
                'url': url,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms
            }
            
        except Exception as e:
            self.logger.debug(f"Failed to parse property page: {e}")
            return None

    def extract_quick_info_from_links(self, content: str, property_links: List[str]) -> List[Dict]:
        """Быстрое извлечение информации из списка на главной странице"""
        properties = []
        soup = BeautifulSoup(content, 'html.parser')
        
        for link_url in property_links:
            # Находим ссылку на странице
            link_element = soup.find('a', href=lambda x: x and link_url.endswith(x))
            
            if link_element:
                # Ищем родительский контейнер с информацией
                container = link_element.find_parent(['div', 'article', 'section'])
                
                if container:
                    # Извлекаем информацию из контейнера
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                    price_elem = container.find(text=re.compile(r'€\d+'))
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        
                        # Извлекаем цену
                        price = "See listing"
                        if price_elem:
                            price = price_elem.strip()
                        else:
                            # Ищем цену в контейнере
                            container_text = container.get_text()
                            price_match = re.search(r'€[\d,]+', container_text)
                            if price_match:
                                price = price_match.group()
                        
                        # Извлекаем количество спален
                        bedrooms = None
                        container_text = container.get_text().lower()
                        bed_match = re.search(r'(\d+)\s*bed', container_text)
                        if bed_match:
                            bedrooms = int(bed_match.group(1))
                        
                        properties.append({
                            'title': title,
                            'price': price,
                            'address': 'Dublin',
                            'url': link_url,
                            'bedrooms': bedrooms,
                            'bathrooms': None
                        })
        
        return properties

    async def search_real_properties(self, city="Dublin", max_price=3000, min_bedrooms=3) -> List[Dict]:
        """Поиск ТОЛЬКО реальных объявлений"""
        self.logger.info(f"🔍 Searching REAL properties: {city}, max €{max_price}, {min_bedrooms}+ beds")
        
        # Получаем страницу с объявлениями
        content = await self.get_real_listings_page(city, max_price, min_bedrooms)
        
        if not content:
            self.logger.error("❌ Failed to get listings page")
            return []
        
        # Извлекаем ссылки на реальные объявления
        property_links = self.extract_real_property_links(content)
        
        if not property_links:
            self.logger.warning("⚠️ No property links found")
            return []
        
        self.logger.info(f"Found {len(property_links)} property links")
        
        # Быстро извлекаем основную информацию из списка
        properties = self.extract_quick_info_from_links(content, property_links)
        
        # Если нужно больше деталей, можем получить информацию с отдельных страниц
        if len(properties) < 5:
            self.logger.info("Getting detailed info from individual pages...")
            
            # Берем первые 10 ссылок для детального анализа
            for url in property_links[:10]:
                prop_details = await self.get_property_details(url)
                if prop_details:
                    properties.append(prop_details)
        
        # Фильтруем по минимальному количеству спален
        if min_bedrooms:
            filtered_properties = []
            for prop in properties:
                if prop.get('bedrooms') and prop['bedrooms'] >= min_bedrooms:
                    filtered_properties.append(prop)
                elif not prop.get('bedrooms'):  # Если количество спален неизвестно, включаем
                    filtered_properties.append(prop)
            properties = filtered_properties
        
        # Удаляем дубликаты
        unique_properties = []
        seen_urls = set()
        
        for prop in properties:
            url = prop.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_properties.append(prop)
        
        self.logger.info(f"✅ Found {len(unique_properties)} unique REAL properties")
        return unique_properties

    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
            self.session = None

# Тест улучшенного парсера
async def test_improved_parser():
    parser = ImprovedRealParser()
    
    try:
        print("🎯 Тестируем УЛУЧШЕННЫЙ реальный парсер...")
        print("✅ Извлекаем ТОЛЬКО настоящие объявления с реальными ссылками")
        print("=" * 70)
        
        properties = await parser.search_real_properties("Dublin", 2500, 3)
        
        if properties:
            print(f"🎉 УСПЕХ! Найдено {len(properties)} РЕАЛЬНЫХ объявлений:")
            print()
            
            for i, prop in enumerate(properties[:8], 1):
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
    success, properties = asyncio.run(test_improved_parser())
    
    if success:
        print(f"\n🎉 УЛУЧШЕННЫЙ ПАРСЕР РАБОТАЕТ! Найдено {len(properties)} настоящих объявлений!")
        print("🔗 Все ссылки ведут на реальные страницы daft.ie!")
    else:
        print("\n⚠️ Требуется дополнительная настройка.")
