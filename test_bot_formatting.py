#!/usr/bin/env python3
"""
Тест форматирования сообщений бота
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from bot.message_formatter import MessageFormatter

def test_all_messages():
    """Тестируем все форматы сообщений"""
    
    print("="*60)
    print("🧪 ТЕСТ ФОРМАТИРОВАНИЯ СООБЩЕНИЙ БОТА")
    print("="*60)
    
    # 1. Приветственное сообщение
    print("\n1️⃣ ПРИВЕТСТВЕННОЕ СООБЩЕНИЕ (новый пользователь):")
    print("-" * 50)
    welcome_msg = MessageFormatter.welcome_message(is_new_user=True)
    print(welcome_msg)
    
    # 2. Главное меню
    print("\n2️⃣ ГЛАВНОЕ МЕНЮ:")
    print("-" * 50)
    main_menu_msg = MessageFormatter.main_menu()
    print(main_menu_msg)
    
    # 3. Меню настроек
    print("\n3️⃣ МЕНЮ НАСТРОЕК:")
    print("-" * 50)
    settings_menu_msg = MessageFormatter.settings_menu()
    print(settings_menu_msg)
    
    # 4. Управление регионами
    print("\n4️⃣ УПРАВЛЕНИЕ РЕГИОНАМИ:")
    print("-" * 50)
    regions_menu_msg = MessageFormatter.regions_menu()
    print(regions_menu_msg)
    
    # 5. Текущие настройки
    print("\n5️⃣ ТЕКУЩИЕ НАСТРОЙКИ:")
    print("-" * 50)
    settings_data = {
        "regions": ["dublin-city", "dublin-south", "cork"],
        "min_bedrooms": 3,
        "max_price": 2500,
        "monitoring_interval": 3600,
        "max_results_per_search": 50
    }
    current_settings_msg = MessageFormatter.current_settings(settings_data)
    print(current_settings_msg)
    
    # 6. Статус мониторинга
    print("\n6️⃣ СТАТУС МОНИТОРИНГА (активен):")
    print("-" * 50)
    monitoring_status_msg = MessageFormatter.monitoring_status(True, settings_data)
    print(monitoring_status_msg)
    
    # 7. Статистика
    print("\n7️⃣ СТАТИСТИКА:")
    print("-" * 50)
    stats_msg = MessageFormatter.statistics_main("@username", 142)
    print(stats_msg)
    
    # 8. Справка
    print("\n8️⃣ СПРАВКА:")
    print("-" * 50)
    help_msg = MessageFormatter.help_message()
    print(help_msg)
    
    # 9. Пример объявления
    print("\n9️⃣ ПРИМЕР ОБЪЯВЛЕНИЯ:")
    print("-" * 50)
    property_data = {
        "title": "28 Royston, Kimmage Road West",
        "location": "Kimmage, Dublin 12",
        "price": 1918,
        "bedrooms": 3,
        "url": "https://www.daft.ie/for-rent/house-28-royston-kimmage-road-west-kimmage-dublin-12/6247980"
    }
    property_msg = MessageFormatter.property_summary(property_data)
    print(property_msg)
    
    print("\n" + "="*60)
    print("✅ ТЕСТ ЗАВЕРШЕН!")
    print("="*60)

def test_html_formatting():
    """Проверяем HTML форматирование"""
    print("\n" + "="*60)
    print("🔍 АНАЛИЗ HTML ФОРМАТИРОВАНИЯ")
    print("="*60)
    
    welcome_msg = MessageFormatter.welcome_message(is_new_user=True)
    
    html_tags = ["<b>", "</b>", "<i>", "</i>", "<code>", "</code>", "<a href=", "</a>"]
    
    print("📋 Используемые HTML теги:")
    for tag in html_tags:
        count = welcome_msg.count(tag)
        if count > 0:
            print(f"  {tag}: {count} раз")
    
    print("\n📏 Длина сообщений:")
    messages = [
        ("Приветствие", MessageFormatter.welcome_message()),
        ("Главное меню", MessageFormatter.main_menu()),
        ("Настройки", MessageFormatter.settings_menu()),
        ("Справка", MessageFormatter.help_message())
    ]
    
    for name, msg in messages:
        print(f"  {name}: {len(msg)} символов")

if __name__ == "__main__":
    test_all_messages()
    test_html_formatting()
