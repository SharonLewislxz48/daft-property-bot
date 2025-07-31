#!/usr/bin/env python3
"""
Простой скрипт для отправки результатов парсера в Telegram
Читает JSON файлы с результатами и отправляет объявления в чат
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import aiohttp
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramSender:
    """Отправщик сообщений в Telegram"""
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("Необходимо указать TELEGRAM_BOT_TOKEN и CHAT_ID в .env файле")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.sent_properties_file = "sent_properties.json"
        self.sent_properties = self._load_sent_properties()
    
    def _load_sent_properties(self) -> set:
        """Загружает список уже отправленных объявлений"""
        try:
            if os.path.exists(self.sent_properties_file):
                with open(self.sent_properties_file, 'r') as f:
                    return set(json.load(f))
        except Exception as e:
            logger.warning(f"Не удалось загрузить список отправленных объявлений: {e}")
        return set()
    
    def _save_sent_properties(self):
        """Сохраняет список отправленных объявлений"""
        try:
            with open(self.sent_properties_file, 'w') as f:
                json.dump(list(self.sent_properties), f)
        except Exception as e:
            logger.error(f"Не удалось сохранить список отправленных объявлений: {e}")
    
    async def send_message(self, text: str) -> bool:
        """Отправляет сообщение в Telegram"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': 'HTML',
                    'disable_web_page_preview': False
                }
                
                async with session.post(f"{self.api_url}/sendMessage", data=data) as response:
                    if response.status == 200:
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка отправки сообщения: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return False
    
    def format_property_message(self, prop: Dict[str, Any]) -> str:
        """Форматирует объявление для отправки в Telegram"""
        title = prop.get('title', 'Без названия')
        price = f"€{prop['price']}" if prop.get('price') else 'Цена не указана'
        bedrooms = prop.get('bedrooms', 'Не указано')
        location = prop.get('location', 'Локация не указана')
        url = prop.get('url', '')
        
        # Форматируем спальни
        if bedrooms == 0:
            bed_text = "Studio"
        elif bedrooms == 1:
            bed_text = "1 спальня"
        elif bedrooms in [2, 3, 4]:
            bed_text = f"{bedrooms} спальни"
        else:
            bed_text = f"{bedrooms} спален"
        
        message = f"""🏠 <b>{title}</b>

💰 <b>Цена:</b> {price}
🛏️ <b>Спальни:</b> {bed_text}
📍 <b>Район:</b> {location}

🔗 <a href="{url}">Посмотреть на Daft.ie</a>"""
        
        return message
    
    async def send_properties(self, properties: List[Dict[str, Any]]) -> int:
        """Отправляет список объявлений в Telegram"""
        sent_count = 0
        
        for prop in properties:
            # Используем URL как уникальный идентификатор
            property_id = prop.get('url', '')
            
            if not property_id:
                logger.warning("Объявление без URL, пропускаем")
                continue
            
            # Проверяем, не отправляли ли уже это объявление
            if property_id in self.sent_properties:
                logger.debug(f"Объявление уже отправлено: {property_id}")
                continue
            
            # Форматируем и отправляем сообщение
            message = self.format_property_message(prop)
            
            if await self.send_message(message):
                self.sent_properties.add(property_id)
                sent_count += 1
                logger.info(f"✅ Отправлено: {prop.get('title', 'Без названия')[:50]}")
                
                # Задержка между сообщениями
                await asyncio.sleep(2)
            else:
                logger.error(f"❌ Не удалось отправить: {prop.get('title', 'Без названия')[:50]}")
        
        # Сохраняем список отправленных объявлений
        self._save_sent_properties()
        
        return sent_count

class PropertySender:
    """Основной класс для отправки объявлений"""
    
    def __init__(self):
        self.telegram = TelegramSender()
        self.results_dir = Path("results")
    
    def find_latest_results_file(self) -> Path:
        """Находит самый свежий файл с результатами"""
        json_files = list(self.results_dir.glob("daft_results_*.json"))
        
        if not json_files:
            raise FileNotFoundError("Не найдено файлов с результатами в папке results/")
        
        # Сортируем по времени модификации
        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Найден файл с результатами: {latest_file}")
        
        return latest_file
    
    def load_properties_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Загружает объявления из JSON файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Файл может содержать объекты разной структуры
            if isinstance(data, list):
                # Прямой список объявлений
                return data
            elif isinstance(data, dict) and 'results' in data:
                # Структура с результатами
                return data['results']
            else:
                logger.error("Неизвестная структура файла")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            return []
    
    async def run(self):
        """Основная функция для запуска отправки"""
        try:
            logger.info("🚀 Запуск отправки объявлений в Telegram")
            
            # Находим последний файл с результатами
            results_file = self.find_latest_results_file()
            
            # Загружаем объявления
            properties = self.load_properties_from_file(results_file)
            logger.info(f"📊 Загружено {len(properties)} объявлений")
            
            if not properties:
                logger.warning("Нет объявлений для отправки")
                return
            
            # Отправляем объявления
            sent_count = await self.telegram.send_properties(properties)
            
            logger.info(f"✅ Отправка завершена: {sent_count} новых объявлений")
            
            # Отправляем сводку
            summary_message = f"""📊 <b>Сводка по поиску</b>

🔍 Найдено объявлений: {len(properties)}
📤 Отправлено новых: {sent_count}
⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
            
            await self.telegram.send_message(summary_message)
            
        except Exception as e:
            logger.error(f"Ошибка в основной функции: {e}")
            # Отправляем сообщение об ошибке
            error_message = f"❌ <b>Ошибка при отправке объявлений</b>\n\n{str(e)}"
            try:
                await self.telegram.send_message(error_message)
            except:
                pass

async def main():
    """Главная функция"""
    sender = PropertySender()
    await sender.run()

if __name__ == "__main__":
    asyncio.run(main())
