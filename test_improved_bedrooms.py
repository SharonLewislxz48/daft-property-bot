#!/usr/bin/env python3
"""
Тестирование улучшенного парсинга количества спален
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from parser.daft_parser import DaftParser
from parser.models import SearchFilters

async def test_improved_bedroom_parsing():
    """Тестируем улучшенный парсинг спален"""
    
    print("🔍 Тестируем улучшенный парсинг количества спален...")
    
    # Создаем парсер
    parser = DaftParser()
    
    # Тестируем с более высоким бюджетом для поиска 3+ спален
    test_filters = [
        # Высокий бюджет для поиска больших квартир
        SearchFilters(max_price=4000, min_bedrooms=3, max_bedrooms=5),
        SearchFilters(max_price=3500, min_bedrooms=3, max_bedrooms=4),
        SearchFilters(max_price=5000, min_bedrooms=2, max_bedrooms=5),  # Для сравнения
    ]
    
    for i, filters in enumerate(test_filters, 1):
        print(f"\n--- ТЕСТ {i}: €{filters.max_price}, {filters.min_bedrooms}-{filters.max_bedrooms} спален ---")
        
        try:
            properties = await parser.search_properties(filters)
            
            print(f"✅ Найдено объявлений: {len(properties)}")
            
            if properties:
                # Показываем первые 5 объявлений с детальной информацией
                for j, prop in enumerate(properties[:5], 1):
                    print(f"\n{j}. {prop.title}")
                    print(f"   💰 Цена: €{prop.price}/месяц")
                    print(f"   🛏️ Спален: {prop.bedrooms}")
                    print(f"   🚿 Ванных: {prop.bathrooms}")
                    print(f"   📍 Адрес: {prop.address}")
                    print(f"   🔗 URL: {prop.url}")
                
                # Статистика по спальням
                bedroom_stats = {}
                for prop in properties:
                    bedrooms = prop.bedrooms
                    bedroom_stats[bedrooms] = bedroom_stats.get(bedrooms, 0) + 1
                
                print(f"\n📊 Статистика по спальням:")
                for bedrooms in sorted(bedroom_stats.keys()):
                    count = bedroom_stats[bedrooms]
                    print(f"   {bedrooms} спален: {count} объявлений")
                
                # Проверяем есть ли объявления с 3+ спальнями
                three_plus = [p for p in properties if p.bedrooms >= 3]
                if three_plus:
                    print(f"\n🎯 Найдено {len(three_plus)} объявлений с 3+ спальнями!")
                    for prop in three_plus[:3]:
                        print(f"   - {prop.title} (€{prop.price}, {prop.bedrooms} спален)")
                else:
                    print(f"\n❌ Объявлений с 3+ спальнями не найдено")
            else:
                print("❌ Объявления не найдены")
                
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
    
    print(f"\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_improved_bedroom_parsing())
