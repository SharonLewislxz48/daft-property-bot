#!/usr/bin/env python3
"""
Тестирование основного парсера на конкретном URL пользователя
"""

import asyncio
import aiohttp
from parser.daft_parser import DaftParser

async def test_specific_url():
    """Тестируем основной парсер на URL от пользователя"""
    
    url = "http://www.daft.ie/for-rent/house-28-cabra-drive-dublin-7-north-circular-road-dublin-7/6193753"
    
    print("🔍 Тестируем основной парсер на URL пользователя:")
    print(f"🔗 {url}")
    print("="*80)
    
    parser = DaftParser()
    
    try:
        # Используем внутренний метод парсера для получения деталей
        property_details = await parser.get_property_info(url)
        
        if property_details:
            print("✅ УСПЕХ! Объявление обработано:")
            print(f"📄 Название: {property_details.title}")
            print(f"💰 Цена: €{property_details.price:,}/month")
            print(f"🛏️ Спальни: {property_details.bedrooms}")
            print(f"🚿 Ванные: {property_details.bathrooms}")
            print(f"🏠 Тип: {property_details.property_type}")
            print(f"📍 Адрес: {property_details.address}")
            print(f"🔗 URL: {property_details.url}")
            
            # Проверяем соответствие нашим фильтрам
            print(f"\n🎯 ПРОВЕРКА ФИЛЬТРОВ:")
            print(f"💰 Цена €{property_details.price:,} <= €2500? {'✅' if property_details.price <= 2500 else '❌'}")
            print(f"🛏️ Спальни {property_details.bedrooms} >= 3? {'✅' if property_details.bedrooms >= 3 else '❌'}")
            
            if property_details.price <= 2500 and property_details.bedrooms >= 3:
                print(f"\n🎉 ОБЪЯВЛЕНИЕ СООТВЕТСТВУЕТ ФИЛЬТРАМ!")
                print(f"   Это именно то, что ищет пользователь: 3+ спальни за €2500")
            else:
                print(f"\n❌ Объявление НЕ соответствует фильтрам")
                
        else:
            print("❌ Не удалось обработать объявление")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await parser.close()

if __name__ == "__main__":
    asyncio.run(test_specific_url())
