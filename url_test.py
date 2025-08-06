#!/usr/bin/env python3
"""
Простой тест URL генерации для парсера daft.ie
"""

import asyncio
import re
from urllib.parse import urlencode

def build_search_url(city, max_price, min_bedrooms, page=1):
    """Тест генерации URL как в production_parser.py"""
    base_url = "https://www.daft.ie"
    
    # Нормализация города
    city_normalized = city.lower().replace(" ", "-")
    if "dublin" in city_normalized:
        location = "dublin-city"
    else:
        location = city_normalized
    
    # Формируем URL с правильной пагинацией
    if page > 1:
        search_url = f"{base_url}/property-for-rent/{location}/houses?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}&page={page}"
    else:
        search_url = f"{base_url}/property-for-rent/{location}/houses?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}"
    
    return search_url

async def test_manual_request():
    """Тест загрузки страницы с aiohttp"""
    import aiohttp
    
    url = build_search_url("dublin", 2500, 3, 1)
    print(f"🔗 Тестируем URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=30) as response:
                print(f"📊 Статус ответа: {response.status}")
                
                if response.status == 200:
                    html = await response.text()
                    print(f"✅ HTML получен, размер: {len(html)} символов")
                    
                    # Ищем объявления
                    rent_links = re.findall(r'href="[^"]*for-rent[^"]*"', html)
                    print(f"🏠 Найдено ссылок на аренду: {len(rent_links)}")
                    
                    # Ищем цены
                    prices = re.findall(r'€[\d,]+', html)
                    print(f"💰 Найдено цен: {len(prices)}")
                    
                    # Ищем количество спален
                    bedrooms = re.findall(r'\d+\s*bed', html, re.IGNORECASE)
                    print(f"🛏️ Найдено упоминаний спален: {len(bedrooms)}")
                    
                    # Проверяем специфические элементы daft.ie
                    if "daft.ie" in html:
                        print("✅ Это действительно страница daft.ie")
                    else:
                        print("❌ Не похоже на страницу daft.ie")
                    
                    # Сохраняем HTML для анализа
                    with open('/tmp/daft_response.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    print("💾 HTML сохранен в /tmp/daft_response.html")
                    
                    return len(rent_links) > 0
                else:
                    print(f"❌ Ошибка HTTP: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            return False

def test_url_generation():
    """Тест генерации URL"""
    print("🔧 Тестирование генерации URL...\n")
    
    test_cases = [
        ("dublin", 2500, 3, 1),
        ("dublin", 2500, 3, 2),
        ("cork", 1500, 2, 1),
    ]
    
    for city, price, beds, page in test_cases:
        url = build_search_url(city, price, beds, page)
        print(f"📍 {city}, €{price}, {beds}+ спален, страница {page}:")
        print(f"   {url}\n")

async def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование URL генерации и запросов к daft.ie\n")
    
    # Тест 1: Генерация URL
    test_url_generation()
    
    # Тест 2: Реальный запрос
    print("🌐 Тестирование реального запроса...")
    success = await test_manual_request()
    
    if success:
        print("\n✅ Тест успешен - найдены объявления!")
    else:
        print("\n❌ Тест неудачен - объявления не найдены")
    
    print("\n📋 Рекомендации:")
    print("1. Проверьте HTML в /tmp/daft_response.html")
    print("2. Возможно, нужно обновить селекторы для поиска объявлений")
    print("3. Проверьте, не блокирует ли daft.ie автоматические запросы")

if __name__ == "__main__":
    asyncio.run(main())
