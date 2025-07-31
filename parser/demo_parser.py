import asyncio
import logging
import random
from typing import List
from datetime import datetime, timedelta

from .models import Property, SearchFilters
from config.settings import settings

logger = logging.getLogger(__name__)

class DemoParser:
    """Демо-парсер с примерами данных для тестирования"""
    
    def __init__(self):
        self.base_url = settings.BASE_URL
        
        # Примеры объявлений для демонстрации
        self.demo_properties = [
            {
                "id": "demo_1",
                "title": "Stunning 2 Bed Apartment in Dublin City Centre",
                "address": "Temple Bar, Dublin 2",
                "price": 2200,
                "bedrooms": 2,
                "bathrooms": 1,
                "property_type": "apartment",
                "area": "Dublin 2",
                "description": "Modern apartment in the heart of Dublin"
            },
            {
                "id": "demo_2", 
                "title": "Spacious 3 Bed House in Rathmines",
                "address": "Rathmines Road, Dublin 6",
                "price": 2400,
                "bedrooms": 3,
                "bathrooms": 2,
                "property_type": "house",
                "area": "Dublin 6",
                "description": "Beautiful Victorian house"
            },
            {
                "id": "demo_3",
                "title": "Modern 1 Bed Apartment with Balcony",
                "address": "Grand Canal Dock, Dublin 4",
                "price": 1800,
                "bedrooms": 1,
                "bathrooms": 1,
                "property_type": "apartment",
                "area": "Dublin 4",
                "description": "New development with amenities"
            },
            {
                "id": "demo_4",
                "title": "Luxury 3 Bed Duplex in Ballsbridge",
                "address": "Ballsbridge, Dublin 4",
                "price": 3200,
                "bedrooms": 3,
                "bathrooms": 2,
                "property_type": "duplex",
                "area": "Dublin 4",
                "description": "Premium location with parking"
            },
            {
                "id": "demo_5",
                "title": "Cozy Studio in Temple Bar",
                "address": "Fleet Street, Dublin 2",
                "price": 1400,
                "bedrooms": 0,
                "bathrooms": 1,
                "property_type": "studio",
                "area": "Dublin 2",
                "description": "Perfect for professionals"
            },
            {
                "id": "demo_6",
                "title": "4 Bed Family Home in Drumcondra",
                "address": "Drumcondra Road, Dublin 9",
                "price": 2800,
                "bedrooms": 4,
                "bathrooms": 3,
                "property_type": "house",
                "area": "Dublin 9",
                "description": "Perfect for families"
            },
            {
                "id": "demo_7",
                "title": "Modern 2 Bed Apartment near Trinity College",
                "address": "Nassau Street, Dublin 2",
                "price": 2500,
                "bedrooms": 2,
                "bathrooms": 1,
                "property_type": "apartment",
                "area": "Dublin 2",
                "description": "Walking distance to city center"
            },
            {
                "id": "demo_8",
                "title": "Bright 3 Bed Apartment in Dun Laoghaire",
                "address": "Marine Road, Dun Laoghaire, Co. Dublin",
                "price": 2100,
                "bedrooms": 3,
                "bathrooms": 2,
                "property_type": "apartment",
                "area": "Co. Dublin",
                "description": "Sea views and DART access"
            }
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        logger.info("Demo parser initialized")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        logger.info("Demo parser closed")
    
    def _matches_filters(self, property_data: dict, filters: SearchFilters) -> bool:
        """Проверка соответствия объявления фильтрам"""
        # Проверка цены
        if property_data["price"] > filters.max_price:
            return False
        
        # Проверка количества спален
        if property_data["bedrooms"] < filters.min_bedrooms:
            return False
        
        # Проверка районов (если указаны)
        if filters.areas and property_data.get("area"):
            area_match = False
            property_area = property_data["area"].lower()
            
            for filter_area in filters.areas:
                filter_area_lower = filter_area.lower()
                if (filter_area_lower in property_area or 
                    property_area in filter_area_lower):
                    area_match = True
                    break
            
            if not area_match:
                return False
        
        return True
    
    async def search_properties(self, filters: SearchFilters, max_pages: int = 5) -> List[Property]:
        """Поиск объявлений с фильтрами (демо-версия)"""
        logger.info(f"Demo search with filters: city={filters.city}, max_price={filters.max_price}, min_bedrooms={filters.min_bedrooms}, areas={filters.areas}")
        
        # Имитируем задержку сети
        await asyncio.sleep(1)
        
        properties = []
        
        for prop_data in self.demo_properties:
            if self._matches_filters(prop_data, filters):
                # Создаем объект Property
                property_obj = Property(
                    id=prop_data["id"],
                    title=prop_data["title"],
                    address=prop_data["address"],
                    price=prop_data["price"],
                    bedrooms=prop_data["bedrooms"],
                    bathrooms=prop_data.get("bathrooms"),
                    property_type=prop_data["property_type"],
                    url=f"{self.base_url}/for-rent/demo-property-{prop_data['id']}",
                    image_url=f"https://via.placeholder.com/400x300?text=Property+{prop_data['id']}",
                    description=prop_data.get("description"),
                    area=prop_data.get("area"),
                    posted_date=datetime.now() - timedelta(hours=random.randint(1, 48))
                )
                properties.append(property_obj)
        
        # Добавляем некоторую случайность для имитации "новых" объявлений
        if random.random() < 0.3:  # 30% вероятность "новых" объявлений
            new_property = Property(
                id=f"demo_new_{random.randint(1000, 9999)}",
                title=f"New Property in {filters.city}",
                address=f"New Street, {filters.city}",
                price=random.randint(filters.max_price - 500, filters.max_price),
                bedrooms=random.randint(filters.min_bedrooms, filters.min_bedrooms + 2),
                bathrooms=1,
                property_type="apartment",
                url=f"{self.base_url}/for-rent/new-demo-property",
                image_url="https://via.placeholder.com/400x300?text=New+Property",
                description="Newly listed property",
                area=f"{filters.city} {random.randint(1, 24)}",
                posted_date=datetime.now()
            )
            properties.append(new_property)
        
        logger.info(f"Demo search completed. Found {len(properties)} properties")
        return properties
