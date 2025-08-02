#!/usr/bin/env python3
"""
Клавиатуры для управления ботом мониторинга недвижимости
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict
import math

from config.regions import (
    DUBLIN_REGIONS, MAIN_CITIES, COUNTIES, ALL_LOCATIONS, 
    REGION_CATEGORIES, POPULAR_COMBINATIONS
)


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = [
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="statistics")
        ],
        [
            InlineKeyboardButton(text="▶️ Запустить мониторинг", callback_data="start_monitoring"),
            InlineKeyboardButton(text="⏹️ Остановить мониторинг", callback_data="stop_monitoring")
        ],
        [
            InlineKeyboardButton(text="🔍 Разовый поиск", callback_data="single_search"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_settings_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню настроек"""
    keyboard = [
        [
            InlineKeyboardButton(text="🏘️ Регионы поиска", callback_data="manage_regions"),
            InlineKeyboardButton(text="🛏️ Количество спален", callback_data="set_bedrooms")
        ],
        [
            InlineKeyboardButton(text="💰 Максимальная цена", callback_data="set_max_price"),
            InlineKeyboardButton(text="⏰ Интервал мониторинга", callback_data="set_interval")
        ],
        [
            InlineKeyboardButton(text="📋 Показать настройки", callback_data="show_settings"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_regions_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню управления регионами"""
    keyboard = [
        [
            InlineKeyboardButton(text="👀 Мои регионы", callback_data="show_regions"),
            InlineKeyboardButton(text="➕ Добавить регион", callback_data="add_region")
        ],
        [
            InlineKeyboardButton(text="❌ Удалить регион", callback_data="remove_region"),
            InlineKeyboardButton(text="📋 Все регионы", callback_data="list_all_regions")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_add_region_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора категории регионов для добавления"""
    keyboard = [
        [
            InlineKeyboardButton(text="🏙️ Районы Дублина (62)", callback_data="category_dublin_areas"),
            InlineKeyboardButton(text="🌆 Основные города (6)", callback_data="category_main_cities")
        ],
        [
            InlineKeyboardButton(text="🗺️ Графства Ирландии (26)", callback_data="category_republic_counties"),
            InlineKeyboardButton(text="🏴󠁧󠁢󠁳󠁣󠁴󠁿 Сев. Ирландия (6)", callback_data="category_northern_counties")
        ],
        [
            InlineKeyboardButton(text="⭐ Популярные комбинации", callback_data="category_popular"),
            InlineKeyboardButton(text="🔍 Поиск по названию", callback_data="search_region")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад к регионам", callback_data="manage_regions"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_region_categories_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора категории регионов - алиас для совместимости"""
    return get_add_region_categories_keyboard()


def get_category_regions_keyboard(category: str, page: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура для выбора регионов в категории"""
    regions_per_page = 8
    
    # Определяем регионы по категории
    if category == "dublin_areas":
        regions = DUBLIN_REGIONS
        title = "🏙️ Районы Дублина"
    elif category == "main_cities":
        regions = MAIN_CITIES
        title = "🌆 Основные города"
    elif category == "republic_counties":
        regions = REGION_CATEGORIES["republic_of_ireland"]
        title = "🗺️ Графства Ирландии"
    elif category == "northern_counties":
        regions = REGION_CATEGORIES["northern_ireland"]
        title = "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Северная Ирландия"
    elif category == "popular":
        # Для популярных комбинаций создаем специальную клавиатуру
        return get_popular_combinations_keyboard()
    else:
        regions = ALL_LOCATIONS
        title = "🌍 Все регионы"
    
    # Пагинация
    region_items = list(regions.items())
    total_pages = math.ceil(len(region_items) / regions_per_page)
    start_idx = page * regions_per_page
    end_idx = start_idx + regions_per_page
    page_regions = region_items[start_idx:end_idx]
    
    keyboard = []
    
    # Добавляем кнопки регионов (по 2 в ряд)
    for i in range(0, len(page_regions), 2):
        row = []
        for j in range(2):
            if i + j < len(page_regions):
                region_key, region_name = page_regions[i + j]
                # Обрезаем длинные названия
                display_name = region_name[:20] + "..." if len(region_name) > 20 else region_name
                row.append(InlineKeyboardButton(
                    text=display_name,
                    callback_data=f"select_region_{region_key}"
                ))
        keyboard.append(row)
    
    # Навигация по страницам
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="⬅️",
                callback_data=f"category_page_{category}_{page-1}"
            ))
        
        nav_row.append(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="noop"
        ))
        
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(
                text="➡️",
                callback_data=f"category_page_{category}_{page+1}"
            ))
        
        keyboard.append(nav_row)
    
    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton(text="🔙 К категориям", callback_data="manage_regions"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_popular_combinations_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура популярных комбинаций"""
    keyboard = []
    
    for combo_key, regions in POPULAR_COMBINATIONS.items():
        # Красивые названия для комбинаций
        combo_names = {
            "dublin_central": "🏛️ Центральный Дублин",
            "dublin_south": "🌳 Южный Дублин", 
            "dublin_north": "🏢 Северный Дублин",
            "dublin_west": "🏘️ Западный Дублин",
            "major_cities": "🌆 Крупные города",
            "student_areas": "🎓 Студенческие районы"
        }
        
        display_name = combo_names.get(combo_key, combo_key.replace("_", " ").title())
        keyboard.append([InlineKeyboardButton(
            text=f"{display_name} ({len(regions)})",
            callback_data=f"select_combo_{combo_key}"
        )])
    
    keyboard.append([
        InlineKeyboardButton(text="🔙 К категориям", callback_data="manage_regions"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_user_regions_keyboard(user_regions: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура с регионами пользователя для удаления"""
    keyboard = []
    
    for region_key in user_regions:
        region_name = ALL_LOCATIONS.get(region_key, region_key)
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {region_name}",
                callback_data=f"remove_region_{region_key}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="manage_regions"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_bedrooms_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора количества спален"""
    keyboard = []
    
    # Ряды по 3 кнопки
    for i in range(0, 11, 3):
        row = []
        for j in range(i, min(i + 3, 11)):
            if j == 0:
                text = "Студия"
            else:
                text = f"{j} спален" if j > 1 else "1 спальня"
            row.append(InlineKeyboardButton(text=text, callback_data=f"bedrooms_{j}"))
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_price_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора максимальной цены"""
    prices = [1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 7500, 10000]
    
    keyboard = []
    
    # Ряды по 2 кнопки
    for i in range(0, len(prices), 2):
        row = []
        for j in range(i, min(i + 2, len(prices))):
            price = prices[j]
            row.append(InlineKeyboardButton(text=f"€{price}", callback_data=f"price_{price}"))
        keyboard.append(row)
    
    # Кнопка для ввода своей цены
    keyboard.append([
        InlineKeyboardButton(text="✏️ Указать свою цену", callback_data="custom_price")
    ])
    
    keyboard.append([
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_interval_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора интервала мониторинга"""
    intervals = [
        (300, "5 минут"),
        (600, "10 минут"),
        (1800, "30 минут"),
        (3600, "1 час"),
        (7200, "2 часа"),
        (10800, "3 часа"),
        (21600, "6 часов"),
        (43200, "12 часов"),
        (86400, "24 часа")
    ]
    
    keyboard = []
    
    for interval_seconds, interval_text in intervals:
        keyboard.append([
            InlineKeyboardButton(
                text=interval_text,
                callback_data=f"interval_{interval_seconds}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура возврата в главное меню"""
    keyboard = [
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_statistics_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для статистики"""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 За неделю", callback_data="stats_7"),
            InlineKeyboardButton(text="📊 За месяц", callback_data="stats_30")
        ],
        [
            InlineKeyboardButton(text="📋 Последние поиски", callback_data="recent_searches"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="statistics")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
