#!/usr/bin/env python3
"""
Простой обход блокировок через ротацию User-Agent и задержки
"""

import asyncio
import aiohttp
import random
import time
import json
import re
from typing import List, Dict

class SimpleBypassParser:
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.user_agents = [
            # Desktop browsers
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
            
            # Mobile browsers
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/121.0 Firefox/121.0",
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        ]
        
        self.referers = [
            "https://www.google.com/",
            "https://www.google.ie/",
            "https://duckduckgo.com/",
            "https://www.bing.com/",
            "https://www.daft.ie/",
        ]

    def get_random_headers(self):
        """Генерируем случайные заголовки"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,en-IE;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "Referer": random.choice(self.referers),
            "DNT": "1",
            "Sec-GPC": "1",
        }

    async def test_access(self) -> bool:
        """Тестируем доступ к daft.ie"""
        for attempt in range(3):
            try:
                headers = self.get_random_headers()
                
                # Случайная задержка между запросами
                if attempt > 0:
                    delay = random.uniform(2, 5)
                    print(f"⏳ Ждем {delay:.1f} секунд...")
                    await asyncio.sleep(delay)
                
                timeout = aiohttp.ClientTimeout(total=15)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    print(f"🔄 Попытка {attempt + 1}/3: Тестируем доступ...")
                    print(f"User-Agent: {headers['User-Agent'][:50]}...")
                    
                    async with session.get(
                        f"{self.base_url}/",
                        headers=headers,
                        allow_redirects=True
                    ) as response:
                        print(f"📊 Ответ сервера: {response.status}")
                        
                        if response.status == 200:
                            print("✅ Доступ к daft.ie восстановлен!")
                            return True
                        elif response.status == 403:
                            print("❌ Все еще заблокированы (403)")
                        elif response.status == 429:
                            print("⚠️ Слишком много запросов (429)")
                            await asyncio.sleep(10)
                        else:
                            print(f"⚠️ Неожиданный статус: {response.status}")
                            
            except asyncio.TimeoutError:
                print("⏰ Таймаут соединения")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        return False

    async def search_properties(self, bedrooms: int = 2, max_price: int = 2500, location: str = "dublin-city") -> List[Dict]:
        """Поиск недвижимости с обходом блокировок"""
        
        # Сначала проверяем доступ
        if not await self.test_access():
            print("❌ Не удалось получить доступ к daft.ie")
            return []
        
        search_url = f"{self.base_url}/property-for-rent/{location}?numBeds={bedrooms}&maxPrice={max_price}"
        
        for attempt in range(3):
            try:
                headers = self.get_random_headers()
                
                # Задержка между запросами
                if attempt > 0:
                    delay = random.uniform(3, 7)
                    print(f"⏳ Ждем {delay:.1f} секунд перед повтором...")
                    await asyncio.sleep(delay)
                
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    print(f"🔍 Поиск недвижимости (попытка {attempt + 1}/3)...")
                    print(f"🌐 URL: {search_url}")
                    
                    async with session.get(
                        search_url,
                        headers=headers,
                        allow_redirects=True
                    ) as response:
                        print(f"📊 Статус ответа: {response.status}")
                        
                        if response.status == 200:
                            html = await response.text()
                            properties = self._extract_properties(html)
                            
                            if properties:
                                print(f"✅ Найдено {len(properties)} объектов!")
                                return properties
                            else:
                                print("⚠️ Страница загружена, но объекты не найдены")
                                
                        elif response.status == 403:
                            print("❌ Заблокированы (403)")
                        elif response.status == 429:
                            print("⚠️ Слишком много запросов (429), увеличиваем задержку")
                            await asyncio.sleep(20)
                        else:
                            print(f"⚠️ Неожиданный статус: {response.status}")
                            
            except Exception as e:
                print(f"❌ Ошибка поиска: {e}")
        
        print("❌ Не удалось выполнить поиск после всех попыток")
        return []

    def _extract_properties(self, html: str) -> List[Dict]:
        """Извлекаем недвижимость из HTML"""
        properties = []
        
        try:
            # Ищем JSON данные
            json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group(1))
                properties = self._extract_from_json(json_data)
                
                if properties:
                    print(f"✅ Извлечено {len(properties)} объектов из JSON")
                    return properties
            
            print("⚠️ JSON данные не найдены в HTML")
            
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
        except Exception as e:
            print(f"❌ Ошибка извлечения данных: {e}")
        
        return properties

    def _extract_from_json(self, json_data: dict) -> List[Dict]:
        """Извлекаем данные из JSON"""
        properties = []
        
        try:
            props_data = json_data.get('props', {}).get('pageProps', {})
            
            # Различные пути к данным о недвижимости
            listings = (
                props_data.get('listings', []) or
                props_data.get('searchResults', {}).get('listings', []) or
                props_data.get('properties', []) or
                props_data.get('results', [])
            )
            
            for item in listings:
                prop = {
                    'title': item.get('title', item.get('name', 'Без названия')),
                    'price': item.get('price', item.get('monthlyPrice', 'Цена не указана')),
                    'location': item.get('location', item.get('address', 'Местоположение не указано')),
                    'bedrooms': item.get('bedrooms', item.get('numBedrooms', 'Не указано')),
                    'url': f"https://www.daft.ie{item.get('seoPath', '')}" if item.get('seoPath') else None
                }
                properties.append(prop)
                
        except Exception as e:
            print(f"❌ Ошибка обработки JSON: {e}")
        
        return properties

async def main():
    """Тестирование простого обхода"""
    parser = SimpleBypassParser()
    
    print("🔧 Тестируем простой обход блокировок...")
    print("=" * 50)
    
    # Проверяем доступ
    if await parser.test_access():
        print("\n🔍 Выполняем поиск недвижимости...")
        properties = await parser.search_properties()
        
        if properties:
            print(f"\n🎉 Успех! Найдено {len(properties)} объектов:")
            print("=" * 50)
            
            for i, prop in enumerate(properties[:5], 1):
                print(f"\n{i}. {prop['title']}")
                print(f"   💰 Цена: {prop['price']}")
                print(f"   📍 Адрес: {prop['location']}")
                print(f"   🛏️ Спальни: {prop['bedrooms']}")
                if prop['url']:
                    print(f"   🔗 URL: {prop['url']}")
        else:
            print("\n❌ Объекты не найдены")
    else:
        print("\n❌ Не удалось получить доступ к сайту")

if __name__ == "__main__":
    asyncio.run(main())
