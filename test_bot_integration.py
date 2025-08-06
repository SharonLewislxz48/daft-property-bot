#!/usr/bin/env python3
"""
Тест интеграции парсера с ботом
"""

import asyncio
import sys
import logging
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from production_parser import ProductionDaftParser

async def test_bot_integration():
    """Тестирует интеграцию парсера с ботом точно как в боте"""
    
    print("🤖 ТЕСТ ИНТЕГРАЦИИ С БОТОМ")
    print("=" * 50)
    
    # Настройки пользователя как в боте
    user_settings = {
        "regions": ["dublin-city"],
        "min_bedrooms": 3,
        "max_price": 2500,
        "max_results_per_search": 10
    }
    
    print(f"📊 Настройки пользователя:")
    print(f"   🏠 Регионы: {user_settings['regions']}")
    print(f"   🛏️ Мин. спален: {user_settings['min_bedrooms']}")
    print(f"   💰 Макс. цена: €{user_settings['max_price']}")
    print(f"   📋 Макс. результатов: {user_settings['max_results_per_search']}")
    
    # Создаем парсер как в боте (без context manager)
    parser = ProductionDaftParser()
    
    try:
        print("\n🔍 Выполняем поиск как в боте...")
        
        all_results = []
        
        # Поиск по каждому региону как в боте
        for region in user_settings["regions"]:
            print(f"   📍 Поиск в регионе: {region}")
            
            # Вызов точно как в боте
            region_results = await parser.search_properties(
                min_bedrooms=user_settings["min_bedrooms"],
                max_price=user_settings["max_price"],
                location=region,
                limit=user_settings["max_results_per_search"] // len(user_settings["regions"])
            )
            
            print(f"   ✅ Найдено в {region}: {len(region_results)} объявлений")
            all_results.extend(region_results)
        
        print(f"\n📊 ИТОГО НАЙДЕНО: {len(all_results)} объявлений")
        
        if all_results:
            print("\n📋 Первые 3 объявления:")
            for i, result in enumerate(all_results[:3], 1):
                print(f"  {i}. {result['title']}")
                print(f"     💰 €{result['price']}/мес | 🛏️ {result['bedrooms']} спален")
                print(f"     🔗 {result['url']}")
                print()
            
            print("🎯 РЕЗУЛЬТАТ: Бот будет показывать результаты вместо '0 объявлений'!")
            return True
        else:
            print("❌ ПРОБЛЕМА: Не найдено объявлений")
            return False
            
    except Exception as e:
        print(f"❌ ОШИБКА ИНТЕГРАЦИИ: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance():
    """Тест производительности поиска"""
    print("\n⚡ ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 30)
    
    import time
    
    parser = ProductionDaftParser()
    
    start_time = time.time()
    results = await parser.search_properties(
        min_bedrooms=3,
        max_price=2500,
        location='dublin-city',
        limit=5,
        max_pages=1
    )
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"⏱️ Время поиска: {duration:.2f} секунд")
    print(f"📊 Найдено: {len(results)} объявлений")
    print(f"🚀 Скорость: {len(results)/duration:.1f} объявлений/сек")
    
    if duration < 10:  # Должно работать быстро
        print("✅ Производительность хорошая")
        return True
    else:
        print("⚠️ Производительность медленная")
        return False

async def main():
    """Основная функция тестирования"""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Тест интеграции
    integration_ok = await test_bot_integration()
    
    # Тест производительности
    performance_ok = await test_performance()
    
    print("\n" + "=" * 50)
    print("🏁 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    if integration_ok and performance_ok:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
        print("🚀 Парсер готов к интеграции с ботом")
        print("📊 Проблема '0 объявлений' будет решена")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ")
        if not integration_ok:
            print("   🔧 Нужно исправить интеграцию")
        if not performance_ok:
            print("   ⚡ Нужно улучшить производительность")

if __name__ == "__main__":
    asyncio.run(main())
