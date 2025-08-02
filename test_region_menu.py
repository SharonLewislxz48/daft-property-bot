#!/usr/bin/env python3
"""
Тест для проверки меню регионов
"""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from bot.enhanced_keyboards import get_regions_menu_keyboard, get_add_region_categories_keyboard

def test_regions_menu():
    """Проверяем работу меню регионов"""
    try:
        print("=== Тест меню управления регионами ===")
        keyboard = get_regions_menu_keyboard()
        print("✅ Функция get_regions_menu_keyboard() работает")
        print(f"Количество рядов кнопок: {len(keyboard.inline_keyboard)}")
        
        for i, row in enumerate(keyboard.inline_keyboard):
            print(f"Ряд {i+1}:")
            for j, button in enumerate(row):
                print(f"  Кнопка {j+1}: {button.text} -> {button.callback_data}")
        
        print("\n=== Тест меню добавления регионов ===")
        add_keyboard = get_add_region_categories_keyboard()
        print("✅ Функция get_add_region_categories_keyboard() работает")
        print(f"Количество рядов кнопок: {len(add_keyboard.inline_keyboard)}")
        
        for i, row in enumerate(add_keyboard.inline_keyboard):
            print(f"Ряд {i+1}:")
            for j, button in enumerate(row):
                print(f"  Кнопка {j+1}: {button.text} -> {button.callback_data}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    test_regions_menu()
