#!/usr/bin/env python3
"""
Модифицированный главный файл для строгого режима (только реальные данные)
"""
import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from bot.handlers import TelegramBot
from database.database import Database
from parser.daft_parser import DaftParser
from parser.demo_parser import DemoParser  # НЕ используем!
from config.settings import settings
from utils.helpers import setup_logging

# Настройка логирования
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

class StrictDaftBot:
    """Daft.ie Telegram Bot - СТРОГИЙ РЕЖИМ (только реальные данные)"""
    
    def __init__(self):
        self.bot = None
        self.database = None
        self.parser = None
        self.is_running = False
        
        # СТРОГИЙ РЕЖИМ
        self.strict_mode = True
        self.demo_mode_disabled = True
        
        logger.info("🎯 StrictDaftBot инициализирован - ТОЛЬКО РЕАЛЬНЫЕ ДАННЫЕ")
    
    async def start(self):
        """Запуск бота в строгом режиме"""
        try:
            logger.info("=" * 50)
            logger.info("🎯 Daft.ie Telegram Bot - СТРОГИЙ РЕЖИМ")
            logger.info("🚫 Демо-данные ОТКЛЮЧЕНЫ")
            logger.info("🌐 Работаем ТОЛЬКО с реальными данными")
            logger.info("=" * 50)
            
            # Проверяем настройки
            if not settings.validate():
                raise ValueError("Некорректные настройки Telegram бота")
            
            logger.info("Bot configuration:")
            logger.info(f"- Chat ID: {settings.CHAT_ID}")
            logger.info(f"- Admin User ID: {settings.ADMIN_USER_ID}")
            logger.info(f"- Update Interval: {settings.UPDATE_INTERVAL} seconds")
            logger.info(f"- Database Path: {settings.DB_PATH}")
            logger.info("🎯 - STRICT MODE: Только реальные данные")
            
            # Инициализация компонентов
            self.database = Database(settings.DB_PATH)
            await self.database.init_database()
            
            # ТОЛЬКО основной парсер, демо отключен
            self.parser = DaftParser()
            logger.info("🎯 Инициализирован основной парсер (демо отключен)")
            
            self.bot = TelegramBot(
                token=settings.TELEGRAM_BOT_TOKEN,
                chat_id=settings.CHAT_ID,
                admin_user_id=settings.ADMIN_USER_ID,
                database=self.database,
                parser=self.parser,
                demo_parser=None,  # НЕ передаём демо-парсер!
                update_interval=settings.UPDATE_INTERVAL
            )
            
            self.is_running = True
            
            # Запуск бота
            await self.bot.start()
            
        except Exception as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА запуска: {e}")
            logger.error("🚫 Бот остановлен - в строгом режиме работаем только с реальными данными")
            raise
    
    async def stop(self):
        """Остановка бота"""
        logger.info("🛑 Останавливаем бота...")
        self.is_running = False
        
        if self.bot:
            await self.bot.stop()
        
        if self.parser and hasattr(self.parser, 'close'):
            await self.parser.close()
        
        if self.database and hasattr(self.database, 'close'):
            await self.database.close()
        
        logger.info("✅ Бот остановлен")

# Глобальная переменная для бота
daft_bot = None

async def main():
    """Главная функция"""
    global daft_bot
    
    try:
        # Создаём и запускаем бота
        daft_bot = StrictDaftBot()
        await daft_bot.start()
        
        # Ожидание сигнала завершения
        while daft_bot.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания (Ctrl+C)")
    except Exception as e:
        logger.error(f"Ошибка в main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if daft_bot:
            await daft_bot.stop()

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"Получен сигнал {signum}")
    if daft_bot:
        daft_bot.is_running = False

if __name__ == "__main__":
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Запуск Daft.ie Telegram Bot в СТРОГОМ РЕЖИМЕ...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("✋ Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 Application shutdown complete")
