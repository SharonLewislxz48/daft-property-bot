#!/usr/bin/env python3
"""
Скрипт для исправления всех проблем с форматированием в боте
"""

import re
import os

def fix_formatting_in_file(file_path):
    """Исправляем форматирование в файле"""
    print(f"Обрабатываем файл: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Исправляем \\n на \n (только в строках)
    content = re.sub(r'\\n', '\n', content)
    
    # 2. Исправляем **text** на <b>text</b> (только в строках)
    content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
    
    # 3. Исправляем некоторые специфичные случаи
    content = content.replace('"\\n"', '"\n"')
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Файл {file_path} исправлен")
        return True
    else:
        print(f"ℹ️ Файл {file_path} не нуждается в исправлениях")
        return False

def main():
    """Основная функция"""
    files_to_fix = [
        'bot/enhanced_bot_handlers.py',
        'bot/enhanced_bot.py'
    ]
    
    fixed_files = 0
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_formatting_in_file(file_path):
                fixed_files += 1
        else:
            print(f"❌ Файл не найден: {file_path}")
    
    print(f"\n📊 Итого исправлено файлов: {fixed_files}")

if __name__ == "__main__":
    main()
