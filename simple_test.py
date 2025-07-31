#!/usr/bin/env python3
"""
Простой тест парсера с базовой страницей
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

async def test_simple_fetch():
    """Простой тест получения страницы"""
    try:
        print("🌐 Тестируем получение базовой страницы daft.ie...")
        
        from parser.daft_parser import DaftParser
        
        async with DaftParser() as parser:
            # Пробуем получить главную страницу
            url = "https://www.daft.ie"
            print(f"   Запрашиваем: {url}")
            
            html = await parser._fetch_page(url)
            
            if html:
                print(f"✅ Успешно! Размер страницы: {len(html)} символов")
                
                # Проверяем содержимое
                if "daft" in html.lower():
                    print("✅ Содержимое корректное (найден текст 'daft')")
                else:
                    print("⚠️ Содержимое может быть некорректным")
                    
                # Попробуем простую страницу поиска
                search_url = "https://www.daft.ie/property-for-rent"
                print(f"\n   Запрашиваем страницу поиска: {search_url}")
                
                search_html = await parser._fetch_page(search_url)
                if search_html:
                    print(f"✅ Страница поиска получена: {len(search_html)} символов")
                    
                    # Ищем элементы объявлений
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(search_html, 'html.parser')
                    
                    # Ищем ссылки на объявления
                    links = soup.find_all("a", href=True)
                    property_links = [link for link in links if "for-rent" in str(link.get("href", ""))]
                    
                    print(f"✅ Найдено ссылок на объявления: {len(property_links)}")
                    
                    if property_links:
                        print("   Первые 3 ссылки:")
                        for i, link in enumerate(property_links[:3], 1):
                            href = link.get("href", "")
                            text = link.get_text(strip=True)[:50]
                            print(f"   {i}. {text}... -> {href}")
                else:
                    print("❌ Не удалось получить страницу поиска")
            else:
                print("❌ Не удалось получить главную страницу")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_fetch())
