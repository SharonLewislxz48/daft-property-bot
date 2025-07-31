#!/usr/bin/env python3
"""
Гибридный режим: Попытка реальных данных + уведомления о блокировке
"""
import asyncio
from aiogram import Bot
import sys
sys.path.append('/home/barss/PycharmProjects/daftparser')

from parser.daft_parser import DaftParser
from parser.demo_parser import DemoParser
from parser.models import SearchFilters
from config.settings import settings

async def test_real_data_with_notification():
    """Тест с уведомлением о статусе данных"""
    
    print("🔍 Проверяем доступность РЕАЛЬНЫХ данных...")
    
    filters = SearchFilters(
        city="Dublin",
        max_price=3000,
        min_bedrooms=2,
        areas=[]
    )
    
    # Пробуем реальные данные
    parser = DaftParser()
    try:
        properties = await parser.search_properties(filters)
        
        if properties:
            print(f"✅ УСПЕХ! Получено {len(properties)} РЕАЛЬНЫХ объявлений")
            
            # Отправляем уведомление в Telegram
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=settings.CHAT_ID,
                text="🌐 <b>РЕАЛЬНЫЕ ДАННЫЕ ДОСТУПНЫ!</b>\n\n"
                     f"✅ Получено <b>{len(properties)}</b> актуальных объявлений с Daft.ie\n"
                     "🎯 Бот работает с реальными данными",
                parse_mode="HTML"
            )
            await bot.session.close()
            return True
            
    except Exception as e:
        print(f"❌ Реальные данные недоступны: {e}")
    
    # Если реальные недоступны - уведомляем и используем демо
    print("🔄 Переключаемся на демо-режим...")
    
    demo_parser = DemoParser()
    demo_properties = await demo_parser.search_properties(filters)
    
    if demo_properties:
        print(f"🎭 Демо-режим: {len(demo_properties)} тестовых объявлений")
        
        # Отправляем честное уведомление
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=settings.CHAT_ID,
            text="⚠️ <b>ВНИМАНИЕ: ДЕМО-РЕЖИМ</b>\n\n"
                 "🛡️ Сайт Daft.ie заблокировал автоматические запросы\n"
                 "🎭 Отправляю ТЕСТОВЫЕ объявления для демонстрации\n\n"
                 "💡 <b>Для получения реальных данных:</b>\n"
                 "• Используйте VPN\n"
                 "• Настройте прокси\n"
                 "• Уменьшите частоту запросов\n\n"
                 f"📊 Тестовых объявлений: <b>{len(demo_properties)}</b>",
            parse_mode="HTML"
        )
        
        # Отправляем демо-объявления с пометкой
        for prop in demo_properties[:2]:
            message = (
                f"🎭 <b>[ДЕМО] {prop.title}</b>\n\n"
                f"📍 <b>Адрес:</b> {prop.address}\n"
                f"🛏️ <b>Спальни:</b> {prop.format_bedrooms()}\n"
                f"💰 <b>Цена:</b> {prop.format_price()}\n\n"
                f"⚠️ <i>Это тестовое объявление для демонстрации</i>\n"
                f"🔗 <a href='{prop.url}'>Демо-ссылка</a>"
            )
            
            await bot.send_message(
                chat_id=settings.CHAT_ID,
                text=message,
                parse_mode="HTML"
            )
        
        await bot.session.close()
        return False

if __name__ == "__main__":
    print("🎯 ГИБРИДНЫЙ РЕЖИМ: Реальные данные + честные уведомления")
    print("=" * 60)
    
    success = asyncio.run(test_real_data_with_notification())
    
    if success:
        print("\n✅ Статус: РЕАЛЬНЫЕ ДАННЫЕ работают")
        print("🎯 Рекомендация: Запускайте бота в обычном режиме")
    else:
        print("\n⚠️ Статус: Сайт заблокирован, используем демо")
        print("🎭 Рекомендация: Настройте VPN для реальных данных")
