#!/usr/bin/env python3
"""
Тест токена Telegram бота
"""
import asyncio
import logging
from aiogram import Bot
from config.settings import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_token():
    """Тестируем токен Telegram бота"""
    try:
        logger.info(f"Токен: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
        logger.info(f"Chat ID: {settings.CHAT_ID}")
        
        # Создаем бота
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот найден: @{bot_info.username} ({bot_info.first_name})")
        
        # Пробуем отправить тестовое сообщение
        try:
            message = await bot.send_message(
                chat_id=settings.CHAT_ID,
                text="🤖 Тест подключения к Daft.ie Bot\n\n✅ Бот успешно подключен!"
            )
            logger.info(f"✅ Сообщение отправлено в чат {settings.CHAT_ID}")
            logger.info(f"Message ID: {message.message_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            if "chat not found" in str(e).lower():
                logger.error("Проверьте правильность CHAT_ID")
            elif "bot was blocked" in str(e).lower():
                logger.error("Бот заблокирован в чате")
        
        await bot.session.close()
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        if "token" in str(e).lower():
            logger.error("Проверьте правильность TELEGRAM_BOT_TOKEN")

if __name__ == "__main__":
    asyncio.run(test_token())
