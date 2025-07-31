#!/usr/bin/env python3
import asyncio
import sys
import os
import aiosqlite

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def migrate_production_db():
    print("🔧 Начинаем миграцию продакшен базы данных...")
    
    try:
        async with aiosqlite.connect('data/enhanced_bot.db') as db:
            # Проверяем, есть ли уже поле chat_id
            async with db.execute("PRAGMA table_info(user_settings)") as cursor:
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
            if 'chat_id' not in column_names:
                print("📝 Добавляем поле chat_id в таблицу user_settings...")
                
                # Добавляем поле chat_id
                await db.execute("ALTER TABLE user_settings ADD COLUMN chat_id INTEGER")
                await db.commit()
                print("✅ Поле chat_id добавлено")
                
                # Устанавливаем chat_id = user_id для всех существующих пользователей
                await db.execute("UPDATE user_settings SET chat_id = user_id WHERE chat_id IS NULL")
                affected_rows = db.total_changes
                await db.commit()
                print(f"✅ Обновлено {affected_rows} записей: chat_id = user_id")
                
                # Если есть конкретный пользователь, который должен получать сообщения в группу,
                # можно обновить его chat_id вручную:
                target_group_id = -1002819366953
                user_id = 1665845754
                
                await db.execute(
                    "UPDATE user_settings SET chat_id = ? WHERE user_id = ?",
                    (target_group_id, user_id)
                )
                await db.commit()
                print(f"✅ Пользователь {user_id} теперь получает сообщения в группу {target_group_id}")
                
            else:
                print("ℹ️  Поле chat_id уже существует, миграция не требуется")
                
                # Все равно проверим и обновим пользователя для группы
                target_group_id = -1002819366953
                user_id = 1665845754
                
                await db.execute(
                    "UPDATE user_settings SET chat_id = ? WHERE user_id = ?",
                    (target_group_id, user_id)
                )
                await db.commit()
                print(f"✅ Пользователь {user_id} настроен на группу {target_group_id}")
            
            # Проверяем итоговое состояние
            async with db.execute("SELECT user_id, chat_id FROM user_settings") as cursor:
                all_users = await cursor.fetchall()
                
                print(f"\n📊 Итоговое состояние ({len(all_users)} пользователей):")
                for user_data in all_users:
                    user_id, chat_id = user_data
                    chat_type = "группа" if chat_id < 0 else "ЛС"
                    print(f"   user_id: {user_id}, chat_id: {chat_id} ({chat_type})")
                    
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(migrate_production_db())
