#!/usr/bin/env python3
"""
API интерфейс для интеграции парсера daft.ie с ботом
Обеспечивает простой интерфейс для вызова парсера из бота
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from production_daft_parser import ProductionDaftParser

class DaftParserAPI:
    """API класс для интеграции с ботом"""
    
    def __init__(self):
        self.parser = ProductionDaftParser(log_level="WARNING")  # Меньше логов для бота
        
    async def search_properties_for_bot(
        self,
        min_bedrooms: int = 3,
        max_price: int = 2500,
        location: str = "dublin",
        property_type: str = "all",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Основная функция для бота - поиск недвижимости
        
        Args:
            min_bedrooms: Минимальное количество спален
            max_price: Максимальная цена в евро
            location: Локация (dublin, cork, etc.)
            property_type: Тип недвижимости (all, houses, apartments)
            max_results: Максимальное количество результатов
            
        Returns:
            Словарь с результатами и статистикой
        """
        try:
            # Определяем количество страниц исходя из желаемого количества результатов
            estimated_pages = min(max(max_results // 20 + 1, 1), 5)
            
            # Выполняем поиск
            results = await self.parser.search_all_properties(
                min_bedrooms=min_bedrooms,
                max_price=max_price,
                location=location,
                property_type=property_type,
                max_pages=estimated_pages
            )
            
            # Ограничиваем результаты
            limited_results = results[:max_results]
            
            # Подготавливаем ответ для бота
            response = {
                'success': True,
                'found_count': len(limited_results),
                'total_available': len(results),
                'search_params': {
                    'min_bedrooms': min_bedrooms,
                    'max_price': max_price,
                    'location': location,
                    'property_type': property_type
                },
                'properties': self._format_properties_for_bot(limited_results),
                'summary': self._create_summary(limited_results),
                'statistics': self._calculate_stats(limited_results)
            }
            
            return response
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'found_count': 0,
                'properties': []
            }
    
    def _format_properties_for_bot(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Форматирует объявления для отправки боту"""
        formatted = []
        
        for prop in properties:
            formatted_prop = {
                'title': prop.get('title', 'Без названия'),
                'price': prop.get('price'),
                'price_formatted': f"€{prop['price']}" if prop.get('price') else 'Цена не указана',
                'bedrooms': prop.get('bedrooms'),
                'bedrooms_formatted': f"{prop['bedrooms']} спален" if prop.get('bedrooms') else 'Спальни не указаны',
                'location': prop.get('location', 'Локация не указана'),
                'property_type': prop.get('property_type', 'Тип не указан'),
                'url': prop.get('url'),
                'description': prop.get('description', '')[:150] + '...' if prop.get('description') and len(prop.get('description', '')) > 150 else prop.get('description', ''),
                'features': prop.get('features', []),
                'ber_rating': prop.get('ber_rating'),
                'bathrooms': prop.get('bathrooms')
            }
            formatted.append(formatted_prop)
        
        return formatted
    
    def _create_summary(self, properties: List[Dict[str, Any]]) -> str:
        """Создает краткую сводку для бота"""
        if not properties:
            return "❌ Объявления не найдены"
        
        count = len(properties)
        prices = [p['price'] for p in properties if p.get('price')]
        bedrooms = [p['bedrooms'] for p in properties if p.get('bedrooms')]
        
        summary_parts = [f"🏠 Найдено {count} объявлений"]
        
        if prices:
            avg_price = sum(prices) // len(prices)
            min_price = min(prices)
            max_price = max(prices)
            summary_parts.append(f"💰 Цены: €{min_price} - €{max_price} (средняя €{avg_price})")
        
        if bedrooms:
            min_beds = min(bedrooms)
            max_beds = max(bedrooms)
            if min_beds == max_beds:
                summary_parts.append(f"🛏️ Спальни: {min_beds}")
            else:
                summary_parts.append(f"🛏️ Спальни: {min_beds} - {max_beds}")
        
        return "\n".join(summary_parts)
    
    def _calculate_stats(self, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Вычисляет статистику для бота"""
        if not properties:
            return {}
        
        prices = [p['price'] for p in properties if p.get('price')]
        bedrooms = [p['bedrooms'] for p in properties if p.get('bedrooms')]
        locations = [p['location'] for p in properties if p.get('location')]
        
        stats = {
            'total_count': len(properties),
            'with_price': len(prices),
            'with_bedrooms': len(bedrooms)
        }
        
        if prices:
            stats.update({
                'avg_price': sum(prices) // len(prices),
                'min_price': min(prices),
                'max_price': max(prices)
            })
        
        if bedrooms:
            stats.update({
                'avg_bedrooms': sum(bedrooms) / len(bedrooms),
                'min_bedrooms': min(bedrooms),
                'max_bedrooms': max(bedrooms)
            })
        
        # Популярные локации
        if locations:
            location_counts = {}
            for loc in locations:
                location_counts[loc] = location_counts.get(loc, 0) + 1
            stats['popular_locations'] = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return stats
    
    def format_property_for_message(self, property_data: Dict[str, Any], include_url: bool = True) -> str:
        """Форматирует одно объявление для сообщения бота"""
        title = property_data.get('title', 'Без названия')
        price = property_data.get('price_formatted', 'Цена не указана')
        bedrooms = property_data.get('bedrooms_formatted', 'Спальни не указаны')
        location = property_data.get('location', 'Локация не указана')
        
        message_parts = [
            f"🏠 {title}",
            f"💰 {price}",
            f"🛏️ {bedrooms}",
            f"📍 {location}"
        ]
        
        if property_data.get('ber_rating'):
            message_parts.append(f"⚡ BER: {property_data['ber_rating']}")
        
        if include_url and property_data.get('url'):
            message_parts.append(f"🔗 {property_data['url']}")
        
        return "\n".join(message_parts)
    
    def format_multiple_properties_for_message(
        self, 
        properties: List[Dict[str, Any]], 
        max_per_message: int = 5,
        include_urls: bool = False
    ) -> List[str]:
        """Форматирует несколько объявлений для отправки в виде сообщений"""
        messages = []
        
        for i in range(0, len(properties), max_per_message):
            batch = properties[i:i + max_per_message]
            
            message_parts = []
            for j, prop in enumerate(batch, 1):
                prop_text = self.format_property_for_message(prop, include_url=include_urls)
                message_parts.append(f"{i + j}. {prop_text}")
            
            messages.append("\n\n".join(message_parts))
        
        return messages

# Пример функций для интеграции с ботом
async def bot_search_properties(
    min_bedrooms: int = 3,
    max_price: int = 2500,
    location: str = "dublin",
    property_type: str = "all",
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Функция-обертка для вызова из бота
    """
    api = DaftParserAPI()
    return await api.search_properties_for_bot(
        min_bedrooms=min_bedrooms,
        max_price=max_price,
        location=location,
        property_type=property_type,
        max_results=max_results
    )

async def bot_quick_search(user_message: str) -> Dict[str, Any]:
    """
    Быстрый поиск по сообщению пользователя
    Парсит параметры из текста сообщения
    """
    import re
    
    # Значения по умолчанию
    min_bedrooms = 3
    max_price = 2500
    location = "dublin"
    property_type = "all"
    max_results = 5
    
    # Парсим сообщение пользователя
    message_lower = user_message.lower()
    
    # Ищем количество спален
    bedroom_match = re.search(r'(\d+)\+?\s*(?:спален|bedroom|bed)', message_lower)
    if bedroom_match:
        min_bedrooms = int(bedroom_match.group(1))
    
    # Ищем цену
    price_match = re.search(r'(?:до|под|максимум|max)?\s*€?(\d+)', message_lower)
    if price_match:
        max_price = int(price_match.group(1))
    
    # Ищем тип недвижимости
    if 'дом' in message_lower or 'house' in message_lower:
        property_type = "houses"
    elif 'квартир' in message_lower or 'apartment' in message_lower:
        property_type = "apartments"
    
    # Ищем локацию
    if 'cork' in message_lower or 'корк' in message_lower:
        location = "cork"
    elif 'galway' in message_lower or 'голуэй' in message_lower:
        location = "galway"
    
    return await bot_search_properties(
        min_bedrooms=min_bedrooms,
        max_price=max_price,
        location=location,
        property_type=property_type,
        max_results=max_results
    )

# Функция для тестирования API
async def test_bot_integration():
    """Тестирование интеграции с ботом"""
    print("🤖 ТЕСТИРОВАНИЕ BOT API")
    print("=" * 50)
    
    api = DaftParserAPI()
    
    # Тестовый поиск
    result = await api.search_properties_for_bot(
        min_bedrooms=3,
        max_price=2500,
        location="dublin",
        property_type="houses",
        max_results=3
    )
    
    if result['success']:
        print(f"✅ Успешно найдено: {result['found_count']} объявлений")
        print(f"📊 Сводка:\n{result['summary']}")
        
        print("\n🏠 ОБЪЯВЛЕНИЯ ДЛЯ БОТА:")
        for i, prop in enumerate(result['properties'][:2], 1):
            formatted = api.format_property_for_message(prop)
            print(f"\n{i}. {formatted}")
            
        # Тест форматирования для сообщений
        messages = api.format_multiple_properties_for_message(
            result['properties'], 
            max_per_message=2, 
            include_urls=False
        )
        
        print(f"\n📱 СООБЩЕНИЯ ДЛЯ БОТА ({len(messages)} сообщений):")
        for i, message in enumerate(messages, 1):
            print(f"\nСообщение {i}:\n{message}")
            
    else:
        print(f"❌ Ошибка: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_bot_integration())
