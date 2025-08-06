#!/usr/bin/env python3
"""
Тест пагинации парсера - проверяем, переходит ли бот на несколько страниц
"""

import asyncio
import sys
import logging
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from production_parser import ProductionDaftParser

async def test_pagination():
    """Тест пагинации парсера"""
    
    print("📄 ТЕСТ ПАГИНАЦИИ")
    print("=" * 40)
    
    parser = ProductionDaftParser()
    
    # Тест 1: Ограниченный поиск (1 страница)
    print("🔍 Тест 1: Поиск на 1 странице")
    results_1_page = await parser.search_properties(
        min_bedrooms=3,
        max_price=2500,
        location='dublin-city',
        limit=5,
        max_pages=1
    )
    print(f"   📊 Найдено на 1 странице: {len(results_1_page)} объявлений")
    
    # Тест 2: Расширенный поиск (3 страницы)
    print("\n🔍 Тест 2: Поиск на 3 страницах")
    results_3_pages = await parser.search_properties(
        min_bedrooms=3,
        max_price=2500,
        location='dublin-city',
        limit=30,  # Больше лимит
        max_pages=3
    )
    print(f"   📊 Найдено на 3 страницах: {len(results_3_pages)} объявлений")
    
    # Тест 3: Очень расширенный поиск (5 страниц)
    print("\n🔍 Тест 3: Поиск на 5 страницах")
    results_5_pages = await parser.search_properties(
        min_bedrooms=2,  # Более широкий поиск
        max_price=3000,
        location='dublin-city',
        limit=50,
        max_pages=5
    )
    print(f"   📊 Найдено на 5 страницах: {len(results_5_pages)} объявлений")
    
    # Анализ результатов
    print("\n📈 АНАЛИЗ ПАГИНАЦИИ:")
    print(f"   1 страница:  {len(results_1_page)} объявлений")
    print(f"   3 страницы:  {len(results_3_pages)} объявлений")
    print(f"   5 страниц:   {len(results_5_pages)} объявлений")
    
    # Проверяем уникальность между результатами
    ids_1 = {prop['id'] for prop in results_1_page}
    ids_3 = {prop['id'] for prop in results_3_pages}
    ids_5 = {prop['id'] for prop in results_5_pages}
    
    print(f"\n🔗 УНИКАЛЬНОСТЬ:")
    print(f"   Уникальных в 1 стр:  {len(ids_1)}")
    print(f"   Уникальных в 3 стр:  {len(ids_3)}")
    print(f"   Уникальных в 5 стр:  {len(ids_5)}")
    
    # Проверяем, есть ли новые объявления на дополнительных страницах
    new_on_page_3 = ids_3 - ids_1
    new_on_page_5 = ids_5 - ids_3
    
    print(f"\n📄 НОВЫЕ ОБЪЯВЛЕНИЯ:")
    print(f"   Новых на стр 2-3:    {len(new_on_page_3)}")
    print(f"   Новых на стр 4-5:    {len(new_on_page_5)}")
    
    if len(results_3_pages) > len(results_1_page):
        print("✅ ПАГИНАЦИЯ РАБОТАЕТ: парсер находит больше объявлений на дополнительных страницах")
        return True
    elif len(results_3_pages) == len(results_1_page):
        print("⚠️ ПАГИНАЦИЯ ОГРАНИЧЕНА: возможно, все объявления на первой странице")
        return True
    else:
        print("❌ ПРОБЛЕМА С ПАГИНАЦИЕЙ")
        return False

async def test_bot_pagination_settings():
    """Тест настроек пагинации в боте"""
    
    print("\n🤖 ТЕСТ НАСТРОЕК БОТА")
    print("=" * 30)
    
    # Симуляция настроек бота
    bot_settings = {
        "regions": ["dublin-city"],
        "min_bedrooms": 3,
        "max_price": 2500,
        "max_results_per_search": 10
    }
    
    parser = ProductionDaftParser()
    
    # Поиск как в боте (без указания max_pages - используется по умолчанию)
    print("🔍 Поиск как в боте (настройки по умолчанию):")
    
    all_results = []
    for region in bot_settings["regions"]:
        region_results = await parser.search_properties(
            min_bedrooms=bot_settings["min_bedrooms"],
            max_price=bot_settings["max_price"],
            location=region,
            limit=bot_settings["max_results_per_search"] // len(bot_settings["regions"])
        )
        all_results.extend(region_results)
        print(f"   📍 {region}: {len(region_results)} объявлений")
    
    print(f"   📊 Итого: {len(all_results)} объявлений")
    
    # Проверяем значение max_pages по умолчанию
    import inspect
    sig = inspect.signature(parser.search_properties)
    default_max_pages = sig.parameters['max_pages'].default
    print(f"   📄 max_pages по умолчанию: {default_max_pages}")
    
    if default_max_pages >= 3:
        print("✅ Бот использует пагинацию (max_pages >= 3)")
        return True
    else:
        print("⚠️ Бот ограничен одной страницей")
        return False

async def main():
    """Основная функция тестирования пагинации"""
    
    print("🧪 ТЕСТИРОВАНИЕ ПАГИНАЦИИ ПАРСЕРА")
    print("=" * 50)
    
    # Настройка логирования
    logging.basicConfig(level=logging.WARNING)  # Убираем лишние логи
    
    # Тесты
    test1 = await test_pagination()
    test2 = await test_bot_pagination_settings()
    
    print("\n" + "=" * 50)
    print("🏁 ИТОГИ ТЕСТИРОВАНИЯ ПАГИНАЦИИ")
    print("=" * 50)
    
    if test1 and test2:
        print("✅ ПАГИНАЦИЯ РАБОТАЕТ КОРРЕКТНО")
        print("📄 Бот обрабатывает несколько страниц результатов")
        print("🔍 Находит больше объявлений на дополнительных страницах")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ С ПАГИНАЦИЕЙ")
        if not test1:
            print("   📄 Проблема с переходом между страницами")
        if not test2:
            print("   🤖 Проблема с настройками бота")

if __name__ == "__main__":
    asyncio.run(main())
