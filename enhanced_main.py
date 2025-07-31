#!/usr/bin/env python3
"""
Главный файл для запуска улучшенного бота мониторинга недвижимости
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from bot.enhanced_bot import EnhancedPropertyBot
from bot.enhanced_bot_handlers import EnhancedPropertyBotHandlers

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CombinedBot(EnhancedPropertyBot, EnhancedPropertyBotHandlers):
    """Объединенный класс бота со всеми обработчиками"""
    
    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        # Вызываем базовую регистрацию
        super()._register_handlers()
        
        # Добавляем дополнительные обработчики
        
        # Настройки
        self.dp.callback_query.register(self.callback_show_settings, F.data == "show_settings")
        
        # Управление регионами
        self.dp.callback_query.register(self.callback_manage_regions, F.data == "manage_regions")
        self.dp.callback_query.register(self.callback_add_region, F.data == "add_region")
        self.dp.callback_query.register(self.callback_remove_region, F.data == "remove_region")
        self.dp.callback_query.register(self.callback_show_regions, F.data == "show_regions")
        self.dp.callback_query.register(self.callback_list_all_regions, F.data == "list_all_regions")
        
        # Новые обработчики категорий
        self.dp.callback_query.register(
            self.callback_category_selection,
            F.data.startswith("category_")
        )
        self.dp.callback_query.register(
            self.callback_select_combo,
            F.data.startswith("select_combo_")
        )
        self.dp.callback_query.register(
            self.callback_category_page,
            F.data.startswith("category_page_")
        )
        
        # Пагинация регионов
        self.dp.callback_query.register(
            self.callback_region_page,
            F.data.startswith("region_page_")
        )
        
        # Выбор конкретных значений
        self.dp.callback_query.register(
            self.callback_select_region,
            F.data.startswith("select_region_")
        )
        self.dp.callback_query.register(
            self.callback_remove_specific_region,
            F.data.startswith("remove_region_")
        )
        self.dp.callback_query.register(
            self.callback_select_bedrooms,
            F.data.startswith("bedrooms_")
        )
        self.dp.callback_query.register(
            self.callback_select_price,
            F.data.startswith("price_")
        )
        self.dp.callback_query.register(
            self.callback_select_interval,
            F.data.startswith("interval_")
        )
        
        # Кастомные настройки
        self.dp.callback_query.register(self.callback_custom_price, F.data == "custom_price")
        
        # Статистика
        self.dp.callback_query.register(
            self.callback_show_stats,
            F.data.startswith("stats_")
        )
        
        # Основные обработчики из enhanced_bot.py
        self.dp.callback_query.register(self.callback_main_menu, F.data == "main_menu")
        self.dp.callback_query.register(self.callback_settings, F.data == "settings")
        self.dp.callback_query.register(self.callback_statistics, F.data == "statistics")
        self.dp.callback_query.register(self.callback_help, F.data == "help")
        self.dp.callback_query.register(self.callback_start_monitoring, F.data == "start_monitoring")
        self.dp.callback_query.register(self.callback_stop_monitoring, F.data == "stop_monitoring")
        self.dp.callback_query.register(self.callback_single_search, F.data == "single_search")
        
        # Обработчики настроек
        self.dp.callback_query.register(self.callback_set_bedrooms, F.data == "set_bedrooms")
        self.dp.callback_query.register(self.callback_set_max_price, F.data == "set_max_price")
        self.dp.callback_query.register(self.callback_set_interval, F.data == "set_interval")
        
        # Поиск регионов
        self.dp.callback_query.register(self.callback_search_region, F.data == "search_region")
        
        # Служебные обработчики
        self.dp.callback_query.register(self.callback_noop, F.data == "noop")
        self.dp.callback_query.register(self.callback_current_page, F.data == "current_page")
        self.dp.callback_query.register(self.callback_recent_searches, F.data == "recent_searches")
        self.dp.callback_query.register(self.callback_show_all_results, F.data == "show_all_results")
        
        # Дополнительные состояния FSM
        from bot.enhanced_bot_handlers import BotStates
        self.dp.message.register(
            self.process_custom_price,
            StateFilter(BotStates.waiting_custom_price)
        )
        self.dp.message.register(
            self.process_region_search,
            StateFilter(BotStates.waiting_region_search)
        )


async def main():
    """Главная функция"""
    
    # Проверяем наличие токена бота
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        logger.error("Создайте файл .env и добавьте:")
        logger.error("TELEGRAM_BOT_TOKEN=ваш_токен_бота")
        return
    
    # Создаем директории если их нет
    Path("logs").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    logger.info("🚀 Запуск улучшенного бота мониторинга недвижимости")
    
    # Создаем и запускаем бота
    bot = CombinedBot(bot_token)
    
    try:
        await bot.start_bot()
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.stop_bot()
        logger.info("🛑 Бот остановлен")


if __name__ == "__main__":
    # Добавляем недостающий импорт для StateFilter
    from aiogram.filters import StateFilter
    from aiogram import F
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 Программа завершена пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
