#!/usr/bin/env python3
"""
Модуль для современного форматирования сообщений бота
Использует HTML форматирование для лучшей читабельности
"""

from typing import Dict, List, Any
from config.regions import ALL_LOCATIONS

class MessageFormatter:
    """Класс для форматирования сообщений в современном стиле"""
    
    @staticmethod
    def welcome_message(is_new_user: bool = False) -> str:
        """Приветственное сообщение"""
        text = """🏠 <b>Daft.ie Property Bot</b>

Добро пожаловать в умный бот для поиска недвижимости в Ирландии!"""
        
        if is_new_user:
            text += "\n\n🆕 <i>Вы новый пользователь! Настройки по умолчанию уже созданы.</i>"
        
        text += """

<b>🚀 Что умеет бот:</b>
• 🔄 Автоматический мониторинг новых объявлений
• 🎯 Гибкие фильтры поиска (регионы, цена, спальни)
• 📊 Детальная статистика и аналитика
• ⚡ Мгновенные уведомления о новых предложениях
• 🌍 Поиск по всей Ирландии

<i>Выберите действие в меню ниже ↓</i>"""
        
        return text
    
    @staticmethod
    def main_menu() -> str:
        """Главное меню"""
        return """🏠 <b>Главное меню</b>

Выберите нужное действие:"""
    
    @staticmethod
    def settings_menu() -> str:
        """Меню настроек"""
        return """⚙️ <b>Настройки поиска</b>

Настройте параметры для поиска недвижимости:"""
    
    @staticmethod
    def regions_menu() -> str:
        """Меню управления регионами"""
        return """🏘️ <b>Управление регионами</b>

Настройте районы и города для поиска недвижимости:"""
    
    @staticmethod
    def add_region_menu() -> str:
        """Меню добавления региона"""
        return """➕ <b>Добавить регион</b>

Выберите категорию для добавления нового региона поиска:"""
    
    @staticmethod
    def current_settings(settings: Dict[str, Any]) -> str:
        """Текущие настройки пользователя"""
        regions_text = ", ".join([
            ALL_LOCATIONS.get(region, region) for region in settings.get("regions", [])
        ])
        
        interval_minutes = settings.get("monitoring_interval", 3600) // 60
        interval_text = f"{interval_minutes} мин" if interval_minutes < 60 else f"{interval_minutes // 60} ч"
        
        return f"""⚙️ <b>Текущие настройки</b>

🏘️ <b>Регионы:</b> {regions_text or "Не выбраны"}
🛏️ <b>Минимум спален:</b> {settings.get("min_bedrooms", 0)}
💰 <b>Максимальная цена:</b> €{settings.get("max_price", 0):,}
⏰ <b>Интервал проверки:</b> {interval_text}
📄 <b>Максимум результатов:</b> {settings.get("max_results_per_search", 50)}"""
    
    @staticmethod
    def monitoring_status(is_active: bool, settings: Dict[str, Any]) -> str:
        """Статус мониторинга"""
        status_emoji = "🟢" if is_active else "🔴"
        status_text = "Активен" if is_active else "Остановлен"
        
        regions_text = ", ".join([
            ALL_LOCATIONS.get(region, region) for region in settings.get("regions", [])
        ])
        
        return f"""📊 <b>Статус мониторинга</b>

{status_emoji} <b>Статус:</b> {status_text}

{MessageFormatter.current_settings(settings)}"""
    
    @staticmethod
    def statistics_main(user_name: str, total_properties: int) -> str:
        """Главное меню статистики"""
        return f"""📊 <b>Статистика поиска</b>

👤 <b>Пользователь:</b> {user_name}
🏠 <b>Найдено объявлений (7 дней):</b> {total_properties}

Выберите период для подробной статистики:"""
    
    @staticmethod
    def help_message() -> str:
        """Справочное сообщение"""
        return """❓ <b>Справка по боту</b>

<b>🎮 Основные команды:</b>
• <code>/start</code> — Запуск бота и главное меню
• <code>/status</code> — Текущий статус мониторинга
• <code>/help</code> — Показать эту справку

<b>🔄 Мониторинг:</b>
• <b>Запустить</b> — начать автоматический поиск
• <b>Остановить</b> — прекратить мониторинг
• <b>Разовый поиск</b> — найти объявления прямо сейчас

<b>⚙️ Настройки:</b>
• <b>Регионы</b> — выбор районов и городов
• <b>Спальни</b> — минимальное количество комнат
• <b>Цена</b> — максимальный бюджет
• <b>Интервал</b> — частота автопроверки

<b>📊 Статистика:</b>
• Просмотр всех найденных объявлений
• Аналитика по периодам
• История поиска и результаты

<i>💡 Подсказка: Используйте кнопки меню для навигации</i>"""
    
    @staticmethod
    def property_summary(property_data: Dict[str, Any]) -> str:
        """Краткое описание объявления"""
        price = f"€{property_data.get('price', 0):,}" if property_data.get('price') else "Цена не указана"
        bedrooms = f"{property_data.get('bedrooms', 'N/A')} спален"
        location = property_data.get('location', 'Локация не указана')
        
        return f"""🏠 <b>{property_data.get('title', 'Без названия')}</b>

📍 <b>Адрес:</b> {location}
💰 <b>Цена:</b> {price}
🛏️ <b>Спальни:</b> {bedrooms}

<a href="{property_data.get('url', '#')}">🔗 Посмотреть объявление</a>"""
    
    @staticmethod
    def search_results_header(total_found: int, filtered_count: int, region: str = "") -> str:
        """Заголовок результатов поиска"""
        region_text = f" в регионе <b>{region}</b>" if region else ""
        
        if total_found == 0:
            return f"""🔍 <b>Результаты поиска</b>{region_text}

😔 Ничего не найдено по вашим критериям.
Попробуйте изменить фильтры поиска."""
        
        return f"""🔍 <b>Результаты поиска</b>{region_text}

✅ <b>Найдено:</b> {total_found} объявлений
🎯 <b>Подходящих:</b> {filtered_count} объявлений"""
    
    @staticmethod
    def error_message(error_type: str = "general") -> str:
        """Сообщения об ошибках"""
        messages = {
            "general": "❌ <b>Произошла ошибка</b>\n\nПопробуйте позже или обратитесь к администратору.",
            "no_settings": "❌ <b>Настройки не найдены</b>\n\nИспользуйте команду /start для инициализации.",
            "parsing_error": "❌ <b>Ошибка парсинга</b>\n\nНе удалось получить данные с сайта. Попробуйте позже.",
            "network_error": "🌐 <b>Проблемы с сетью</b>\n\nПроверьте подключение к интернету и попробуйте снова."
        }
        return messages.get(error_type, messages["general"])
    
    @staticmethod
    def success_message(action: str, details: str = "") -> str:
        """Сообщения об успешных действиях"""
        base_text = f"✅ <b>{action}</b>"
        if details:
            base_text += f"\n\n{details}"
        return base_text
    
    @staticmethod
    def confirmation_message(action: str, details: str = "") -> str:
        """Сообщения подтверждения действий"""
        base_text = f"❓ <b>Подтверждение</b>\n\n{action}"
        if details:
            base_text += f"\n\n<i>{details}</i>"
        return base_text
