#!/usr/bin/env python3
import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.enhanced_database import EnhancedDatabase

async def test_migration():
    print("🔄 Начинаем тест миграции базы данных...")
    
    try:
        db = EnhancedDatabase('test_migration.db')
        await db.init_database()
        print('✅ Миграция базы данных выполнена успешно')
        
        # Создаем тестового пользователя
        user = await db.get_or_create_user(123456, 789012, 'test_user', 'Test', 'User')
        print(f'✅ Создан пользователь: {user}')
        
        # Проверяем настройки
        settings = await db.get_user_settings(123456)
        print(f'✅ Настройки пользователя: {settings}')
        
        # Обновляем chat_id
        await db.update_user_settings(123456, chat_id=999888)
        updated_settings = await db.get_user_settings(123456)
        print(f'✅ Обновленные настройки: chat_id = {updated_settings["chat_id"]}')
        
        print('🎉 Все тесты прошли успешно!')
        
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_migration())
