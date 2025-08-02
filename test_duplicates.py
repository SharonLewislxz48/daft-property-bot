#!/usr/bin/env python3
"""
Тест проверки дубликатов в парсере и базе данных
"""

import asyncio
import sys
import os

# Добавляем корневую папку в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from production_parser import ProductionDaftParser
from database.enhanced_database import EnhancedDatabase

async def test_duplicate_removal():
    """Тестируем удаление дубликатов на всех уровнях"""
    
    print("🧪 ТЕСТ УДАЛЕНИЯ ДУБЛИКАТОВ")
    print("=" * 50)
    
    # Создаем тестовые данные с дубликатами
    test_properties = [
        {
            "url": "https://www.daft.ie/for-rent/house-1-test-street-dublin/123456",
            "title": "1 Test Street, Dublin",
            "price": 2000,
            "bedrooms": 3,
            "location": "Dublin",
            "property_type": "House"
        },
        {
            "url": "https://www.daft.ie/for-rent/house-1-test-street-dublin/123456",  # Дубликат по URL
            "title": "1 Test Street, Dublin", 
            "price": 2000,
            "bedrooms": 3,
            "location": "Dublin",
            "property_type": "House"
        },
        {
            "url": "https://www.daft.ie/for-rent/house-2-test-street-dublin/123457",
            "title": "2 Test Street, Dublin",
            "price": 2100,
            "bedrooms": 3,
            "location": "Dublin",
            "property_type": "House"
        },
        {
            # Дубликат по характеристикам (нет URL)
            "title": "2 Test Street, Dublin",
            "price": 2100,
            "bedrooms": 3,
            "location": "Dublin",
            "property_type": "House"
        },
        {
            "url": "https://www.daft.ie/for-rent/house-3-test-street-dublin/123458",
            "title": "3 Test Street, Dublin",
            "price": 2200,
            "bedrooms": 4,
            "location": "Dublin",
            "property_type": "House"
        }
    ]
    
    print(f"📊 Тестовых объявлений: {len(test_properties)}")
    print("   - 2 дубликата по URL")
    print("   - 1 дубликат по характеристикам")
    print("   - Ожидаем: 3 уникальных\n")
    
    # Тест 1: Удаление дубликатов в парсере
    print("🔧 ТЕСТ 1: Удаление дубликатов в парсере")
    parser = ProductionDaftParser()
    unique_properties = parser._remove_duplicates(test_properties)
    
    print(f"✅ Результат: {len(unique_properties)} уникальных объявлений")
    
    for i, prop in enumerate(unique_properties, 1):
        print(f"   {i}. {prop['title']} - €{prop['price']} - {prop['bedrooms']} спален")
    
    # Тест 2: Проверка в базе данных
    print("\n🗄️ ТЕСТ 2: Фильтрация в базе данных")
    
    db = EnhancedDatabase("data/test_duplicates.db")
    await db.init_database()
    
    # Добавляем объявления в базу как будто они были найдены ранее
    test_user_id = 12345
    search_params = {"min_bedrooms": 3, "max_price": 2500, "regions": ["dublin-city"]}
    
    # Добавляем первое объявление в историю
    await db.add_property_to_history(test_user_id, unique_properties[0], search_params)
    
    # Проверяем фильтрацию недавних дубликатов
    filtered_properties = await db.filter_recent_duplicates(unique_properties, hours=24)
    
    print(f"✅ После фильтрации глобальных дубликатов: {len(filtered_properties)} объявлений")
    
    # Проверяем новые объявления для пользователя
    new_properties = await db.get_new_properties(test_user_id, filtered_properties, search_params)
    
    print(f"✅ Новых объявлений для пользователя: {len(new_properties)} объявлений")
    
    print("\n📋 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
    for i, prop in enumerate(new_properties, 1):
        print(f"   {i}. {prop['title']} - €{prop['price']} - {prop['bedrooms']} спален")
    
    print(f"\n🎯 ИТОГО: Из {len(test_properties)} исходных объявлений получили {len(new_properties)} уникальных и новых")
    
    # Очистка тестовой базы
    import os
    if os.path.exists("data/test_duplicates.db"):
        os.remove("data/test_duplicates.db")
        print("🧹 Тестовая база данных очищена")

if __name__ == "__main__":
    asyncio.run(test_duplicate_removal())
