#!/usr/bin/env python3
"""
Автоматический поиск и отправка объявлений в Telegram
Запускает парсер, затем отправляет результаты в чат
"""

import asyncio
import subprocess
import logging
import sys
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_parser(min_bedrooms: int = 3, max_price: int = 2500, limit: int = 20):
    """Запускает production парсер с заданными параметрами"""
    try:
        logger.info(f"🔍 Запуск парсера: {min_bedrooms}+ спален, до €{max_price}, лимит {limit}")
        
        # Запускаем production парсер
        cmd = [
            str(Path(".venv/bin/python")),
            "production_parser.py"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            logger.info("✅ Парсер завершен успешно")
            logger.info(f"Вывод парсера:\n{stdout.decode()}")
            return True
        else:
            logger.error(f"❌ Ошибка парсера: {stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка запуска парсера: {e}")
        return False

async def send_to_telegram():
    """Отправляет результаты в Telegram"""
    try:
        logger.info("📤 Запуск отправки в Telegram")
        
        # Импортируем и запускаем отправщик
        from telegram_sender import PropertySender
        
        sender = PropertySender()
        await sender.run()
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")
        return False

async def main():
    """Основная функция - парсинг + отправка"""
    logger.info("🚀 АВТОМАТИЧЕСКИЙ ПОИСК И ОТПРАВКА ОБЪЯВЛЕНИЙ")
    logger.info("=" * 60)
    
    # Параметры поиска
    search_params = {
        'min_bedrooms': 3,
        'max_price': 2500,
        'limit': 15
    }
    
    logger.info("🎯 Параметры поиска:")
    for key, value in search_params.items():
        logger.info(f"   {key}: {value}")
    
    # Шаг 1: Запускаем парсер
    if await run_parser(**search_params):
        logger.info("✅ Этап 1: Парсинг завершен успешно")
        
        # Шаг 2: Отправляем в Telegram
        if await send_to_telegram():
            logger.info("✅ Этап 2: Отправка в Telegram завершена")
            logger.info("🎉 Все задачи выполнены успешно!")
        else:
            logger.error("❌ Этап 2: Ошибка отправки в Telegram")
            return 1
    else:
        logger.error("❌ Этап 1: Ошибка парсинга")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
