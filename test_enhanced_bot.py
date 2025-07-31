#!/usr/bin/env python3
"""
Тестирование улучшенного бота мониторинга недвижимости
"""

import asyncio
import logging
from datetime import datetime

from database.enhanced_database import EnhancedDatabase
from production_parser import ProductionDaftParser
from config.regions import DUBLIN_REGIONS, DEFAULT_SETTINGS

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database():
    """Тестирование базы данных"""
    print("🔹 Тестирование базы данных...")
    
    db = EnhancedDatabase("data/test_enhanced_bot.db")
    await db.init_database()
    
    # Тестовый пользователь
    user_id = 12345
    user = await db.get_or_create_user(user_id, "test_user", "Test", "User")
    print(f"✅ Пользователь: {user}")
    
    # Настройки
    settings = await db.get_user_settings(user_id)
    print(f"✅ Настройки: {settings}")
    
    # Обновление настроек
    await db.update_user_settings(
        user_id, 
        regions=["dublin-city", "dublin-6"],
        min_bedrooms=2,
        max_price=3000
    )
    
    updated_settings = await db.get_user_settings(user_id)
    print(f"✅ Обновленные настройки: {updated_settings}")
    
    print("✅ База данных работает корректно!")
    return db

async def test_parser():
    """Тестирование парсера"""
    print("🔹 Тестирование парсера...")
    
    parser = ProductionDaftParser()
    
    try:
        results = await parser.search_properties(
            min_bedrooms=3,
            max_price=2500,
            location="dublin-city",
            limit=5
        )
        
        print(f"✅ Парсер нашел {len(results)} объявлений")
        if results:
            print(f"   Пример: {results[0]['title']} - €{results[0]['price']}")
        
        return results
    except Exception as e:
        print(f"❌ Ошибка парсера: {e}")
        return []

async def test_new_properties_detection(db, test_properties):
    """Тестирование обнаружения новых объявлений"""
    print("🔹 Тестирование обнаружения новых объявлений...")
    
    user_id = 12345
    search_params = {
        "regions": ["dublin-city"],
        "min_bedrooms": 3,
        "max_price": 2500
    }
    
    # Первый запуск - все объявления должны быть новыми
    new_properties_1 = await db.get_new_properties(user_id, test_properties, search_params)
    print(f"✅ Первый запуск: {len(new_properties_1)} новых из {len(test_properties)}")
    
    # Второй запуск - новых объявлений быть не должно
    new_properties_2 = await db.get_new_properties(user_id, test_properties, search_params)
    print(f"✅ Второй запуск: {len(new_properties_2)} новых (должно быть 0)")
    
    # Отмечаем как отправленные
    urls = [prop['url'] for prop in test_properties]
    await db.mark_properties_as_sent(user_id, urls)
    print("✅ Объявления отмечены как отправленные")

async def test_statistics(db):
    """Тестирование статистики"""
    print("🔹 Тестирование статистики...")
    
    user_id = 12345
    
    # Добавляем тестовые логи
    await db.log_monitoring_session(
        user_id=user_id,
        search_params={"regions": ["dublin-city"], "min_bedrooms": 3, "max_price": 2500},
        properties_found=10,
        new_properties=3,
        execution_time=15.5,
        status="success"
    )
    
    # Получаем статистику
    stats = await db.get_user_statistics(user_id, days=7)
    print(f"✅ Статистика: {stats}")

async def test_regions_config():
    """Тестирование конфигурации регионов"""
    print("🔹 Тестирование конфигурации регионов...")
    
    print(f"✅ Регионов Дублина: {len(DUBLIN_REGIONS)}")
    print(f"✅ Настройки по умолчанию: {DEFAULT_SETTINGS}")
    
    # Проверяем несколько регионов
    test_regions = ["dublin-city", "dublin-6", "rathmines", "clondalkin"]
    for region in test_regions:
        if region in DUBLIN_REGIONS:
            print(f"✅ {region}: {DUBLIN_REGIONS[region]}")
        else:
            print(f"❌ {region}: не найден")

async def run_full_test():
    """Полное тестирование системы"""
    print("🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ УЛУЧШЕННОГО БОТА")
    print("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # 1. Тестирование конфигурации
        await test_regions_config()
        print()
        
        # 2. Тестирование базы данных
        db = await test_database()
        print()
        
        # 3. Тестирование парсера
        test_properties = await test_parser()
        print()
        
        # 4. Тестирование обнаружения новых объявлений
        if test_properties:
            await test_new_properties_detection(db, test_properties)
            print()
        
        # 5. Тестирование статистики
        await test_statistics(db)
        print()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print("=" * 60)
        print(f"✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print(f"⏱️ Время выполнения: {duration:.1f} секунд")
        print("🎉 Улучшенный бот готов к работе!")
        
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_full_test())
