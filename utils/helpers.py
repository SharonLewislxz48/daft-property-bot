import logging
import re
from typing import Optional, List
from datetime import datetime
import unicodedata

def setup_logging(level: str = "INFO") -> None:
    """Настройка логирования"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Настройка основного логгера
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("data/bot.log", encoding="utf-8")
        ]
    )
    
    # Уменьшаем уровень логирования для внешних библиотек
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)

def clean_text(text: str) -> str:
    """Очистка текста от лишних символов"""
    if not text:
        return ""
    
    # Удаляем лишние пробелы и переносы строк
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Удаляем HTML теги если есть
    text = re.sub(r'<[^>]+>', '', text)
    
    # Нормализация Unicode
    text = unicodedata.normalize('NFKD', text)
    
    return text

def extract_price_from_text(text: str) -> Optional[int]:
    """Извлечение цены из текста"""
    if not text:
        return None
    
    # Ищем паттерны цен
    patterns = [
        r'€\s*(\d{1,3}(?:,\d{3})*)',  # €1,500 или € 1500
        r'(\d{1,3}(?:,\d{3})*)\s*€',  # 1500€ или 1,500 €
        r'(\d{1,3}(?:,\d{3})*)\s*euro',  # 1500 euro
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return int(price_str)
            except ValueError:
                continue
    
    return None

def format_price(price: int) -> str:
    """Форматирование цены для отображения"""
    return f"€{price:,}/month"

def format_duration(seconds: float) -> str:
    """Форматирование времени выполнения"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def is_valid_email(email: str) -> bool:
    """Проверка валидности email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def extract_dublin_area(text: str) -> Optional[str]:
    """Извлечение района Дублина из текста"""
    if not text:
        return None
    
    # Паттерны для районов Дублина
    patterns = [
        r'Dublin\s+(\d+[WwEe]?)',  # Dublin 1, Dublin 6W
        r'D(\d+[WwEe]?)',  # D1, D6W
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            area_num = match.group(1).upper()
            return f"Dublin {area_num}"
    
    # Проверка на Co. Dublin
    if re.search(r'Co\.?\s*Dublin', text, re.IGNORECASE):
        return "Co. Dublin"
    
    return None

def sanitize_filename(filename: str) -> str:
    """Очистка имени файла от недопустимых символов"""
    # Удаляем недопустимые символы
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Ограничиваем длину
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename

def parse_bedrooms(text: str) -> int:
    """Извлечение количества спален из текста"""
    if not text:
        return 0
    
    text = text.lower()
    
    # Студия
    if 'studio' in text:
        return 0
    
    # Ищем паттерны спален
    patterns = [
        r'(\d+)\s*bed',
        r'(\d+)\s*br',
        r'(\d+)\s*bedroom',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    return 0

def parse_bathrooms(text: str) -> Optional[int]:
    """Извлечение количества ванных из текста"""
    if not text:
        return None
    
    text = text.lower()
    
    patterns = [
        r'(\d+)\s*bath',
        r'(\d+)\s*shower',
        r'(\d+)\s*wc',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    return None

def get_property_type(text: str) -> str:
    """Определение типа недвижимости"""
    if not text:
        return "apartment"
    
    text = text.lower()
    
    if 'house' in text:
        return "house"
    elif 'studio' in text:
        return "studio"
    elif 'apartment' in text or 'flat' in text:
        return "apartment"
    elif 'townhouse' in text:
        return "townhouse"
    elif 'duplex' in text:
        return "duplex"
    
    return "apartment"

def truncate_text(text: str, max_length: int = 200) -> str:
    """Обрезка текста до определенной длины"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # Обрезаем по словам
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Если пробел найден в последних 20%
        truncated = truncated[:last_space]
    
    return truncated + "..."

def escape_html(text: str) -> str:
    """Экранирование HTML символов"""
    if not text:
        return ""
    
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text

def get_area_variations(area: str) -> List[str]:
    """Получение вариаций названия района для поиска"""
    variations = [area]
    
    # Для Dublin районов
    if area.startswith("Dublin"):
        # Dublin 1 -> D1, dublin-1
        area_parts = area.split()
        if len(area_parts) == 2:
            number = area_parts[1]
            variations.extend([
                f"D{number}",
                f"dublin-{number}",
                f"Dublin {number}",
                area.lower(),
                area.replace(" ", "-").lower()
            ])
    
    # Удаляем дубликаты
    return list(set(variations))

def validate_price_range(min_price: int = None, max_price: int = None) -> bool:
    """Валидация диапазона цен"""
    if min_price is not None and min_price < 0:
        return False
    
    if max_price is not None and max_price < 0:
        return False
    
    if min_price is not None and max_price is not None:
        return min_price <= max_price
    
    return True

def format_datetime(dt: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
    """Форматирование даты и времени"""
    if not dt:
        return "—"
    
    return dt.strftime(format_str)

def chunks(lst: List, n: int):
    """Разделение списка на чанки заданного размера"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
