#!/usr/bin/env python3
"""
Тест нового парсера с обходом блокировки
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append('/home/barss/PycharmProjects/daftparser')

from parser.daft_parser import DaftParser
from parser.models import SearchFilters

async def test_new_parser():
    print('🔍 Тестируем новый парсер с обходом блокировки...')
    print('=' * 60)
    
    parser = DaftParser()
    
    filters = SearchFilters(
        city='Dublin',
        max_price=2500,
        min_bedrooms=3,
        areas=['Temple Bar', 'Grafton Street']
    )
    
    try:
        properties = await parser.search_properties(filters)
        print(f'✅ УСПЕХ! Найдено {len(properties)} объявлений!')
        print()
        
        for i, prop in enumerate(properties[:5], 1):
            print(f'{i}. 🏠 {prop.title}')
            print(f'   💰 {prop.price}')
            print(f'   📍 {prop.address}')
            print(f'   🛏️ {prop.bedrooms} спален')
            print(f'   🔗 {prop.url[:70]}...')
            print()
            
        return True
        
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await parser.close()

if __name__ == "__main__":
    success = asyncio.run(test_new_parser())
    
    if success:
        print("🎉 НОВЫЙ ПАРСЕР РАБОТАЕТ! Теперь бот использует реальные данные!")
    else:
        print("⚠️ Проблемы с новым парсером")
