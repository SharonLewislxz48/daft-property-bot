#!/usr/bin/env python3
"""
Скрипт для ручного запуска мониторинга
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append('/home/barss/PycharmProjects/daftparser')

from bot.handlers import TelegramBot
from database.database import Database
from parser.daft_parser import DaftParser
from parser.demo_parser import DemoParser
from parser.models import SearchFilters

async def run_single_monitoring_cycle():
    """Запускаем один цикл мониторинга"""
    try:
        # Инициализация компонентов
        database = Database()
        await database.init_database()
        
        # Получаем настройки поиска
        chat_id = "-1002819366953"
        bot_settings = await database.get_bot_settings(chat_id)
        if not bot_settings:
            # Создаём настройки по умолчанию
            filters = SearchFilters(
                city="Dublin",
                max_price=2500,
                min_bedrooms=3,
                areas=["Temple Bar", "Dublin 2", "Dublin 4"]
            )
            await database.save_bot_settings(chat_id, filters, is_monitoring=True)
            bot_settings = await database.get_bot_settings(chat_id)
        
        print(f"🔍 Начинаем поиск объявлений...")
        
        # Сначала пробуем демо-парсер для демонстрации
        try:
            print("🔄 Используем демо-парсер для демонстрации...")
            demo_parser = DemoParser()
            properties = await demo_parser.search_properties(bot_settings.get_search_filters())
            print(f"✅ Демо-парсер: найдено {len(properties)} объявлений")
        except Exception as e:
            print(f"❌ Ошибка демо-парсера: {e}")
            # Пробуем основной парсер
            try:
                parser = DaftParser()
                properties = await parser.search_properties(bot_settings.get_search_filters())
                print(f"✅ Основной парсер: найдено {len(properties)} объявлений")
            except Exception as e2:
                print(f"⚠️ Основной парсер также недоступен: {e2}")
                properties = []
        
        # Сохраняем новые объявления
        new_properties = []
        for prop in properties:
            # Проверяем, отправлено ли уже это объявление в этот чат
            if not await database.is_property_sent(prop.url, chat_id):
                # Сначала сохраняем объявление
                await database.save_property(prop)
                # Потом помечаем как отправленное
                await database.mark_property_sent(prop.url, chat_id)
                new_properties.append(prop)
        
        print(f"🆕 Новых объявлений: {len(new_properties)}")
        
        # Если есть новые объявления, отправляем их
        if new_properties:
            from aiogram import Bot
            from config.settings import settings
            
            def format_property_message(property_obj):
                """Форматирование сообщения об объявлении"""
                message_text = (
                    f"🏠 <b>{property_obj.title}</b>\n\n"
                    f"📍 <b>Адрес:</b> {property_obj.address}\n"
                    f"🛏️ <b>Спальни:</b> {property_obj.format_bedrooms()}\n"
                    f"💰 <b>Цена:</b> {property_obj.format_price()}\n"
                )
                
                if property_obj.bathrooms:
                    message_text += f"🚿 <b>Ванные:</b> {property_obj.bathrooms}\n"
                
                if property_obj.area:
                    message_text += f"🗺️ <b>Район:</b> {property_obj.area}\n"
                
                if property_obj.description:
                    desc = property_obj.description[:200] + "..." if len(property_obj.description) > 200 else property_obj.description
                    message_text += f"\n📝 <b>Описание:</b> {desc}\n"
                
                message_text += f"\n🔗 <a href='{property_obj.url}'>Посмотреть объявление</a>"
                
                return message_text
            
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            
            for prop in new_properties:
                message = format_property_message(prop)
                await bot.send_message(
                    chat_id=bot_settings.chat_id,
                    text=message,
                    parse_mode="HTML",
                    disable_web_page_preview=False
                )
                print(f"📤 Отправлено: {prop.title[:50]}...")
            
            await bot.session.close()
            
            print(f"✅ Отправлено {len(new_properties)} новых объявлений в группу!")
        else:
            print("ℹ️ Новых объявлений не найдено")
        
        # Закрываем соединение с базой данных
        if hasattr(database, 'close'):
            await database.close()
        
    except Exception as e:
        print(f"❌ Ошибка в мониторинге: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_single_monitoring_cycle())
