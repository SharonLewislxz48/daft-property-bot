#!/usr/bin/env python3
"""
Готовый к продакшену парсер daft.ie с JSON подходом и обратной совместимостью
"""

import asyncio
import re
import json
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

class ProductionDaftParser:
    """
    Продакшен-готовый парсер для daft.ie с JSON подходом
    Поддерживает как async context manager, так и прямой вызов
    """
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
        self._should_close_session = False
        
    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
            self._should_close_session = True
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and self._should_close_session:
            await self.session.close()
            self.session = None
            self._should_close_session = False
    
    def extract_json_data(self, html_content: str) -> List[Dict[str, Any]]:
        """Извлекает JSON данные из React приложения"""
        try:
            # Поиск script элемента с __NEXT_DATA__
            pattern = r'<script id="__NEXT_DATA__"[^>]*>([^<]+)</script>'
            match = re.search(pattern, html_content)
            
            if not match:
                logging.error("__NEXT_DATA__ script не найден")
                return []
            
            json_str = match.group(1)
            data = json.loads(json_str)
            
            # Извлекаем listings из структуры данных
            listings = data.get('props', {}).get('pageProps', {}).get('listings', [])
            logging.info(f"Найдено объявлений в JSON: {len(listings)}")
            
            # Парсим каждое объявление
            properties = []
            for item in listings:
                listing = item.get('listing', {})
                if not listing:
                    continue
                    
                property_data = self.parse_listing(listing)
                if property_data:
                    properties.append(property_data)
            
            return properties
            
        except Exception as e:
            logging.error(f"Ошибка парсинга JSON: {e}")
            return []
    
    def parse_listing(self, listing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Парсит отдельное объявление из JSON"""
        try:
            # Основная информация
            property_id = str(listing.get('id', ''))
            title = listing.get('title', '')
            price = listing.get('price', '')
            bedrooms_str = listing.get('numBedrooms', '')
            property_type = listing.get('propertyType', '')
            
            # URL для объявления
            seo_path = listing.get('seoFriendlyPath', '')
            url = f"https://www.daft.ie{seo_path}" if seo_path else ""
            
            # Местоположение (извлекаем из заголовка)
            location_parts = title.split(',')
            if len(location_parts) >= 2:
                location = ', '.join(location_parts[-2:]).strip()
            else:
                location = title
            
            # Дата публикации
            publish_date = listing.get('publishDate')
            date_published = None
            if publish_date:
                try:
                    date_published = datetime.fromtimestamp(publish_date / 1000).strftime('%Y-%m-%d')
                except:
                    pass
            
            # Изображения
            media = listing.get('media', {})
            images = media.get('images', [])
            image_urls = []
            for img in images[:3]:  # Берем первые 3 изображения
                if 'size720x480' in img:
                    image_urls.append(img['size720x480'])
            
            # Продавец
            seller = listing.get('seller', {})
            agent_name = seller.get('name', '')
            phone = seller.get('phone', '')
            
            # Энергоэффективность
            ber = listing.get('ber', {})
            energy_rating = ber.get('rating', '') if ber else ''
            
            # Парсим количество спален
            bedrooms = self._parse_bedrooms_from_json(bedrooms_str)
            
            # Парсим цену
            monthly_rent = self._parse_price(price)
            
            property_data = {
                'id': property_id,
                'title': title,
                'url': url,
                'price': monthly_rent,
                'bedrooms': bedrooms,
                'property_type': property_type,
                'location': location,
                'date_published': date_published,
                'images': image_urls,
                'agent_name': agent_name,
                'phone': phone,
                'energy_rating': energy_rating
            }
            
            logging.debug(f"Обработано объявление: {title} - {price}")
            return property_data
            
        except Exception as e:
            logging.error(f"Ошибка парсинга объявления из JSON: {e}")
            return None
    
    def _parse_bedrooms_from_json(self, bedrooms_str: str) -> int:
        """Парсит количество спален из JSON строки"""
        try:
            # Ищем числа в строке типа "1, 2, 3 & 5 bed" или "3 Bed"
            numbers = re.findall(r'\d+', bedrooms_str)
            if numbers:
                # Берем первое число как основное количество спален
                return int(numbers[0])
        except (ValueError, AttributeError):
            pass
        return 1  # По умолчанию
    
    def _parse_price(self, price_str: str) -> int:
        """Извлечение цены из строки"""
        try:
            # Убираем все кроме цифр
            price_clean = re.sub(r'[^\d]', '', price_str)
            if price_clean:
                return int(price_clean)
        except (ValueError, AttributeError):
            pass
        return 0
    
    async def search_properties(
        self, 
        min_bedrooms: int = 3, 
        max_price: int = 2500, 
        location: str = "dublin-city", 
        limit: int = 20,
        max_pages: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Ищет недвижимость на daft.ie с заданными параметрами
        Работает как с context manager, так и без него
        
        Args:
            min_bedrooms: Минимальное количество спален
            max_price: Максимальная цена в евро
            location: Локация для поиска (dublin-city, cork, etc.)
            limit: Максимальное количество результатов
            max_pages: Максимальное количество страниц для просмотра
            
        Returns:
            Список словарей с данными о недвижимости
        """
        logging.info(f"🔍 ПОИСК: {min_bedrooms}+ спален, до €{max_price}, {location} (до {max_pages} страниц)")
        
        properties = []
        seen_ids = set()
        
        # Управление сессией - создаем если нет, закрываем если создали здесь
        should_close_session = False
        if not self.session:
            self.session = aiohttp.ClientSession()
            should_close_session = True
        
        try:
            for page in range(1, max_pages + 1):
                try:
                    # Формируем URL
                    url = self._build_search_url(min_bedrooms, max_price, location, page)
                    logging.info(f"Обработка страницы {page}: {url}")
                    
                    # Делаем HTTP запрос с реалистичными заголовками
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                        'Sec-Ch-Ua-Mobile': '?0',
                        'Sec-Ch-Ua-Platform': '"Linux"',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    # Небольшая задержка
                    await asyncio.sleep(1)
                    
                    async with self.session.get(url, headers=headers) as response:
                        if response.status != 200:
                            logging.error(f"HTTP ошибка {response.status} для страницы {page}")
                            continue
                        
                        html_content = await response.text()
                        logging.info(f"Получено {len(html_content)} символов HTML для страницы {page}")
                        
                        # Извлекаем и парсим JSON данные
                        page_properties = self.extract_json_data(html_content)
                        
                        if not page_properties:
                            logging.info(f"Нет объявлений на странице {page}, останавливаем пагинацию")
                            break
                        
                        # Фильтруем по критериям и добавляем новые объявления
                        new_properties = []
                        for prop in page_properties:
                            if (prop and prop['id'] not in seen_ids and 
                                self._matches_criteria(prop, min_bedrooms, max_price)):
                                seen_ids.add(prop['id'])
                                new_properties.append(prop)
                        
                        properties.extend(new_properties)
                        logging.info(f"Добавлено {len(new_properties)} новых объявлений со страницы {page}")
                        
                        # Проверяем лимит
                        if len(properties) >= limit:
                            properties = properties[:limit]
                            break
                        
                except Exception as e:
                    logging.error(f"Ошибка обработки страницы {page}: {e}")
                    continue
        
        finally:
            # Закрываем сессию только если создали её здесь
            if should_close_session and self.session:
                await self.session.close()
                self.session = None
        
        logging.info(f"JSON поиск завершен. Найдено {len(properties)} объявлений")
        return properties
    
    def _build_search_url(self, min_bedrooms: int, max_price: int, location: str, page: int = 1) -> str:
        """Построение URL для поиска"""
        base_url = f"{self.base_url}/property-for-rent/{location}/houses"
        
        params = [
            f"rentalPrice_to={max_price}",
            f"numBeds_from={min_bedrooms}"
        ]
        
        if page > 1:
            params.append(f"page={page}")
        
        return f"{base_url}?{'&'.join(params)}"
    
    def _matches_criteria(self, property_data: Dict[str, Any], min_bedrooms: int, max_price: int) -> bool:
        """Проверяет соответствие объявления критериям поиска"""
        try:
            # Проверка спален
            bedrooms = property_data.get('bedrooms', 0)
            if bedrooms < min_bedrooms:
                return False
            
            # Проверка цены
            price = property_data.get('price', 0)
            if price > max_price:
                return False
            
            return True
        except Exception:
            return False

# Основной класс для обратной совместимости
class DaftParser:
    """Алиас для обратной совместимости"""
    
    def __init__(self):
        self._parser = ProductionDaftParser()
    
    async def search_properties(self, **kwargs):
        return await self._parser.search_properties(**kwargs)

# Пример использования
async def main():
    """Тестирование парсера"""
    # Тест 1: С context manager
    print("🧪 Тест 1: С async context manager")
    async with ProductionDaftParser() as parser:
        properties = await parser.search_properties(
            min_bedrooms=3,
            max_price=2500,
            location='dublin-city',
            limit=3,
            max_pages=1
        )
        print(f"✅ Найдено {len(properties)} объявлений")
    
    # Тест 2: Без context manager (как в боте)
    print("\n🧪 Тест 2: Без context manager (режим бота)")
    parser = ProductionDaftParser()
    properties = await parser.search_properties(
        min_bedrooms=3,
        max_price=2500,
        location='dublin-city',
        limit=3,
        max_pages=1
    )
    print(f"✅ Найдено {len(properties)} объявлений")
    
    if properties:
        print("\n📋 Пример найденного объявления:")
        prop = properties[0]
        print(f"  📍 {prop['title']}")
        print(f"  💰 €{prop['price']}/мес | 🛏️ {prop['bedrooms']} спален")
        print(f"  🔗 {prop['url']}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
