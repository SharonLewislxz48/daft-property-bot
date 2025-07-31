#!/usr/bin/env python3
"""
Конфигуратор поиска - позволяет легко настраивать параметры поиска
"""

import asyncio
import json
from pathlib import Path
from production_parser import ProductionDaftParser

class SearchConfigurator:
    """Класс для настройки и запуска поиска с пользовательскими параметрами"""
    
    def __init__(self):
        self.parser = ProductionDaftParser()
        self.config_file = "search_config.json"
    
    def get_user_preferences(self):
        """Интерактивный сбор предпочтений пользователя"""
        print("🏠 НАСТРОЙКА ПОИСКА НЕДВИЖИМОСТИ")
        print("=" * 50)
        
        # Количество спален
        while True:
            try:
                min_bedrooms = input("Минимальное количество спален (0-10, по умолчанию 3): ").strip()
                if not min_bedrooms:
                    min_bedrooms = 3
                else:
                    min_bedrooms = int(min_bedrooms)
                    if min_bedrooms < 0 or min_bedrooms > 10:
                        raise ValueError
                break
            except ValueError:
                print("❌ Введите число от 0 до 10")
        
        # Максимальная цена
        while True:
            try:
                max_price = input("Максимальная цена в месяц (€, по умолчанию 2500): ").strip()
                if not max_price:
                    max_price = 2500
                else:
                    max_price = int(max_price)
                    if max_price < 500 or max_price > 10000:
                        raise ValueError
                break
            except ValueError:
                print("❌ Введите сумму от €500 до €10000")
        
        # Локация
        print("\n📍 Доступные локации:")
        print("1. dublin-city (Dublin City)")
        print("2. dublin (Dublin общая)")
        print("3. cork (Cork)")
        print("4. galway (Galway)")
        print("5. waterford (Waterford)")
        print("6. limerick (Limerick)")
        
        location_map = {
            '1': 'dublin-city',
            '2': 'dublin',
            '3': 'cork',
            '4': 'galway',
            '5': 'waterford',
            '6': 'limerick'
        }
        
        while True:
            choice = input("Выберите локацию (1-6, по умолчанию 1): ").strip()
            if not choice:
                choice = '1'
            if choice in location_map:
                location = location_map[choice]
                break
            print("❌ Выберите число от 1 до 6")
        
        # Количество результатов
        while True:
            try:
                limit = input("Максимальное количество результатов (по умолчанию 20): ").strip()
                if not limit:
                    limit = 20
                else:
                    limit = int(limit)
                    if limit < 1 or limit > 100:
                        raise ValueError
                break
            except ValueError:
                print("❌ Введите число от 1 до 100")
        
        return {
            'min_bedrooms': min_bedrooms,
            'max_price': max_price,
            'location': location,
            'limit': limit
        }
    
    def save_config(self, config):
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"✅ Конфигурация сохранена в {self.config_file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации: {e}")
    
    def load_config(self):
        """Загрузка конфигурации из файла"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфигурации: {e}")
        return None
    
    def display_config(self, config):
        """Отображение текущей конфигурации"""
        print("\n🎯 ПАРАМЕТРЫ ПОИСКА:")
        print(f"   Минимум спален: {config['min_bedrooms']}")
        print(f"   Максимальная цена: €{config['max_price']}")
        print(f"   Локация: {config['location']}")
        print(f"   Лимит результатов: {config['limit']}")
        print()
    
    async def run_search(self, config):
        """Запуск поиска с заданной конфигурацией"""
        print("🚀 ЗАПУСК ПОИСКА...")
        print("=" * 50)
        
        results = await self.parser.search_properties(**config)
        
        if results:
            print(f"\n✅ Найдено {len(results)} подходящих объявлений!")
            
            # Показываем краткую сводку
            print("\n📋 КРАТКАЯ СВОДКА:")
            for i, prop in enumerate(results[:5], 1):
                title = prop.get('title', 'Без названия')[:60]
                price = prop.get('price', 0)
                bedrooms = prop.get('bedrooms', '?')
                print(f"{i}. {title} - €{price}, {bedrooms} спален")
            
            if len(results) > 5:
                print(f"   ... и еще {len(results) - 5} объявлений")
        else:
            print("❌ Объявления не найдены с указанными параметрами")
        
        return results

async def main():
    """Главная функция"""
    configurator = SearchConfigurator()
    
    print("🏠 КОНФИГУРАТОР ПОИСКА НЕДВИЖИМОСТИ")
    print("=" * 50)
    
    # Проверяем существующую конфигурацию
    existing_config = configurator.load_config()
    
    if existing_config:
        print("📁 Найдена сохраненная конфигурация:")
        configurator.display_config(existing_config)
        
        use_existing = input("Использовать сохраненную конфигурацию? (y/n, по умолчанию y): ").strip().lower()
        if use_existing in ['', 'y', 'yes', 'да']:
            config = existing_config
        else:
            config = configurator.get_user_preferences()
            configurator.save_config(config)
    else:
        config = configurator.get_user_preferences()
        configurator.save_config(config)
    
    # Показываем финальную конфигурацию
    configurator.display_config(config)
    
    # Запускаем поиск
    results = await configurator.run_search(config)
    
    # Предлагаем отправить в Telegram
    if results:
        send_to_telegram = input("\n📤 Отправить результаты в Telegram? (y/n, по умолчанию n): ").strip().lower()
        if send_to_telegram in ['y', 'yes', 'да']:
            try:
                from telegram_sender import PropertySender
                sender = PropertySender()
                
                # Создаем временный JSON файл с результатами
                import datetime
                filename = f"results/daft_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                Path("results").mkdir(exist_ok=True)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                print(f"💾 Результаты сохранены в {filename}")
                
                # Отправляем в Telegram
                await sender.run()
                
            except Exception as e:
                print(f"❌ Ошибка отправки в Telegram: {e}")

if __name__ == "__main__":
    asyncio.run(main())
