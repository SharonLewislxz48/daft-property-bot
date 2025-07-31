#!/usr/bin/env python3
"""
Улучшенный Telegram бот для мониторинга недвижимости на Daft.ie
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
import time

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

from database.enhanced_database import EnhancedDatabase
from production_parser import ProductionDaftParser
from config.regions import ALL_LOCATIONS, DEFAULT_SETTINGS, LIMITS, TARGET_GROUP_ID
from bot.enhanced_keyboards import (
    get_main_menu_keyboard, get_settings_menu_keyboard, get_regions_menu_keyboard,
    get_region_categories_keyboard, get_category_regions_keyboard, 
    get_popular_combinations_keyboard, get_user_regions_keyboard, 
    get_bedrooms_keyboard, get_price_keyboard, get_interval_keyboard, 
    get_confirmation_keyboard, get_back_to_main_keyboard, get_statistics_keyboard
)

logger = logging.getLogger(__name__)

# Состояния для FSM
class BotStates(StatesGroup):
    waiting_custom_price = State()
    waiting_custom_interval = State()

class EnhancedPropertyBot:
    """Улучшенный бот для мониторинга недвижимости"""
    
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.db = EnhancedDatabase()
        self.parser = ProductionDaftParser()
        
        # Словарь активных задач мониторинга {user_id: task}
        self.monitoring_tasks: Dict[int, asyncio.Task] = {}
        
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        
        # Команды
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_status, Command("status"))
        
        # Главное меню
        self.dp.callback_query.register(self.callback_main_menu, F.data == "main_menu")
        self.dp.callback_query.register(self.callback_settings, F.data == "settings")
        self.dp.callback_query.register(self.callback_statistics, F.data == "statistics")
        self.dp.callback_query.register(self.callback_help, F.data == "help")
        
        # Мониторинг
        self.dp.callback_query.register(self.callback_start_monitoring, F.data == "start_monitoring")
        self.dp.callback_query.register(self.callback_stop_monitoring, F.data == "stop_monitoring")
        self.dp.callback_query.register(self.callback_single_search, F.data == "single_search")
        
        # Настройки
        self.dp.callback_query.register(self.callback_manage_regions, F.data == "manage_regions")
        self.dp.callback_query.register(self.callback_set_bedrooms, F.data == "set_bedrooms")
        self.dp.callback_query.register(self.callback_set_max_price, F.data == "set_max_price")
        self.dp.callback_query.register(self.callback_set_interval, F.data == "set_interval")
        self.dp.callback_query.register(self.callback_show_settings, F.data == "show_settings")
        
        # Управление регионами
        self.dp.callback_query.register(self.callback_add_region, F.data == "add_region")
        self.dp.callback_query.register(self.callback_remove_region, F.data == "remove_region")
        self.dp.callback_query.register(self.callback_show_regions, F.data == "show_regions")
        self.dp.callback_query.register(self.callback_list_all_regions, F.data == "list_all_regions")
        
        # Категории регионов
        self.dp.callback_query.register(
            self.callback_category_selection,
            F.data.startswith("category_")
        )
        self.dp.callback_query.register(
            self.callback_category_page,
            F.data.startswith("category_page_")
        )
        self.dp.callback_query.register(
            self.callback_select_combo,
            F.data.startswith("select_combo_")
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
        
        # Показ всех результатов
        self.dp.callback_query.register(self.callback_show_all_results, F.data == "show_all_results")
        
        # Состояния FSM
        self.dp.message.register(
            self.process_custom_price,
            StateFilter(BotStates.waiting_custom_price)
        )
        self.dp.message.register(
            self.process_custom_interval,
            StateFilter(BotStates.waiting_custom_interval)
        )
    
    async def start_bot(self):
        """Запуск бота"""
        await self.db.init_database()
        logger.info("Бот запущен")
        await self.dp.start_polling(self.bot)
    
    async def stop_bot(self):
        """Остановка бота"""
        # Останавливаем все задачи мониторинга
        for task in self.monitoring_tasks.values():
            task.cancel()
        self.monitoring_tasks.clear()
        
        await self.bot.session.close()
        logger.info("Бот остановлен")
    
    # === КОМАНДЫ ===
    
    async def cmd_start(self, message: Message, state: FSMContext):
        """Обработчик команды /start"""
        await state.clear()
        
        user = await self.db.get_or_create_user(
            user_id=message.from_user.id,
            chat_id=message.chat.id,  # Добавляем ID чата
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        welcome_text = "🏠 **Добро пожаловать в бот мониторинга недвижимости Daft.ie!**\\n\\n"
        
        if not user["exists"]:
            welcome_text += "🎉 Вы новый пользователь! Настройки по умолчанию уже созданы.\\n\\n"
        
        welcome_text += (
            "✨ **Возможности бота:**\\n"
            "🔍 Автоматический мониторинг новых объявлений\\n"
            "⚙️ Гибкие настройки поиска (регионы, цена, спальни)\\n"
            "📊 Статистика и история поиска\\n"
            "📱 Уведомления о новых объявлениях\\n\\n"
            "Выберите действие в меню ниже:"
        )
        
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    
    async def cmd_help(self, message: Message):
        """Обработчик команды /help"""
        help_text = (
            "❓ **Помощь по использованию бота**\\n\\n"
            "**Основные функции:**\\n"
            "• `/start` - Запуск бота и главное меню\\n"
            "• `/status` - Статус мониторинга\\n"
            "• `/help` - Эта справка\\n\\n"
            "**Мониторинг:**\\n"
            "▶️ Запустить - начать автоматический поиск\\n"
            "⏹️ Остановить - прекратить мониторинг\\n"
            "🔍 Разовый поиск - найти объявления сейчас\\n\\n"
            "**Настройки:**\\n"
            "🏘️ Регионы - выбор районов для поиска\\n"
            "🛏️ Спальни - минимальное количество\\n"
            "💰 Цена - максимальный бюджет\\n"
            "⏰ Интервал - частота проверки\\n\\n"
            "**Статистика:**\\n"
            "📊 Просмотр найденных объявлений\\n"
            "📋 История поиска\\n"
        )
        
        await message.answer(
            help_text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="Markdown"
        )
    
    async def cmd_status(self, message: Message):
        """Обработчик команды /status"""
        user_id = message.from_user.id
        settings = await self.db.get_user_settings(user_id)
        
        if not settings:
            await message.answer("❌ Настройки не найдены. Используйте /start")
            return
        
        is_monitoring = user_id in self.monitoring_tasks and not self.monitoring_tasks[user_id].done()
        status_emoji = "✅" if is_monitoring else "⏸️"
        status_text = "Активен" if is_monitoring else "Остановлен"
        
        regions_text = ", ".join([
            ALL_LOCATIONS.get(region, region) for region in settings["regions"]
        ])
        
        interval_text = self._format_interval(settings["monitoring_interval"])
        
        status_msg = (
            f"📊 **Статус мониторинга:** {status_emoji} {status_text}\\n\\n"
            f"⚙️ **Текущие настройки:**\\n"
            f"🏘️ Регионы: {regions_text}\\n"
            f"🛏️ Минимум спален: {settings['min_bedrooms']}\\n"
            f"💰 Максимальная цена: €{settings['max_price']}\\n"
            f"⏰ Интервал проверки: {interval_text}\\n"
            f"📊 Лимит результатов: {settings['max_results_per_search']}"
        )
        
        await message.answer(
            status_msg,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    
    # === ГЛАВНОЕ МЕНЮ ===
    
    async def callback_main_menu(self, callback: CallbackQuery):
        """Возврат в главное меню"""
        await callback.message.edit_text(
            "🏠 **Главное меню**\\n\\nВыберите действие:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_settings(self, callback: CallbackQuery):
        """Меню настроек"""
        await callback.message.edit_text(
            "⚙️ **Настройки бота**\\n\\nВыберите параметр для изменения:",
            reply_markup=get_settings_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_statistics(self, callback: CallbackQuery):
        """Меню статистики"""
        user_id = callback.from_user.id
        
        # Получаем базовую статистику
        total_properties = await self.db.get_user_properties_count(user_id)
        
        stats_text = (
            f"📊 **Статистика**\\n\\n"
            f"👤 Пользователь: {callback.from_user.first_name}\\n"
            f"🏠 Найдено объявлений: {total_properties}\\n\\n"
            "Выберите период для подробной статистики:"
        )
        
        try:
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_statistics_keyboard(),
                parse_mode="Markdown"
            )
        except Exception as e:
            # Если сообщение не изменилось, просто отвечаем
            await callback.answer("📊 Статистика обновлена")
            return
            
        await callback.answer()
    
    async def callback_help(self, callback: CallbackQuery):
        """Показать помощь"""
        help_text = (
            "❓ **Помощь по использованию бота**\\n\\n"
            "**Мониторинг:**\\n"
            "▶️ Запустить - начать автоматический поиск\\n"
            "⏹️ Остановить - прекратить мониторинг\\n"
            "🔍 Разовый поиск - найти объявления сейчас\\n\\n"
            "**Настройки:**\\n"
            "🏘️ Регионы - выбор районов для поиска\\n"
            "🛏️ Спальни - минимальное количество\\n"
            "💰 Цена - максимальный бюджет\\n"
            "⏰ Интервал - частота проверки\\n\\n"
            "Бот автоматически отслеживает новые объявления и присылает уведомления."
        )
        
        await callback.message.edit_text(
            help_text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    # === МОНИТОРИНГ ===
    
    async def callback_start_monitoring(self, callback: CallbackQuery):
        """Запуск автоматического мониторинга"""
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id
        
        # Обновляем chat_id в настройках пользователя
        await self.db.update_user_settings(user_id, chat_id=chat_id)
        
        # Проверяем, не запущен ли уже мониторинг
        if user_id in self.monitoring_tasks and not self.monitoring_tasks[user_id].done():
            await callback.message.edit_text(
                "⚠️ Мониторинг уже запущен!",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        # Получаем настройки пользователя
        settings = await self.db.get_user_settings(user_id)
        if not settings:
            await callback.message.edit_text(
                "❌ Настройки не найдены. Используйте /start",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        # Обновляем статус мониторинга в БД
        await self.db.update_user_settings(user_id, is_monitoring_active=True)
        
        # Запускаем задачу мониторинга
        task = asyncio.create_task(self._monitoring_loop(user_id))
        self.monitoring_tasks[user_id] = task
        
        interval_text = self._format_interval(settings["monitoring_interval"])
        
        await callback.message.edit_text(
            f"✅ **Мониторинг запущен!**\\n\\n"
            f"⏰ Интервал проверки: {interval_text}\\n"
            f"🔍 Поиск будет выполняться автоматически\\n\\n"
            f"Вы получите уведомление о каждом новом объявлении.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("Мониторинг запущен!")
    
    async def callback_stop_monitoring(self, callback: CallbackQuery):
        """Остановка автоматического мониторинга"""
        user_id = callback.from_user.id
        
        # Проверяем, запущен ли мониторинг
        if user_id not in self.monitoring_tasks or self.monitoring_tasks[user_id].done():
            await callback.message.edit_text(
                "⚠️ Мониторинг не запущен!",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        # Останавливаем задачу
        self.monitoring_tasks[user_id].cancel()
        del self.monitoring_tasks[user_id]
        
        # Обновляем статус в БД
        await self.db.update_user_settings(user_id, is_monitoring_active=False)
        
        await callback.message.edit_text(
            "⏹️ **Мониторинг остановлен**\\n\\n"
            "Автоматический поиск новых объявлений прекращен.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("Мониторинг остановлен!")
    
    async def callback_single_search(self, callback: CallbackQuery):
        """Разовый поиск"""
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id
        
        # Обновляем chat_id в настройках пользователя
        await self.db.update_user_settings(user_id, chat_id=chat_id)
        
        settings = await self.db.get_user_settings(user_id)
        
        if not settings:
            await callback.message.edit_text(
                "❌ Настройки не найдены. Используйте /start",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        await callback.message.edit_text(
            "🔍 **Выполняется поиск...**\\n\\nПожалуйста, подождите.",
            parse_mode="Markdown"
        )
        await callback.answer()
        
        # Выполняем поиск
        try:
            start_time = time.time()
            results = await self._perform_search(settings)
            execution_time = time.time() - start_time
            
            if results:
                # Проверяем новые объявления
                search_params = self._get_search_params(settings)
                new_properties = await self.db.get_new_properties(user_id, results, search_params)
                
                # Логируем результат
                await self.db.log_monitoring_session(
                    user_id, search_params, len(results), len(new_properties), execution_time
                )
                
                if new_properties:
                    # Отправляем новые объявления в текущий чат
                    await self._send_new_properties(user_id, new_properties, chat_id)
                    
                    await callback.message.edit_text(
                        f"✅ **Поиск завершен!**\\n\\n"
                        f"📊 Найдено объявлений: {len(results)}\\n"
                        f"🆕 Новых объявлений: {len(new_properties)}\\n"
                        f"⏱️ Время выполнения: {execution_time:.1f}с",
                        reply_markup=get_main_menu_keyboard(),
                        parse_mode="Markdown"
                    )
                else:
                    # Создаем клавиатуру с опцией показать все
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔍 Показать все найденные", callback_data="show_all_results")],
                        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                    ])
                    
                    await callback.message.edit_text(
                        f"✅ **Поиск завершен!**\\n\\n"
                        f"📊 Найдено объявлений: {len(results)}\\n"
                        f"🔄 Все объявления уже известны\\n"
                        f"⏱️ Время выполнения: {execution_time:.1f}с\\n\\n"
                        f"💡 Хотите увидеть все найденные объявления?",
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    
                    # Сохраняем результаты в кэш для показа
                    await self.db.cache_search_results(user_id, results)
            else:
                await callback.message.edit_text(
                    "❌ **Объявления не найдены**\\n\\n"
                    "Попробуйте изменить параметры поиска.",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при разовом поиске для пользователя {user_id}: {e}")
            await callback.message.edit_text(
                f"❌ **Ошибка при поиске**\\n\\n{str(e)[:100]}...",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _format_interval(self, seconds: int) -> str:
        """Форматирует интервал в читаемый вид"""
        if seconds < 60:
            return f"{seconds} сек"
        elif seconds < 3600:
            return f"{seconds // 60} мин"
        elif seconds < 86400:
            return f"{seconds // 3600} ч"
        else:
            return f"{seconds // 86400} дн"
    
    def _get_search_params(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Создает параметры для поиска"""
        return {
            "regions": settings["regions"],
            "min_bedrooms": settings["min_bedrooms"],
            "max_price": settings["max_price"],
            "max_results": settings["max_results_per_search"]
        }
    
    async def _perform_search(self, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Выполняет поиск недвижимости"""
        all_results = []
        
        # Поиск по каждому региону
        for region in settings["regions"]:
            try:
                region_results = await self.parser.search_properties(
                    min_bedrooms=settings["min_bedrooms"],
                    max_price=settings["max_price"],
                    location=region,
                    limit=settings["max_results_per_search"] // len(settings["regions"])
                )
                all_results.extend(region_results)
            except asyncio.CancelledError:
                logger.info(f"Поиск в регионе {region} был отменен")
                raise  # Переподнимаем для правильной обработки в мониторинге
            except Exception as e:
                logger.error(f"Ошибка поиска в регионе {region}: {e}")
                continue
        
        return all_results
    
    async def _monitoring_loop(self, user_id: int):
        """Основной цикл мониторинга"""
        logger.info(f"Запущен мониторинг для пользователя {user_id}")
        
        while True:
            try:
                start_time = time.time()
                
                # Получаем актуальные настройки пользователя
                settings = await self.db.get_user_settings(user_id)
                if not settings:
                    logger.error(f"Настройки пользователя {user_id} не найдены, останавливаем мониторинг")
                    break
                
                # Выполняем поиск
                results = await self._perform_search(settings)
                execution_time = time.time() - start_time
                
                if results:
                    # Проверяем новые объявления
                    search_params = self._get_search_params(settings)
                    new_properties = await self.db.get_new_properties(user_id, results, search_params)
                    
                    # Логируем результат
                    await self.db.log_monitoring_session(
                        user_id, search_params, len(results), len(new_properties), execution_time
                    )
                    
                    if new_properties:
                        # Отправляем новые объявления в тот чат, откуда был запущен мониторинг
                        target_chat = settings.get("chat_id", TARGET_GROUP_ID)
                        await self._send_new_properties(user_id, new_properties, target_chat)
                        
                        # Уведомление о мониторинге - отправляем в тот же чат
                        await self.bot.send_message(
                            target_chat,
                            f"🔍 **Мониторинг:** найдено {len(new_properties)} новых объявлений!",
                            parse_mode="Markdown"
                        )
                    else:
                        logger.info(f"Мониторинг пользователя {user_id}: новых объявлений нет")
                
                # Ждем следующей проверки
                await asyncio.sleep(settings["monitoring_interval"])
                
            except asyncio.CancelledError:
                logger.info(f"Мониторинг пользователя {user_id} остановлен")
                break
            except Exception as e:
                logger.error(f"Ошибка в мониторинге пользователя {user_id}: {e}")
                
                # Получаем настройки для логирования ошибки
                settings = await self.db.get_user_settings(user_id)
                if settings:
                    # Логируем ошибку
                    await self.db.log_monitoring_session(
                        user_id, self._get_search_params(settings), 0, 0, 0, "error", str(e)
                    )
                    
                    # Ждем перед повторной попыткой
                    await asyncio.sleep(settings["monitoring_interval"])
                else:
                    logger.error(f"Не удалось получить настройки для пользователя {user_id}")
                    break
    
    async def _send_new_properties(self, user_id: int, properties: List[Dict[str, Any]], chat_id: int = None):
        """Отправляет новые объявления в указанный чат"""
        sent_urls = []
        target_chat = chat_id or user_id  # Используем chat_id, если задан, иначе user_id
        
        # Получаем информацию о пользователе только для специальной целевой группы
        user_info = ""
        if target_chat == TARGET_GROUP_ID:
            try:
                # Получаем информацию о пользователе из базы
                import aiosqlite
                async with aiosqlite.connect(self.db.db_path) as db:
                    async with db.execute(
                        "SELECT username, first_name FROM users WHERE user_id = ?", (user_id,)
                    ) as cursor:
                        user_row = await cursor.fetchone()
                    
                    if user_row:
                        username, first_name = user_row
                        if username:
                            user_info = f"\n👤 От пользователя: @{username}"
                        elif first_name:
                            user_info = f"\n👤 От пользователя: {first_name}"
                        else:
                            user_info = f"\n👤 От пользователя: {user_id}"
                    else:
                        user_info = f"\n👤 От пользователя: {user_id}"
            except Exception as e:
                logger.error(f"Ошибка получения информации о пользователе {user_id}: {e}")
                user_info = f"\n👤 От пользователя: {user_id}"
        
        for prop in properties:
            try:
                message = self._format_property_message(prop, user_info)
                await self.bot.send_message(target_chat, message, parse_mode="Markdown")
                sent_urls.append(prop["url"])
            except Exception as e:
                logger.error(f"Ошибка отправки объявления в чат {target_chat}: {e}")
        
        # Отмечаем отправленные объявления
        if sent_urls:
            await self.db.mark_properties_as_sent(user_id, sent_urls)
    
    def _format_property_message(self, prop: Dict[str, Any], user_info: str = "") -> str:
        """Форматирует объявление для отправки"""
        title = prop.get('title', 'Без названия')
        price = f"€{prop['price']}" if prop.get('price') else 'Цена не указана'
        bedrooms = f"{prop['bedrooms']} спален" if prop.get('bedrooms') else 'Спальни не указаны'
        location = prop.get('location', 'Локация не указана')
        property_type = prop.get('property_type', 'Тип не указан')
        url = prop.get('url', '')
        
        message = (
            f"🏠 **{title}**\\n\\n"
            f"💰 {price}\\n"
            f"🛏️ {bedrooms}\\n"
            f"📍 {location}\\n"
            f"🏠 {property_type}"
        )
        
        # Добавляем информацию о пользователе, если есть
        if user_info:
            message += user_info
        
        message += "\\n\\n"
        
        if prop.get('description'):
            desc = prop['description'][:150] + "..." if len(prop['description']) > 150 else prop['description']
            message += f"📝 {desc}\\n\\n"
        
        if url:
            message += f"🔗 [Посмотреть объявление]({url})"
        
        return message

    # === ДОПОЛНИТЕЛЬНЫЕ ОБРАБОТЧИКИ ===
    
    async def callback_category_selection(self, callback: CallbackQuery):
        """Обработчик выбора категории регионов"""
        category = callback.data.replace("category_", "")
        
        if category == "popular":
            await callback.message.edit_text(
                "⭐ **Популярные комбинации**\n\n"
                "Выберите готовую комбинацию регионов:",
                reply_markup=get_popular_combinations_keyboard(),
                parse_mode="Markdown"
            )
        else:
            # Названия категорий
            category_names = {
                "dublin_areas": "🏙️ Районы Дублина",
                "main_cities": "🌆 Основные города",
                "republic_counties": "🗺️ Графства Ирландии", 
                "northern_counties": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Северная Ирландия"
            }
            
            title = category_names.get(category, "Регионы")
            await callback.message.edit_text(
                f"{title}\n\n"
                "Выберите регионы для поиска:",
                reply_markup=get_category_regions_keyboard(category, page=0),
                parse_mode="Markdown"
            )
        
        await callback.answer()
    
    async def callback_category_page(self, callback: CallbackQuery):
        """Обработчик пагинации категорий"""
        # Формат: category_page_{category}_{page}
        logger.info(f"Callback data: {callback.data}")
        data_parts = callback.data.split("_", 3)  # Разбиваем максимум на 4 части
        logger.info(f"Data parts: {data_parts}")
        
        if len(data_parts) >= 4:
            category = data_parts[2]
            page = int(data_parts[3])
        else:
            # Fallback для старого формата
            category = data_parts[2] if len(data_parts) > 2 else "dublin_areas"
            page = int(data_parts[3]) if len(data_parts) > 3 else 0
        
        logger.info(f"Category: {category}, Page: {page}")
        
        # Названия категорий
        category_names = {
            "dublin_areas": "🏙️ Районы Дублина",
            "main_cities": "🌆 Основные города",
            "republic_counties": "🗺️ Графства Ирландии", 
            "northern_counties": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Северная Ирландия"
        }
        
        title = category_names.get(category, "Регионы")
        
        # Обновляем весь текст сообщения с правильным заголовком
        await callback.message.edit_text(
            f"{title}\n\n"
            "Выберите регионы для поиска:",
            reply_markup=get_category_regions_keyboard(category, page),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_select_combo(self, callback: CallbackQuery):
        """Обработчик выбора популярной комбинации"""
        from config.regions import POPULAR_COMBINATIONS
        
        combo_key = callback.data.replace("select_combo_", "")
        user_id = callback.from_user.id
        
        if combo_key in POPULAR_COMBINATIONS:
            regions = POPULAR_COMBINATIONS[combo_key]
            
            # Обновляем настройки пользователя
            await self.db.update_user_settings(
                user_id,
                regions=regions
            )
            
            combo_names = {
                "dublin_central": "🏛️ Центральный Дублин",
                "dublin_south": "🌳 Южный Дублин",
                "dublin_north": "🏢 Северный Дублин", 
                "dublin_west": "🏘️ Западный Дублин",
                "major_cities": "🌆 Крупные города",
                "student_areas": "🎓 Студенческие районы"
            }
            
            combo_name = combo_names.get(combo_key, combo_key)
            regions_text = ", ".join(regions[:3])
            if len(regions) > 3:
                regions_text += f" и еще {len(regions) - 3}"
            
            await callback.message.edit_text(
                f"✅ **Выбрана комбинация: {combo_name}**\n\n"
                f"📍 Регионы: {regions_text}\n"
                f"📊 Всего регионов: {len(regions)}",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                "❌ Комбинация не найдена",
                reply_markup=get_main_menu_keyboard()
            )
        
        await callback.answer()

    async def callback_manage_regions(self, callback: CallbackQuery):
        """Меню управления регионами"""
        await callback.message.edit_text(
            "🏘️ **Управление регионами поиска**\n\n"
            "Выберите действие:",
            reply_markup=get_regions_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()

    async def callback_add_region(self, callback: CallbackQuery):
        """Добавление региона - переходим к категориям"""
        await callback.message.edit_text(
            "➕ **Добавить регион**\n\n"
            "Выберите категорию регионов:",
            reply_markup=get_region_categories_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()

    async def callback_select_region(self, callback: CallbackQuery):
        """Выбор региона для добавления"""
        region_key = callback.data.replace("select_region_", "")
        user_id = callback.from_user.id
        
        settings = await self.db.get_user_settings(user_id)
        if not settings:
            await callback.answer("❌ Настройки не найдены")
            return
        
        current_regions = settings.get("regions", [])
        
        if region_key in current_regions:
            await callback.answer("⚠️ Регион уже добавлен", show_alert=True)
            return
        
        # Добавляем регион
        current_regions.append(region_key)
        await self.db.update_user_settings(user_id, regions=current_regions)
        
        region_name = ALL_LOCATIONS.get(region_key, region_key)
        
        await callback.message.edit_text(
            f"✅ **Регион добавлен!**\n\n"
            f"📍 {region_name}\n"
            f"📊 Всего регионов: {len(current_regions)}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer(f"✅ Добавлен: {region_name}")

    async def callback_show_all_results(self, callback: CallbackQuery):
        """Показать все найденные объявления"""
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id  # ID чата, где была нажата кнопка
        
        # Получаем кэшированные результаты
        results = await self.db.get_cached_search_results(user_id)
        
        if not results:
            await callback.message.edit_text(
                "❌ Результаты поиска не найдены",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        await callback.message.edit_text(
            f"📤 **Отправляю {len(results)} объявлений...**",
            parse_mode="Markdown"
        )
        await callback.answer()
        
        # Отправляем в тот же чат, где была нажата кнопка
        await self._send_new_properties(user_id, results, chat_id)
        
        await callback.message.edit_text(
            f"✅ **Отправлено!**\n\n"
            f"📤 {len(results)} объявлений отправлено в {'группу' if chat_id < 0 else 'личные сообщения'}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )


# Дополнительные обработчики будут добавлены в следующей части...
