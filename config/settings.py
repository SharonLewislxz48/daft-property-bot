import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv(override=True)

class Settings:
    # Telegram настройки
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    CHAT_ID: str = os.getenv("CHAT_ID", "")
    ADMIN_USER_ID: int = int(os.getenv("ADMIN_USER_ID", "0"))
    
    # База данных
    DB_PATH: str = os.getenv("DB_PATH", "./data/daftbot.db")
    
    # Парсер настройки
    UPDATE_INTERVAL: int = int(os.getenv("UPDATE_INTERVAL", "120"))  # секунды
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_DELAY: float = 1.0  # секунды между запросами
    
    # Фильтры по умолчанию
    DEFAULT_CITY: str = "Dublin"
    DEFAULT_MAX_PRICE: int = 2500
    DEFAULT_MIN_BEDROOMS: int = 3
    DEFAULT_AREAS: List[str] = []
    
    # Daft.ie URLs
    BASE_URL: str = "https://www.daft.ie"
    SEARCH_URL: str = "https://www.daft.ie/property-for-rent"
    
    # Логирование
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # User Agent для парсера
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка обязательных настроек"""
        required_fields = [
            cls.TELEGRAM_BOT_TOKEN,
            cls.CHAT_ID,
        ]
        return all(field for field in required_fields)

settings = Settings()
