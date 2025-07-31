#!/usr/bin/env python3
"""
Обход блокировки - метод 3: Бесплатные прокси и TOR
"""
import asyncio
import aiohttp
import random
import json
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyDaftParser:
    """Парсер с использованием прокси"""
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
        
        # Список бесплатных прокси (обновляется автоматически)
        self.free_proxies = []
        
    async def get_free_proxies(self) -> List[str]:
        """Получение списка бесплатных прокси"""
        proxy_sources = [
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
        ]
        
        proxies = []
        
        # Создаем временную сессию без прокси для получения списка прокси
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for source in proxy_sources:
                try:
                    logger.info(f"Fetching proxies from: {source}")
                    async with session.get(source) as response:
                        if response.status == 200:
                            text = await response.text()
                            lines = text.strip().split('\n')
                            
                            for line in lines:
                                line = line.strip()
                                if ':' in line and len(line.split(':')) == 2:
                                    ip, port = line.split(':')
                                    if self.is_valid_ip(ip) and port.isdigit():
                                        proxies.append(f"http://{line}")
                                        
                except Exception as e:
                    logger.debug(f"Failed to fetch from {source}: {e}")
                    continue
        
        logger.info(f"Collected {len(proxies)} proxy addresses")
        return proxies[:50]  # Берем первые 50 для тестирования
    
    def is_valid_ip(self, ip: str) -> bool:
        """Проверка валидности IP адреса"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    async def test_proxy(self, proxy: str) -> bool:
        """Тестирование работоспособности прокси"""
        try:
            connector = aiohttp.TCPConnector(limit=1)
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                trust_env=False
            ) as session:
                
                # Тестируем на простом сайте
                test_url = "http://httpbin.org/ip"
                
                async with session.get(test_url, proxy=proxy) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Proxy works: {proxy} -> IP: {data.get('origin')}")
                        return True
                        
        except Exception as e:
            logger.debug(f"❌ Proxy failed: {proxy} - {e}")
            return False
        
        return False
    
    async def find_working_proxies(self, max_proxies: int = 5) -> List[str]:
        """Поиск работающих прокси"""
        logger.info("🔍 Searching for working proxies...")
        
        all_proxies = await self.get_free_proxies()
        if not all_proxies:
            logger.error("No proxies found")
            return []
        
        # Перемешиваем для случайности
        random.shuffle(all_proxies)
        
        working_proxies = []
        tasks = []
        
        # Тестируем прокси параллельно
        for proxy in all_proxies[:20]:  # Тестируем первые 20
            tasks.append(self.test_proxy(proxy))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if result is True and len(working_proxies) < max_proxies:
                    working_proxies.append(all_proxies[i])
        
        logger.info(f"Found {len(working_proxies)} working proxies")
        return working_proxies
    
    async def create_proxy_session(self, proxy: str = None):
        """Создание сессии с прокси"""
        if self.session:
            await self.session.close()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        connector = aiohttp.TCPConnector(
            limit=5,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        session_kwargs = {
            'headers': headers,
            'connector': connector,
            'timeout': timeout,
            'trust_env': False
        }
        
        self.session = aiohttp.ClientSession(**session_kwargs)
        logger.info(f"Session created with proxy: {proxy or 'None'}")
        return self.session
    
    async def try_tor_connection(self) -> bool:
        """Попытка подключения через TOR"""
        try:
            # TOR обычно работает на порту 9050 (SOCKS) или 8118 (HTTP)
            tor_proxies = [
                "socks5://127.0.0.1:9050",
                "http://127.0.0.1:8118",
                "socks5://localhost:9050"
            ]
            
            for tor_proxy in tor_proxies:
                try:
                    logger.info(f"Trying TOR proxy: {tor_proxy}")
                    
                    connector = aiohttp.TCPConnector()
                    timeout = aiohttp.ClientTimeout(total=15)
                    
                    async with aiohttp.ClientSession(
                        connector=connector,
                        timeout=timeout,
                        trust_env=False
                    ) as session:
                        
                        # Проверяем IP через TOR
                        async with session.get("http://httpbin.org/ip", proxy=tor_proxy) as response:
                            if response.status == 200:
                                data = await response.json()
                                logger.info(f"✅ TOR works! IP: {data.get('origin')}")
                                return True
                                
                except Exception as e:
                    logger.debug(f"TOR proxy {tor_proxy} failed: {e}")
                    continue
            
            logger.warning("TOR is not available")
            return False
            
        except Exception as e:
            logger.error(f"TOR connection error: {e}")
            return False
    
    async def fetch_with_proxy(self, url: str, proxy: str = None) -> Optional[str]:
        """Получение страницы через прокси"""
        session = await self.create_proxy_session()
        
        try:
            await asyncio.sleep(random.uniform(1, 3))
            
            kwargs = {}
            if proxy:
                kwargs['proxy'] = proxy
                logger.info(f"Fetching {url} via proxy: {proxy}")
            else:
                logger.info(f"Fetching {url} direct")
            
            async with session.get(url, **kwargs) as response:
                logger.info(f"Response: {response.status}")
                
                if response.status == 200:
                    content = await response.text()
                    
                    if len(content) > 10000 and 'daft.ie' in content:
                        logger.info(f"✅ Success via proxy! Content: {len(content)} chars")
                        return content
                    else:
                        logger.warning(f"Content seems incomplete: {len(content)} chars")
                else:
                    logger.warning(f"HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"Proxy fetch error: {e}")
            
        return None
    
    async def search_with_proxies(self, city="Dublin", max_price=3000, min_bedrooms=2) -> List[Dict]:
        """Поиск через прокси"""
        logger.info(f"🔍 Proxy search: {city}, max €{max_price}, {min_bedrooms}+ beds")
        
        # Формируем URL
        search_url = f"{self.base_url}/property-for-rent/{city.lower()}"
        params = []
        
        if max_price:
            params.append(f"rentalPrice_to={max_price}")
        if min_bedrooms:
            params.append(f"numBeds_from={min_bedrooms}")
        
        if params:
            search_url += "?" + "&".join(params)
        
        # Метод 1: Пробуем TOR
        if await self.try_tor_connection():
            logger.info("Trying with TOR...")
            html = await self.fetch_with_proxy(search_url, "socks5://127.0.0.1:9050")
            if html:
                return self.parse_html_for_properties(html)
        
        # Метод 2: Пробуем бесплатные прокси
        working_proxies = await self.find_working_proxies()
        
        for proxy in working_proxies:
            logger.info(f"Trying proxy: {proxy}")
            html = await self.fetch_with_proxy(search_url, proxy)
            
            if html:
                properties = self.parse_html_for_properties(html)
                if properties:
                    logger.info(f"✅ Success with proxy {proxy}!")
                    return properties
            
            await asyncio.sleep(2)  # Пауза между попытками
        
        # Метод 3: Прямое подключение как последний шанс
        logger.info("Trying direct connection...")
        html = await self.fetch_with_proxy(search_url)
        if html:
            return self.parse_html_for_properties(html)
        
        return []
    
    def parse_html_for_properties(self, html: str) -> List[Dict]:
        """Упрощенный парсинг HTML"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        properties = []
        
        # Ищем любые ссылки на объявления
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            if 'for-rent' in href and 'property' in href:
                title = link.get_text(strip=True)
                if title and len(title) > 10:
                    prop = {
                        'title': title,
                        'url': f"{self.base_url}{href}" if href.startswith('/') else href,
                        'address': 'Dublin',
                        'price': 'See listing'
                    }
                    properties.append(prop)
        
        # Также ищем в скриптах
        scripts = soup.find_all('script')
        for script in scripts:
            content = script.string or ""
            if 'property' in content.lower() and '{' in content:
                try:
                    # Ищем JSON-подобные структуры
                    import re
                    json_matches = re.findall(r'\{[^{}]*"title"[^{}]*\}', content)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if isinstance(data, dict) and 'title' in data:
                                prop = {
                                    'title': data.get('title', 'Property'),
                                    'address': data.get('address', 'Dublin'),
                                    'price': data.get('price', 'See listing'),
                                    'url': f"{self.base_url}/property"
                                }
                                properties.append(prop)
                        except:
                            continue
                except:
                    continue
        
        # Удаляем дубликаты
        unique_properties = []
        seen_titles = set()
        
        for prop in properties:
            if prop['title'] not in seen_titles:
                seen_titles.add(prop['title'])
                unique_properties.append(prop)
        
        logger.info(f"Parsed {len(unique_properties)} unique properties")
        return unique_properties
    
    async def close(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()

# Тест прокси парсера
async def test_proxy_parser():
    parser = ProxyDaftParser()
    
    try:
        print("🌐 Тестируем обход через ПРОКСИ и TOR...")
        print("=" * 60)
        
        properties = await parser.search_with_proxies("Dublin", 3000, 2)
        
        if properties:
            print(f"✅ УСПЕХ! Найдено {len(properties)} объявлений через прокси:")
            print()
            
            for i, prop in enumerate(properties[:5], 1):
                print(f"   {i}. 🏠 {prop['title']}")
                print(f"      📍 {prop['address']}")
                print(f"      💰 {prop['price']}")
                print(f"      🔗 {prop['url'][:80]}...")
                print()
            
            return True
        else:
            print("❌ Прокси методы не дали результатов")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await parser.close()

if __name__ == "__main__":
    success = asyncio.run(test_proxy_parser())
    
    if success:
        print("\n🎉 МЕТОД 3 УСПЕШЕН! Прокси обход работает!")
    else:
        print("\n⚠️ Метод 3 не сработал, переходим к методу 4...")
