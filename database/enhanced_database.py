#!/usr/bin/env python3
"""
Улучшенная база данных для хранения настроек пользователей и истории поиска
"""

import aiosqlite
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class EnhancedDatabase:
    """Класс для работы с базой данных пользователей и поиска"""
    
    def __init__(self, db_path: str = "data/enhanced_bot.db"):
        self.db_path = db_path
    
    async def init_database(self):
        """Инициализация базы данных с созданием таблиц"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей и их настроек
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Таблица настроек поиска пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    chat_id INTEGER,  -- ID чата для отправки сообщений
                    regions TEXT DEFAULT '["dublin-city"]',  -- JSON массив регионов
                    min_bedrooms INTEGER DEFAULT 3,
                    max_price INTEGER DEFAULT 2500,
                    monitoring_interval INTEGER DEFAULT 3600,  -- в секундах
                    max_results_per_search INTEGER DEFAULT 50,
                    is_monitoring_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Миграция: добавляем chat_id к существующим записям, если поле не существует
            try:
                await db.execute("ALTER TABLE user_settings ADD COLUMN chat_id INTEGER")
                await db.commit()
                logger.info("Добавлено поле chat_id в таблицу user_settings")
            except Exception:
                # Поле уже существует
                pass
            
            # Проверяем и исправляем NULL chat_id для существующих пользователей
            await db.execute("""
                UPDATE user_settings 
                SET chat_id = user_id 
                WHERE chat_id IS NULL
            """)
            await db.commit()
            
            # Таблица истории найденных объявлений
            await db.execute("""
                CREATE TABLE IF NOT EXISTS property_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    property_url TEXT NOT NULL,
                    property_title TEXT,
                    price INTEGER,
                    bedrooms INTEGER,
                    location TEXT,
                    property_type TEXT,
                    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_sent BOOLEAN DEFAULT 0,
                    search_params TEXT,  -- JSON с параметрами поиска
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, property_url)  -- Предотвращаем дубликаты для пользователя
                )
            """)
            
            # Таблица логов мониторинга
            await db.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    search_params TEXT,  -- JSON параметров
                    properties_found INTEGER DEFAULT 0,
                    new_properties INTEGER DEFAULT 0,
                    execution_time REAL,  -- время выполнения в секундах
                    status TEXT DEFAULT 'success',  -- success, error
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            await db.commit()
            logger.info("База данных инициализирована")
    
    async def get_or_create_user(self, user_id: int, chat_id: int, username: str = None, 
                                first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        """Получает или создает пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем существование пользователя
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                user = await cursor.fetchone()
            
            if user:
                # Обновляем последнюю активность
                await db.execute(
                    "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
                
                # Получаем настройки
                async with db.execute(
                    "SELECT * FROM user_settings WHERE user_id = ?", (user_id,)
                ) as cursor:
                    settings = await cursor.fetchone()
                
                if not settings:
                    # Создаем настройки по умолчанию
                    await self.create_default_settings(user_id, chat_id, db)
                    settings = await self.get_user_settings(user_id)
                
                return {
                    "user_id": user_id,
                    "username": username or user[1],
                    "first_name": first_name or user[2],
                    "last_name": last_name or user[3],
                    "exists": True
                }
            else:
                # Создаем нового пользователя
                await db.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, first_name, last_name))
                
                # Создаем настройки по умолчанию
                await self.create_default_settings(user_id, chat_id, db)
                await db.commit()
                
                logger.info(f"Создан новый пользователь: {user_id}")
                return {
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "exists": False
                }
    
    async def create_default_settings(self, user_id: int, chat_id: int, db: aiosqlite.Connection):
        """Создает настройки по умолчанию для пользователя"""
        await db.execute("""
            INSERT INTO user_settings (user_id, chat_id) VALUES (?, ?)
        """, (user_id, chat_id))
    
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получает настройки пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM user_settings WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
            
            if row:
                # Проверяем структуру таблицы - возможно chat_id не существует
                async with db.execute("PRAGMA table_info(user_settings)") as cursor_info:
                    columns = await cursor_info.fetchall()
                    column_names = [col[1] for col in columns]
                
                # Адаптируемся к разным структурам таблицы
                if 'chat_id' in column_names:
                    # Новая структура с chat_id
                    chat_id_index = column_names.index('chat_id')
                    original_chat_id = row[chat_id_index]
                    chat_id = original_chat_id if original_chat_id is not None else user_id
                    
                    if original_chat_id is None:
                        logger.warning(f"Пользователь {user_id} имеет NULL chat_id, используем fallback: {chat_id}")
                    else:
                        logger.debug(f"Пользователь {user_id} имеет chat_id: {chat_id}")
                        
                    regions_index = column_names.index('regions')
                    min_bedrooms_index = column_names.index('min_bedrooms') 
                    max_price_index = column_names.index('max_price')
                    monitoring_interval_index = column_names.index('monitoring_interval')
                    max_results_per_search_index = column_names.index('max_results_per_search')
                    is_monitoring_active_index = column_names.index('is_monitoring_active')
                    created_at_index = column_names.index('created_at')
                    updated_at_index = column_names.index('updated_at')
                else:
                    # Старая структура без chat_id
                    chat_id = user_id  # Используем user_id как fallback
                    logger.warning(f"Старая структура БД: пользователь {user_id} получает chat_id = user_id")
                    
                    # Старая структура: user_id, regions, min_bedrooms, max_price, monitoring_interval, max_results_per_search, is_monitoring_active, created_at, updated_at
                    regions_index = 1
                    min_bedrooms_index = 2
                    max_price_index = 3
                    monitoring_interval_index = 4
                    max_results_per_search_index = 5
                    is_monitoring_active_index = 6
                    created_at_index = 7
                    updated_at_index = 8
                
                return {
                    "user_id": row[0],
                    "chat_id": chat_id,  # Гарантированно не NULL
                    "regions": json.loads(row[regions_index]) if row[regions_index] and isinstance(row[regions_index], str) else ["dublin-city"],
                    "min_bedrooms": row[min_bedrooms_index],
                    "max_price": row[max_price_index],
                    "monitoring_interval": row[monitoring_interval_index],
                    "max_results_per_search": row[max_results_per_search_index],
                    "is_monitoring_active": bool(row[is_monitoring_active_index]),
                    "created_at": row[created_at_index],
                    "updated_at": row[updated_at_index]
                }
            return None
    
    async def update_user_settings(self, user_id: int, **kwargs) -> bool:
        """Обновляет настройки пользователя"""
        if not kwargs:
            return False
        
        # Обрабатываем регионы отдельно (JSON)
        if 'regions' in kwargs:
            kwargs['regions'] = json.dumps(kwargs['regions'])
        
        # Логируем изменение chat_id
        if 'chat_id' in kwargs:
            logger.info(f"Обновляем chat_id для пользователя {user_id}: {kwargs['chat_id']}")
        
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)
        
        query = f"UPDATE user_settings SET {', '.join(fields)} WHERE user_id = ?"
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, values)
            await db.commit()
            
        logger.info(f"Обновлены настройки пользователя {user_id}: {kwargs}")
        return True
    
    async def add_property_to_history(self, user_id: int, property_data: Dict[str, Any], 
                                     search_params: Dict[str, Any]) -> bool:
        """Добавляет объявление в историю (если его там еще нет)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("""
                    INSERT INTO property_history 
                    (user_id, property_url, property_title, price, bedrooms, location, 
                     property_type, search_params)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    property_data.get('url'),
                    property_data.get('title'),
                    property_data.get('price'),
                    property_data.get('bedrooms'),
                    property_data.get('location'),
                    property_data.get('property_type'),
                    json.dumps(search_params)
                ))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                # Объявление уже существует для этого пользователя
                return False
    
    async def get_new_properties(self, user_id: int, properties: List[Dict[str, Any]], 
                                search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Возвращает только новые объявления, которых нет в истории"""
        new_properties = []
        
        for prop in properties:
            if await self.add_property_to_history(user_id, prop, search_params):
                new_properties.append(prop)
        
        return new_properties
    
    async def mark_properties_as_sent(self, user_id: int, property_urls: List[str]):
        """Отмечает объявления как отправленные"""
        if not property_urls:
            return
        
        placeholders = ', '.join(['?' for _ in property_urls])
        query = f"""
            UPDATE property_history 
            SET is_sent = 1 
            WHERE user_id = ? AND property_url IN ({placeholders})
        """
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, [user_id] + property_urls)
            await db.commit()
    
    async def log_monitoring_session(self, user_id: int, search_params: Dict[str, Any],
                                   properties_found: int, new_properties: int,
                                   execution_time: float, status: str = "success",
                                   error_message: str = None):
        """Логирует сессию мониторинга"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO monitoring_logs 
                (user_id, search_params, properties_found, new_properties, 
                 execution_time, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                json.dumps(search_params),
                properties_found,
                new_properties,
                execution_time,
                status,
                error_message
            ))
            await db.commit()
    
    async def get_user_statistics(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """Получает статистику пользователя за указанное количество дней"""
        since_date = datetime.now() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Общая статистика по объявлениям
            async with db.execute("""
                SELECT COUNT(*) as total_properties,
                       COUNT(CASE WHEN is_sent = 1 THEN 1 END) as sent_properties,
                       AVG(price) as avg_price,
                       MIN(price) as min_price,
                       MAX(price) as max_price
                FROM property_history 
                WHERE user_id = ? AND found_at >= ?
            """, (user_id, since_date)) as cursor:
                property_stats = await cursor.fetchone()
            
            # Статистика мониторинга
            async with db.execute("""
                SELECT COUNT(*) as total_sessions,
                       COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_sessions,
                       AVG(execution_time) as avg_execution_time,
                       SUM(new_properties) as total_new_properties
                FROM monitoring_logs 
                WHERE user_id = ? AND created_at >= ?
            """, (user_id, since_date)) as cursor:
                monitoring_stats = await cursor.fetchone()
            
            return {
                "days": days,
                "properties": {
                    "total": property_stats[0] or 0,
                    "sent": property_stats[1] or 0,
                    "avg_price": round(property_stats[2] or 0, 2),
                    "min_price": property_stats[3] or 0,
                    "max_price": property_stats[4] or 0
                },
                "monitoring": {
                    "total_sessions": monitoring_stats[0] or 0,
                    "successful_sessions": monitoring_stats[1] or 0,
                    "avg_execution_time": round(monitoring_stats[2] or 0, 2),
                    "total_new_properties": monitoring_stats[3] or 0
                }
            }
    
    async def cleanup_old_data(self, days: int = 30):
        """Очищает старые данные старше указанного количества дней"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Удаляем старые логи мониторинга
            await db.execute(
                "DELETE FROM monitoring_logs WHERE created_at < ?", 
                (cutoff_date,)
            )
            
            # Удаляем старые объявления (только отправленные)
            await db.execute(
                "DELETE FROM property_history WHERE found_at < ? AND is_sent = 1", 
                (cutoff_date,)
            )
            
            await db.commit()
            logger.info(f"Очищены данные старше {days} дней")

    def get_user_recent_searches(self, user_id: int, limit: int = 5):
        """Получает недавние поиски пользователя"""
        # Заглушка - возвращаем пустой список пока не реализован
        return []

    async def cache_search_results(self, user_id: int, results: List[Dict[str, Any]]):
        """Кэширует результаты поиска для последующего показа - глобальный кэш для группы"""
        # Простой кэш в памяти (в реальном проекте лучше использовать Redis)
        if not hasattr(self, '_search_cache'):
            self._search_cache = {}
        
        # Используем фиксированный ключ для группы вместо user_id
        self._search_cache['group_results'] = results
        logger.info(f"Кэшированы результаты поиска для группы: {len(results)} объявлений")

    async def get_cached_search_results(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает кэшированные результаты поиска - глобальный кэш для группы"""
        if not hasattr(self, '_search_cache'):
            return []
        
        # Возвращаем результаты из глобального кэша группы
        return self._search_cache.get('group_results', [])
