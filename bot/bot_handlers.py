#!/usr/bin/env python3
"""
Дополнительные обработчики для улучшенного бота (часть 2)
"""

import asyncio
import logging
from typing import List, Dict, Any

from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)

from config.regions import ALL_LOCATIONS, LIMITS
from bot.keyboards import (
    get_settings_menu_keyboard, get_regions_menu_keyboard,
    get_region_categories_keyboard, get_category_regions_keyboard,
    get_popular_combinations_keyboard, get_user_regions_keyboard, get_bedrooms_keyboard,
    get_price_keyboard, get_interval_keyboard, get_main_menu_keyboard,
    get_statistics_keyboard, get_replace_regions_keyboard
)

# Состояния для FSM
class BotStates(StatesGroup):
    waiting_custom_price = State()
    waiting_custom_interval = State()
    waiting_region_search = State()

class EnhancedPropertyBotHandlers:
    """Дополнительные обработчики для бота"""
    
    # === НАСТРОЙКИ ===
    
    async def callback_show_settings(self, callback: CallbackQuery):
        """Показать текущие настройки"""
        user_id = callback.from_user.id
        settings = await self.db.get_user_settings(user_id)
        
        if not settings:
            await callback.message.edit_text(
                "❌ Настройки не найдены.",
                reply_markup=get_main_menu_keyboard()
            )
            await callback.answer()
            return
        
        regions_text = ", ".join([
            ALL_LOCATIONS.get(region, region) for region in settings["regions"]
        ])
        interval_text = self._format_interval(settings["monitoring_interval"])
        
        settings_text = (
            f"⚙️ **Ваши текущие настройки:**\n\n"
            f"🏘️ **Регионы поиска:**\n{regions_text}\n\n"
            f"🛏️ **Минимум спален:** {settings['min_bedrooms']}\n"
            f"💰 **Максимальная цена:** €{settings['max_price']}\n"
            f"⏰ **Интервал мониторинга:** {interval_text}\n"
            f"📊 **Лимит результатов:** {settings['max_results_per_search']}"
        )
        
        try:
            await callback.message.edit_text(
                settings_text,
                reply_markup=get_settings_menu_keyboard(),
                parse_mode="Markdown"
            )
        except Exception as e:
            # Если сообщение не изменилось, просто отвечаем
            if "message is not modified" in str(e):
                await callback.answer("Настройки уже актуальны ✅")
            else:
                await callback.answer("Ошибка обновления настроек")
        await callback.answer()
    
    # === УПРАВЛЕНИЕ РЕГИОНАМИ ===
    
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
    
    async def callback_add_region(self, callback: CallbackQuery):
        """Добавление нового региона"""
        await callback.message.edit_text(
            "➕ **Добавить регион**\n\n"
            "Выберите категорию регионов:",
            reply_markup=get_region_categories_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()

    async def callback_remove_region(self, callback: CallbackQuery):
        """Удаление региона"""
        user_id = callback.from_user.id
        settings = await self.db.get_user_settings(user_id)
        
        if not settings or not settings["regions"]:
            await callback.message.edit_text(
                "❌ У вас нет добавленных регионов.",
                reply_markup=get_regions_menu_keyboard()
            )
            await callback.answer()
            return
        
        await callback.message.edit_text(
            "➖ **Удалить регион**\n\n"
            "Выберите регион для удаления:",
            reply_markup=get_user_regions_keyboard(settings["regions"]),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_show_regions(self, callback: CallbackQuery):
        """Показать текущие регионы пользователя"""
        user_id = callback.from_user.id
        settings = await self.db.get_user_settings(user_id)
        
        if not settings or not settings["regions"]:
            await callback.message.edit_text(
                "📋 **Ваши регионы:** пусто\n\n"
                "Добавьте регионы для поиска.",
                reply_markup=get_regions_menu_keyboard(),
                parse_mode="Markdown"
            )
            await callback.answer()
            return
        
        regions_list = "\n".join([
            f"• {ALL_LOCATIONS.get(region, region)}"
            for region in settings["regions"]
        ])
        
        await callback.message.edit_text(
            f"📋 **Ваши регионы:**\n\n{regions_list}\n\n"
            f"Всего регионов: {len(settings['regions'])}",
            reply_markup=get_regions_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_list_all_regions(self, callback: CallbackQuery):
        """Показать все доступные регионы"""
        regions_text = "\n".join([
            f"• {name}" for name in sorted(ALL_LOCATIONS.values())
        ])
        
        await callback.message.edit_text(
            f"🗂️ **Все доступные регионы:**\n\n{regions_text}\n\n"
            f"Всего регионов: {len(ALL_LOCATIONS)}",
            reply_markup=get_regions_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_region_page(self, callback: CallbackQuery):
        """Пагинация регионов в категории"""
        data_parts = callback.data.split("_")
        if len(data_parts) >= 4:
            category = data_parts[2]
            page = int(data_parts[3])
            
            await callback.message.edit_reply_markup(
                reply_markup=get_category_regions_keyboard(category, page)
            )
        await callback.answer()
    
    async def callback_category_page(self, callback: CallbackQuery):
        """Обработчик пагинации категорий"""
        data_parts = callback.data.split("_")
        category = data_parts[2]
        page = int(data_parts[3])
        
        await callback.message.edit_reply_markup(
            reply_markup=get_category_regions_keyboard(category, page)
        )
        await callback.answer()
    
    async def callback_select_region(self, callback: CallbackQuery):
        """Выбор региона для добавления"""
        region_key = callback.data.replace("select_region_", "")
        user_id = callback.from_user.id
        
        settings = await self.db.get_user_settings(user_id)
        if not settings:
            await callback.answer("❌ Ошибка получения настроек")
            return
        
        # Проверяем, если это первый регион после "заменить все" - очищаем старые
        # Для простоты, будем проверять по специальному флагу в callback data или другому способу
        
        # Проверяем лимит регионов
        if len(settings["regions"]) >= LIMITS["max_regions"]:
            await callback.answer(
                f"❌ Превышен лимит регионов ({LIMITS['max_regions']})",
                show_alert=True
            )
            return
        
        # Проверяем, не добавлен ли уже регион
        if region_key in settings["regions"]:
            await callback.answer("⚠️ Регион уже добавлен", show_alert=True)
            return
        
        # Добавляем регион
        new_regions = settings["regions"] + [region_key]
        await self.db.update_user_settings(user_id, regions=new_regions)
        
        region_name = ALL_LOCATIONS.get(region_key, region_key)
        
        await callback.message.edit_text(
            f"✅ **Регион добавлен!**\n\n"
            f"🏘️ {region_name}\n\n"
            f"Всего регионов: {len(new_regions)}",
            reply_markup=get_regions_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer(f"✅ Добавлен: {region_name}")
    
    async def callback_replace_select_region(self, callback: CallbackQuery):
        """Выбор региона в режиме замены"""
        region_key = callback.data.replace("replace_select_region_", "")
        user_id = callback.from_user.id
        
        settings = await self.db.get_user_settings(user_id)
        if not settings:
            await callback.answer("❌ Ошибка получения настроек")
            return
        
        # В режиме замены добавляем регион к уже очищенному списку
        new_regions = settings["regions"] + [region_key]
        await self.db.update_user_settings(user_id, regions=new_regions)
        
        region_name = ALL_LOCATIONS.get(region_key, region_key)
        
        await callback.message.edit_text(
            f"🔄 **Регион добавлен в новый список!**\n\n"
            f"🏘️ {region_name}\n\n"
            f"Новых регионов: {len(new_regions)}\n\n"
            f"Можете добавить еще регионы или вернуться в меню.",
            reply_markup=get_regions_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer(f"🔄 Заменен на: {region_name}")

    async def callback_remove_specific_region(self, callback: CallbackQuery):
        """Удаление конкретного региона"""
        region_key = callback.data.replace("remove_region_", "")
        user_id = callback.from_user.id
        
        settings = await self.db.get_user_settings(user_id)
        if not settings:
            await callback.answer("❌ Ошибка получения настроек")
            return
        
        # Проверяем, что это не последний регион
        if len(settings["regions"]) <= 1:
            await callback.answer(
                "❌ Нельзя удалить последний регион",
                show_alert=True
            )
            return
        
        # Удаляем регион
        new_regions = [r for r in settings["regions"] if r != region_key]
        await self.db.update_user_settings(user_id, regions=new_regions)
        
        region_name = ALL_LOCATIONS.get(region_key, region_key)
        
        await callback.message.edit_text(
            f"✅ **Регион удален!**\n\n"
            f"🏘️ {region_name}\n\n"
            f"Осталось регионов: {len(new_regions)}",
            reply_markup=get_regions_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer(f"❌ Удален: {region_name}")
    
    async def callback_replace_all_regions(self, callback: CallbackQuery):
        """Заменить все регионы - очистить и добавить новые"""
        await callback.message.edit_text(
            "🔄 **Заменить все регионы**\n\n"
            "Все текущие регионы будут удалены.\n"
            "Выберите категорию для добавления новых регионов:",
            reply_markup=get_replace_regions_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_replace_category_selection(self, callback: CallbackQuery):
        """Обработчик выбора категории в режиме замены регионов"""
        category = callback.data.replace("replace_category_", "")
        
        # Сначала очищаем все регионы пользователя
        user_id = callback.from_user.id
        await self.db.clear_user_regions(user_id)
        
        # Показываем регионы выбранной категории с префиксом replace_
        await callback.message.edit_text(
            f"🔄 **Замена регионов**\n\n"
            f"Старые регионы очищены.\n"
            f"Выберите новые регионы:",
            reply_markup=get_category_regions_keyboard(category, 0, "replace_select_region_"),
            parse_mode="Markdown"
        )
        await callback.answer("✅ Регионы очищены")

    # === НАСТРОЙКА СПАЛЕН ===
    
    async def callback_set_bedrooms(self, callback: CallbackQuery):
        """Настройка количества спален"""
        await callback.message.edit_text(
            "🛏️ **Минимальное количество спален**\n\n"
            "Выберите значение:",
            reply_markup=get_bedrooms_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_select_bedrooms(self, callback: CallbackQuery):
        """Выбор количества спален"""
        bedrooms = int(callback.data.replace("bedrooms_", ""))
        user_id = callback.from_user.id
        
        # Валидация
        if bedrooms < LIMITS["min_bedrooms"]["min"] or bedrooms > LIMITS["min_bedrooms"]["max"]:
            await callback.answer(
                f"❌ Неверное количество спален ({LIMITS['min_bedrooms']['min']}-{LIMITS['min_bedrooms']['max']})",
                show_alert=True
            )
            return
        
        # Обновляем настройки
        await self.db.update_user_settings(user_id, min_bedrooms=bedrooms)
        
        bedrooms_text = "Студия" if bedrooms == 0 else f"{bedrooms} спален"
        
        await callback.message.edit_text(
            f"✅ **Количество спален обновлено!**\n\n"
            f"🛏️ Минимум: {bedrooms_text}",
            reply_markup=get_settings_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer(f"✅ Установлено: {bedrooms_text}")
    
    # === НАСТРОЙКА ЦЕНЫ ===
    
    async def callback_set_max_price(self, callback: CallbackQuery):
        """Настройка максимальной цены"""
        await callback.message.edit_text(
            "💰 **Максимальная цена**\n\n"
            "Выберите бюджет:",
            reply_markup=get_price_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_select_price(self, callback: CallbackQuery):
        """Выбор цены"""
        price = int(callback.data.replace("price_", ""))
        user_id = callback.from_user.id
        
        # Валидация
        if price < LIMITS["max_price"]["min"] or price > LIMITS["max_price"]["max"]:
            await callback.answer(
                f"❌ Неверная цена (€{LIMITS['max_price']['min']}-€{LIMITS['max_price']['max']})",
                show_alert=True
            )
            return
        
        # Обновляем настройки
        await self.db.update_user_settings(user_id, max_price=price)
        
        await callback.message.edit_text(
            f"✅ **Максимальная цена обновлена!**\n\n"
            f"💰 До €{price}",
            reply_markup=get_settings_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer(f"✅ Установлено: €{price}")
    
    async def callback_custom_price(self, callback: CallbackQuery, state: FSMContext):
        """Ввод пользовательской цены"""
        await state.set_state(BotStates.waiting_custom_price)
        
        await callback.message.edit_text(
            f"✏️ **Введите максимальную цену**\n\n"
            f"Диапазон: €{LIMITS['max_price']['min']} - €{LIMITS['max_price']['max']}\n\n"
            f"Отправьте число (только цифры):",
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def process_custom_price(self, message: Message, state: FSMContext):
        """Обработка пользовательской цены"""
        try:
            price = int(message.text.strip())
            
            # Валидация
            if price < LIMITS["max_price"]["min"] or price > LIMITS["max_price"]["max"]:
                await message.answer(
                    f"❌ Неверная цена. Диапазон: €{LIMITS['max_price']['min']} - €{LIMITS['max_price']['max']}"
                )
                return
            
            # Обновляем настройки
            user_id = message.from_user.id
            await self.db.update_user_settings(user_id, max_price=price)
            
            await message.answer(
                f"✅ **Максимальная цена установлена!**\n\n"
                f"💰 До €{price}",
                reply_markup=get_settings_menu_keyboard(),
                parse_mode="Markdown"
            )
            
        except ValueError:
            await message.answer("❌ Введите корректное число!")
            return
        
        await state.clear()
    
    # === НАСТРОЙКА ИНТЕРВАЛА ===
    
    async def callback_set_interval(self, callback: CallbackQuery):
        """Настройка интервала мониторинга"""
        await callback.message.edit_text(
            "⏰ **Интервал мониторинга**\n\n"
            "Как часто проверять новые объявления:",
            reply_markup=get_interval_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def callback_select_interval(self, callback: CallbackQuery):
        """Выбор интервала"""
        interval = int(callback.data.replace("interval_", ""))
        user_id = callback.from_user.id
        
        # Валидация
        if interval < LIMITS["monitoring_interval"]["min"] or interval > LIMITS["monitoring_interval"]["max"]:
            await callback.answer(
                f"❌ Неверный интервал",
                show_alert=True
            )
            return
        
        # Обновляем настройки
        await self.db.update_user_settings(user_id, monitoring_interval=interval)
        
        interval_text = self._format_interval(interval)
        
        await callback.message.edit_text(
            f"✅ **Интервал мониторинга обновлен!**\n\n"
            f"⏰ Каждые {interval_text}",
            reply_markup=get_settings_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer(f"✅ Установлено: {interval_text}")
    
    # === СТАТИСТИКА ===
    
    async def callback_show_stats(self, callback: CallbackQuery):
        """Показать статистику"""
        days = int(callback.data.replace("stats_", ""))
        user_id = callback.from_user.id
        
        stats = await self.db.get_user_statistics(user_id, days)
        
        stats_text = (
            f"📊 **Статистика за {days} дней**\n\n"
            f"**🏠 Объявления:**\n"
            f"• Всего найдено: {stats['properties']['total']}\n"
            f"• Отправлено: {stats['properties']['sent']}\n"
        )
        
        if stats['properties']['total'] > 0:
            stats_text += (
                f"• Средняя цена: €{stats['properties']['avg_price']}\n"
                f"• Диапазон цен: €{stats['properties']['min_price']} - €{stats['properties']['max_price']}\n\n"
            )
        else:
            stats_text += "\n"
        
        stats_text += (
            f"**🔍 Мониторинг:**\n"
            f"• Всего сессий: {stats['monitoring']['total_sessions']}\n"
            f"• Успешных: {stats['monitoring']['successful_sessions']}\n"
            f"• Среднее время: {stats['monitoring']['avg_execution_time']}с\n"
            f"• Новых объявлений: {stats['monitoring']['total_new_properties']}"
        )
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_statistics_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
    
    async def process_custom_interval(self, message: Message, state: FSMContext):
        """Обработка пользовательского интервала мониторинга"""
        try:
            # Получаем число из сообщения
            interval_minutes = int(message.text)
            
            # Проверяем ограничения (5 минут - 24 часа)
            if interval_minutes < 5:
                await message.reply(
                    "❌ Минимальный интервал: 5 минут"
                )
                return
            
            if interval_minutes > 1440:  # 24 часа
                await message.reply(
                    "❌ Максимальный интервал: 24 часа (1440 минут)"
                )
                return
            
            # Конвертируем в секунды
            interval_seconds = interval_minutes * 60
            
            # Обновляем настройки
            user_id = message.from_user.id
            await self.db.update_user_settings(
                user_id,
                monitoring_interval=interval_seconds
            )
            
            await message.reply(
                f"✅ Интервал установлен: {interval_minutes} минут",
                reply_markup=get_main_menu_keyboard()
            )
            
            # Очищаем состояние
            await state.clear()
            
        except ValueError:
            await message.reply(
                "❌ Введите число (количество минут)\n"
                "Например: 60"
            )
    
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

    async def callback_search_region(self, callback: CallbackQuery, state: FSMContext):
        """Обработчик поиска региона по названию"""
        await callback.message.edit_text(
            "🔍 **Поиск региона**\n\n"
            "Введите название региона для поиска:\n"
            "(например: Dublin, Cork, Galway)",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="manage_regions")]
            ]),
            parse_mode="Markdown"
        )
        await state.set_state(BotStates.waiting_region_search)
        await callback.answer()

    async def process_region_search(self, message: Message, state: FSMContext):
        """Обработка поискового запроса региона"""
        from config.regions import ALL_REGIONS
        from bot.keyboards import get_main_menu_keyboard
        
        search_term = message.text.lower().strip()
        
        # Поиск по всем регионам
        found_regions = []
        for region_id, region_name in ALL_REGIONS.items():
            if search_term in region_name.lower():
                found_regions.append((region_id, region_name))
        
        if found_regions:
            if len(found_regions) == 1:
                # Найден один регион - добавляем его
                region_id, region_name = found_regions[0]
                user_id = message.from_user.id
                
                # Добавляем регион
                success = self.db.add_user_region(user_id, region_id)
                
                if success:
                    await message.answer(
                        f"✅ **Регион добавлен**\n\n"
                        f"📍 {region_name}\n\n"
                        "Теперь этот регион будет включен в поиск.",
                        reply_markup=get_main_menu_keyboard(),
                        parse_mode="Markdown"
                    )
                else:
                    await message.answer(
                        f"⚠️ **Регион уже добавлен**\n\n"
                        f"📍 {region_name}",
                        reply_markup=get_main_menu_keyboard(),
                        parse_mode="Markdown"
                    )
            else:
                # Найдено несколько регионов
                text = f"🔍 **Найдено регионов: {len(found_regions)}**\n\n"
                for i, (region_id, region_name) in enumerate(found_regions[:10], 1):
                    text += f"{i}. {region_name}\n"
                
                if len(found_regions) > 10:
                    text += f"\n... и еще {len(found_regions) - 10} регионов"
                
                text += "\n\nУточните поиск для выбора конкретного региона."
                
                await message.answer(
                    text,
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
        else:
            await message.answer(
                f"❌ **Регион не найден**\n\n"
                f"По запросу '{search_term}' ничего не найдено.\n"
                "Попробуйте другое название.",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )
        
        await state.clear()

    async def callback_noop(self, callback: CallbackQuery):
        """Пустой обработчик для неактивных кнопок"""
        await callback.answer()

    async def callback_current_page(self, callback: CallbackQuery):
        """Обработчик текущей страницы (обычно неактивная кнопка)"""
        await callback.answer("📍 Вы уже на этой странице")

    async def callback_recent_searches(self, callback: CallbackQuery):
        """Обработчик недавних поисков"""
        user_id = callback.from_user.id
        
        # Получаем недавние поиски пользователя
        recent_searches = self.db.get_user_recent_searches(user_id, limit=5)
        
        if recent_searches:
            text = "📋 **Недавние поиски**\n\n"
            for i, search in enumerate(recent_searches, 1):
                text += f"{i}. {search['regions']} | "
                text += f"💰 до {search['max_price']}€ | "
                text += f"🛏️ {search['bedrooms']} комн.\n"
            
            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                "📋 **Недавние поиски**\n\n"
                "У вас пока нет недавних поисков.\n"
                "Начните мониторинг, чтобы увидеть историю.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
        
        await callback.answer()

    async def callback_show_all_results(self, callback: CallbackQuery):
        """Показать все результаты последнего поиска"""
        user_id = callback.from_user.id
        
        results = await self.db.get_cached_search_results(user_id)
        
        if not results:
            await callback.message.edit_text(
                "❌ **Нет сохраненных результатов**\n\n"
                "Выполните поиск заново.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="single_search")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
            await callback.answer()
            return
        
        await callback.message.edit_text(
            f"📋 **Все найденные объявления ({len(results)})**\n\n"
            "Отправляю все объявления...",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        
        # Сразу отвечаем на callback, чтобы избежать timeout
        try:
            await callback.answer("📤 Начинаю отправку объявлений...")
        except Exception as e:
            # Игнорируем ошибки timeout для callback
            logger.warning(f"Callback timeout: {e}")
        
        # Отправляем все результаты
        await self._send_all_properties(user_id, results)

    async def _send_all_properties(self, user_id: int, properties: List[Dict[str, Any]]):
        """Отправляет все объявления пользователю"""
        if not properties:
            return
        
        count = 0
        for prop in properties:
            try:
                # Формируем сообщение
                message = self._format_property_message(prop)
                
                # Отправляем
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="Markdown",
                    disable_web_page_preview=False
                )
                
                count += 1
                
                # Увеличенная задержка между сообщениями для избежания ошибок
                await asyncio.sleep(1.2)
                
            except Exception as e:
                logger.error(f"Ошибка отправки объявления: {e}")
                # Дополнительная задержка при ошибке
                await asyncio.sleep(2.0)
                continue
        
        logger.info(f"Отправлено {count} объявлений пользователю {user_id}")

    def _escape_markdown(self, text: str) -> str:
        """Экранирует специальные символы для Markdown"""
        if not text:
            return str(text) if text is not None else ""
        
        text = str(text)
        # Символы, которые нужно экранировать в Markdown
        chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in chars_to_escape:
            text = text.replace(char, f'\\{char}')
        
        return text

    def _format_property_message(self, prop: Dict[str, Any]) -> str:
        """Форматирует сообщение об объявлении"""
        title = self._escape_markdown(prop.get('title', 'Без названия'))
        price = self._escape_markdown(prop.get('price', 'Цена не указана'))
        bedrooms = self._escape_markdown(prop.get('bedrooms', 'Не указано'))
        location = self._escape_markdown(prop.get('location', 'Местоположение не указано'))
        url = prop.get('url', '')
        
        message = f"🏠 **{title}**\n\n"
        message += f"💰 **Цена:** {price}\n"
        message += f"🛏️ **Спален:** {bedrooms}\n"
        message += f"📍 **Местоположение:** {location}\n"
        
        if url:
            message += f"\n🔗 [Подробнее на Daft\\.ie]({url})"
        
        return message
