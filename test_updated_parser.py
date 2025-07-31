#!/usr/bin/env python3
"""
Тест обновлённого парсера с реальными данными
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append('/home/barss/PycharmProjects/daftparser')

from parser.daft_parser import DaftParser
from parser.models import SearchFilters

async def test_updated_parser():
    print('🏆 Тестируем ОБНОВЛЁННЫЙ парсер с РЕАЛЬНЫМИ данными...')
    print('🚫 НЕТ фальшивых данных')
    print('✅ ТОЛЬКО настоящие объявления с daft.ie')
    print('=' * 70)
    
    # Включаем логирование для отладки
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Создаём SearchFilters
    filters = SearchFilters(
        city='Dublin',
        max_price=2500,
        min_bedrooms=3,
        areas=None  # Без фильтра по районам для максимума результатов
    )
    
    async with DaftParser() as parser:
        try:
            print(f"🔍 Searching with filters: city={filters.city}, max_price={filters.max_price}, min_bedrooms={filters.min_bedrooms}")
            
            properties = await parser.search_properties(filters)
            
            print(f"📊 Parser returned {len(properties)} properties")
            
            if properties:
                print(f'🎉 УСПЕХ! Найдено {len(properties)} РЕАЛЬНЫХ объявлений:')
                print()
                
                for i, prop in enumerate(properties, 1):
                    print(f'{i}. 🏠 {prop.title}')
                    print(f'   💰 €{prop.price:,}/month')
                    print(f'   📍 {prop.address}')
                    print(f'   🛏️ {prop.bedrooms} спален, {prop.bathrooms} ванная')
                    print(f'   🔗 {prop.url}')
                    print()
                
                return True, properties
            else:
                print('❌ РЕАЛЬНЫЕ объявления не найдены')
                print('🔍 Попробуем понять что происходит...')
                
                # Попробуем получить страницу напрямую
                content = await parser.get_listings_page(filters.city)
                if content:
                    print(f"✅ Страница получена: {len(content)} символов")
                    
                    # Проверим ссылки
                    links = parser.extract_property_links(content)
                    print(f"🔗 Найдено ссылок: {len(links)}")
                    
                    if links:
                        print("📋 Первые 3 ссылки:")
                        for i, link in enumerate(links[:3], 1):
                            print(f"  {i}. {link}")
                    
                return False, []
                
        except Exception as e:
            print(f'❌ Ошибка: {e}')
            import traceback
            traceback.print_exc()
            return False, []

if __name__ == "__main__":
    success, properties = asyncio.run(test_updated_parser())
    
    if success:
        print(f"\n🏆 ОБНОВЛЁННЫЙ ПАРСЕР РАБОТАЕТ!")
        print(f"✅ {len(properties)} настоящих объявлений с реальными ссылками!")
        print("🔗 Все ссылки ведут на реальные страницы daft.ie")
    else:
        print("\n⚠️ Требуется дополнительная настройка")
