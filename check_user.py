#!/usr/bin/env python3
import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.enhanced_database import EnhancedDatabase

async def check_user_settings():
    print("🔍 Проверяем настройки пользователя 1665845754...")
    
    try:
        db = EnhancedDatabase('data/enhanced_bot.db')
        
        # Проверяем настройки пользователя из логов
        user_id = 1665845754
        settings = await db.get_user_settings(user_id)
        
        if settings:
            print(f"✅ Настройки найдены:")
            print(f"   user_id: {settings['user_id']}")
            print(f"   chat_id: {settings['chat_id']}")
            print(f"   regions: {settings['regions']}")
            print(f"   min_bedrooms: {settings['min_bedrooms']}")
            print(f"   max_price: {settings['max_price']}")
            print(f"   monitoring_interval: {settings['monitoring_interval']}")
            print(f"   is_monitoring_active: {settings['is_monitoring_active']}")
            
            # Проверяем тип чата
            if settings['chat_id'] == user_id:
                print(f"⚠️  ПРОБЛЕМА: chat_id равен user_id - сообщения идут в ЛС!")
            elif settings['chat_id'] == -1002819366953:
                print(f"✅ chat_id указывает на целевую группу")
            elif settings['chat_id'] < 0:
                print(f"✅ chat_id указывает на группу: {settings['chat_id']}")
            else:
                print(f"⚠️  chat_id указывает на ЛС: {settings['chat_id']}")
        else:
            print(f"❌ Настройки для пользователя {user_id} не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_user_settings())
