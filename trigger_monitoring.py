#!/usr/bin/env python3
"""
Скрипт для запуска мониторинга через API
"""
import asyncio
from aiogram import Bot
from config.settings import settings

async def start_monitoring():
    """Отправляем команду старта мониторинга"""
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    try:
        # Отправляем команду запуска мониторинга
        await bot.send_message(
            chat_id=settings.CHAT_ID,
            text="🚀 Запускаем мониторинг Daft.ie!\n\n"
                 "Бот будет автоматически искать новые объявления каждые 2 минуты.\n"
                 "Поиск ведётся по следующим критериям:\n"
                 "• 📍 Dublin\n"
                 "• 💰 До €2,500/месяц\n"
                 "• 🛏️ 3+ спальни"
        )
        
        print("✅ Сообщение о запуске отправлено")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(start_monitoring())
