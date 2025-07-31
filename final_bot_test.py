#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ Telegram бот с интегрированным обходом блокировки
"""
import asyncio
import logging
from datetime import datetime
from typing import List
from aiogram import Bot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinalTelegramBot:
    """Финальный Telegram бот с реальными данными"""
    
    def __init__(self, token: str, chat_id: str):
        self.bot = Bot(token=token)
        self.chat_id = chat_id
        
    async def send_real_properties(self, city="Dublin", max_price=2500, min_bedrooms=3):
        """Отправка реальных объявлений в группу"""
        try:
            # Импортируем наш парсер с обходом блокировки
            import sys
            sys.path.append('/home/barss/PycharmProjects/daftparser')
            from parser.final_daft_parser import FinalDaftParser
            
            logger.info(f"🔍 Searching properties: {city}, max €{max_price}, {min_bedrooms}+ beds")
            
            # Получаем данные через наш продвинутый парсер
            parser = FinalDaftParser()
            properties = await parser.search_with_bypass(city, max_price, min_bedrooms)
            
            if not properties:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text="⚠️ Объявления не найдены. Проверяю источники данных...",
                    parse_mode="Markdown"
                )
                await parser.close()
                return False
            
            # Формируем красивое сообщение
            current_time = datetime.now().strftime('%H:%M')
            current_date = datetime.now().strftime('%d.%m.%Y')
            
            message = f"🏠 *Новые объявления в {city}* ({current_time})\n\n"
            message += f"🔍 *Параметры поиска:*\n"
            message += f"💰 Максимальная цена: €{max_price:,}\n"
            message += f"🛏️ Минимум спален: {min_bedrooms}\n"
            message += f"📊 Найдено: {len(properties)} объявлений\n\n"
            
            # Добавляем лучшие объявления
            message += "📋 *ТОП объявления:*\n\n"
            
            for i, prop in enumerate(properties[:6], 1):
                message += f"*{i}. {prop['title']}*\n"
                message += f"💰 {prop['price']}\n"
                message += f"📍 {prop['address']}\n"
                
                if prop.get('bedrooms'):
                    bedrooms = prop['bedrooms']
                    bathrooms = prop.get('bathrooms', 1)
                    message += f"🏠 {bedrooms} спален, {bathrooms} ванная\n"
                
                message += f"🔗 [Смотреть объявление]({prop['url']})\n\n"
            
            # Добавляем информацию об обновлении
            message += f"─────────────────────\n"
            message += f"🔄 Обновлено: {current_date} {current_time}\n"
            message += f"✅ *Используются РЕАЛЬНЫЕ данные*\n"
            message += f"🔓 *Блокировка обойдена успешно*\n"
            message += f"🤖 Автоматический мониторинг daft.ie"
            
            # Отправляем сообщение
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
            logger.info(f"✅ Sent {len(properties[:6])} properties out of {len(properties)} found")
            
            await parser.close()
            return True
            
        except Exception as e:
            logger.error(f"Error sending properties: {e}")
            
            # Отправляем сообщение об ошибке
            error_message = f"❌ *Ошибка при получении данных*\n\n"
            error_message += f"🕐 Время: {datetime.now().strftime('%H:%M')}\n"
            error_message += f"⚠️ Причина: {str(e)[:100]}...\n"
            error_message += f"🔄 Повторная попытка через несколько минут"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=error_message,
                parse_mode="Markdown"
            )
            return False
    
    async def close(self):
        """Закрытие бота"""
        await self.bot.session.close()

# Быстрый тест
async def test_final_bot():
    """Тестирование финального бота"""
    logger.info("🚀 Starting FINAL bot test with bypass...")
    
    bot = FinalTelegramBot(
        token="8219994646:AAEJMZGow2b_F4OcTQBqGqZp0-8baLVnatQ",
        chat_id="-1002819366953"
    )
    
    try:
        success = await bot.send_real_properties("Dublin", 2500, 3)
        
        if success:
            logger.info("🎉 FINAL BOT TEST SUCCESSFUL!")
            print("🎉 ФИНАЛЬНЫЙ ТЕСТ УСПЕШЕН!")
            print("✅ Бот отправил реальные данные в группу")
            print("🔓 Блокировка обойдена")
            print("📊 Данные получены с daft.ie")
        else:
            logger.warning("⚠️ Final bot test had issues")
            print("⚠️ Проблемы с финальным тестом")
            
    except Exception as e:
        logger.error(f"Final bot test failed: {e}")
        print(f"❌ Ошибка финального теста: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_final_bot())
