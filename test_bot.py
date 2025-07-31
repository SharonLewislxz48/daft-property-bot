#!/usr/bin/env python3
"""
Тестовый скрипт для проверки парсера
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

async def test_parser():
    """Тест парсера"""
    try:
        print("🔍 Тестируем парсер Daft.ie...")
        
        # Импортируем модули
        from parser.daft_parser import DaftParser
        from parser.models import SearchFilters
        
        print("✅ Модули импортированы успешно")
        
        # Создаем фильтры
        filters = SearchFilters(
            city="Dublin",
            max_price=2500,
            min_bedrooms=3,
            areas=["Dublin 1", "Dublin 2"]
        )
        
        print(f"✅ Фильтры созданы: {filters}")
        print(f"   URL параметры: {filters.to_url_params()}")
        
        # Тестируем парсер
        async with DaftParser() as parser:
            print("✅ Парсер инициализирован")
            
            # Строим URL
            url = parser._build_search_url(filters, page=1)
            print(f"   Построенный URL: {url}")
            
            # Пробуем получить страницу
            print("🌐 Получаем первую страницу...")
            html = await parser._fetch_page(url)
            
            if html:
                print(f"✅ Страница получена! Размер: {len(html)} символов")
                
                # Пробуем парсить объявления
                print("🔍 Ищем объявления (ограничено 1 страницей)...")
                properties = await parser.search_properties(filters, max_pages=1)
                
                print(f"✅ Найдено объявлений: {len(properties)}")
                
                if properties:
                    print("\n📋 Первые 3 объявления:")
                    for i, prop in enumerate(properties[:3], 1):
                        print(f"   {i}. {prop.title}")
                        print(f"      💰 {prop.format_price()}")
                        print(f"      🛏️ {prop.format_bedrooms()}")
                        print(f"      📍 {prop.address}")
                        print(f"      🔗 {prop.url}")
                        print()
                else:
                    print("   ℹ️ Объявления не найдены или не соответствуют фильтрам")
            else:
                print("❌ Не удалось получить страницу")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

async def test_database():
    """Тест базы данных"""
    try:
        print("\n🗄️ Тестируем базу данных...")
        
        from database.database import Database
        
        db = Database("./data/test.db")
        await db.init_database()
        
        print("✅ База данных инициализирована")
        
        # Тестируем настройки бота
        from parser.models import BotSettings
        
        settings = BotSettings(
            chat_id="test_chat",
            city="Dublin",
            max_price=2000,
            min_bedrooms=2,
            areas=["Dublin 1", "Dublin 2"]
        )
        
        await db.save_bot_settings(settings)
        print("✅ Настройки сохранены")
        
        loaded_settings = await db.get_bot_settings("test_chat")
        print(f"✅ Настройки загружены: {loaded_settings.city}, €{loaded_settings.max_price}")
        
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Главная функция тестирования"""
    print("=" * 50)
    print("🤖 Тест Daft.ie Telegram Bot")
    print("=" * 50)
    
    await test_parser()
    await test_database()
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
