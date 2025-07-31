import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.media_group import MediaGroupBuilder

from config.settings import settings
from database.database import Database
try:
    from parser.bot_adapter import BotDaftParser as DaftParser
except ImportError:
    try:
        from parser.playwright_parser import PlaywrightDaftParser as DaftParser
    except ImportError:
        from parser.daft_parser import DaftParser
from parser.demo_parser import DemoParser
from parser.models import SearchFilters, Property
from .keyboards import (
    get_main_menu_keyboard, get_settings_keyboard, get_areas_keyboard,
    get_dublin_areas_keyboard, get_confirmation_keyboard, get_cancel_keyboard
)

logger = logging.getLogger(__name__)

# Состояния для FSM
class BotStates(StatesGroup):
    waiting_city = State()
    waiting_max_price = State()
    waiting_min_bedrooms = State()
    waiting_area_name = State()

class TelegramBot:
    """Основной класс Telegram бота"""
    
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.db = Database()
        self.parser = DaftParser()
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        
        # Регистрируем обработчики
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков команд и колбэков"""
        
        # Команды
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.cmd_help, Command("help"))
        self.dp.message.register(self.cmd_status, Command("status"))
        self.dp.message.register(self.cmd_add_area, Command("add_area"))
        self.dp.message.register(self.cmd_remove_area, Command("remove_area"))
        self.dp.message.register(self.cmd_list_areas, Command("list_areas"))
        self.dp.message.register(self.cmd_set_city, Command("set_city"))
        self.dp.message.register(self.cmd_set_max_price, Command("set_max_price"))
        self.dp.message.register(self.cmd_set_min_bedrooms, Command("set_min_bedrooms"))
        
        # Колбэки
        self.dp.callback_query.register(self.callback_main_menu, F.data == "main_menu")
        self.dp.callback_query.register(self.callback_settings, F.data == "settings")
        self.dp.callback_query.register(self.callback_stats, F.data == "stats")
        self.dp.callback_query.register(self.callback_help, F.data == "help")
        self.dp.callback_query.register(self.callback_start_monitoring, F.data == "start_monitoring")
        self.dp.callback_query.register(self.callback_stop_monitoring, F.data == "stop_monitoring")
        self.dp.callback_query.register(self.callback_manage_areas, F.data == "manage_areas")
        self.dp.callback_query.register(self.callback_add_area, F.data == "add_area")
        self.dp.callback_query.register(self.callback_remove_area, F.data == "remove_area")
        self.dp.callback_query.register(self.callback_list_areas, F.data == "list_areas")
        self.dp.callback_query.register(self.callback_set_city, F.data == "set_city")
        self.dp.callback_query.register(self.callback_set_max_price, F.data == "set_max_price")
        self.dp.callback_query.register(self.callback_set_min_bedrooms, F.data == "set_min_bedrooms")
        self.dp.callback_query.register(self.callback_cancel, F.data == "cancel")
        
        # Выбор района из списка
        self.dp.callback_query.register(
            self.callback_select_area, 
            F.data.startswith("select_area_")
        )
        
        # Состояния FSM
        self.dp.message.register(self.process_city_input, StateFilter(BotStates.waiting_city))
        self.dp.message.register(self.process_max_price_input, StateFilter(BotStates.waiting_max_price))
        self.dp.message.register(self.process_min_bedrooms_input, StateFilter(BotStates.waiting_min_bedrooms))
        self.dp.message.register(self.process_area_input, StateFilter(BotStates.waiting_area_name))
    
    def _is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id == settings.ADMIN_USER_ID
    
    async def cmd_start(self, message: Message, state: FSMContext):
        """Обработчик команды /start"""
        await state.clear()
        
        welcome_text = (
            "🏠 <b>Добро пожаловать в Daft.ie Property Bot!</b>\n\n"
            "Я помогу вам отслеживать новые объявления об аренде жилья в Ирландии.\n\n"
            "🔍 <b>Возможности:</b>\n"
            "• Автоматический поиск новых объявлений\n"
            "• Настройка фильтров (город, цена, районы)\n"
            "• Уведомления о новых предложениях\n\n"
            "Используйте кнопки ниже для настройки и управления:"
        )
        
        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    
    async def cmd_help(self, message: Message):
        """Обработчик команды /help"""
        help_text = (
            "📋 <b>Доступные команды:</b>\n\n"
            "<b>Настройка фильтров:</b>\n"
            "/add_area <i>Dublin 1</i> - добавить район\n"
            "/remove_area <i>Dublin 6</i> - удалить район\n"
            "/list_areas - список районов\n"
            "/set_city <i>Dublin</i> - установить город\n"
            "/set_max_price <i>2500</i> - максимальная цена\n"
            "/set_min_bedrooms <i>3</i> - минимум спален\n\n"
            "<b>Управление:</b>\n"
            "/status - текущие настройки\n"
            "/start - главное меню\n"
            "/help - эта справка\n\n"
            "💡 <b>Совет:</b> Используйте кнопки для удобной настройки!"
        )
        
        await message.answer(help_text, parse_mode="HTML")
    
    async def cmd_status(self, message: Message):
        """Обработчик команды /status"""
        chat_id = str(message.chat.id)
        bot_settings = await self.db.get_bot_settings(chat_id)
        stats = await self.db.get_statistics(chat_id)
        
        monitoring_status = "🟢 Активен" if bot_settings.is_monitoring else "🔴 Неактивен"
        areas_text = ", ".join(bot_settings.areas) if bot_settings.areas else "Не указаны"
        
        status_text = (
            f"📊 <b>Текущий статус бота</b>\n\n"
            f"🔍 <b>Мониторинг:</b> {monitoring_status}\n"
            f"🏙️ <b>Город:</b> {bot_settings.city}\n"
            f"💰 <b>Макс. цена:</b> €{bot_settings.max_price:,}/месяц\n"
            f"🛏️ <b>Мин. спальни:</b> {bot_settings.min_bedrooms}\n"
            f"📍 <b>Районы:</b> {areas_text}\n\n"
            f"📈 <b>Статистика:</b>\n"
            f"• Всего объявлений: {stats.get('total_properties', 0)}\n"
            f"• Отправлено в чат: {stats.get('sent_properties', 0)}\n"
        )
        
        if bot_settings.last_check:
            status_text += f"• Последняя проверка: {bot_settings.last_check.strftime('%d.%m.%Y %H:%M')}\n"
        
        await message.answer(status_text, parse_mode="HTML")
    
    async def cmd_add_area(self, message: Message):
        """Обработчик команды /add_area"""
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        if not args:
            await message.answer(
                "❌ Укажите название района.\n"
                "Пример: <code>/add_area Dublin 1</code>",
                parse_mode="HTML"
            )
            return
        
        area = " ".join(args)
        chat_id = str(message.chat.id)
        
        bot_settings = await self.db.get_bot_settings(chat_id)
        if area not in bot_settings.areas:
            bot_settings.areas.append(area)
            await self.db.save_bot_settings(bot_settings)
            await message.answer(f"✅ Район '{area}' добавлен в поиск!")
        else:
            await message.answer(f"ℹ️ Район '{area}' уже в списке.")
    
    async def cmd_remove_area(self, message: Message):
        """Обработчик команды /remove_area"""
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        if not args:
            await message.answer(
                "❌ Укажите название района.\n"
                "Пример: <code>/remove_area Dublin 6</code>",
                parse_mode="HTML"
            )
            return
        
        area = " ".join(args)
        chat_id = str(message.chat.id)
        
        bot_settings = await self.db.get_bot_settings(chat_id)
        if area in bot_settings.areas:
            bot_settings.areas.remove(area)
            await self.db.save_bot_settings(bot_settings)
            await message.answer(f"✅ Район '{area}' удален из поиска!")
        else:
            await message.answer(f"ℹ️ Район '{area}' не найден в списке.")
    
    async def cmd_list_areas(self, message: Message):
        """Обработчик команды /list_areas"""
        chat_id = str(message.chat.id)
        bot_settings = await self.db.get_bot_settings(chat_id)
        
        if bot_settings.areas:
            areas_text = "\n".join([f"• {area}" for area in bot_settings.areas])
            await message.answer(
                f"📍 <b>Районы для поиска:</b>\n\n{areas_text}",
                parse_mode="HTML"
            )
        else:
            await message.answer("📍 Районы не настроены. Будет производиться поиск по всему городу.")
    
    async def cmd_set_city(self, message: Message):
        """Обработчик команды /set_city"""
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        if not args:
            await message.answer(
                "❌ Укажите название города.\n"
                "Пример: <code>/set_city Dublin</code>",
                parse_mode="HTML"
            )
            return
        
        city = " ".join(args)
        chat_id = str(message.chat.id)
        
        bot_settings = await self.db.get_bot_settings(chat_id)
        bot_settings.city = city
        await self.db.save_bot_settings(bot_settings)
        await message.answer(f"✅ Город установлен: {city}")
    
    async def cmd_set_max_price(self, message: Message):
        """Обработчик команды /set_max_price"""
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        if not args:
            await message.answer(
                "❌ Укажите максимальную цену.\n"
                "Пример: <code>/set_max_price 2500</code>",
                parse_mode="HTML"
            )
            return
        
        try:
            max_price = int(args[0])
            if max_price <= 0:
                raise ValueError()
            
            chat_id = str(message.chat.id)
            bot_settings = await self.db.get_bot_settings(chat_id)
            bot_settings.max_price = max_price
            await self.db.save_bot_settings(bot_settings)
            await message.answer(f"✅ Максимальная цена установлена: €{max_price:,}/месяц")
            
        except ValueError:
            await message.answer("❌ Укажите корректную цену (целое число больше 0).")
    
    async def cmd_set_min_bedrooms(self, message: Message):
        """Обработчик команды /set_min_bedrooms"""
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        if not args:
            await message.answer(
                "❌ Укажите минимальное количество спален.\n"
                "Пример: <code>/set_min_bedrooms 3</code>",
                parse_mode="HTML"
            )
            return
        
        try:
            min_bedrooms = int(args[0])
            if min_bedrooms < 0:
                raise ValueError()
            
            chat_id = str(message.chat.id)
            bot_settings = await self.db.get_bot_settings(chat_id)
            bot_settings.min_bedrooms = min_bedrooms
            await self.db.save_bot_settings(bot_settings)
            
            bedrooms_text = "студии" if min_bedrooms == 0 else f"{min_bedrooms}+ спален"
            await message.answer(f"✅ Минимальное количество спален: {bedrooms_text}")
            
        except ValueError:
            await message.answer("❌ Укажите корректное количество спален (целое число от 0).")
    
    # Колбэк обработчики
    async def callback_main_menu(self, callback: CallbackQuery, state: FSMContext):
        """Главное меню"""
        await state.clear()
        await callback.message.edit_text(
            "🏠 <b>Главное меню</b>\n\nВыберите действие:",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
    
    async def callback_settings(self, callback: CallbackQuery, state: FSMContext):
        """Настройки"""
        await state.clear()
        chat_id = str(callback.message.chat.id)
        bot_settings = await self.db.get_bot_settings(chat_id)
        
        areas_text = ", ".join(bot_settings.areas) if bot_settings.areas else "не указаны"
        
        settings_text = (
            f"⚙️ <b>Настройки поиска</b>\n\n"
            f"🏙️ <b>Город:</b> {bot_settings.city}\n"
            f"💰 <b>Макс. цена:</b> €{bot_settings.max_price:,}/месяц\n"
            f"🛏️ <b>Мин. спальни:</b> {bot_settings.min_bedrooms}\n"
            f"📍 <b>Районы:</b> {areas_text}\n\n"
            "Выберите параметр для изменения:"
        )
        
        await callback.message.edit_text(
            settings_text,
            parse_mode="HTML",
            reply_markup=get_settings_keyboard()
        )
        await callback.answer()
    
    async def callback_stats(self, callback: CallbackQuery):
        """Статистика"""
        chat_id = str(callback.message.chat.id)
        stats = await self.db.get_statistics(chat_id)
        bot_settings = await self.db.get_bot_settings(chat_id)
        
        monitoring_status = "🟢 Активен" if bot_settings.is_monitoring else "🔴 Неактивен"
        
        stats_text = (
            f"📊 <b>Статистика</b>\n\n"
            f"🔍 <b>Мониторинг:</b> {monitoring_status}\n"
            f"📈 <b>Всего объявлений в базе:</b> {stats.get('total_properties', 0)}\n"
            f"📤 <b>Отправлено в этот чат:</b> {stats.get('sent_properties', 0)}\n"
        )
        
        if bot_settings.last_check:
            stats_text += f"🕐 <b>Последняя проверка:</b> {bot_settings.last_check.strftime('%d.%m.%Y %H:%M')}\n"
        
        if stats.get('last_parsing_run'):
            stats_text += f"🔄 <b>Последний парсинг:</b> {stats['last_parsing_run']}\n"
        
        await callback.message.edit_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
    
    async def callback_help(self, callback: CallbackQuery):
        """Помощь"""
        help_text = (
            "❓ <b>Помощь</b>\n\n"
            "🔍 <b>Как работает бот:</b>\n"
            "1. Настройте фильтры поиска\n"
            "2. Запустите мониторинг\n"
            "3. Получайте уведомления о новых объявлениях\n\n"
            "⚙️ <b>Настройки:</b>\n"
            "• <b>Город</b> - где искать (Dublin, Cork, etc.)\n"
            "• <b>Макс. цена</b> - максимальная стоимость аренды\n"
            "• <b>Мин. спальни</b> - минимальное количество спален\n"
            "• <b>Районы</b> - конкретные районы для поиска\n\n"
            "🔄 <b>Мониторинг:</b>\n"
            "Бот проверяет новые объявления каждые 2 минуты и присылает только те, "
            "которые еще не отправлялись в этот чат.\n\n"
            "📱 <b>Команды:</b>\n"
            "Все настройки доступны через кнопки или команды (см. /help)"
        )
        
        await callback.message.edit_text(
            help_text,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
    
    async def callback_start_monitoring(self, callback: CallbackQuery):
        """Запуск мониторинга"""
        chat_id = str(callback.message.chat.id)
        
        if chat_id in self.monitoring_tasks:
            await callback.answer("⚠️ Мониторинг уже запущен!", show_alert=True)
            return
        
        bot_settings = await self.db.get_bot_settings(chat_id)
        bot_settings.is_monitoring = True
        await self.db.save_bot_settings(bot_settings)
        
        # Запускаем задачу мониторинга
        task = asyncio.create_task(self._monitoring_loop(chat_id))
        self.monitoring_tasks[chat_id] = task
        
        await callback.message.edit_text(
            "✅ <b>Мониторинг запущен!</b>\n\n"
            "🔍 Бот будет проверять новые объявления каждые 2 минуты\n"
            "📬 Новые предложения будут приходить автоматически",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer("🚀 Мониторинг запущен!")
    
    async def callback_stop_monitoring(self, callback: CallbackQuery):
        """Остановка мониторинга"""
        chat_id = str(callback.message.chat.id)
        
        if chat_id not in self.monitoring_tasks:
            await callback.answer("⚠️ Мониторинг не активен!", show_alert=True)
            return
        
        # Останавливаем задачу
        task = self.monitoring_tasks.pop(chat_id)
        task.cancel()
        
        bot_settings = await self.db.get_bot_settings(chat_id)
        bot_settings.is_monitoring = False
        await self.db.save_bot_settings(bot_settings)
        
        await callback.message.edit_text(
            "⏹️ <b>Мониторинг остановлен</b>\n\n"
            "Вы можете запустить его снова в любое время.",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer("⏹️ Мониторинг остановлен")
    
    async def callback_manage_areas(self, callback: CallbackQuery):
        """Управление районами"""
        await callback.message.edit_text(
            "📍 <b>Управление районами</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=get_areas_keyboard()
        )
        await callback.answer()
    
    async def callback_add_area(self, callback: CallbackQuery):
        """Добавление района"""
        await callback.message.edit_text(
            "📍 <b>Выберите район для добавления:</b>",
            parse_mode="HTML",
            reply_markup=get_dublin_areas_keyboard()
        )
        await callback.answer()
    
    async def callback_select_area(self, callback: CallbackQuery):
        """Выбор района из списка"""
        area = callback.data.replace("select_area_", "").replace("_", " ")
        chat_id = str(callback.message.chat.id)
        
        bot_settings = await self.db.get_bot_settings(chat_id)
        if area not in bot_settings.areas:
            bot_settings.areas.append(area)
            await self.db.save_bot_settings(bot_settings)
            await callback.answer(f"✅ Район '{area}' добавлен!")
        else:
            await callback.answer(f"ℹ️ Район '{area}' уже в списке", show_alert=True)
        
        # Возвращаемся к списку районов
        await self.callback_add_area(callback)
    
    async def callback_remove_area(self, callback: CallbackQuery):
        """Удаление района"""
        chat_id = str(callback.message.chat.id)
        bot_settings = await self.db.get_bot_settings(chat_id)
        
        if not bot_settings.areas:
            await callback.answer("ℹ️ Список районов пуст", show_alert=True)
            return
        
        # Создаем клавиатуру с текущими районами
        keyboard_rows = []
        for area in bot_settings.areas:
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"❌ {area}",
                    callback_data=f"delete_area_{area.replace(' ', '_')}"
                )
            ])
        
        keyboard_rows.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="manage_areas")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
        
        await callback.message.edit_text(
            "📍 <b>Выберите район для удаления:</b>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()
    
    async def callback_list_areas(self, callback: CallbackQuery):
        """Список районов"""
        chat_id = str(callback.message.chat.id)
        bot_settings = await self.db.get_bot_settings(chat_id)
        
        if bot_settings.areas:
            areas_text = "\n".join([f"• {area}" for area in bot_settings.areas])
            text = f"📍 <b>Настроенные районы:</b>\n\n{areas_text}"
        else:
            text = "📍 <b>Районы не настроены</b>\n\nБудет производиться поиск по всему городу."
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_areas_keyboard()
        )
        await callback.answer()
    
    async def callback_set_city(self, callback: CallbackQuery, state: FSMContext):
        """Установка города"""
        await state.set_state(BotStates.waiting_city)
        await callback.message.edit_text(
            "🏙️ <b>Установка города</b>\n\n"
            "Введите название города для поиска (например: Dublin, Cork, Galway):",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
    
    async def callback_set_max_price(self, callback: CallbackQuery, state: FSMContext):
        """Установка максимальной цены"""
        await state.set_state(BotStates.waiting_max_price)
        await callback.message.edit_text(
            "💰 <b>Установка максимальной цены</b>\n\n"
            "Введите максимальную цену аренды в евро (например: 2500):",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
    
    async def callback_set_min_bedrooms(self, callback: CallbackQuery, state: FSMContext):
        """Установка минимального количества спален"""
        await state.set_state(BotStates.waiting_min_bedrooms)
        await callback.message.edit_text(
            "🛏️ <b>Установка минимального количества спален</b>\n\n"
            "Введите минимальное количество спален (0 для студий, 1, 2, 3...):",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
    
    async def callback_cancel(self, callback: CallbackQuery, state: FSMContext):
        """Отмена операции"""
        await state.clear()
        await self.callback_main_menu(callback, state)
    
    # Обработчики ввода для FSM
    async def process_city_input(self, message: Message, state: FSMContext):
        """Обработка ввода города"""
        city = message.text.strip()
        chat_id = str(message.chat.id)
        
        bot_settings = await self.db.get_bot_settings(chat_id)
        bot_settings.city = city
        await self.db.save_bot_settings(bot_settings)
        
        await state.clear()
        await message.answer(
            f"✅ Город установлен: <b>{city}</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard()
        )
    
    async def process_max_price_input(self, message: Message, state: FSMContext):
        """Обработка ввода максимальной цены"""
        try:
            max_price = int(message.text.strip())
            if max_price <= 0:
                raise ValueError()
            
            chat_id = str(message.chat.id)
            bot_settings = await self.db.get_bot_settings(chat_id)
            bot_settings.max_price = max_price
            await self.db.save_bot_settings(bot_settings)
            
            await state.clear()
            await message.answer(
                f"✅ Максимальная цена установлена: <b>€{max_price:,}/месяц</b>",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
            
        except ValueError:
            await message.answer(
                "❌ Пожалуйста, введите корректную цену (целое число больше 0)."
            )
    
    async def process_min_bedrooms_input(self, message: Message, state: FSMContext):
        """Обработка ввода минимального количества спален"""
        try:
            min_bedrooms = int(message.text.strip())
            if min_bedrooms < 0:
                raise ValueError()
            
            chat_id = str(message.chat.id)
            bot_settings = await self.db.get_bot_settings(chat_id)
            bot_settings.min_bedrooms = min_bedrooms
            await self.db.save_bot_settings(bot_settings)
            
            await state.clear()
            bedrooms_text = "студии" if min_bedrooms == 0 else f"{min_bedrooms}+ спален"
            await message.answer(
                f"✅ Минимальное количество спален: <b>{bedrooms_text}</b>",
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
            
        except ValueError:
            await message.answer(
                "❌ Пожалуйста, введите корректное количество спален (целое число от 0)."
            )
    
    async def process_area_input(self, message: Message, state: FSMContext):
        """Обработка ввода названия района"""
        area = message.text.strip()
        chat_id = str(message.chat.id)
        
        bot_settings = await self.db.get_bot_settings(chat_id)
        if area not in bot_settings.areas:
            bot_settings.areas.append(area)
            await self.db.save_bot_settings(bot_settings)
            await message.answer(f"✅ Район '{area}' добавлен в поиск!")
        else:
            await message.answer(f"ℹ️ Район '{area}' уже в списке.")
        
        await state.clear()
        await message.answer(
            "Вернуться к главному меню:",
            reply_markup=get_main_menu_keyboard()
        )
    
    async def _monitoring_loop(self, chat_id: str):
        """Цикл мониторинга новых объявлений"""
        logger.info(f"Starting monitoring loop for chat {chat_id}")
        
        while True:
            try:
                start_time = datetime.now()
                
                # Получаем настройки
                bot_settings = await self.db.get_bot_settings(chat_id)
                if not bot_settings.is_monitoring:
                    logger.info(f"Monitoring disabled for chat {chat_id}")
                    break
                
                # Создаем фильтры поиска
                search_filters = bot_settings.get_search_filters()
                
                # Пробуем основной парсер, если не работает - используем демо
                properties = []
                try:
                    async with DaftParser() as parser:
                        properties = await parser.search_properties(search_filters, max_pages=2)
                except Exception as e:
                    logger.warning(f"Main parser failed: {e}, switching to demo mode")
                    async with DemoParser() as demo_parser:
                        properties = await demo_parser.search_properties(search_filters)
                
                # Сохраняем новые объявления
                await self.db.save_properties(properties)
                
                # Получаем новые объявления для этого чата
                new_properties = await self.db.get_new_properties(chat_id)
                
                # Отправляем новые объявления
                sent_count = 0
                for property_obj in new_properties:
                    if await self._send_property_message(chat_id, property_obj):
                        await self.db.mark_property_sent(property_obj.id, chat_id)
                        sent_count += 1
                        await asyncio.sleep(1)  # Задержка между сообщениями
                
                # Обновляем время последней проверки
                bot_settings.last_check = datetime.now()
                await self.db.save_bot_settings(bot_settings)
                
                # Логируем результаты
                duration = (datetime.now() - start_time).total_seconds()
                await self.db.log_parsing_run(
                    chat_id=chat_id,
                    properties_found=len(properties),
                    new_properties=sent_count,
                    filters_used=search_filters.to_url_params(),
                    duration_seconds=duration
                )
                
                logger.info(f"Monitoring cycle completed for chat {chat_id}: "
                           f"{len(properties)} found, {sent_count} sent")
                
                # Ждем до следующей проверки
                await asyncio.sleep(settings.UPDATE_INTERVAL)
                
            except asyncio.CancelledError:
                logger.info(f"Monitoring loop cancelled for chat {chat_id}")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop for chat {chat_id}: {e}")
                await asyncio.sleep(60)  # Ждем минуту при ошибке
    
    async def _send_property_message(self, chat_id: str, property_obj: Property) -> bool:
        """Отправка сообщения об объявлении"""
        try:
            # Формируем текст сообщения
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
            
            message_text += f"\n🔗 <a href='{property_obj.url}'>Смотреть объявление</a>"
            
            # Отправляем сообщение
            if property_obj.image_url:
                try:
                    await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=property_obj.image_url,
                        caption=message_text,
                        parse_mode="HTML"
                    )
                except Exception:
                    # Если изображение не загружается, отправляем без него
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message_text,
                        parse_mode="HTML",
                        disable_web_page_preview=False
                    )
            else:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="HTML",
                    disable_web_page_preview=False
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending property message: {e}")
            return False
    
    async def start(self):
        """Запуск бота"""
        # Инициализируем базу данных
        await self.db.init_database()
        
        logger.info("Starting Telegram bot...")
        
        # Запускаем поллинг
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Остановка бота"""
        logger.info("Stopping bot...")
        
        # Останавливаем все задачи мониторинга
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        await self.bot.session.close()
