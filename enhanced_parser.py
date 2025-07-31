#!/usr/bin/env python3
"""
Улучшенный парсер с обходом блокировки
"""
import asyncio
import aiohttp
import random
from typing import List, Optional
from bs4 import BeautifulSoup
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedDaftParser:
    """Улучшенный парсер с обходом блокировки"""
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
        
        # Ротация User-Agent
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
    
    async def get_session(self):
        """Получение сессии с настройками для обхода блокировки"""
        if not self.session:
            # Случайный User-Agent
            user_agent = random.choice(self.user_agents)
            
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            # Настройки сессии
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=2,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                connector=connector,
                timeout=timeout,
                trust_env=True  # Использует системные прокси если есть
            )
        
        return self.session
    
    async def fetch_page(self, url: str, delay: float = None) -> Optional[str]:
        """Получение страницы с задержкой и повторными попытками"""
        session = await self.get_session()
        
        # Случайная задержка для имитации человека
        if delay is None:
            delay = random.uniform(2.0, 5.0)
        
        logger.info(f"Fetching {url} with delay {delay:.1f}s")
        await asyncio.sleep(delay)
        
        for attempt in range(3):  # 3 попытки
            try:
                # Добавляем рефферер для предыдущих страниц
                headers = {}
                if 'page=' in url and 'page=1' not in url:
                    headers['Referer'] = self.base_url
                
                async with session.get(url, headers=headers) as response:
                    logger.info(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 1000:  # Проверяем, что получили полноценную страницу
                            logger.info(f"Successfully fetched page, content length: {len(content)}")
                            return content
                        else:
                            logger.warning(f"Received short content: {len(content)} bytes")
                    
                    elif response.status == 403:
                        logger.warning(f"Attempt {attempt + 1}: Access forbidden (403)")
                        # Увеличиваем задержку при блокировке
                        await asyncio.sleep(random.uniform(5.0, 10.0))
                    
                    elif response.status == 429:
                        logger.warning(f"Attempt {attempt + 1}: Rate limited (429)")
                        await asyncio.sleep(random.uniform(10.0, 20.0))
                    
                    else:
                        logger.warning(f"Attempt {attempt + 1}: Unexpected status {response.status}")
                        
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:  # Не ждём после последней попытки
                    await asyncio.sleep(random.uniform(3.0, 8.0))
        
        logger.error(f"Failed to fetch {url} after 3 attempts")
        return None
    
    async def parse_listings(self, html: str) -> List[dict]:
        """Парсинг объявлений из HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        
        # Различные селекторы для поиска объявлений
        selectors = [
            'div[data-testid="results"] > div',
            '.SearchPage__Results > div',
            '[data-testid="property-card"]',
            '.PropertySearchCard',
            'div[data-testid*="property"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"Found {len(elements)} elements with selector: {selector}")
                
                for element in elements:
                    try:
                        listing = self.parse_single_listing(element)
                        if listing:
                            listings.append(listing)
                    except Exception as e:
                        logger.debug(f"Error parsing listing: {e}")
                        continue
                
                if listings:
                    break
        
        logger.info(f"Successfully parsed {len(listings)} listings")
        return listings
    
    def parse_single_listing(self, element) -> Optional[dict]:
        """Парсинг одного объявления"""
        try:
            # Поиск ссылки
            link_elem = element.find('a', href=True)
            if not link_elem:
                return None
            
            url = link_elem['href']
            if not url.startswith('http'):
                url = self.base_url + url
            
            # Поиск заголовка
            title_selectors = ['h2', 'h3', '.title', '[data-testid*="title"]']
            title = None
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                return None
            
            # Поиск цены
            price_selectors = [
                '[data-testid*="price"]',
                '.price',
                '[class*="price" i]',
                'span:contains("€")'
            ]
            price = None
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem and '€' in price_elem.get_text():
                    price = price_elem.get_text(strip=True)
                    break
            
            # Поиск адреса
            address_selectors = [
                '[data-testid*="address"]',
                '.address',
                '[class*="address" i]'
            ]
            address = None
            for selector in address_selectors:
                addr_elem = element.select_one(selector)
                if addr_elem:
                    address = addr_elem.get_text(strip=True)
                    break
            
            return {
                'title': title,
                'price': price or 'Price on request',
                'address': address or 'Address not specified',
                'url': url,
                'bedrooms': '2+ beds',  # Заглушка
                'description': f"Property in {address or 'Dublin'}"
            }
            
        except Exception as e:
            logger.debug(f"Error parsing single listing: {e}")
            return None
    
    async def search_properties(self, city="Dublin", max_price=3000, min_bedrooms=2):
        """Поиск объявлений"""
        logger.info(f"Searching properties in {city}, max price: €{max_price}, min bedrooms: {min_bedrooms}")
        
        # Строим URL поиска
        search_url = f"{self.base_url}/property-for-rent/{city.lower()}"
        params = []
        
        if max_price:
            params.append(f"rentalPrice_to={max_price}")
        if min_bedrooms:
            params.append(f"numBeds_from={min_bedrooms}")
        
        if params:
            search_url += "?" + "&".join(params)
        
        all_listings = []
        
        # Пробуем получить несколько страниц
        for page in range(1, 4):  # Первые 3 страницы
            page_url = f"{search_url}&page={page}" if '?' in search_url else f"{search_url}?page={page}"
            
            html = await self.fetch_page(page_url)
            if html:
                listings = await self.parse_listings(html)
                all_listings.extend(listings)
                
                if not listings:  # Если на странице нет объявлений, прекращаем
                    break
            else:
                logger.warning(f"Failed to fetch page {page}")
                break
        
        logger.info(f"Total listings found: {len(all_listings)}")
        return all_listings
    
    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()

# Тест улучшенного парсера
async def test_enhanced_parser():
    parser = EnhancedDaftParser()
    
    try:
        print("🔍 Тестируем улучшенный парсер с обходом блокировки...")
        print("=" * 60)
        
        listings = await parser.search_properties("Dublin", 3000, 2)
        
        if listings:
            print(f"✅ УСПЕХ! Найдено {len(listings)} РЕАЛЬНЫХ объявлений:")
            print()
            
            for i, listing in enumerate(listings[:5], 1):
                print(f"   {i}. 🏠 {listing['title']}")
                print(f"      📍 {listing['address']}")
                print(f"      💰 {listing['price']}")
                print(f"      🔗 {listing['url']}")
                print()
            
            return True
        else:
            print("❌ Объявления не найдены")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        await parser.close()

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_parser())
    if success:
        print("🎉 Улучшенный парсер работает! Получены реальные данные.")
    else:
        print("⚠️ Улучшенный парсер тоже заблокирован.")
