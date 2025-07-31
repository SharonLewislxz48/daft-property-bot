#!/usr/bin/env python3
"""
Диагностика компонентов системы
"""

import sys
import traceback

def test_component(name, import_func):
    try:
        result = import_func()
        print(f"✅ {name}: OK")
        if result:
            print(f"   Результат: {result}")
        return True
    except Exception as e:
        print(f"❌ {name}: ОШИБКА")
        print(f"   {e}")
        traceback.print_exc()
        return False

def main():
    print("🔍 ДИАГНОСТИКА КОМПОНЕНТОВ СИСТЕМЫ")
    print("="*50)
    
    results = []
    
    # Тест 1: Импорт регионов
    def test_regions():
        from config.regions import ALL_LOCATIONS, DUBLIN_REGIONS, MAIN_CITIES, COUNTIES
        return f"{len(ALL_LOCATIONS)} локаций"
    results.append(test_component("config.regions", test_regions))
    
    # Тест 2: Импорт клавиатур
    def test_keyboards():
        from bot.enhanced_keyboards import get_main_menu_keyboard, get_region_categories_keyboard
        kb1 = get_main_menu_keyboard()
        kb2 = get_region_categories_keyboard()
        return f"клавиатуры работают"
    results.append(test_component("bot.enhanced_keyboards", test_keyboards))
    
    # Тест 3: Импорт обработчиков
    def test_handlers():
        from bot.enhanced_bot_handlers import BotStates, EnhancedPropertyBotHandlers
        return "обработчики загружены"
    results.append(test_component("bot.enhanced_bot_handlers", test_handlers))
    
    # Тест 4: Импорт основного бота
    def test_bot():
        from bot.enhanced_bot import EnhancedPropertyBot
        return "основной класс бота"
    results.append(test_component("bot.enhanced_bot", test_bot))
    
    # Тест 5: Импорт базы данных
    def test_database():
        from database.enhanced_database import EnhancedDatabase
        return "база данных"
    results.append(test_component("database.enhanced_database", test_database))
    
    print("\n" + "="*50)
    print(f"📊 РЕЗУЛЬТАТЫ: {sum(results)}/{len(results)} компонентов работают")
    
    if all(results):
        print("🎉 ВСЕ КОМПОНЕНТЫ ИСПРАВНЫ!")
        return True
    else:
        print("⚠️ ЕСТЬ ПРОБЛЕМЫ С КОМПОНЕНТАМИ")
        return False

if __name__ == "__main__":
    main()
