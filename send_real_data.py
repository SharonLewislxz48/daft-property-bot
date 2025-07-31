#!/usr/bin/env python3
"""
Отправка тестового сообщения в группу с реальными данными
"""
import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append('/home/barss/PycharmProjects/daftparser')

async def send_test_message():
    print('📤 Отправляем тестовое сообщение с реальными данными...')
    
    # Импортируем необходимые модули
    from aiogram import Bot
    from parser.final_daft_parser import FinalDaftParser
    
    # Инициализируем бота
    bot = Bot(token="8219994646:AAEJMZGow2b_F4OcTQBqGqZp0-8baLVnatQ")
    chat_id = "-1002819366953"
    
    parser = FinalDaftParser()
    
    try:
        # Получаем свежие данные через наш парсер с обходом
        print("🔍 Получаем свежие данные...")
        properties = await parser.search_with_bypass("Dublin", 2500, 3)
        
        if properties:
            print(f"✅ Найдено {len(properties)} объявлений!")
            
            # Формируем сообщение
            message = f"🏠 *Новые объявления в Дублине* ({datetime.now().strftime('%H:%M')})\n"
            message += f"💰 Макс. цена: €2,500\n"
            message += f"🛏️ Минимум спален: 3\n\n"
            
            # Добавляем первые 5 объявлений
            for i, prop in enumerate(properties[:5], 1):
                message += f"*{i}. {prop['title']}*\n"
                message += f"💰 {prop['price']}\n"
                message += f"📍 {prop['address']}\n"
                if prop.get('bedrooms'):
                    message += f"🛏️ {prop['bedrooms']} спален\n"
                message += f"🔗 [Смотреть объявление]({prop['url']})\n\n"
            
            message += f"📊 Всего найдено: {len(properties)} объявлений\n"
            message += f"🔄 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            message += f"✅ *Используются РЕАЛЬНЫЕ данные с daft.ie*"
            
            # Отправляем сообщение
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
            print("✅ Сообщение отправлено в группу!")
            print(f"📋 Отправлено {len(properties[:5])} объявлений из {len(properties)} найденных")
            
        else:
            await bot.send_message(
                chat_id=chat_id,
                text="⚠️ Объявления не найдены, проверяю парсер...",
                parse_mode="Markdown"
            )
            print("⚠️ Объявления не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ Ошибка при получении данных: {str(e)}",
            parse_mode="Markdown"
        )
        import traceback
        traceback.print_exc()
        
    finally:
        await parser.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(send_test_message())
