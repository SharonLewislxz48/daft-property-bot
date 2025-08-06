#!/usr/bin/env python3
"""
Продакшен парсер с продвинутым анти-блокировочным механизмом
"""

import asyncio
import re
import json
import aiohttp
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

class ProductionDaftParserAntiBlock:
    """
    Парсер с продвинутыми методами обхода блокировок
    """
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
        self._should_close_session = False
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0'
        ]
        
    async def __aenter__(self):
        if not self.session:
            # Создаем сессию с настройками против блокировки
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=2,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            self._should_close_session = True
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and self._should_close_session:
            await self.session.close()
            self.session = None
            self._should_close_session = False
    
    def _get_random_headers(self) -> Dict[str, str]:
        """Генерирует случайные реалистичные заголовки"""
        user_agent = random.choice(self.user_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive'
        }
        
        # Добавляем специфичные заголовки для Chrome
        if 'Chrome' in user_agent:
            headers['Sec-Ch-Ua'] = '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"'
            headers['Sec-Ch-Ua-Mobile'] = '?0'
            headers['Sec-Ch-Ua-Platform'] = '"Linux"'
        
        return headers
    
    async def search_properties(self, min_bedrooms: int = 1, max_price: int = 5000, 
                              location: str = 'dublin-city', limit: int = 10, max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Поиск объявлений с продвинутым обходом блокировок
        """
        all_properties = []
        
        # Создаем сессию если её нет
        should_close_session = False
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=2,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            should_close_session = True
        
        try:
            for page in range(1, max_pages + 1):
                try:
                    # Случайная задержка между запросами
                    if page > 1:
                        delay = random.uniform(2.0, 5.0)
                        logging.info(f"Задержка {delay:.1f} сек перед страницей {page}")
                        await asyncio.sleep(delay)
                    
                    # Формируем URL
                    url = self._build_search_url(min_bedrooms, max_price, location, page)
                    logging.info(f"Обработка страницы {page}: {url}")
                    
                    # Получаем случайные заголовки
                    headers = self._get_random_headers()
                    
                    # Несколько попыток с разными стратегиями
                    page_properties = await self._try_multiple_strategies(url, headers)
                    
                    if page_properties:
                        all_properties.extend(page_properties)
                        logging.info(f"Найдено {len(page_properties)} объявлений на странице {page}")
                        
                        # Проверяем лимит
                        if len(all_properties) >= limit:
                            break
                    else:
                        logging.warning(f"Не удалось получить данные со страницы {page}")
                        
                except Exception as e:
                    logging.error(f"Ошибка обработки страницы {page}: {e}")
                    continue
                    
        finally:
            if should_close_session and self.session:
                await self.session.close()
                self.session = None
        
        # Ограничиваем результат
        result = all_properties[:limit]
        logging.info(f"Итого найдено: {len(result)} объявлений")
        return result
    
    async def _try_multiple_strategies(self, url: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Пытается получить данные несколькими способами"""
        
        strategies = [
            self._strategy_direct_request,
            self._strategy_with_referer,
            self._strategy_with_cookies,
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logging.info(f"Попытка {i}: {strategy.__name__}")
                result = await strategy(url, headers)
                if result:
                    logging.info(f"Стратегия {i} сработала, найдено {len(result)} объявлений")
                    return result
            except Exception as e:
                logging.warning(f"Стратегия {i} не сработала: {e}")
                continue
        
        return []
    
    async def _strategy_direct_request(self, url: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Стратегия 1: Прямой запрос"""
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                content = await response.text()
                return self.extract_json_data(content)
            else:
                logging.error(f"HTTP {response.status} для прямого запроса")
                return []
    
    async def _strategy_with_referer(self, url: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Стратегия 2: Запрос с Referer"""
        headers_with_referer = headers.copy()
        headers_with_referer['Referer'] = 'https://www.daft.ie/'
        
        async with self.session.get(url, headers=headers_with_referer) as response:
            if response.status == 200:
                content = await response.text()
                return self.extract_json_data(content)
            else:
                logging.error(f"HTTP {response.status} для запроса с Referer")
                return []
    
    async def _strategy_with_cookies(self, url: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Стратегия 3: Сначала главная страница, потом поиск"""
        # Сначала идем на главную страницу
        main_headers = headers.copy()
        async with self.session.get('https://www.daft.ie/', headers=main_headers) as response:
            if response.status != 200:
                raise Exception(f"Не удалось загрузить главную страницу: {response.status}")
        
        # Задержка
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # Теперь делаем поиск с cookies и referer
        search_headers = headers.copy()
        search_headers['Referer'] = 'https://www.daft.ie/'
        
        async with self.session.get(url, headers=search_headers) as response:
            if response.status == 200:
                content = await response.text()
                return self.extract_json_data(content)
            else:
                logging.error(f"HTTP {response.status} для запроса с cookies")
                return []
    
    def _build_search_url(self, min_bedrooms: int, max_price: int, location: str, page: int = 1) -> str:
        """Создает URL для поиска"""
        base_search_url = f"{self.base_url}/property-for-rent/{location}/houses"
        params = []
        
        if max_price:
            params.append(f"rentalPrice_to={max_price}")
        if min_bedrooms:
            params.append(f"numBeds_from={min_bedrooms}")
        if page > 1:
            params.append(f"pageNumber={page}")
            
        if params:
            return f"{base_search_url}?{'&'.join(params)}"
        return base_search_url
    
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
            
            # Извлекаем свойства
            properties = self._extract_properties_from_json(data)
            return properties
            
        except Exception as e:
            logging.error(f"Ошибка извлечения JSON данных: {e}")
            return []
    
    def _extract_properties_from_json(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлекает список свойств из JSON структуры"""
        try:
            # Навигация по JSON структуре Next.js
            page_props = data.get('props', {}).get('pageProps', {})
            
            # Ищем listings в разных возможных местах
            listings = None
            if 'listings' in page_props:
                listings = page_props['listings']
            elif 'initialData' in page_props and 'listings' in page_props['initialData']:
                listings = page_props['initialData']['listings']
            elif 'searchResults' in page_props:
                listings = page_props['searchResults'].get('listings', [])
            
            if not listings:
                logging.warning("Listings не найдены в JSON структуре")
                return []
            
            properties = []
            for listing in listings:
                property_data = self._parse_property_from_json(listing)
                if property_data:
                    properties.append(property_data)
            
            return properties
            
        except Exception as e:
            logging.error(f"Ошибка извлечения свойств из JSON: {e}")
            return []
    
    def _parse_property_from_json(self, listing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Парсит одно объявление из JSON"""
        try:
            # Базовые поля
            property_id = listing.get('id', '')
            title = listing.get('title', '')
            price = listing.get('price', '')
            property_type = listing.get('propertyType', '')
            
            # URL
            seo_friendly_path = listing.get('seoFriendlyPath', '')
            url = f"https://www.daft.ie{seo_friendly_path}" if seo_friendly_path else ""
            
            # Локация
            location = listing.get('displayAddress', '')
            
            # Спальни
            bedrooms_str = listing.get('bedrooms', '')
            bedrooms = self._parse_bedrooms_from_json(bedrooms_str)
            
            # Парсим цену
            monthly_rent = self._parse_price(price)
            
            # Изображения
            image_urls = []
            media = listing.get('media', {})
            if isinstance(media, dict) and 'images' in media:
                images = media['images']
                if isinstance(images, list):
                    for img in images[:3]:  # Берем первые 3 изображения
                        if isinstance(img, dict) and 'url' in img:
                            image_urls.append(img['url'])
            
            # Дата публикации
            date_published = listing.get('publishDate', '')
            
            # Агент
            agent_name = ''
            agent_info = listing.get('seller', {})
            if isinstance(agent_info, dict):
                agent_name = agent_info.get('name', '')
            
            # Телефон (часто скрыт)
            phone = ''
            
            # Энергетический рейтинг
            energy_rating = listing.get('ber', {}).get('rating', '') if listing.get('ber') else ''
            
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
            if not bedrooms_str:
                return 0
            
            # Ищем числа в строке
            numbers = re.findall(r'\d+', str(bedrooms_str))
            if numbers:
                return int(numbers[0])
            return 0
        except:
            return 0
    
    def _parse_price(self, price_str: str) -> int:
        """Парсит цену из строки"""
        try:
            if not price_str:
                return 0
            
            # Убираем все символы кроме цифр
            price_numbers = re.sub(r'[^\d]', '', str(price_str))
            if price_numbers:
                return int(price_numbers)
            return 0
        except:
            return 0


# Обратная совместимость
class ProductionDaftParser(ProductionDaftParserAntiBlock):
    """Алиас для обратной совместимости"""
    pass


async def main():
    """Тестирование парсера"""
    parser = ProductionDaftParser()
    
    try:
        results = await parser.search_properties(
            min_bedrooms=2,
            max_price=3000,
            location='dublin-city',
            limit=5
        )
        
        print(f"✅ Найдено: {len(results)} объявлений")
        
        for i, prop in enumerate(results, 1):
            print(f"\n{i}. {prop['title']}")
            print(f"   💰 {prop['price']}€")
            print(f"   🛏️ {prop['bedrooms']} спален")
            print(f"   📍 {prop['location']}")
            print(f"   🔗 {prop['url'][:50]}...")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
