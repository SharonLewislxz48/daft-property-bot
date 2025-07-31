#!/usr/bin/env python3
"""
Тест с мягкими фильтрами
"""
import asyncio
import sys
import os
import logging

# Добавляем путь к проекту
sys.path.append('/home/barss/PycharmProjects/daftparser')

from parser.daft_parser import DaftParser
from parser.models import SearchFilters

async def test_with_soft_filters():
    print('🔍 Тестируем с МЯГКИМИ фильтрами...')
    print('=' * 50)
    
    logging.basicConfig(level=logging.INFO)
    
    # Создаём более мягкие фильтры
    filters = SearchFilters(
        city='Dublin',
        max_price=4000,  # Увеличиваем лимит цены
        min_bedrooms=1,  # Уменьшаем минимум спален
        areas=None
    )
    
    async with DaftParser() as parser:
        try:
            print(f"🔍 Фильтры: max_price={filters.max_price}, min_bedrooms={filters.min_bedrooms}")
            
            properties = await parser.search_properties(filters)
            
            if properties:
                print(f'🎉 УСПЕХ! Найдено {len(properties)} объявлений:')
                print()
                
                for i, prop in enumerate(properties[:5], 1):
                    print(f'{i}. 🏠 {prop.title}')
                    print(f'   💰 €{prop.price:,}/month')
                    print(f'   📍 {prop.address}')
                    print(f'   🛏️ {prop.bedrooms} спален')
                    print(f'   🔗 {prop.url}')
                    print()
                
                # Теперь протестируем с более строгими фильтрами
                print("\n🔧 Теперь тестируем с фильтрами: max_price=2500, min_bedrooms=3")
                
                strict_filters = SearchFilters(
                    city='Dublin',
                    max_price=2500,
                    min_bedrooms=3,
                    areas=None
                )
                
                strict_properties = await parser.search_properties(strict_filters)
                
                if strict_properties:
                    print(f'✅ С строгими фильтрами найдено: {len(strict_properties)} объявлений')
                    
                    for i, prop in enumerate(strict_properties[:3], 1):
                        print(f'  {i}. {prop.title} - €{prop.price:,} - {prop.bedrooms} спален')
                else:
                    print('⚠️ С строгими фильтрами ничего не найдено')
                    print('📊 Анализ всех объявлений:')
                    
                    for prop in properties:
                        fits_price = prop.price <= 2500
                        fits_beds = prop.bedrooms >= 3
                        
                        print(f'  • {prop.title[:50]}...')
                        print(f'    Цена: €{prop.price:,} {"✅" if fits_price else "❌"} (лимит €2500)')
                        print(f'    Спальни: {prop.bedrooms} {"✅" if fits_beds else "❌"} (мин. 3)')
                        print()
                
                return True
            else:
                print('❌ Даже с мягкими фильтрами ничего не найдено')
                return False
                
        except Exception as e:
            print(f'❌ Ошибка: {e}')
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_with_soft_filters())
