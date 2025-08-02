#!/usr/bin/env python3
"""
Тест для проверки новых сообщений бота
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from bot.message_formatter import MessageFormatter

def test_message_formatting():
    """Тестируем новое форматирование сообщений"""
    
    print("=== Тест форматирования сообщений ===\n")
    
    # Тест приветственного сообщения
    print("1. Приветственное сообщение для нового пользователя:")
    print(MessageFormatter.welcome_message(True))
    print("\n" + "="*50 + "\n")
    
    # Тест главного меню
    print("2. Главное меню:")
    print(MessageFormatter.main_menu())
    print("\n" + "="*50 + "\n")
    
    # Тест настроек
    settings = {
        "regions": ["dublin-city", "cork"],
        "min_bedrooms": 3,
        "max_price": 2500,
        "monitoring_interval": 3600,
        "max_results_per_search": 100
    }
    
    print("3. Текущие настройки:")
    print(MessageFormatter.current_settings(settings))
    print("\n" + "="*50 + "\n")
    
    # Тест статуса мониторинга
    print("4. Статус мониторинга (активен):")
    print(MessageFormatter.monitoring_status(True, settings))
    print("\n" + "="*50 + "\n")
    
    # Тест справки
    print("5. Справочное сообщение:")
    print(MessageFormatter.help_message())
    print("\n" + "="*50 + "\n")
    
    # Тест объявления
    property_data = {
        "title": "Уютный дом в центре Дублина",
        "location": "Dublin City Centre",
        "price": 2200,
        "bedrooms": 3,
        "url": "https://daft.ie/example"
    }
    
    print("6. Описание объявления:")
    print(MessageFormatter.property_summary(property_data))
    print("\n" + "="*50 + "\n")
    
    print("✅ Все сообщения успешно отформатированы!")

if __name__ == "__main__":
    test_message_formatting()
