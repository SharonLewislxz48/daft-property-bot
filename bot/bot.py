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

from database.database import EnhancedDatabase
from parser.production_parser import ProductionDaftParser
from config.regions import ALL_LOCATIONS, DEFAULT_SETTINGS, LIMITS
from bot.keyboards import (
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
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        welcome_text = "🏠 **Добро пожаловать в бот мониторинга недвижимости Daft.ie!**\n\n"
        
        if not user["exists"]:
            welcome_text += "🎉 Вы новый пользователь! Настройки по умолчанию уже созданы.\n\n"
        
        welcome_text += (
            "✨ **Возможности бота:**\n"
            "🔍 Автоматический мониторинг новых объявлений\n"
            "⚙️ Гибкие настройки поиска (регионы, цена, спальни)\n"
            "📊 Статистика и история поиска\n"
            "📱 Уведомления о новых объявлениях\n\n"
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
            "❓ **Помощь по использованию бота**\n\n"
            "**Основные функции:**\n"
            "• `/start` - Запуск бота и главное меню\n"
            "• `/status` - Статус мониторинга\n"
            "• `/help` - Эта справка\n\n"
            "**Мониторинг:**\n"
            "▶️ Запустить - начать автоматический поиск\n"
            "⏹️ Остановить - прекратить мониторинг\n"
            "🔍 Разовый поиск - найти объявления сейчас\n\n"
            "**Настройки:**\n"
            "🏘️ Регионы - выбор районов для поиска\n"
            "🛏️ Спальни - минимальное количество\n"
            "💰 Цена - максимальный бюджет\n"
            "⏰ Интервал - частота проверки\n\n"
            "**Статистика:**\n"
            "📊 Просмотр найденных объявлений\n"
            "📋 История поиска\n"
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
            f"📊 **Статус мониторинга:** {status_emoji} {status_text}\n\n"
            f"⚙️ **Текущие настройки:**\n"
            f"🏘️ Регионы: {regions_text}\n"
            f"🛏️ Минимум спален: {settings['min_bedrooms']}\n"
            f"💰 Максимальная цена: €{settings['max_price']}\n"
            f"⏰ Интервал проверки: {interval_text}\n"
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
            "🏠 **Главное меню**\n\nВыберите действие:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_settings(self, callback: CallbackQuery):
        """Меню настроек"""
        await callback.message.edit_text(
            "⚙️ **Настройки бота**\n\nВыберите параметр для изменения:",
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
            f"📊 **Статистика**\n\n"
            f"👤 Пользователь: {callback.from_user.first_name}\n"
            f"🏠 Найдено объявлений: {total_properties}\n\n"
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
            "❓ **Помощь по использованию бота**\n\n"
            "**Мониторинг:**\n"
            "▶️ Запустить - начать автоматический поиск\n"
            "⏹️ Остановить - прекратить мониторинг\n"
            "🔍 Разовый поиск - найти объявления сейчас\n\n"
            "**Настройки:**\n"
            "🏘️ Регионы - выбор районов для поиска\n"
            "🛏️ Спальни - минимальное количество\n"
            "💰 Цена - максимальный бюджет\n"
            "⏰ Интервал - частота проверки\n\n"
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
        task = asyncio.create_task(self._monitoring_loop(user_id, settings))
        self.monitoring_tasks[user_id] = task
        
        interval_text = self._format_interval(settings["monitoring_interval"])
        
        await callback.message.edit_text(
            f"✅ **Мониторинг запущен!**\n\n"
            f"⏰ Интервал проверки: {interval_text}\n"
            f"🔍 Поиск будет выполняться автоматически\n\n"
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
            "⏹️ **Мониторинг остановлен**\n\n"
            "Автоматический поиск новых объявлений прекращен.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("Мониторинг остановлен!")
    
    async def callback_single_search(self, callback: CallbackQuery):
        """Разовый поиск"""
        user_id = callback.from_user.id
        settings = await self.db.get_user_settings(user_id)
        
        if not settings:
            await callback.message.edit_text(
                "❌ Настройки не найдены. Используйте /start",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        await callback.message.edit_text(
            "🔍 **Выполняется поиск...**\n\nПожалуйста, подождите.",
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
                    # Отправляем новые объявления
                    await self._send_new_properties(user_id, new_properties)
                    
                    await callback.message.edit_text(
                        f"✅ **Поиск завершен!**\n\n"
                        f"📊 Найдено объявлений: {len(results)}\n"
                        f"🆕 Новых объявлений: {len(new_properties)}\n"
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
                        f"✅ **Поиск завершен!**\n\n"
                        f"📊 Найдено объявлений: {len(results)}\n"
                        f"🔄 Все объявления уже известны\n"
                        f"⏱️ Время выполнения: {execution_time:.1f}с\n\n"
                        f"💡 Хотите увидеть все найденные объявления?",
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    
                    # Сохраняем результаты в кэш для показа
                    await self.db.cache_search_results(user_id, results)
            else:
                await callback.message.edit_text(
                    "❌ **Объявления не найдены**\n\n"
                    "Попробуйте изменить параметры поиска.",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при разовом поиске для пользователя {user_id}: {e}")
            await callback.message.edit_text(
                f"❌ **Ошибка при поиске**\n\n{str(e)[:100]}...",
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
            except Exception as e:
                logger.error(f"Ошибка поиска в регионе {region}: {e}")
                continue
        
        return all_results
    
    async def _monitoring_loop(self, user_id: int, settings: Dict[str, Any]):
        """Основной цикл мониторинга"""
        logger.info(f"Запущен мониторинг для пользователя {user_id}")
        
        while True:
            try:
                start_time = time.time()
                
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
                        # Отправляем новые объявления пользователю
                        await self._send_new_properties(user_id, new_properties)
                        
                        # Уведомление о мониторинге
                        await self.bot.send_message(
                            user_id,
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
                
                # Логируем ошибку
                await self.db.log_monitoring_session(
                    user_id, self._get_search_params(settings), 0, 0, 0, "error", str(e)
                )
                
                # Ждем перед повторной попыткой
                await asyncio.sleep(settings["monitoring_interval"])
    
    async def _send_new_properties(self, user_id: int, properties: List[Dict[str, Any]]):
        """Отправляет новые объявления пользователю с задержкой между сообщениями"""
        sent_urls = []
        
        for i, prop in enumerate(properties):
            try:
                message = self._format_property_message(prop)
                await self.bot.send_message(user_id, message, parse_mode="Markdown")
                sent_urls.append(prop["url"])
                
                # Добавляем задержку между сообщениями (кроме последнего)
                if i < len(properties) - 1:
                    await asyncio.sleep(1.5)  # Задержка 1.5 секунды между сообщениями
                    
            except Exception as e:
                logger.error(f"Ошибка отправки объявления пользователю {user_id}: {e}")
                # Увеличиваем задержку при ошибке
                await asyncio.sleep(2.0)
        
        # Отмечаем отправленные объявления
        if sent_urls:
            await self.db.mark_properties_as_sent(user_id, sent_urls)
    
    def _escape_markdown(self, text: str) -> str:
        """Экранирует специальные символы для Markdown"""
        if not text:
            return text
        
        # Символы, которые нужно экранировать в Markdown
        chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in chars_to_escape:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def _format_property_message(self, prop: Dict[str, Any]) -> str:
        """Форматирует объявление для отправки"""
        title = self._escape_markdown(prop.get('title', 'Без названия'))
        price = f"€{prop['price']}" if prop.get('price') else 'Цена не указана'
        bedrooms = f"{prop['bedrooms']} спален" if prop.get('bedrooms') else 'Спальни не указаны'
        location = self._escape_markdown(prop.get('location', 'Локация не указана'))
        property_type = self._escape_markdown(prop.get('property_type', 'Тип не указан'))
        url = prop.get('url', '')
        
        message = (
            f"🏠 **{title}**\n\n"
            f"💰 {price}\n"
            f"🛏️ {bedrooms}\n"
            f"📍 {location}\n"
            f"🏠 {property_type}\n\n"
        )
        
        if prop.get('description'):
            desc = self._escape_markdown(prop['description'])
            desc = desc[:150] + "..." if len(desc) > 150 else desc
            message += f"📝 {desc}\n\n"
        
        if url:
            message += f"🔗 [Посмотреть объявление]({url})"
        
        return message


# Дополнительные обработчики будут добавлены в следующей части...
