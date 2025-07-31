#!/usr/bin/env python3
import asyncio
import sys
import os
import aiosqlite

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def check_db_structure():
    print("🔍 Проверяем структуру базы данных...")
    
    try:
        async with aiosqlite.connect('data/enhanced_bot.db') as db:
            # Проверяем структуру таблицы user_settings
            async with db.execute("PRAGMA table_info(user_settings)") as cursor:
                columns = await cursor.fetchall()
                
                print("📋 Структура таблицы user_settings:")
                for col in columns:
                    print(f"   {col[0]}: {col[1]} ({col[2]})")
                
            # Проверяем данные пользователя
            user_id = 1665845754
            async with db.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    print(f"\n📄 Данные пользователя {user_id}:")
                    for i, value in enumerate(row):
                        print(f"   Колонка {i}: {value} (тип: {type(value)})")
                else:
                    print(f"\n❌ Пользователь {user_id} не найден")
                    
            # Проверяем всех пользователей
            async with db.execute("SELECT user_id, chat_id FROM user_settings") as cursor:
                all_users = await cursor.fetchall()
                
                print(f"\n👥 Всего пользователей: {len(all_users)}")
                for user_data in all_users:
                    print(f"   user_id: {user_data[0]}, chat_id: {user_data[1] if len(user_data) > 1 else 'НЕТ'}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_db_structure())
