#!/usr/bin/env python3
"""
Тестирование парсера недвижимости daft.ie
"""

import asyncio
import logging
import sys
from dataclasses import dataclass
from typing import List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Имитируем необходимые классы
@dataclass
class SearchFilters:
    city: str
    max_price: int
    min_bedrooms: int
    areas: List[str] = None

@dataclass  
class Property:
    id: str
    title: str
    address: str
    price: int
    bedrooms: int
    bathrooms: int
    property_type: str
    url: str
    image_url: str = None
    description: str = None
    area: str = None
    posted_date: str = None
    
    def format_price(self):
        return f"€{self.price:,}"

# Создаем фейковый settings модуль
class Settings:
    SEARCH_URL = "https://www.daft.ie"

settings = Settings()

# Добавляем путь к парсеру
sys.path.append('/home/barss/PycharmProjects/daftparser')

from parser.playwright_parser import PlaywrightDaftParser

async def test_url_generation():
    """Тест генерации URL"""
    print("🔧 Тестирование генерации URL...")
    
    parser = PlaywrightDaftParser()
    
    # Тест 1: Первая страница
    filters1 = SearchFilters(
        city="dublin",
        max_price=2500,
        min_bedrooms=3
    )
    url1 = parser._build_search_url(filters1, page=1)
    print(f"✅ Страница 1: {url1}")
    
    # Тест 2: Вторая страница  
    url2 = parser._build_search_url(filters1, page=2)
    print(f"✅ Страница 2: {url2}")
    
    # Тест 3: С районами
    filters2 = SearchFilters(
        city="dublin", 
        max_price=2500,
        min_bedrooms=3,
        areas=["Dublin 1", "Dublin 2"]
    )
    url3 = parser._build_search_url(filters2, page=1)
    print(f"✅ С районами: {url3}")

async def test_real_search():
    """Тест реального поиска"""
    print("\n🚀 Тестирование реального поиска...")
    
    filters = SearchFilters(
        city="dublin",
        max_price=2500,
        min_bedrooms=3
    )
    
    async with PlaywrightDaftParser() as parser:
        print(f"🔍 Поиск: {filters.min_bedrooms}+ спален, до €{filters.max_price}, {filters.city}")
        
        # Ищем только на первой странице для теста
        properties = await parser.search_properties(filters, max_pages=1)
        
        print(f"\n📊 Результаты:")
        print(f"  Найдено объявлений: {len(properties)}")
        
        if properties:
            print(f"\n📋 Первые 3 объявления:")
            for i, prop in enumerate(properties[:3], 1):
                print(f"  {i}. {prop.title}")
                print(f"     💰 {prop.format_price()}/месяц")
                print(f"     🛏️ {prop.bedrooms} спален, 🚿 {prop.bathrooms} ванных")
                print(f"     📍 {prop.address}")
                print(f"     🔗 {prop.url}")
                print()
        else:
            print("❌ Объявления не найдены")

async def test_manual_url():
    """Тест загрузки конкретного URL"""
    print("\n🔗 Тестирование загрузки конкретного URL...")
    
    test_url = "https://www.daft.ie/property-for-rent/dublin-city/houses?rentalPrice_to=2500&numBeds_from=3"
    print(f"URL: {test_url}")
    
    async with PlaywrightDaftParser() as parser:
        html_content = await parser._get_page_content(test_url)
        
        if html_content:
            print(f"✅ Страница загружена, размер: {len(html_content)} символов")
            
            # Проверяем наличие объявлений в HTML
            if "for-rent" in html_content:
                print("✅ Найдены ссылки на аренду в HTML")
            else:
                print("❌ Ссылки на аренду не найдены")
                
            if "€" in html_content or "euro" in html_content.lower():
                print("✅ Найдены цены в HTML")
            else:
                print("❌ Цены не найдены")
                
            # Сохраняем часть HTML для анализа
            with open('/tmp/daft_test.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("💾 HTML сохранен в /tmp/daft_test.html для анализа")
                
        else:
            print("❌ Не удалось загрузить страницу")

async def main():
    """Главная функция тестирования"""
    print("🧪 Запуск тестов парсера daft.ie\n")
    
    try:
        # Тест 1: Генерация URL
        await test_url_generation()
        
        # Тест 2: Загрузка страницы
        await test_manual_url()
        
        # Тест 3: Полный поиск
        await test_real_search()
        
        print("\n✅ Тестирование завершено")
        
    except Exception as e:
        print(f"\n❌ Ошибка во время тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
