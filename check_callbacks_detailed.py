#!/usr/bin/env python3
"""
Детальная проверка callback-обработчиков с учетом паттернов
"""

import os
import sys
import re
from pathlib import Path

def get_callback_data_from_keyboards():
    """Извлекает все callback_data из клавиатур"""
    keyboard_file = Path("bot/enhanced_keyboards.py")
    if not keyboard_file.exists():
        return set()
    
    callback_data = set()
    
    with open(keyboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Ищем все callback_data в InlineKeyboardButton
        pattern = r'callback_data=["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)
        
        for match in matches:
            callback_data.add(match)
            
    return callback_data

def get_registered_patterns():
    """Извлекает все зарегистрированные паттерны из enhanced_main.py"""
    main_file = Path("enhanced_main.py")
    if not main_file.exists():
        return []
    
    patterns = []
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Ищем регистрации с точными данными
        exact_pattern = r'F\.data\s*==\s*["\']([^"\']+)["\']'
        exact_matches = re.findall(exact_pattern, content)
        
        for match in exact_matches:
            patterns.append(('exact', match))
        
        # Ищем регистрации с startswith
        startswith_pattern = r'F\.data\.startswith\(["\']([^"\']+)["\']'
        startswith_matches = re.findall(startswith_pattern, content)
        
        for match in startswith_matches:
            patterns.append(('startswith', match))
    
    return patterns

def check_coverage(callback_data, patterns):
    """Проверяет покрытие callback_data паттернами"""
    covered = set()
    uncovered = set()
    
    for data in callback_data:
        is_covered = False
        
        for pattern_type, pattern in patterns:
            if pattern_type == 'exact' and data == pattern:
                is_covered = True
                break
            elif pattern_type == 'startswith' and data.startswith(pattern):
                is_covered = True
                break
        
        if is_covered:
            covered.add(data)
        else:
            uncovered.add(data)
    
    return covered, uncovered

def main():
    print("🔍 ДЕТАЛЬНАЯ ПРОВЕРКА CALLBACK-ОБРАБОТЧИКОВ")
    print("=" * 50)
    
    # Получаем данные
    callback_data = get_callback_data_from_keyboards()
    patterns = get_registered_patterns()
    
    print(f"📊 Всего callback_data в клавиатурах: {len(callback_data)}")
    print(f"🎯 Зарегистрированных паттернов: {len(patterns)}")
    print()
    
    # Показываем паттерны
    print("🎯 ЗАРЕГИСТРИРОВАННЫЕ ПАТТЕРНЫ:")
    print("-" * 30)
    for pattern_type, pattern in patterns:
        if pattern_type == 'exact':
            print(f"  ✓ {pattern} (точное совпадение)")
        else:
            print(f"  ✓ {pattern}* (начинается с)")
    print()
    
    # Проверяем покрытие
    covered, uncovered = check_coverage(callback_data, patterns)
    
    print(f"✅ Покрытые callback_data: {len(covered)}")
    print(f"❌ Непокрытые callback_data: {len(uncovered)}")
    print()
    
    if uncovered:
        print("⚠️ НЕПОКРЫТЫЕ CALLBACK_DATA:")
        print("-" * 30)
        for data in sorted(uncovered):
            print(f"   • {data}")
        print()
    
    # Подробная проверка
    print("📋 ДЕТАЛЬНАЯ ПРОВЕРКА:")
    print("-" * 30)
    for data in sorted(callback_data):
        is_covered = data in covered
        status = "✅" if is_covered else "❌"
        print(f"  {status} {data}")
    
    print()
    if uncovered:
        print("⚠️ НАЙДЕНЫ ПРОБЛЕМЫ - ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ")
        return False
    else:
        print("🎉 ВСЕ CALLBACK_DATA ПОКРЫТЫ ОБРАБОТЧИКАМИ!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
