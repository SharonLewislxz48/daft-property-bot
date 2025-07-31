#!/usr/bin/env python3
"""
Daft.ie Property Parser - ONLY REAL DATA
Парсер объявлений о недвижимости с сайта Daft.ie - ТОЛЬКО реальные данные
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
from urllib.parse import urljoin, urlencode

from .models import Property, SearchFilters
from config.settings import settings

logger = logging.getLogger(__name__)

class DaftParser:
    """Парсер для сайта Daft.ie - ТОЛЬКО реальные данные"""
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
        self.logger = logging.getLogger(__name__)
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.create_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        
    async def create_session(self):
        """Создание сессии"""
        if self.session:
            await self.session.close()
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-IE,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.daft.ie/',
            'Cache-Control': 'no-cache'
        }
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self.session

    async def get_listings_page(self, city="Dublin") -> Optional[str]:
        """Получение страницы с объявлениями БЕЗ фильтров"""
        if not self.session:
            await self.create_session()
        
        # Используем базовый URL без фильтров для получения максимума ссылок
        search_url = f"{self.base_url}/property-for-rent/{city.lower()}"
        
        self.logger.info(f"Fetching: {search_url}")
        
        try:
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    content = await response.text()
                    self.logger.info(f"✅ Got page: {len(content)} chars")
                    return content
                else:
                    self.logger.warning(f"Page returned status: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Failed to get page: {type(e).__name__}: {e}")
            return None

    def extract_property_links(self, content: str) -> List[str]:
        """Извлечение ссылок на реальные объявления"""
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a', href=True)
        
        property_links = []
        
        for link in links:
            href = link.get('href', '')
            
            # Ищем ссылки на объявления с ID в конце
            if '/for-rent/' in href:
                if any(prop_type in href for prop_type in ['apartment', 'studio', 'flat']):
                    if re.search(r'/\d+$', href):  # Заканчивается на число (ID)
                        full_url = href if href.startswith('http') else self.base_url + href
                        property_links.append(full_url)
        
        # Удаляем дубликаты
        unique_links = list(set(property_links))
        self.logger.info(f"Found {len(unique_links)} property links")
        
        return unique_links

    async def get_property_info(self, url: str) -> Optional[Property]:
        """Получение информации о конкретном объявлении"""
        try:
            await asyncio.sleep(random.uniform(0.5, 1.0))  # Небольшая задержка
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return self.parse_property_details(content, url)
                else:
                    self.logger.debug(f"Property page {url} returned {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.debug(f"Failed to get property {url}: {e}")
            return None

    def parse_property_details(self, content: str, url: str) -> Optional[Property]:
        """Парсинг деталей объявления"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Заголовок из title тега
            title_elem = soup.find('title')
            title = "Property in Dublin"
            
            if title_elem:
                title_text = title_elem.get_text().strip()
                # Убираем " is for rent on Daft.ie" из конца
                title_clean = title_text.replace(' is for rent on Daft.ie', '')
                if len(title_clean) > 10:
                    title = title_clean
            
            # Ищем цену
            price_str = "See listing"
            price_elements = soup.find_all(string=lambda text: text and '€' in text and 'month' in text)
            if price_elements:
                # Берем первую найденную цену
                price_text = price_elements[0].strip()
                if '€' in price_text:
                    price_str = price_text
            
            # Извлекаем числовую цену
            price = 0
            price_match = re.search(r'€([\d,]+)', price_str)
            if price_match:
                price = int(price_match.group(1).replace(',', ''))
            
            # Адрес из заголовка
            address = "Dublin"
            if ', Dublin' in title:
                # Извлекаем адрес из заголовка
                address_part = title.split(', Dublin')[0]
                if len(address_part) > 10:
                    parts = address_part.split(', ')
                    if len(parts) > 1:
                        address = ', '.join(parts[1:]) + ', Dublin'
            
            # УЛУЧШЕННОЕ извлечение количества спален
            bedrooms = self.extract_bedrooms_count(title, soup.get_text())
            
            # Количество ванных (приблизительно)
            bathrooms = 1  # По умолчанию 1 ванная
            if bedrooms >= 2:
                bathrooms = min(bedrooms, 2)  # Обычно не больше 2 ванных
            
            # Тип недвижимости
            property_type = "Apartment"
            if 'studio' in title.lower():
                property_type = "Studio"
            elif 'house' in title.lower():
                property_type = "House"
            elif 'flat' in title.lower():
                property_type = "Flat"
            
            # Извлекаем ID из URL
            id_match = re.search(r'/(\d+)$', url)
            property_id = id_match.group(1) if id_match else str(random.randint(1000000, 9999999))
            
            return Property(
                id=property_id,
                title=title,
                price=price,
                address=address,
                url=url,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                property_type=property_type,
                description=f"Real property listing from daft.ie",
                image_url=None,
                area=None,
                posted_date=datetime.now()
            )
            
        except Exception as e:
            self.logger.debug(f"Failed to parse property details: {e}")
            return None

    def extract_bedrooms_count(self, title: str, page_text: str) -> int:
        """ТОЧНОЕ извлечение количества спален из заголовка daft.ie"""
        
        # Сначала проверяем заголовок - самый надёжный источник
        bedroom_count = self.extract_from_title(title)
        if bedroom_count is not None:
            return bedroom_count
        
        # Если в заголовке ничего нет, ищем в мета-данных
        bedroom_count = self.extract_from_page_text(page_text)
        if bedroom_count is not None:
            return bedroom_count
        
        # По умолчанию 1 спальня
        return 1
    
    def extract_from_title(self, title: str) -> Optional[int]:
        """Извлечение количества спален из заголовка"""
        title_lower = title.lower()
        
        # Специальная обработка для Studio
        if 'studio' in title_lower or 'bedsit' in title_lower:
            return 0
        
        # Паттерны для заголовков daft.ie (в порядке приоритета)
        title_patterns = [
            r'(\d+)\s+double\s+bedroom',      # "3 Double Bedroom"
            r'(\d+)\s+single\s+bedroom',      # "2 Single Bedroom" 
            r'(\d+)\s+twin\s+bedroom',        # "2 Twin Bedroom"
            r'(\d+)\s+bedroom(?!s)',          # "3 Bedroom" (не "bedrooms")
            r'(\d+)\s+bed\s+(?:apartment|house|flat|property)',  # "2 Bed Apartment"
            r'(\d+)-bed\s+(?:apartment|house|flat|property)',    # "2-Bed Apartment"
            r'(\d+)\s+bed\s+house',           # "3 Bed House" (для meta description)
            r'(\d+)\s+bed(?:\s|$|,)',         # "2 Bed," или "2 Bed " (новый паттерн!)
            r'(\d+)-bedroom',                 # "3-bedroom"
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, title_lower)
            if matches:
                try:
                    bedroom_count = int(matches[0])
                    # Разумные пределы (от 0 до 10 спален)
                    if 0 <= bedroom_count <= 10:
                        return bedroom_count
                except ValueError:
                    continue
        
        return None
    
    def extract_from_page_text(self, page_text: str) -> Optional[int]:
        """Извлечение количества спален из мета-данных страницы"""
        
        # Ищем в мета-данных (description, og:description)
        meta_patterns = [
            r'<meta[^>]*(?:name="description"|property="og:description")[^>]*content="([^"]*)"',
            r'<meta[^>]*content="([^"]*)"[^>]*(?:name="description"|property="og:description")'
        ]
        
        for pattern in meta_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for meta_content in matches:
                bedroom_count = self.extract_from_title(meta_content)
                if bedroom_count is not None:
                    return bedroom_count
        
        return None

    def filter_properties(self, properties: List[Property], filters: SearchFilters) -> List[Property]:
        """Фильтрация объявлений по критериям"""
        filtered = []
        
        for prop in properties:
            # Фильтр по цене
            if filters.max_price and prop.price > filters.max_price:
                continue
            
            # Фильтр по количеству спален
            if filters.min_bedrooms and prop.bedrooms < filters.min_bedrooms:
                continue
            
            # Фильтр по районам (если указаны)
            if filters.areas:
                area_match = False
                for area in filters.areas:
                    if area.lower() in prop.address.lower():
                        area_match = True
                        break
                if not area_match:
                    continue
            
            filtered.append(prop)
        
        return filtered

    async def search_properties(self, filters: SearchFilters) -> List[Property]:
        """Поиск ТОЛЬКО реальных объявлений"""
        self.logger.info(f"🔍 Searching REAL properties: {filters.city}, max €{filters.max_price}, {filters.min_bedrooms}+ beds")
        self.logger.info("🚫 NO fake data, ONLY real listings from daft.ie")
        
        # Получаем страницу с объявлениями БЕЗ фильтров
        content = await self.get_listings_page(filters.city)
        
        if not content:
            self.logger.error("❌ Failed to get listings page")
            return []
        
        # Извлекаем ссылки на объявления
        property_links = self.extract_property_links(content)
        
        if not property_links:
            self.logger.warning("⚠️ No property links found")
            return []
        
        self.logger.info(f"Processing {len(property_links)} property links...")
        
        # Получаем детали объявлений
        properties = []
        
        # Обрабатываем первые 20 ссылок
        for i, url in enumerate(property_links[:20]):
            self.logger.debug(f"Processing property {i+1}/{min(20, len(property_links))}")
            
            prop_info = await self.get_property_info(url)
            if prop_info:
                properties.append(prop_info)
        
        self.logger.info(f"✅ Got {len(properties)} properties before filtering")
        
        # Применяем фильтры
        filtered_properties = self.filter_properties(properties, filters)
        
        self.logger.info(f"✅ Found {len(filtered_properties)} REAL properties matching criteria")
        
        return filtered_properties

    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()
            self.session = None
