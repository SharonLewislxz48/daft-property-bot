#!/usr/bin/env python3
"""
Тест основных функций бота
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.enhanced_keyboards import *
from enhanced_main import CombinedBot

async def test_keyboards():
    """Тестируем клавиатуры"""
    print("🎹 ТЕСТ КЛАВИАТУР")
    print("=" * 30)
    
    # Тестируем основные клавиатуры
    keyboards = [
        ("Главное меню", get_main_menu_keyboard()),
        ("Меню настроек", get_settings_menu_keyboard()),
        ("Меню регионов", get_regions_menu_keyboard()),
        ("Категории регионов", get_region_categories_keyboard()),
        ("Популярные комбинации", get_popular_combinations_keyboard()),
        ("Районы Дублина", get_category_regions_keyboard("dublin_areas")),
        ("Основные города", get_category_regions_keyboard("main_cities"))
    ]
    
    for name, keyboard in keyboards:
        if keyboard and keyboard.inline_keyboard:
            button_count = sum(len(row) for row in keyboard.inline_keyboard)
            print(f"  ✅ {name}: {button_count} кнопок")
        else:
            print(f"  ❌ {name}: НЕТ КНОПОК")
    
    print()

async def test_bot_handlers():
    """Тестируем обработчики бота"""
    print("🤖 ТЕСТ ОБРАБОТЧИКОВ")
    print("=" * 30)
    
    # Создаем мок-бота
    bot_token = "TEST_TOKEN"
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        os.environ['TELEGRAM_BOT_TOKEN'] = bot_token
    
    bot = CombinedBot(bot_token)
    
    # Проверяем наличие методов
    methods_to_check = [
        "cmd_start", "cmd_help", "cmd_status",
        "callback_main_menu", "callback_settings", "callback_statistics",
        "callback_start_monitoring", "callback_stop_monitoring",
        "callback_single_search", "callback_help",
        "callback_show_settings", "callback_manage_regions",
        "callback_search_region", "callback_noop", "callback_current_page",
        "callback_recent_searches"
    ]
    
    for method_name in methods_to_check:
        if hasattr(bot, method_name):
            print(f"  ✅ {method_name}")
        else:
            print(f"  ❌ {method_name}")
    
    print()

async def test_imports():
    """Тестируем импорты"""
    print("📦 ТЕСТ ИМПОРТОВ")
    print("=" * 30)
    
    imports_to_check = [
        ("config.regions", "ALL_REGIONS"),
        ("database.enhanced_database", "PropertyDatabase"),
        ("bot.enhanced_keyboards", "get_main_menu_keyboard"),
        ("bot.enhanced_bot", "PropertyBot"),
        ("bot.enhanced_bot_handlers", "EnhancedPropertyBotHandlers")
    ]
    
    for module_name, class_name in imports_to_check:
        try:
            module = __import__(module_name, fromlist=[class_name])
            if hasattr(module, class_name):
                print(f"  ✅ {module_name}.{class_name}")
            else:
                print(f"  ❌ {module_name}.{class_name} - класс не найден")
        except Exception as e:
            print(f"  ❌ {module_name}.{class_name} - ошибка импорта: {e}")
    
    print()

async def main():
    """Главная функция тестирования"""
    print("🧪 ЗАПУСК ТЕСТОВ БОТА")
    print("=" * 50)
    print()
    
    await test_imports()
    await test_keyboards()
    await test_bot_handlers()
    
    print("=" * 50)
    print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    asyncio.run(main())
