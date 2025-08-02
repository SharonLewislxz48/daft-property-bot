#!/usr/bin/env python3
"""
Тест нового форматирования сообщений
"""

from bot.message_formatter import MessageFormatter

# Тестовые данные объявления
test_property = {
    "title": "8 Finnswalk, Lucan, Co. Dublin",
    "price": 2400,
    "bedrooms": 3,
    "location": "Lucan, Co. Dublin",
    "property_type": "House", 
    "description": "This property is located at the end of a cul de sac overlooking a green, has a sunny back garden and is a short stroll to parks, schools, shops and transport.",
    "url": "https://www.daft.ie/for-rent/house-8-finnswalk-lucan-co-dublin/6239177"
}

def test_new_formatting():
    """Тестируем новое HTML-форматирование"""
    print("=== ТЕСТ НОВОГО ФОРМАТИРОВАНИЯ ===\n")
    
    # Используем новый форматировщик
    formatted_message = MessageFormatter.property_summary(test_property)
    
    print("HTML-форматированное сообщение:")
    print("-" * 50)
    print(formatted_message)
    print("-" * 50)
    
    print("\nКак это будет выглядеть в Telegram:")
    print("-" * 50)
    # Симулируем как это будет отображаться
    html_preview = formatted_message.replace("<b>", "**").replace("</b>", "**")
    html_preview = html_preview.replace("<i>", "_").replace("</i>", "_")
    html_preview = html_preview.replace('<a href="', "").replace('">', " - ").replace("</a>", "")
    print(html_preview)
    print("-" * 50)

if __name__ == "__main__":
    test_new_formatting()
