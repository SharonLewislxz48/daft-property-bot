"""
Адаптер для интеграции рабочего production_parser.py с ботом
"""
import asyncio
import logging
from typing import List
from datetime import datetime

from .models import Property, SearchFilters

logger = logging.getLogger(__name__)

class BotDaftParser:
    """Адаптер для production парсера совместимый с ботом"""
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        
    async def __aenter__(self):
        """Async context manager entry"""
        # Импортируем и инициализируем production парсер
        try:
            from production_parser import ProductionDaftParser
            self.parser = ProductionDaftParser()
            return self
        except ImportError as e:
            logger.error(f"Failed to import ProductionDaftParser: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Очистка не требуется для production парсера
        pass
    
    async def search_properties(self, filters: SearchFilters, max_pages: int = 3) -> List[Property]:
        """Поиск объявлений с фильтрами в формате бота"""
        try:
            logger.info(f"Starting search with filters: city={filters.city}, max_price={filters.max_price}, min_bedrooms={filters.min_bedrooms}, areas={filters.areas}")
            
            # Конвертируем city для правильного URL
            location = "dublin-city" if "dublin" in filters.city.lower() else filters.city.lower().replace(" ", "-")
            
            # Вызываем production парсер
            raw_results = await self.parser.search_properties(
                min_bedrooms=filters.min_bedrooms,
                max_price=filters.max_price,
                location=location,
                limit=max_pages * 20  # 20 на страницу
            )
            
            # Конвертируем результаты в формат Property для бота
            properties = []
            for raw_prop in raw_results:
                try:
                    property_obj = Property(
                        id=raw_prop.get('url', '').split('/')[-1] if raw_prop.get('url') else str(hash(str(raw_prop)))[:10],
                        title=raw_prop.get('title', 'Unknown Property')[:200],
                        address=raw_prop.get('location', 'Dublin')[:200] if raw_prop.get('location') else 'Dublin',
                        price=raw_prop.get('price', 0),
                        bedrooms=raw_prop.get('bedrooms', 1),
                        bathrooms=1,  # production parser не всегда возвращает bathrooms
                        property_type=raw_prop.get('property_type', 'apartment'),
                        url=raw_prop.get('url', ''),
                        image_url=None,
                        description=raw_prop.get('description'),
                        area=raw_prop.get('location'),
                        posted_date=datetime.now()
                    )
                    
                    # Проверяем соответствие фильтрам
                    if self._matches_filters(property_obj, filters):
                        properties.append(property_obj)
                        
                except Exception as e:
                    logger.error(f"Error converting property: {e}")
                    continue
            
            logger.info(f"Search completed. Found {len(properties)} properties matching filters")
            return properties
            
        except Exception as e:
            logger.error(f"Error in search_properties: {e}")
            return []
    
    def _matches_filters(self, property_obj: Property, filters: SearchFilters) -> bool:
        """Проверка соответствия объявления фильтрам"""
        # Проверка цены
        if property_obj.price > filters.max_price:
            return False
        
        # Проверка количества спален
        if property_obj.bedrooms < filters.min_bedrooms:
            return False
        
        # Проверка районов (если указаны)
        if filters.areas and property_obj.area:
            area_match = False
            for filter_area in filters.areas:
                # Нормализуем сравнение районов
                filter_area_norm = filter_area.lower().replace(" ", "")
                property_area_norm = property_obj.area.lower().replace(" ", "")
                
                if filter_area_norm in property_area_norm or property_area_norm in filter_area_norm:
                    area_match = True
                    break
            if not area_match:
                return False
        
        return True
