#!/usr/bin/env python3

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append('/home/barss/PycharmProjects/daftparser')

from parser.playwright_parser import PlaywrightDaftParser
from parser.models import SearchFilters

async def test_updated_parser():
    """Тестирование обновленного парсера с JSON подходом"""
    
    # Создаем фильтры поиска
    filters = SearchFilters(
        city='Dublin City',
        max_price=2500,
        min_bedrooms=3,
        areas=[]
    )
    
    # Создаем и тестируем парсер
    async with PlaywrightDaftParser() as parser:
        print("🔍 Запуск поиска с обновленным JSON парсером...")
        print(f"📋 Параметры: город={filters.city}, макс. цена={filters.max_price}, мин. спален={filters.min_bedrooms}")
        
        # Поиск объявлений
        properties = await parser.search_properties(filters, max_pages=2)
        
        print(f"\n✅ Поиск завершен!")
        print(f"📊 Найдено объявлений: {len(properties)}")
        
        # Показываем результаты
        for i, prop in enumerate(properties[:10], 1):  # Показываем первые 10
            print(f"\n{i}. {prop.title}")
            print(f"   💰 Цена: €{prop.price}/месяц")
            print(f"   🛏️ Спальни: {prop.bedrooms}")
            print(f"   📍 Адрес: {prop.address}")
            print(f"   🔗 URL: {prop.url}")
            if hasattr(prop, 'area') and prop.area:
                print(f"   � Район: {prop.area}")
        
        if len(properties) > 10:
            print(f"\n... и еще {len(properties) - 10} объявлений")
        
        # Статистика
        if properties:
            avg_price = sum(p.price for p in properties if p.price) / len([p for p in properties if p.price])
            avg_bedrooms = sum(p.bedrooms for p in properties) / len(properties)
            print(f"\n📈 Статистика:")
            print(f"   Средняя цена: €{avg_price:.0f}/месяц")
            print(f"   Среднее количество спален: {avg_bedrooms:.1f}")

if __name__ == "__main__":
    asyncio.run(test_updated_parser())
