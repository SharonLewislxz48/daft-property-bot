#!/usr/bin/env python3
"""
Тест Playwright парсера для получения реальных данных
"""
import asyncio
import sys
sys.path.append('/home/barss/PycharmProjects/daftparser')

from parser.playwright_parser import PlaywrightDaftParser
from parser.models import SearchFilters

async def test_real_data():
    """Тестируем получение реальных данных через браузер"""
    print("🌐 Тестируем получение РЕАЛЬНЫХ данных с daft.ie")
    print("=" * 50)
    
    filters = SearchFilters(
        city="Dublin",
        max_price=3000,
        min_bedrooms=2,
        areas=[]
    )
    
    try:
        print("🚀 Запускаем браузерный парсер (Playwright)...")
        parser = PlaywrightDaftParser()
        properties = await parser.search_properties(filters)
        
        if properties:
            print(f"✅ УСПЕХ! Получено {len(properties)} РЕАЛЬНЫХ объявлений:")
            print()
            
            for i, prop in enumerate(properties[:3], 1):
                print(f"   {i}. 🏠 {prop.title}")
                print(f"      📍 {prop.address}")
                print(f"      💰 {prop.format_price()}")
                print(f"      🛏️ {prop.format_bedrooms()}")
                print(f"      🔗 {prop.url}")
                print()
                
            return True
        else:
            print("❌ Объявления не найдены")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка браузерного парсера: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_data())
    if success:
        print("🎉 Браузерный парсер работает! Можно использовать реальные данные.")
    else:
        print("⚠️ Браузерный парсер не работает. Нужны другие методы.")
