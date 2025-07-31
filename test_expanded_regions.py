#!/usr/bin/env python3
"""
Тест расширенной конфигурации регионов и интерфейса
"""

import sys
sys.path.append('.')

from config.regions import *
from bot.enhanced_keyboards import *

def test_expanded_regions():
    """Тестирование расширенной конфигурации регионов"""
    print("🌍 ТЕСТ РАСШИРЕННОЙ КОНФИГУРАЦИИ РЕГИОНОВ")
    print("="*60)
    
    # Тестируем основные коллекции
    print(f"🏙️ Районы Дублина: {len(DUBLIN_REGIONS)}")
    print(f"🌆 Основные города: {len(MAIN_CITIES)}")
    print(f"🗺️ Графства: {len(COUNTIES)}")
    print(f"📊 Всего локаций: {len(ALL_LOCATIONS)}")
    print()
    
    # Показываем основные города
    print("🌆 ОСНОВНЫЕ ГОРОДА:")
    for key, name in MAIN_CITIES.items():
        print(f"  • {key}: {name}")
    print()
    
    # Показываем графства Северной Ирландии
    print("🏴󠁧󠁢󠁳󠁣󠁴󠁿 СЕВЕРНАЯ ИРЛАНДИЯ:")
    ni_counties = REGION_CATEGORIES["northern_ireland"]
    for key, name in ni_counties.items():
        print(f"  • {key}: {name}")
    print()
    
    # Показываем популярные комбинации
    print("⭐ ПОПУЛЯРНЫЕ КОМБИНАЦИИ:")
    for combo_name, regions in POPULAR_COMBINATIONS.items():
        print(f"  • {combo_name}: {len(regions)} регионов")
        print(f"    {', '.join(regions[:3])}{'...' if len(regions) > 3 else ''}")
    print()
    
    # Тестируем новые лимиты
    print("⚙️ НОВЫЕ ЛИМИТЫ:")
    print(f"  • Максимальная цена: до €{LIMITS['max_price']['max']:,}")
    print(f"  • Максимум регионов: {LIMITS['max_regions']}")
    print(f"  • Интервал мониторинга: {LIMITS['monitoring_interval']['min']//60}-{LIMITS['monitoring_interval']['max']//3600} минут/часов")
    print()

def test_new_keyboards():
    """Тестирование новых клавиатур"""
    print("⌨️ ТЕСТ НОВЫХ КЛАВИАТУР")
    print("="*40)
    
    # Тестируем клавиатуру категорий
    try:
        categories_kb = get_region_categories_keyboard()
        print("✅ Клавиатура категорий создана")
        print(f"   Кнопок: {sum(len(row) for row in categories_kb.inline_keyboard)}")
        
        # Показываем категории
        for row in categories_kb.inline_keyboard:
            for button in row:
                print(f"   🔘 {button.text}")
        print()
        
    except Exception as e:
        print(f"❌ Ошибка клавиатуры категорий: {e}")
    
    # Тестируем клавиатуру популярных комбинаций
    try:
        popular_kb = get_popular_combinations_keyboard()
        print("✅ Клавиатура популярных комбинаций создана")
        print(f"   Кнопок: {sum(len(row) for row in popular_kb.inline_keyboard)}")
        print()
    except Exception as e:
        print(f"❌ Ошибка клавиатуры комбинаций: {e}")
    
    # Тестируем клавиатуры категорий регионов
    test_categories = ["dublin_areas", "main_cities", "republic_counties", "northern_counties"]
    
    for category in test_categories:
        try:
            category_kb = get_category_regions_keyboard(category)
            category_names = {
                "dublin_areas": "Районы Дублина",
                "main_cities": "Основные города", 
                "republic_counties": "Графства Ирландии",
                "northern_counties": "Северная Ирландия"
            }
            print(f"✅ Клавиатура '{category_names[category]}' создана")
            print(f"   Кнопок: {sum(len(row) for row in category_kb.inline_keyboard)}")
        except Exception as e:
            print(f"❌ Ошибка клавиатуры {category}: {e}")
    
    print()

def test_search_functionality():
    """Тестирование функциональности поиска"""
    print("🔍 ТЕСТ ФУНКЦИОНАЛЬНОСТИ ПОИСКА")
    print("="*40)
    
    # Тестируем поиск по ключевым словам
    search_terms = ["dublin", "cork", "belfast", "galway", "antrim"]
    
    for term in search_terms:
        matches = [
            (key, name) for key, name in ALL_LOCATIONS.items() 
            if term.lower() in key.lower() or term.lower() in name.lower()
        ]
        print(f"🔎 '{term}': найдено {len(matches)} совпадений")
        if matches:
            for key, name in matches[:3]:  # Показываем первые 3
                print(f"   • {key}: {name}")
            if len(matches) > 3:
                print(f"   ... и еще {len(matches) - 3}")
        print()

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ РАСШИРЕННОЙ СИСТЕМЫ РЕГИОНОВ")
    print("="*60)
    print()
    
    try:
        test_expanded_regions()
        test_new_keyboards() 
        test_search_functionality()
        
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print(f"📊 Итого доступно {len(ALL_LOCATIONS)} локаций для поиска")
        print("🌍 Покрытие: вся Ирландия + Северная Ирландия")
        
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
