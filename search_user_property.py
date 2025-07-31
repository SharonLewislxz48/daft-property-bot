#!/usr/bin/env python3
"""
Поиск объявлений пользователя в общем списке daft.ie
"""

import asyncio
from parser.daft_parser import DaftParser
from parser.models import SearchFilters

async def search_for_user_property():
    """Ищем объявление пользователя в общем поиске"""
    
    user_url = "http://www.daft.ie/for-rent/house-28-cabra-drive-dublin-7-north-circular-road-dublin-7/6193753"
    user_id = "6193753"  # ID из URL
    
    print("🔍 Ищем объявление пользователя в общем поиске по Дублину")
    print(f"🎯 Целевое объявление: {user_url}")
    print(f"🆔 ID: {user_id}")
    print("="*80)
    
    parser = DaftParser()
    
    # Поиск с очень мягкими фильтрами
    filters = SearchFilters(
        city="Dublin",
        max_price=10000,  # Очень высокий лимит
        min_bedrooms=0    # Без ограничений
    )
    
    try:
        properties = await parser.search_properties(filters)
        print(f"✅ Найдено {len(properties)} объявлений всего")
        
        # Ищем наше объявление по ID
        found_property = None
        for prop in properties:
            if user_id in prop.url:
                found_property = prop
                break
        
        if found_property:
            print(f"\n🎉 НАЙДЕНО! Объявление пользователя обнаружено:")
            print(f"📄 Название: {found_property.title}")
            print(f"💰 Цена: €{found_property.price:,}/month")
            print(f"🛏️ Спальни: {found_property.bedrooms}")
            print(f"🚿 Ванные: {found_property.bathrooms}")
            print(f"🏠 Тип: {found_property.property_type}")
            print(f"📍 Адрес: {found_property.address}")
            print(f"🔗 URL: {found_property.url}")
            
            # Проверяем фильтры
            print(f"\n🎯 ПРОВЕРКА ФИЛЬТРОВ (3+ спальни, до €2500):")
            price_ok = found_property.price <= 2500
            bedrooms_ok = found_property.bedrooms >= 3
            
            print(f"💰 Цена €{found_property.price:,} <= €2500? {'✅' if price_ok else '❌'}")
            print(f"🛏️ Спальни {found_property.bedrooms} >= 3? {'✅' if bedrooms_ok else '❌'}")
            
            if price_ok and bedrooms_ok:
                print(f"\n🎉 ОБЪЯВЛЕНИЕ ПОЛНОСТЬЮ СООТВЕТСТВУЕТ ФИЛЬТРАМ!")
                print(f"   Пользователь прав - такие объявления существуют!")
            else:
                print(f"\n❌ Объявление НЕ соответствует одному из фильтров")
                if not bedrooms_ok:
                    print(f"   Проблема с количеством спален: {found_property.bedrooms} < 3")
                    print(f"   Возможно, парсер неправильно определил количество спален")
                
        else:
            print(f"\n❌ Объявление с ID {user_id} НЕ найдено в текущем поиске")
            print(f"   Возможные причины:")
            print(f"   • Объявление было удалено")
            print(f"   • Объявление не индексируется в общем поиске")
            print(f"   • Наш парсер видит только часть объявлений")
            
            # Показываем несколько примеров найденных объявлений
            print(f"\n📋 Примеры найденных объявлений:")
            for i, prop in enumerate(properties[:5], 1):
                print(f"{i}. {prop.title[:50]}... - €{prop.price:,} - {prop.bedrooms} спален")
                print(f"   🔗 {prop.url}")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await parser.close()

if __name__ == "__main__":
    asyncio.run(search_for_user_property())
