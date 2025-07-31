#!/usr/bin/env python3
"""
Тест Playwright парсера
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

async def test_playwright_parser():
    """Тест Playwright парсера"""
    try:
        print("🎭 Тестируем Playwright парсер...")
        
        from parser.playwright_parser import PlaywrightDaftParser
        from parser.models import SearchFilters
        
        # Создаем фильтры
        filters = SearchFilters(
            city="Dublin",
            max_price=3000,  # Увеличиваем лимит для тестирования
            min_bedrooms=2,  # Уменьшаем для большего количества результатов
            areas=["Dublin 1", "Dublin 2"]
        )
        
        print(f"✅ Фильтры: {filters}")
        
        async with PlaywrightDaftParser() as parser:
            print("✅ Playwright парсер инициализирован")
            
            # Пробуем получить базовую страницу поиска
            base_url = "https://www.daft.ie/property-for-rent/dublin"
            print(f"🌐 Тестируем доступ к: {base_url}")
            
            content = await parser._get_page_content(base_url)
            
            if content:
                print(f"✅ Страница загружена! Размер: {len(content)} символов")
                
                # Проверяем содержимое
                if "dublin" in content.lower() and "rent" in content.lower():
                    print("✅ Содержимое корректное")
                    
                    # Пробуем поиск объявлений
                    print("🔍 Запускаем поиск объявлений...")
                    properties = await parser.search_properties(filters, max_pages=1)
                    
                    print(f"✅ Найдено объявлений: {len(properties)}")
                    
                    if properties:
                        print("\n📋 Первые 3 объявления:")
                        for i, prop in enumerate(properties[:3], 1):
                            print(f"   {i}. {prop.title}")
                            print(f"      💰 {prop.format_price()}")
                            print(f"      🛏️ {prop.format_bedrooms()}")
                            print(f"      📍 {prop.address}")
                            print(f"      🔗 {prop.url}")
                            print()
                    else:
                        print("   ℹ️ Объявления не найдены или не соответствуют фильтрам")
                        print("   💡 Попробуйте изменить фильтры (увеличить цену, уменьшить спальни)")
                else:
                    print("⚠️ Содержимое может быть некорректным")
            else:
                print("❌ Не удалось загрузить страницу")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_playwright_parser())
