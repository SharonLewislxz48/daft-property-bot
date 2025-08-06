#!/usr/bin/env python3
"""
Тест клавиатур бота
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from bot.enhanced_keyboards import (
    get_main_menu_keyboard, get_settings_menu_keyboard, 
    get_regions_menu_keyboard, get_add_region_categories_keyboard
)

def test_keyboards():
    """Тестируем все клавиатуры"""
    
    print("="*60)
    print("⌨️ ТЕСТ КЛАВИАТУР БОТА")
    print("="*60)
    
    keyboards = [
        ("Главное меню", get_main_menu_keyboard()),
        ("Меню настроек", get_settings_menu_keyboard()),
        ("Управление регионами", get_regions_menu_keyboard()),
        ("Добавить регион", get_add_region_categories_keyboard())
    ]
    
    for name, keyboard in keyboards:
        print(f"\n🔹 {name}:")
        print("-" * 40)
        
        for i, row in enumerate(keyboard.inline_keyboard):
            print(f"  Ряд {i+1}: ", end="")
            buttons = []
            for button in row:
                buttons.append(f"[{button.text}]")
            print(" | ".join(buttons))
        
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        print(f"  📊 Всего кнопок: {total_buttons}")
        print(f"  📊 Рядов: {len(keyboard.inline_keyboard)}")
    
    print("\n" + "="*60)
    print("✅ ТЕСТ КЛАВИАТУР ЗАВЕРШЕН!")
    print("="*60)

def check_button_texts():
    """Проверяем тексты кнопок на правильность"""
    print("\n🔍 АНАЛИЗ ТЕКСТОВ КНОПОК:")
    print("-" * 50)
    
    main_keyboard = get_main_menu_keyboard()
    settings_keyboard = get_settings_menu_keyboard()
    
    all_buttons = []
    for keyboard in [main_keyboard, settings_keyboard]:
        for row in keyboard.inline_keyboard:
            for button in row:
                all_buttons.append(button.text)
    
    print("📋 Все тексты кнопок:")
    for i, text in enumerate(all_buttons, 1):
        print(f"  {i:2d}. {text}")
    
    # Проверка на emoji
    emoji_count = sum(1 for text in all_buttons if any(ord(char) > 127 for char in text))
    print(f"\n📊 Кнопок с emoji: {emoji_count}/{len(all_buttons)}")
    
    # Проверка длины текстов
    max_length = max(len(text) for text in all_buttons)
    min_length = min(len(text) for text in all_buttons)
    avg_length = sum(len(text) for text in all_buttons) / len(all_buttons)
    
    print(f"📏 Длина текстов кнопок:")
    print(f"  Максимальная: {max_length} символов")
    print(f"  Минимальная: {min_length} символов")
    print(f"  Средняя: {avg_length:.1f} символов")

if __name__ == "__main__":
    test_keyboards()
    check_button_texts()
