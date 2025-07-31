#!/usr/bin/env python3
"""
Тестирование с разными фильтрами для поиска 3+ спальных квартир
"""

import asyncio
from parser.daft_parser import DaftParser
from parser.models import SearchFilters

async def test_different_filters():
    """Тестируем различные фильтры"""
    
    parser = DaftParser()
    
    # Тест 1: Ищем 3+ спальни без ограничения по цене
    print("🔍 ТЕСТ 1: 3+ спальни, любая цена")
    print("="*50)
    
    filters = SearchFilters(
        city="Dublin",
        max_price=None,  # Без ограничений по цене
        min_bedrooms=3
    )
    
    properties = await parser.search_properties(filters)
    print(f"✅ Найдено {len(properties)} объявлений с 3+ спальнями")
    
    for i, prop in enumerate(properties[:5], 1):  # Показываем первые 5
        print(f"{i}. 🏠 {prop.title}")
        print(f"   💰 €{prop.price:,}/month")
        print(f"   🛏️ {prop.bedrooms} спален")
        print(f"   🔗 {prop.url}")
        print()
    
    if len(properties) > 5:
        print(f"... и ещё {len(properties) - 5} объявлений")
    
    print("\n" + "="*70)
    
    # Тест 2: Ищем 3+ спальни до €4000
    print("🔍 ТЕСТ 2: 3+ спальни, до €4000")
    print("="*50)
    
    filters.max_price = 4000
    
    properties = await parser.search_properties(filters)
    print(f"✅ Найдено {len(properties)} объявлений (3+ спальни, до €4000)")
    
    for i, prop in enumerate(properties[:10], 1):  # Показываем первые 10
        print(f"{i}. {prop.title[:60]}...")
        print(f"   💰 €{prop.price:,}/month, 🛏️ {prop.bedrooms} спален")
        print()
    
    print("\n" + "="*70)
    
    # Тест 3: Ищем 2+ спальни до €3000 (более реалистично)
    print("🔍 ТЕСТ 3: 2+ спальни, до €3000")
    print("="*50)
    
    filters.min_bedrooms = 2
    filters.max_price = 3000
    
    properties = await parser.search_properties(filters)
    print(f"✅ Найдено {len(properties)} объявлений (2+ спальни, до €3000)")
    
    for i, prop in enumerate(properties[:10], 1):  # Показываем первые 10
        print(f"{i}. {prop.title[:60]}...")
        print(f"   💰 €{prop.price:,}/month, 🛏️ {prop.bedrooms} спален")
        print()
    
    await parser.close()

if __name__ == "__main__":
    asyncio.run(test_different_filters())
