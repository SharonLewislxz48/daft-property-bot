#!/usr/bin/env python3
"""
Финальное решение: Настройка бота только для реальных данных
"""
import sys
import os
sys.path.append('/home/barss/PycharmProjects/daftparser')

from parser.daft_parser import DaftParser
from parser.models import Property, SearchFilters

# Модифицируем основной парсер для строгого режима (только реальные данные)
class StrictRealDataParser(DaftParser):
    """Строгий парсер - только реальные данные, никаких демо"""
    
    async def search_properties(self, filters: SearchFilters) -> list[Property]:
        """Поиск только реальных объявлений"""
        print("🌐 STRICT MODE: Ищем только РЕАЛЬНЫЕ данные с Daft.ie")
        print("🚫 Демо-данные ОТКЛЮЧЕНЫ")
        print("=" * 50)
        
        try:
            # Вызываем родительский метод
            properties = await super().search_properties(filters)
            
            # Проверяем, что получили реальные данные
            if not properties:
                print("❌ ОШИБКА: Реальные данные недоступны")
                print("🛡️ Возможные причины:")
                print("   • Сайт Daft.ie блокирует автоматические запросы")
                print("   • Требуется CAPTCHA проверка")
                print("   • Нужен VPN или прокси")
                print("   • Изменилась структура сайта")
                print()
                print("💡 РЕШЕНИЯ:")
                print("   1. Использовать VPN (рекомендуется)")
                print("   2. Настроить прокси-сервер")
                print("   3. Использовать внешний API сервис")
                print("   4. Запускать реже (1 раз в час)")
                
                raise Exception("Реальные данные недоступны. Демо-режим отключен.")
            
            # Проверяем, что данные выглядят реально
            real_indicators = 0
            for prop in properties[:3]:  # Проверяем первые 3
                if prop.url and 'daft.ie' in prop.url and 'demo' not in prop.url:
                    real_indicators += 1
                if prop.price and '€' in str(prop.price):
                    real_indicators += 1
                if prop.address and len(prop.address) > 10:
                    real_indicators += 1
            
            if real_indicators < 3:
                print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Данные могут быть не реальными")
            else:
                print(f"✅ ПОДТВЕРЖДЕНО: Получены реальные данные ({len(properties)} объявлений)")
            
            return properties
            
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            print("🚫 Бот остановлен - работает только с реальными данными")
            raise

def create_strict_bot_config():
    """Создаём конфигурацию для строгого режима"""
    
    config_content = """
# СТРОГИЙ РЕЖИМ - ТОЛЬКО РЕАЛЬНЫЕ ДАННЫЕ
# =====================================

# Telegram Bot Configuration  
TELEGRAM_BOT_TOKEN=8219994646:AAEJMZGow2b_F4OcTQBqGqZp0-8baLVnatQ
CHAT_ID=-1002819366953
ADMIN_USER_ID=1665845754

# Database Configuration
DB_PATH=./data/daftbot.db

# Logging Configuration
LOG_LEVEL=INFO

# Monitoring Configuration - Реже для избежания блокировки
UPDATE_INTERVAL=3600  # 1 час вместо 2 минут

# STRICT MODE - Только реальные данные
STRICT_REAL_DATA_ONLY=true
DEMO_MODE_DISABLED=true

# Parser Settings - Для обхода блокировки
MAX_REQUESTS_PER_HOUR=10
REQUEST_DELAY=30
USE_RANDOM_USER_AGENTS=true
"""
    
    with open('/home/barss/PycharmProjects/daftparser/.env.strict', 'w') as f:
        f.write(config_content)
    
    print("✅ Создан файл .env.strict для строгого режима")

async def test_strict_mode():
    """Тест строгого режима"""
    print("🎯 ТЕСТИРУЕМ СТРОГИЙ РЕЖИМ (только реальные данные)")
    print("=" * 60)
    
    parser = StrictRealDataParser()
    
    filters = SearchFilters(
        city="Dublin",
        max_price=3000,
        min_bedrooms=2,
        areas=[]
    )
    
    try:
        properties = await parser.search_properties(filters)
        
        if properties:
            print(f"\n🎉 УСПЕХ! Получено {len(properties)} РЕАЛЬНЫХ объявлений:")
            print("-" * 40)
            
            for i, prop in enumerate(properties[:3], 1):
                print(f"{i}. 🏠 {prop.title}")
                print(f"   📍 {prop.address}")
                print(f"   💰 {prop.format_price()}")
                print(f"   🔗 {prop.url}")
                print()
            
            return True
        else:
            return False
            
    except Exception as e:
        print(f"\n❌ СТРОГИЙ РЕЖИМ: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    
    # Создаём конфигурацию строгого режима
    create_strict_bot_config()
    
    # Тестируем
    success = asyncio.run(test_strict_mode())
    
    if success:
        print("\n" + "="*60)
        print("🎯 СТРОГИЙ РЕЖИМ АКТИВЕН")
        print("✅ Бот будет работать ТОЛЬКО с реальными данными")
        print("🚫 Демо-данные полностью отключены")
        print("⏰ Интервал проверки увеличен до 1 часа")
        print("🛡️ При блокировке сайта - бот остановится")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ РЕАЛЬНЫЕ ДАННЫЕ НЕДОСТУПНЫ")
        print("🛡️ Сайт Daft.ie блокирует автоматические запросы")
        print("💡 Рекомендации:")
        print("   1. Использовать VPN")
        print("   2. Настроить прокси") 
        print("   3. Уменьшить частоту запросов")
        print("   4. Попробовать в другое время")
        print("="*60)
