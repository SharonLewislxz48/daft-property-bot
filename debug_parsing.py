#!/usr/bin/env python3
"""
Тестирование парсинга на конкретном объявлении из найденных
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_parsing_issue():
    """Тестируем проблемное объявление"""
    
    # Объявление которое показывает неправильное количество спален
    url = "https://www.daft.ie/for-rent/apartment-2-bed-oneill-court-main-street-belmayne-dublin-13/5987931"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    print("🔍 Анализируем проблемное объявление:")
    print(f"🔗 {url}")
    print("📝 Ожидаем: 2 спальни (из названия '2 Bed')")
    print("❌ Парсер показал: 1 спальня")
    print("="*80)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Получаем заголовок
                    title_elem = soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else "No title"
                    print(f"📄 Заголовок: {title}")
                    
                    # Тестируем наш парсинг
                    bedrooms = test_bedroom_parsing(title, content)
                    print(f"🛏️ Наш парсер определил: {bedrooms} спален")
                    
                    # Проверяем meta description
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        meta_content = meta_desc.get('content', '')
                        print(f"📋 Meta description: {meta_content}")
                        meta_bedrooms = test_bedroom_parsing_title_only(meta_content)
                        print(f"🛏️ Спальни из meta: {meta_bedrooms}")
                        
                else:
                    print(f"❌ Ошибка доступа: {response.status}")
                    
        except Exception as e:
            print(f"❌ Исключение: {e}")

def test_bedroom_parsing(title: str, page_text: str) -> int:
    """Тестируем наш метод парсинга"""
    
    # Сначала заголовок
    bedroom_count = test_bedroom_parsing_title_only(title)
    if bedroom_count is not None:
        print(f"   ✅ Найдено в заголовке: {bedroom_count}")
        return bedroom_count
    
    # Потом meta
    import re
    meta_patterns = [
        r'<meta[^>]*(?:name="description"|property="og:description")[^>]*content="([^"]*)"',
        r'<meta[^>]*content="([^"]*)"[^>]*(?:name="description"|property="og:description")'
    ]
    
    for pattern in meta_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        for meta_content in matches:
            bedroom_count = test_bedroom_parsing_title_only(meta_content)
            if bedroom_count is not None:
                print(f"   ✅ Найдено в meta: {bedroom_count}")
                return bedroom_count
    
    print(f"   ❌ Ничего не найдено, возвращаем 1")
    return 1

def test_bedroom_parsing_title_only(title: str) -> int:
    """Парсинг только заголовка"""
    import re
    
    if not title:
        return None
        
    title_lower = title.lower()
    print(f"   🔍 Анализируем: '{title_lower}'")
    
    # Специальная обработка для Studio
    if 'studio' in title_lower or 'bedsit' in title_lower:
        print("   ✅ Найдено: Studio (0 спален)")
        return 0
    
    # Наши паттерны (обновленные)
    title_patterns = [
        (r'(\d+)\s+double\s+bedroom', "Double Bedroom"),
        (r'(\d+)\s+single\s+bedroom', "Single Bedroom"),
        (r'(\d+)\s+twin\s+bedroom', "Twin Bedroom"),
        (r'(\d+)\s+bedroom(?!s)', "Bedroom (singular)"),
        (r'(\d+)\s+bed\s+(?:apartment|house|flat|property)', "Bed + type"),
        (r'(\d+)-bed\s+(?:apartment|house|flat|property)', "X-bed + type"),
        (r'(\d+)\s+bed\s+house', "Bed House"),
        (r'(\d+)\s+bed(?:\s|$|,)', "Bed (end or space)"),  # НОВЫЙ ПАТТЕРН
        (r'(\d+)-bedroom', "X-bedroom"),
    ]
    
    for pattern, description in title_patterns:
        matches = re.findall(pattern, title_lower)
        if matches:
            try:
                bedroom_count = int(matches[0])
                print(f"   ✅ Найдено: {description} = {bedroom_count}")
                if 0 <= bedroom_count <= 10:
                    return bedroom_count
            except ValueError:
                continue
    
    print("   ❌ Паттерны не найдены")
    return None

if __name__ == "__main__":
    asyncio.run(test_parsing_issue())
