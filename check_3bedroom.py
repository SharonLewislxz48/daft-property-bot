#!/usr/bin/env python3
"""
Прямая проверка конкретного объявления с 3 спальнями
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def check_specific_property():
    """Проверяем конкретное объявление с 3 спальнями"""
    
    # URL который мы видели в предыдущем тесте
    url = "https://www.daft.ie/for-rent/apartment-3-bedroom-apartment-occu-hayfield-churchview-road-killiney-co-dublin/5900759"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    print("🔍 Проверяем конкретное объявление с 3 спальнями:")
    print(f"🔗 {url}")
    print("="*80)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                print(f"📡 Статус ответа: {response.status}")
                
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Получаем заголовок
                    title_elem = soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else "No title"
                    print(f"📄 Заголовок: {title}")
                    
                    # Анализируем спальни нашим улучшенным методом
                    bedrooms = extract_bedrooms_advanced(title, soup.get_text())
                    print(f"🛏️ Определено спален: {bedrooms}")
                    
                    # Ищем цену
                    price_elements = soup.find_all(string=lambda text: text and '€' in text and 'month' in text)
                    if price_elements:
                        price_text = price_elements[0].strip()
                        print(f"💰 Цена: {price_text}")
                    
                elif response.status == 404:
                    print("❌ Объявление больше не доступно (404)")
                else:
                    print(f"❌ Ошибка доступа: {response.status}")
                    
        except Exception as e:
            print(f"❌ Исключение: {e}")

def extract_bedrooms_advanced(title: str, page_text: str) -> int:
    """Точное извлечение спален"""
    
    # Сначала заголовок
    bedroom_count = extract_from_title_advanced(title)
    if bedroom_count is not None:
        return bedroom_count
    
    # Если в заголовке ничего нет, ищем в мета-данных
    meta_patterns = [
        r'<meta[^>]*(?:name="description"|property="og:description")[^>]*content="([^"]*)"',
        r'<meta[^>]*content="([^"]*)"[^>]*(?:name="description"|property="og:description")'
    ]
    
    for pattern in meta_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        for meta_content in matches:
            bedroom_count = extract_from_title_advanced(meta_content)
            if bedroom_count is not None:
                return bedroom_count
    
    return 1

def extract_from_title_advanced(title: str) -> int:
    """Извлечение количества спален из заголовка"""
    title_lower = title.lower()
    
    print(f"   🔍 Анализируем: {title_lower}")
    
    # Специальная обработка для Studio
    if 'studio' in title_lower or 'bedsit' in title_lower:
        print("   ✅ Найдено: Studio (0 спален)")
        return 0
    
    # Паттерны для заголовков daft.ie (в порядке приоритета)
    title_patterns = [
        (r'(\d+)\s+double\s+bedroom', "Double Bedroom"),
        (r'(\d+)\s+single\s+bedroom', "Single Bedroom"),
        (r'(\d+)\s+twin\s+bedroom', "Twin Bedroom"),
        (r'(\d+)\s+bedroom(?!s)', "Bedroom (singular)"),
        (r'(\d+)\s+bed\s+(?:apartment|house|flat|property)', "Bed + type"),
        (r'(\d+)-bed\s+(?:apartment|house|flat|property)', "X-bed + type"),
        (r'(\d+)-bedroom', "X-bedroom"),
    ]
    
    for pattern, description in title_patterns:
        matches = re.findall(pattern, title_lower)
        if matches:
            try:
                bedroom_count = int(matches[0])
                print(f"   ✅ Найдено: {description} = {bedroom_count}")
                # Разумные пределы (от 0 до 10 спален)
                if 0 <= bedroom_count <= 10:
                    return bedroom_count
            except ValueError:
                continue
    
    print("   ❌ Паттерны не найдены")
    return None

if __name__ == "__main__":
    asyncio.run(check_specific_property())
