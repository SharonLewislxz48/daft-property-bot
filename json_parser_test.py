#!/usr/bin/env python3
"""
Улучшенный парсер daft.ie с поддержкой JSON данных
"""

import asyncio
import json
import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DaftJSONParser:
    """Парсер JSON данных с daft.ie"""
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
    
    def extract_json_data(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Извлечение JSON данных из HTML"""
        try:
            # Ищем JSON в <script id="__NEXT_DATA__">
            pattern = r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>'
            match = re.search(pattern, html_content, re.DOTALL)
            
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            
            # Альтернативный поиск JSON данных
            pattern2 = r'"props":\s*{.*?"searchApi":\s*({.*?})\s*,'
            match2 = re.search(pattern2, html_content, re.DOTALL)
            
            if match2:
                logger.info("Найден альтернативный JSON")
                return json.loads(match2.group(1))
                
            logger.warning("JSON данные не найдены")
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка извлечения JSON: {e}")
            return None
    
    def parse_listing(self, listing_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Парсинг одного объявления из JSON"""
        try:
            listing = listing_data.get('listing', {})
            
            # Основные данные
            property_id = str(listing.get('id', ''))
            title = listing.get('title', '')
            price_text = listing.get('price', '')
            bedrooms_text = listing.get('numBedrooms', '')
            property_type = listing.get('propertyType', 'apartment')
            
            # Парсинг цены
            price = self._parse_price(price_text)
            if not price:
                logger.debug(f"Не удалось извлечь цену из: {price_text}")
                return None
            
            # Парсинг количества спален
            bedrooms = self._parse_bedrooms(bedrooms_text)
            
            # URL объявления
            seo_path = listing.get('seoFriendlyPath', '')
            if seo_path:
                property_url = urljoin(self.base_url, seo_path)
            else:
                property_url = f"{self.base_url}/for-rent/{property_id}"
            
            # Адрес
            address = title  # Заголовок обычно содержит адрес
            
            # Изображение
            image_url = None
            media = listing.get('media', {})
            if media and 'images' in media and media['images']:
                first_image = media['images'][0]
                image_url = first_image.get('size720x480') or first_image.get('size72x52')
            
            # Район (извлекаем из адреса)
            area = self._extract_area_from_address(address)
            
            return {
                'id': property_id,
                'title': title[:200],
                'address': address[:200],
                'price': price,
                'bedrooms': bedrooms,
                'bathrooms': None,  # В JSON не всегда есть
                'property_type': property_type.lower(),
                'url': property_url,
                'image_url': image_url,
                'area': area,
                'raw_price': price_text,
                'raw_bedrooms': bedrooms_text
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга объявления: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> Optional[int]:
        """Извлечение цены из текста"""
        try:
            # Убираем "From " и ищем число
            clean_text = price_text.replace("From ", "").replace("€", "").replace(",", "")
            
            # Ищем число
            price_match = re.search(r'(\d+)', clean_text)
            if price_match:
                price = int(price_match.group(1))
                if 500 <= price <= 10000:  # Разумные пределы
                    return price
                    
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _parse_bedrooms(self, bedrooms_text: str) -> int:
        """Извлечение количества спален"""
        try:
            # Ищем первое число в строке
            bed_match = re.search(r'(\d+)', bedrooms_text)
            if bed_match:
                bedrooms = int(bed_match.group(1))
                if 0 <= bedrooms <= 10:
                    return bedrooms
                    
        except (ValueError, AttributeError):
            pass
        
        return 1  # По умолчанию 1 спальня
    
    def _extract_area_from_address(self, address: str) -> Optional[str]:
        """Извлечение района из адреса"""
        try:
            # Ищем Dublin X
            dublin_match = re.search(r'Dublin\s+(\d+[WwEe]?)', address)
            if dublin_match:
                return f"Dublin {dublin_match.group(1)}"
            
            # Co. Dublin
            if "Co. Dublin" in address:
                return "Co. Dublin"
                
        except Exception:
            pass
        return None
    
    def parse_search_results(self, html_content: str, min_bedrooms: int = 3, max_price: int = 2500) -> List[Dict[str, Any]]:
        """Парсинг результатов поиска"""
        properties = []
        
        try:
            # Извлекаем JSON данные
            json_data = self.extract_json_data(html_content)
            if not json_data:
                logger.error("JSON данные не найдены")
                return properties
            
            # Ищем объявления в JSON
            search_api = json_data.get('props', {}).get('pageProps', {}).get('searchApi', {})
            listings = search_api.get('listings', [])
            
            logger.info(f"Найдено объявлений в JSON: {len(listings)}")
            
            for listing_data in listings:
                property_data = self.parse_listing(listing_data)
                if property_data:
                    # Проверяем фильтры
                    if (property_data['price'] <= max_price and 
                        property_data['bedrooms'] >= min_bedrooms):
                        properties.append(property_data)
                        logger.debug(f"Добавлено: {property_data['title']} - €{property_data['price']} - {property_data['bedrooms']} bed")
                    else:
                        logger.debug(f"Отфильтровано: {property_data['title']} - €{property_data['price']} - {property_data['bedrooms']} bed")
            
            logger.info(f"Результат: {len(properties)} подходящих объявлений из {len(listings)}")
            
        except Exception as e:
            logger.error(f"Ошибка парсинга результатов: {e}")
        
        return properties

async def test_json_parser():
    """Тест JSON парсера"""
    print("🧪 Тестирование JSON парсера daft.ie\n")
    
    # Читаем сохраненный HTML
    try:
        with open('/tmp/daft_response.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("❌ Файл /tmp/daft_response.html не найден. Сначала запустите url_test.py")
        return
    
    parser = DaftJSONParser()
    
    # Тест с параметрами: 3+ спален, до €2500
    properties = parser.parse_search_results(html_content, min_bedrooms=3, max_price=2500)
    
    print(f"📊 Результаты:")
    print(f"  Найдено объявлений: {len(properties)}")
    
    if properties:
        print(f"\n📋 Первые 5 объявлений:")
        for i, prop in enumerate(properties[:5], 1):
            print(f"  {i}. {prop['title']}")
            print(f"     💰 €{prop['price']}/месяц")
            print(f"     🛏️ {prop['bedrooms']} спален")
            print(f"     📍 {prop['address']}")
            print(f"     🔗 {prop['url']}")
            if prop['area']:
                print(f"     📍 Район: {prop['area']}")
            print()
    else:
        print("❌ Объявления не найдены")
    
    # Дополнительная диагностика
    json_data = parser.extract_json_data(html_content)
    if json_data:
        search_api = json_data.get('props', {}).get('pageProps', {}).get('searchApi', {})
        total_results = search_api.get('paging', {}).get('totalResults', 0)
        print(f"\n📊 Общая статистика:")
        print(f"  Всего результатов на сайте: {total_results}")
        print(f"  Найдено в JSON: {len(search_api.get('listings', []))}")
        print(f"  Подходящих по фильтрам: {len(properties)}")

if __name__ == "__main__":
    asyncio.run(test_json_parser())
