#!/usr/bin/env python3
"""
Тест для проверки работы парсера с несколькими страницами
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from production_parser import ProductionDaftParser

async def test_multi_page_parser():
    """Тестируем парсер с несколькими страницами"""
    parser = ProductionDaftParser()
    
    print("=== Тест парсера с поддержкой нескольких страниц ===")
    
    # Тест 1: Одна страница
    print("\n🧪 Тест 1: Одна страница (лимит 20)")
    results_1_page = await parser.search_properties(
        min_bedrooms=3,
        max_price=2500,
        location="dublin-city",
        limit=20,
        max_pages=1
    )
    print(f"✅ Результатов с 1 страницы: {len(results_1_page)}")
    
    # Тест 2: Три страницы
    print("\n🧪 Тест 2: Три страницы (лимит 60)")
    results_3_pages = await parser.search_properties(
        min_bedrooms=3,
        max_price=2500,
        location="dublin-city",
        limit=60,
        max_pages=3
    )
    print(f"✅ Результатов с 3 страниц: {len(results_3_pages)}")
    
    print(f"\n📊 Сравнение:")
    print(f"   1 страница: {len(results_1_page)} результатов")
    print(f"   3 страницы: {len(results_3_pages)} результатов")
    print(f"   Прирост: +{len(results_3_pages) - len(results_1_page)} результатов")
    
    if len(results_3_pages) > len(results_1_page):
        print("🎉 Поддержка нескольких страниц работает!")
    else:
        print("⚠️ Возможно проблема с пагинацией или недостаточно объявлений")

if __name__ == "__main__":
    asyncio.run(test_multi_page_parser())
