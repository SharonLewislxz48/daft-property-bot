#!/usr/bin/env python3
"""
Быстрый тест парсера без лишних импортов
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append('/home/barss/PycharmProjects/daftparser')

async def test_parser_direct():
    print('🔍 Прямой тест парсера с обходом блокировки...')
    print('=' * 60)
    
    # Прямой импорт без лишних зависимостей
    from parser.final_daft_parser import FinalDaftParser
    
    parser = FinalDaftParser()
    
    try:
        properties = await parser.search_with_bypass("Dublin", 2500, 3)
        print(f'✅ УСПЕХ! Найдено {len(properties)} объявлений!')
        print()
        
        for i, prop in enumerate(properties[:5], 1):
            print(f'{i}. 🏠 {prop["title"]}')
            print(f'   💰 {prop["price"]}')
            print(f'   📍 {prop["address"]}')
            print(f'   🛏️ {prop.get("bedrooms", "?")} спален')
            print(f'   🔗 {prop["url"][:70]}...')
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
    success = asyncio.run(test_parser_direct())
    
    if success:
        print("🎉 ПАРСЕР С ОБХОДОМ БЛОКИРОВКИ РАБОТАЕТ!")
        print("📋 Теперь интегрируем его в основной бот...")
    else:
        print("⚠️ Проблемы с парсером")
