#!/usr/bin/env python3
"""
Полный тест системы с демо-данными
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

async def test_complete_system():
    """Полный тест системы"""
    try:
        print("🤖 Полный тест Daft.ie Telegram Bot системы")
        print("=" * 50)
        
        # Тест 1: Конфигурация
        print("\n1️⃣ Тестируем конфигурацию...")
        from config.settings import settings
        print(f"   ✅ Base URL: {settings.BASE_URL}")
        print(f"   ✅ Update interval: {settings.UPDATE_INTERVAL}s")
        print(f"   ✅ Database path: {settings.DB_PATH}")
        
        # Тест 2: База данных
        print("\n2️⃣ Тестируем базу данных...")
        from database.database import Database
        from parser.models import BotSettings, Property
        
        db = Database("./data/test_system.db")
        await db.init_database()
        print("   ✅ База данных инициализирована")
        
        # Создаем тестовые настройки
        test_settings = BotSettings(
            chat_id="test_system_chat",
            city="Dublin",
            max_price=2500,
            min_bedrooms=2,
            areas=["Dublin 1", "Dublin 2", "Dublin 4"]
        )
        
        await db.save_bot_settings(test_settings)
        print("   ✅ Настройки сохранены")
        
        # Тест 3: Демо-парсер
        print("\n3️⃣ Тестируем демо-парсер...")
        from parser.demo_parser import DemoParser
        from parser.models import SearchFilters
        
        filters = SearchFilters(
            city="Dublin",
            max_price=2500,
            min_bedrooms=2,
            areas=["Dublin 2", "Dublin 4"]
        )
        
        async with DemoParser() as parser:
            properties = await parser.search_properties(filters)
            print(f"   ✅ Найдено объявлений: {len(properties)}")
            
            if properties:
                print("   📋 Примеры объявлений:")
                for i, prop in enumerate(properties[:3], 1):
                    print(f"      {i}. {prop.title}")
                    print(f"         💰 {prop.format_price()}")
                    print(f"         🛏️ {prop.format_bedrooms()}")
                    print(f"         📍 {prop.address}")
        
        # Тест 4: Сохранение объявлений
        print("\n4️⃣ Тестируем сохранение объявлений...")
        if properties:
            saved_count = await db.save_properties(properties)
            print(f"   ✅ Сохранено объявлений: {saved_count}")
            
            # Проверяем новые объявления
            new_properties = await db.get_new_properties("test_system_chat")
            print(f"   ✅ Новых объявлений для чата: {len(new_properties)}")
        
        # Тест 5: Клавиатуры бота
        print("\n5️⃣ Тестируем клавиатуры бота...")
        from bot.keyboards import (
            get_main_menu_keyboard, get_settings_keyboard, 
            get_dublin_areas_keyboard
        )
        
        main_keyboard = get_main_menu_keyboard()
        settings_keyboard = get_settings_keyboard()
        areas_keyboard = get_dublin_areas_keyboard()
        
        print(f"   ✅ Главное меню: {len(main_keyboard.inline_keyboard)} рядов кнопок")
        print(f"   ✅ Настройки: {len(settings_keyboard.inline_keyboard)} рядов кнопок")
        print(f"   ✅ Районы: {len(areas_keyboard.inline_keyboard)} рядов кнопок")
        
        # Тест 6: Форматирование сообщений
        print("\n6️⃣ Тестируем форматирование сообщений...")
        if properties:
            test_property = properties[0]
            
            message_text = (
                f"🏠 <b>{test_property.title}</b>\n\n"
                f"📍 <b>Адрес:</b> {test_property.address}\n"
                f"🛏️ <b>Спальни:</b> {test_property.format_bedrooms()}\n"
                f"💰 <b>Цена:</b> {test_property.format_price()}\n"
                f"🔗 <a href='{test_property.url}'>Смотреть объявление</a>"
            )
            
            print("   ✅ Пример сообщения:")
            print("   " + "─" * 40)
            print(f"   🏠 {test_property.title}")
            print(f"   📍 Адрес: {test_property.address}")
            print(f"   🛏️ Спальни: {test_property.format_bedrooms()}")
            print(f"   💰 Цена: {test_property.format_price()}")
            print(f"   🔗 URL: {test_property.url}")
            print("   " + "─" * 40)
        
        # Тест 7: Статистика
        print("\n7️⃣ Тестируем статистику...")
        stats = await db.get_statistics("test_system_chat")
        print(f"   ✅ Всего объявлений: {stats.get('total_properties', 0)}")
        print(f"   ✅ Отправлено в чат: {stats.get('sent_properties', 0)}")
        
        # Тест 8: Утилиты
        print("\n8️⃣ Тестируем утилиты...")
        from utils.helpers import (
            extract_price_from_text, extract_dublin_area, 
            format_price, truncate_text
        )
        
        test_price = extract_price_from_text("Rent €2,500 per month")
        test_area = extract_dublin_area("Beautiful apartment in Dublin 4")
        formatted_price = format_price(2500)
        truncated = truncate_text("Very long description text that should be truncated", 30)
        
        print(f"   ✅ Извлечение цены: €{test_price}")
        print(f"   ✅ Извлечение района: {test_area}")
        print(f"   ✅ Форматирование цены: {formatted_price}")
        print(f"   ✅ Обрезка текста: {truncated}")
        
        print("\n" + "=" * 50)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("🎉 Система готова к работе!")
        print("=" * 50)
        
        print("\n📝 Для запуска бота:")
        print("   1. Настройте .env файл с токенами Telegram")
        print("   2. Запустите: python main.py")
        print("   3. Используйте команды бота для настройки фильтров")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_complete_system())
    sys.exit(0 if success else 1)
