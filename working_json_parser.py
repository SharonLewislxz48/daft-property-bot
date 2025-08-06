import re
import json
import logging
import aiohttp
import asyncio
from datetime import datetime
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkingDaftParser:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def extract_json_data(self, html_content: str) -> List[Dict[str, Any]]:
        """Извлекает JSON данные из React приложения"""
        try:
            # Поиск script элемента с __NEXT_DATA__
            pattern = r'<script id="__NEXT_DATA__"[^>]*>([^<]+)</script>'
            match = re.search(pattern, html_content)
            
            if not match:
                logger.error("__NEXT_DATA__ script не найден")
                return []
            
            json_str = match.group(1)
            data = json.loads(json_str)
            
            # Извлекаем listings из структуры данных
            listings = data.get('props', {}).get('pageProps', {}).get('listings', [])
            logger.info(f"Найдено объявлений в JSON: {len(listings)}")
            
            # Парсим каждое объявление
            properties = []
            for item in listings:
                listing = item.get('listing', {})
                if not listing:
                    continue
                    
                property_data = self.parse_listing(listing)
                if property_data:
                    properties.append(property_data)
            
            return properties
            
        except Exception as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return []
    
    def parse_listing(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        """Парсит отдельное объявление"""
        try:
            # Основная информация
            property_id = listing.get('id')
            title = listing.get('title', '')
            price = listing.get('price', '')
            bedrooms = listing.get('numBedrooms', '')
            property_type = listing.get('propertyType', '')
            
            # URL для объявления
            seo_path = listing.get('seoFriendlyPath', '')
            url = f"https://www.daft.ie{seo_path}" if seo_path else ""
            
            # Местоположение (извлекаем из координат если есть)
            point = listing.get('point', {})
            coordinates = point.get('coordinates', []) if point else []
            location = title.split(',')[-2:] if ',' in title else [title]
            location_str = ', '.join(location).strip()
            
            # Дата публикации
            publish_date = listing.get('publishDate')
            date_published = None
            if publish_date:
                try:
                    date_published = datetime.fromtimestamp(publish_date / 1000).strftime('%Y-%m-%d')
                except:
                    pass
            
            # Изображения
            media = listing.get('media', {})
            images = media.get('images', [])
            image_urls = []
            for img in images[:3]:  # Берем первые 3 изображения
                if 'size720x480' in img:
                    image_urls.append(img['size720x480'])
            
            # Продавец
            seller = listing.get('seller', {})
            agent_name = seller.get('name', '')
            phone = seller.get('phone', '')
            
            # Энергоэффективность
            ber = listing.get('ber', {})
            energy_rating = ber.get('rating', '') if ber else ''
            
            property_data = {
                'id': property_id,
                'title': title,
                'url': url,
                'price': price,
                'bedrooms': bedrooms,
                'property_type': property_type,
                'location': location_str,
                'date_published': date_published,
                'images': image_urls,
                'agent_name': agent_name,
                'phone': phone,
                'energy_rating': energy_rating,
                'coordinates': coordinates
            }
            
            logger.info(f"Обработано объявление: {title} - {price}")
            return property_data
            
        except Exception as e:
            logger.error(f"Ошибка парсинга объявления: {e}")
            return None
    
    async def search_properties(self, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Поиск недвижимости с заданными параметрами"""
        try:
            # Формируем URL
            base_url = "https://www.daft.ie/property-for-rent"
            
            # Добавляем локацию и тип недвижимости в путь
            location = params.get('location', 'dublin-city')
            property_type = params.get('property_type', 'houses')
            url = f"{base_url}/{location}/{property_type}"
            
            # Добавляем параметры запроса
            query_params = []
            if params.get('max_price'):
                query_params.append(f"rentalPrice_to={params['max_price']}")
            if params.get('min_bedrooms'):
                query_params.append(f"numBeds_from={params['min_bedrooms']}")
            if params.get('page'):
                query_params.append(f"page={params['page']}")
            
            if query_params:
                url += "?" + "&".join(query_params)
            
            logger.info(f"Запрос к URL: {url}")
            
            # Небольшая задержка для избежания блокировки
            await asyncio.sleep(1)
            
            # Заголовки для имитации браузера
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Linux"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"HTTP ошибка {response.status}")
                    return []
                
                html = await response.text()
                logger.info(f"Получено {len(html)} символов HTML")
                
                # Извлекаем и парсим JSON данные
                properties = self.extract_json_data(html)
                
                logger.info(f"Найдено {len(properties)} объявлений")
                return properties
                
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []

async def test_parser():
    """Тестирование парсера"""
    params = {
        'location': 'dublin-city',
        'property_type': 'houses',
        'max_price': '2500',
        'min_bedrooms': '3'
    }
    
    async with WorkingDaftParser() as parser:
        properties = await parser.search_properties(params)
        
        print(f"\n🏠 Найдено объявлений: {len(properties)}")
        
        for i, prop in enumerate(properties, 1):
            print(f"\n{i}. {prop['title']}")
            print(f"   💰 Цена: {prop['price']}")
            print(f"   🛏️ Спальни: {prop['bedrooms']}")
            print(f"   📍 Местоположение: {prop['location']}")
            print(f"   🔗 URL: {prop['url']}")
            if prop['agent_name']:
                print(f"   👤 Агент: {prop['agent_name']}")
            if prop['phone']:
                print(f"   📞 Телефон: {prop['phone']}")

if __name__ == "__main__":
    asyncio.run(test_parser())
