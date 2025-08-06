#!/usr/bin/env python3
"""
Быстрый тест восстановленного production_parser.py
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from production_parser import ProductionDaftParser

async def test_production_parser():
    """Тест восстановленного парсера"""
    print("🧪 Тестирование восстановленного production_parser.py...")
    
    try:
        async with ProductionDaftParser() as parser:
            print("✅ Парсер успешно инициализирован")
            
            # Тест поиска с параметрами как в боте
            properties = await parser.search_properties(
                min_bedrooms=3,
                max_price=2500,
                location='dublin-city',
                limit=5,
                max_pages=1
            )
            
            print(f"✅ Найдено {len(properties)} объявлений")
            
            if properties:
                print("\n📋 Примеры найденных объявлений:")
                for i, prop in enumerate(properties[:3], 1):
                    print(f"  {i}. {prop['title']}")
                    print(f"     💰 €{prop['price']}/мес | 🛏️ {prop['bedrooms']} спален")
                    print(f"     🔗 {prop['url']}")
                    print()
                
                print("🎯 РЕЗУЛЬТАТ: Парсер работает корректно - проблема '0 объявлений' решена!")
                return True
            else:
                print("❌ Объявления не найдены")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка при тестировании парсера: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Основная функция"""
    print("🔧 ТЕСТИРОВАНИЕ ВОССТАНОВЛЕННОГО ПАРСЕРА")
    print("=" * 50)
    
    success = await test_production_parser()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО")
        print("📊 Парсер готов к продакшену")
        print("🚀 Можно деплоить исправления")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН")
        print("🔍 Требуется дополнительная отладка")

if __name__ == "__main__":
    asyncio.run(main())
