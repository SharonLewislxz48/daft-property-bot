#!/usr/bin/env python3
"""
Проверка источника данных в системе
"""
import asyncio
import sys
sys.path.append('/home/barss/PycharmProjects/daftparser')

from parser.daft_parser import DaftParser
from parser.demo_parser import DemoParser
from parser.models import SearchFilters

async def check_data_sources():
    """Проверяем, какие источники данных доступны"""
    print("🔍 Проверка источников данных для Daft.ie Bot")
    print("=" * 50)
    
    filters = SearchFilters(
        city="Dublin",
        max_price=3000,
        min_bedrooms=2,
        areas=[]
    )
    
    # 1. Проверяем основной парсер (реальные данные)
    print("\n1️⃣ Тестируем ОСНОВНОЙ парсер (реальные данные с daft.ie):")
    try:
        parser = DaftParser()
        properties = await parser.search_properties(filters)
        if properties:
            print(f"   ✅ РЕАЛЬНЫЕ ДАННЫЕ: найдено {len(properties)} объявлений")
            print("   📋 Пример реального объявления:")
            prop = properties[0]
            print(f"      • {prop.title}")
            print(f"      • {prop.address}")
            print(f"      • {prop.format_price()}")
            print(f"      • URL: {prop.url}")
        else:
            print("   ⚠️ ОСНОВНОЙ ПАРСЕР: объявления не найдены (возможно блокировка)")
    except Exception as e:
        print(f"   ❌ ОСНОВНОЙ ПАРСЕР недоступен: {e}")
        if "403" in str(e) or "blocked" in str(e).lower():
            print("   🛡️ Причина: Сайт daft.ie блокирует автоматические запросы")
    
    # 2. Проверяем демо-парсер (тестовые данные)
    print("\n2️⃣ Тестируем ДЕМО-парсер (тестовые данные):")
    try:
        demo_parser = DemoParser()
        demo_properties = await demo_parser.search_properties(filters)
        if demo_properties:
            print(f"   ✅ ДЕМО ДАННЫЕ: найдено {len(demo_properties)} объявлений")
            print("   📋 Примеры демо-объявлений:")
            for i, prop in enumerate(demo_properties[:3], 1):
                print(f"      {i}. {prop.title}")
                print(f"         • {prop.address}")
                print(f"         • {prop.format_price()}")
                print(f"         • URL: {prop.url}")
        else:
            print("   ❌ ДЕМО ПАРСЕР: объявления не найдены")
    except Exception as e:
        print(f"   ❌ ДЕМО ПАРСЕР ошибка: {e}")
    
    # 3. Логика переключения
    print("\n3️⃣ Логика работы системы:")
    print("   🔄 АВТОМАТИЧЕСКОЕ ПЕРЕКЛЮЧЕНИЕ:")
    print("   • Сначала пробует получить РЕАЛЬНЫЕ данные с daft.ie")
    print("   • Если сайт блокирует → переключается на ДЕМО данные")
    print("   • Демо данные используются для демонстрации и тестирования")
    
    print("\n4️⃣ Текущий статус:")
    try:
        parser = DaftParser()
        real_props = await parser.search_properties(filters)
        if real_props:
            print("   🌐 ИСПОЛЬЗУЮТСЯ: РЕАЛЬНЫЕ данные с daft.ie")
        else:
            print("   🎭 ИСПОЛЬЗУЮТСЯ: ДЕМО данные (сайт заблокирован)")
    except:
        print("   🎭 ИСПОЛЬЗУЮТСЯ: ДЕМО данные (сайт недоступен)")

if __name__ == "__main__":
    asyncio.run(check_data_sources())
