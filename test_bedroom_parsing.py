#!/usr/bin/env python3
"""
Тестирование парсинга спален для исправления проблемы с определением количества
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def test_bedroom_parsing():
    """Тестирование парсинга количества спален на реальных данных"""
    
    test_urls = [
        "https://www.daft.ie/for-rent/apartment-1-bedroom-apartment-marshall-yards-east-road-dublin-3/6141962",
        "https://www.daft.ie/for-rent/apartment-2-bed-apartment-eglinton-place-eglinton-road-dublin-4/5811438",
        "https://www.daft.ie/for-rent/apartment-2-bedroom-apartment-occu-hayfield-churchview-road-killiney-co-dublin/5900743"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for url in test_urls:
            print(f"\n{'='*60}")
            print(f"🔍 Тестируем: {url}")
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Получаем заголовок
                        title_elem = soup.find('title')
                        title = title_elem.get_text().strip() if title_elem else "No title"
                        print(f"📄 Заголовок: {title}")
                        
                        # Анализируем содержимое страницы
                        analyze_bedroom_content(title, soup)
                        
                    else:
                        print(f"❌ Ошибка: {response.status}")
                        
            except Exception as e:
                print(f"❌ Исключение: {e}")

def analyze_bedroom_content(title: str, soup: BeautifulSoup):
    """Анализируем контент страницы для определения спален"""
    
    # Получаем весь текст страницы
    page_text = soup.get_text()
    
    print(f"\n🔍 Анализ заголовка:")
    extract_bedrooms_from_title(title)
    
    print(f"\n🔍 Поиск в тексте страницы:")
    search_bedroom_patterns(page_text)
    
    print(f"\n🔍 Поиск в структурированных данных:")
    search_structured_data(soup)

def extract_bedrooms_from_title(title: str) -> int:
    """Извлекаем количество спален из заголовка"""
    
    title_lower = title.lower()
    print(f"   Заголовок (lower): {title_lower}")
    
    # Паттерны специально для заголовков daft.ie
    title_patterns = [
        (r'(\d+)\s+double\s+bedroom', "Double Bedroom"),
        (r'(\d+)\s+single\s+bedroom', "Single Bedroom"),
        (r'(\d+)\s+twin\s+bedroom', "Twin Bedroom"),
        (r'(\d+)\s+bedroom(?!s)', "Bedroom (singular)"),
        (r'(\d+)\s+bed\s+(?:apartment|house|flat)', "Bed + type"),
        (r'(\d+)-bed\s+(?:apartment|house|flat)', "X-bed + type"),
        (r'(\d+)-bedroom', "X-bedroom"),
        (r'studio', "Studio (0 beds)"),
    ]
    
    for pattern, description in title_patterns:
        if pattern == r'studio':
            if 'studio' in title_lower:
                print(f"   ✅ Найдено: {description}")
                return 0
        else:
            matches = re.findall(pattern, title_lower)
            if matches:
                bedroom_count = int(matches[0])
                print(f"   ✅ Найдено: {description} = {bedroom_count}")
                return bedroom_count
    
    print(f"   ❌ Паттерны не найдены в заголовке")
    return -1

def search_bedroom_patterns(page_text: str):
    """Ищем паттерны спален в тексте страницы"""
    
    text_lower = page_text.lower()
    
    # Ключевые фразы для поиска
    bedroom_phrases = [
        "double bedroom",
        "single bedroom", 
        "twin bedroom",
        "master bedroom",
        "en-suite bedroom",
        "bedroom with",
        "large bedroom",
        "spacious bedroom"
    ]
    
    print(f"   Ищем фразы со спальнями:")
    for phrase in bedroom_phrases:
        count = text_lower.count(phrase)
        if count > 0:
            print(f"   ✅ '{phrase}' найдено {count} раз")
    
    # Ищем числовые паттерны
    numeric_patterns = [
        (r'(\d+)\s+double\s+bedroom', "X double bedroom"),
        (r'(\d+)\s+single\s+bedroom', "X single bedroom"),
        (r'(\d+)\s+bedroom', "X bedroom"),
        (r'(\d+)\s+bed\b', "X bed"),
    ]
    
    print(f"\n   Ищем числовые паттерны:")
    for pattern, description in numeric_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            for match in matches:
                print(f"   ✅ {description}: {match}")

def search_structured_data(soup: BeautifulSoup):
    """Ищем структурированные данные о спальнях"""
    
    # Ищем в метатегах
    meta_tags = soup.find_all('meta')
    for meta in meta_tags:
        if meta.get('property') or meta.get('name'):
            content = meta.get('content', '')
            if 'bedroom' in content.lower():
                print(f"   📋 Meta: {meta.get('property') or meta.get('name')} = {content}")
    
    # Ищем в JSON-LD данных
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        if script.string and 'bedroom' in script.string.lower():
            print(f"   📋 JSON-LD содержит 'bedroom'")
    
    # Ищем в классах и ID
    bedroom_elements = soup.find_all(lambda tag: tag.get('class') and 
                                   any('bedroom' in str(cls).lower() for cls in tag.get('class')))
    if bedroom_elements:
        print(f"   📋 Найдено {len(bedroom_elements)} элементов с классом 'bedroom'")
    
    # Ищем в data атрибутах
    data_elements = soup.find_all(lambda tag: any(attr.startswith('data-') and 'bedroom' in attr.lower() 
                                                for attr in tag.attrs.keys()))
    if data_elements:
        print(f"   📋 Найдено {len(data_elements)} элементов с data-bedroom атрибутами")

if __name__ == "__main__":
    asyncio.run(test_bedroom_parsing())
