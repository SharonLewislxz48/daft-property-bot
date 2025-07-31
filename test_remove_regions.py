#!/usr/bin/env python3
"""
Тест функций удаления регионов
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from bot.enhanced_keyboards import get_user_regions_keyboard
from config.regions import ALL_LOCATIONS

def test_user_regions_keyboard():
    """Тестируем клавиатуру удаления регионов"""
    print("🧪 ТЕСТ КЛАВИАТУРЫ УДАЛЕНИЯ РЕГИОНОВ")
    print("=" * 40)
    
    # Тестовые регионы
    test_regions = ["dublin-city", "cork", "galway"]
    
    print("Тестовые регионы:")
    for region in test_regions:
        name = ALL_LOCATIONS.get(region, region)
        print(f"  • {region} → {name}")
    
    print("\nСоздаем клавиатуру...")
    keyboard = get_user_regions_keyboard(test_regions)
    
    print(f"Количество рядов: {len(keyboard.inline_keyboard)}")
    
    for i, row in enumerate(keyboard.inline_keyboard):
        print(f"Ряд {i + 1}:")
        for button in row:
            print(f"  - '{button.text}' → {button.callback_data}")
    
    print("\n✅ Тест завершен")

def test_all_locations():
    """Тестируем ALL_LOCATIONS"""
    print("\n🧪 ТЕСТ ALL_LOCATIONS")
    print("=" * 40)
    
    print(f"Всего регионов: {len(ALL_LOCATIONS)}")
    
    # Проверяем несколько ключей
    test_keys = ["dublin-city", "cork", "galway", "waterford", "limerick"]
    
    for key in test_keys:
        name = ALL_LOCATIONS.get(key, "НЕ НАЙДЕНО")
        status = "✅" if name != "НЕ НАЙДЕНО" else "❌"
        print(f"  {status} {key} → {name}")
    
    print("\n✅ Тест завершен")

if __name__ == "__main__":
    test_all_locations()
    test_user_regions_keyboard()
