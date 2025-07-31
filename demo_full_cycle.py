#!/usr/bin/env python3
"""
Демонстрация работы системы - очистка базы и новый поиск
"""
import asyncio
import os
import sys

# Добавляем путь к проекту
sys.path.append('/home/barss/PycharmProjects/daftparser')

from bot.handlers import TelegramBot
from database.database import Database
from parser.demo_parser import DemoParser
from parser.models import SearchFilters, BotSettings
from aiogram import Bot
from config.settings import settings

async def demo_fresh_search():
    """Демонстрируем свежий поиск с отправкой объявлений"""
    try:
        print("🧹 Очищаем базу данных для демонстрации...")
        
        # Удаляем базу данных для демонстрации
        db_path = "./data/daftbot.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            print("✅ База данных очищена")
        
        # Инициализация компонентов
        database = Database()
        await database.init_database()
        
        # Настройки поиска (более мягкие для демонстрации)
        chat_id = "-1002819366953"
        filters = SearchFilters(
            city="Dublin",
            max_price=3000,  # Увеличили лимит
            min_bedrooms=2,  # Снизили требование по спальням
            areas=[]  # Убрали фильтр по районам
        )
        
        # Создаём объект настроек бота
        bot_settings = BotSettings(
            chat_id=chat_id,
            city=filters.city,
            max_price=filters.max_price,
            min_bedrooms=filters.min_bedrooms,
            areas=filters.areas,
            is_monitoring=True
        )
        await database.save_bot_settings(bot_settings)
        
        print("🔍 Запускаем поиск объявлений с демо-парсером...")
        
        # Используем демо-парсер
        demo_parser = DemoParser()
        properties = await demo_parser.search_properties(filters)
        print(f"✅ Найдено объявлений: {len(properties)}")
        
        # Отправляем объявления в группу
        if properties:
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            
            # Отправляем приветственное сообщение
            await bot.send_message(
                chat_id=chat_id,
                text="🎉 <b>Новые объявления от Daft.ie Bot!</b>\n\n"
                     f"Найдено <b>{len(properties)}</b> новых объявлений по вашим критериям:\n"
                     f"• 📍 {filters.city}\n"
                     f"• 💰 До €{filters.max_price}/месяц\n"
                     f"• 🛏️ {filters.min_bedrooms}+ спален\n"
                     f"• 🗺️ Районы: {', '.join(filters.areas[:3])}{'...' if len(filters.areas) > 3 else ''}\n\n"
                     "Объявления будут отправлены ниже:",
                parse_mode="HTML"
            )
            
            # Отправляем каждое объявление
            for i, prop in enumerate(properties, 1):
                # Сохраняем в базу
                await database.save_property(prop)
                await database.mark_property_sent(prop.url, chat_id)
                
                # Форматируем сообщение
                message_text = (
                    f"🏠 <b>{prop.title}</b>\n\n"
                    f"📍 <b>Адрес:</b> {prop.address}\n"
                    f"🛏️ <b>Спальни:</b> {prop.format_bedrooms()}\n"
                    f"💰 <b>Цена:</b> {prop.format_price()}\n"
                )
                
                if prop.bathrooms:
                    message_text += f"🚿 <b>Ванные:</b> {prop.bathrooms}\n"
                
                if prop.area:
                    message_text += f"🗺️ <b>Район:</b> {prop.area}\n"
                
                if prop.description:
                    desc = prop.description[:200] + "..." if len(prop.description) > 200 else prop.description
                    message_text += f"\n📝 <b>Описание:</b> {desc}\n"
                
                message_text += f"\n🔗 <a href='{prop.url}'>Посмотреть объявление</a>"
                
                # Отправляем сообщение
                await bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="HTML",
                    disable_web_page_preview=False
                )
                
                print(f"📤 Отправлено {i}/{len(properties)}: {prop.title[:50]}...")
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(1)
            
            # Финальное сообщение
            await bot.send_message(
                chat_id=chat_id,
                text="✅ <b>Поиск завершён!</b>\n\n"
                     "Бот будет автоматически проверять новые объявления каждые 2 минуты.\n"
                     "Для настройки фильтров используйте команды:\n"
                     "• /settings - Настройки поиска\n"
                     "• /status - Статус мониторинга\n"
                     "• /stats - Статистика",
                parse_mode="HTML"
            )
            
            await bot.session.close()
            print(f"🎉 Успешно отправлено {len(properties)} объявлений в группу!")
        else:
            print("ℹ️ Объявления не найдены")
        
        # Закрываем соединение с базой данных
        if hasattr(database, 'close'):
            await database.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Демонстрация работы Daft.ie Telegram Bot")
    print("=" * 50)
    asyncio.run(demo_fresh_search())
