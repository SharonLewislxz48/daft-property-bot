#!/usr/bin/env python3
"""
Проверка всех callback-обработчиков
"""

def check_handlers():
    print("🔍 ПРОВЕРКА CALLBACK-ОБРАБОТЧИКОВ")
    print("="*50)
    
    # Все callback_data из клавиатур
    expected_callbacks = [
        # Основное меню
        "settings", "statistics", "start_monitoring", "stop_monitoring", 
        "single_search", "help", "main_menu",
        
        # Настройки
        "manage_regions", "set_bedrooms", "set_max_price", "set_interval",
        "show_settings",
        
        # Новые категории регионов
        "category_dublin_areas", "category_main_cities", 
        "category_republic_counties", "category_northern_counties",
        "category_popular", "search_region",
        
        # Управление регионами
        "add_region", "remove_region", "show_regions", "list_all_regions",
        
        # Популярные комбинации
        "select_combo_dublin_central", "select_combo_dublin_south",
        "select_combo_dublin_north", "select_combo_dublin_west",
        "select_combo_major_cities", "select_combo_student_areas",
        
        # Выбор конкретных значений
        "select_region_", "remove_region_", "bedrooms_", "price_", "interval_",
        
        # Пагинация
        "region_page_", "category_page_",
        
        # Прочие
        "custom_price", "stats_"
    ]
    
    # Проверяем enhanced_main.py на наличие всех обработчиков
    try:
        with open('enhanced_main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        registered_handlers = []
        missing_handlers = []
        
        for callback in expected_callbacks:
            # Ищем точные совпадения или паттерны
            if callback.endswith('_'):
                # Паттерн типа "startswith"
                if f'F.data.startswith("{callback}")' in main_content:
                    registered_handlers.append(callback)
                else:
                    missing_handlers.append(callback + "*")
            else:
                # Точное совпадение
                if f'F.data == "{callback}"' in main_content:
                    registered_handlers.append(callback)
                else:
                    missing_handlers.append(callback)
        
        print(f"✅ Зарегистрированных обработчиков: {len(registered_handlers)}")
        print(f"❌ Отсутствующих обработчиков: {len(missing_handlers)}")
        
        if missing_handlers:
            print("\n⚠️ ОТСУТСТВУЮЩИЕ ОБРАБОТЧИКИ:")
            for handler in missing_handlers[:10]:  # Показываем первые 10
                print(f"   • {handler}")
            if len(missing_handlers) > 10:
                print(f"   ... и еще {len(missing_handlers) - 10}")
        
        return len(missing_handlers) == 0
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

def check_keyboard_callbacks():
    print("\n🎹 ПРОВЕРКА КЛАВИАТУР")
    print("="*30)
    
    try:
        # Импортируем все клавиатуры
        import sys
        sys.path.append('.')
        from bot.enhanced_keyboards import (
            get_main_menu_keyboard, get_settings_menu_keyboard, get_regions_menu_keyboard,
            get_region_categories_keyboard, get_popular_combinations_keyboard,
            get_category_regions_keyboard
        )
        
        # Создаем все клавиатуры и извлекаем callback_data
        keyboards = [
            ("main_menu", get_main_menu_keyboard()),
            ("settings_menu", get_settings_menu_keyboard()),
            ("regions_menu", get_regions_menu_keyboard()),
            ("region_categories", get_region_categories_keyboard()),
            ("popular_combinations", get_popular_combinations_keyboard()),
            ("category_dublin", get_category_regions_keyboard("dublin_areas")),
            ("category_cities", get_category_regions_keyboard("main_cities")),
        ]
        
        all_callbacks = set()
        
        for name, keyboard in keyboards:
            callbacks = []
            if hasattr(keyboard, 'inline_keyboard'):
                for row in keyboard.inline_keyboard:
                    for button in row:
                        if hasattr(button, 'callback_data') and button.callback_data:
                            callbacks.append(button.callback_data)
                            all_callbacks.add(button.callback_data)
            
            print(f"  {name}: {len(callbacks)} кнопок")
        
        print(f"\n📊 Всего уникальных callback_data: {len(all_callbacks)}")
        
        # Показываем несколько примеров
        print("\n🔍 Примеры callback_data:")
        for callback in sorted(list(all_callbacks))[:10]:
            print(f"   • {callback}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки клавиатур: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    handlers_ok = check_handlers()
    keyboards_ok = check_keyboard_callbacks()
    
    print("\n" + "="*50)
    if handlers_ok and keyboards_ok:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    else:
        print("⚠️ НАЙДЕНЫ ПРОБЛЕМЫ - ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ")

if __name__ == "__main__":
    main()
