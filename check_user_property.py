#!/usr/bin/env python3
"""
Проверка конкретного объявления с 3 спальнями за €2500
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def check_user_property():
    """Проверяем объявление предоставленное пользователем"""
    
    # URL от пользователя
    url = "http://www.daft.ie/for-rent/house-28-cabra-drive-dublin-7-north-circular-road-dublin-7/6193753"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    print("🔍 Проверяем объявление от пользователя:")
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
                    
                    # Анализируем спальни нашим методом
                    bedrooms = extract_bedrooms_from_title(title)
                    print(f"🛏️ Определено спален нашим парсером: {bedrooms}")
                    
                    # Ищем цену
                    price_elements = soup.find_all(string=lambda text: text and '€' in text and ('month' in text or 'per' in text))
                    if price_elements:
                        for price_text in price_elements[:3]:  # Первые 3 варианта
                            print(f"💰 Найденная цена: {price_text.strip()}")
                    
                    # Ищем информацию о спальнях в тексте
                    page_text = soup.get_text().lower()
                    
                    bedroom_indicators = [
                        'bedroom', 'double bedroom', 'single bedroom', 'twin bedroom',
                        'bed ', ' bed', 'beds'
                    ]
                    
                    print(f"\n🔍 Поиск упоминаний спален в тексте:")
                    for indicator in bedroom_indicators:
                        if indicator in page_text:
                            # Ищем контекст вокруг
                            import re
                            pattern = rf'.{{0,20}}{re.escape(indicator)}.{{0,20}}'
                            matches = re.findall(pattern, page_text)
                            if matches:
                                print(f"   ✅ '{indicator}': {matches[0]}")
                    
                    # Проверяем мета-данные
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        print(f"\n📋 Meta description: {meta_desc.get('content')}")
                        meta_bedrooms = extract_bedrooms_from_title(meta_desc.get('content', ''))
                        print(f"🛏️ Спальни из meta: {meta_bedrooms}")
                    
                elif response.status == 404:
                    print("❌ Объявление больше не доступно (404)")
                else:
                    print(f"❌ Ошибка доступа: {response.status}")
                    
        except Exception as e:
            print(f"❌ Исключение: {e}")

def extract_bedrooms_from_title(title: str) -> int:
    """Наша функция извлечения спален"""
    if not title:
        return 0
        
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
    
    print("   ❌ Паттерны не найдены в заголовке")
    return 0

if __name__ == "__main__":
    asyncio.run(check_user_property())
