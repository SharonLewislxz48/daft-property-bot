from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Property:
    """Модель объявления о недвижимости"""
    id: str
    title: str
    address: str
    price: int  # в евро
    bedrooms: int
    bathrooms: Optional[int]
    property_type: str  # apartment, house, etc.
    url: str
    image_url: Optional[str]
    description: Optional[str]
    area: Optional[str]  # Dublin 1, Dublin 2, etc.
    posted_date: Optional[datetime]
    
    def __post_init__(self):
        """Валидация и обработка данных после создания"""
        if not self.id:
            raise ValueError("Property ID cannot be empty")
        if not self.url.startswith("http"):
            self.url = f"https://www.daft.ie{self.url}"
    
    def format_price(self) -> str:
        """Форматирование цены для отображения"""
        return f"€{self.price:,}/month"
    
    def format_bedrooms(self) -> str:
        """Форматирование количества спален"""
        if self.bedrooms == 0:
            return "Studio"
        elif self.bedrooms == 1:
            return "1 bedroom"
        else:
            return f"{self.bedrooms} bedrooms"

@dataclass 
class SearchFilters:
    """Фильтры поиска"""
    city: str = "Dublin"
    max_price: int = 2500
    min_bedrooms: int = 3
    areas: List[str] = None
    property_types: List[str] = None
    
    def __post_init__(self):
        if self.areas is None:
            self.areas = []
        if self.property_types is None:
            self.property_types = ["apartment", "house"]
    
    def to_url_params(self) -> dict:
        """Преобразование фильтров в параметры URL"""
        params = {
            "location": self.city.lower(),
            "rentalPrice_to": str(self.max_price),
            "numBeds_from": str(self.min_bedrooms)
        }
        
        if self.areas:
            # Добавляем районы как отдельные параметры
            params["area"] = ",".join(self.areas)
            
        return params

@dataclass
class BotSettings:
    """Настройки бота для чата"""
    chat_id: str
    city: str = "Dublin"
    max_price: int = 2500
    min_bedrooms: int = 3
    areas: List[str] = None
    is_monitoring: bool = False
    last_check: Optional[datetime] = None
    
    def __post_init__(self):
        if self.areas is None:
            self.areas = []
    
    def get_search_filters(self) -> SearchFilters:
        """Получение объекта фильтров поиска"""
        return SearchFilters(
            city=self.city,
            max_price=self.max_price,
            min_bedrooms=self.min_bedrooms,
            areas=self.areas.copy()
        )
