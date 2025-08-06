import asyncio
import logging
import re
import json
import aiohttp
import random
from typing import List, Optional, Dict, Set, Any
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode

from .models import Property, SearchFilters
from config.settings import settings

logger = logging.getLogger(__name__)

class PlaywrightDaftParser:
    """Улучшенный парсер для сайта daft.ie с использованием Playwright"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.base_url = "https://www.daft.ie"
        self.search_url = settings.SEARCH_URL if hasattr(settings, 'SEARCH_URL') else self.base_url
        
        # Статистика парсинга
        self.stats = {
            'total_pages_processed': 0,
            'total_links_found': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'retries': 0
        }
        
        # Настройки
        self.max_retries = 3
        self.retry_delay = 2
        self.page_timeout = 30000
        self.property_timeout = 15000
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        
        # Запускаем браузер в headless режиме с улучшенными настройками против блокировки
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-default-apps',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-blink-features=AutomationControlled',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        
        # Создаем новую страницу с реалистичным user agent и настройками
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        self.page = await self.context.new_page()
        
        # Скрываем автоматизацию
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.page:
            await self.page.close()
        if hasattr(self, 'context'):
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
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
                    
                property_data = self.parse_json_listing(listing)
                if property_data:
                    properties.append(property_data)
            
            return properties
            
        except Exception as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return []
    
    def parse_json_listing(self, listing: Dict[str, Any]) -> Optional[Property]:
        """Парсит отдельное объявление из JSON"""
        try:
            # Основная информация
            property_id = str(listing.get('id', ''))
            title = listing.get('title', '')
            price = listing.get('price', '')
            bedrooms_str = listing.get('numBedrooms', '')
            property_type = listing.get('propertyType', '')
            
            # URL для объявления
            seo_path = listing.get('seoFriendlyPath', '')
            url = f"https://www.daft.ie{seo_path}" if seo_path else ""
            
            # Местоположение (извлекаем из заголовка)
            location_parts = title.split(',')
            if len(location_parts) >= 2:
                location = ', '.join(location_parts[-2:]).strip()
            else:
                location = title
            
            # Дата публикации
            publish_date = listing.get('publishDate')
            date_published = None
            if publish_date:
                try:
                    date_published = datetime.fromtimestamp(publish_date / 1000)
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
            
            # Парсим количество спален
            bedrooms = self._parse_bedrooms_from_json(bedrooms_str)
            
            # Парсим цену
            monthly_rent = self._parse_price(price)
            
            # Создаем объект Property
            property_obj = Property(
                id=property_id,
                title=title,
                address=location,
                price=monthly_rent,  # Исправлено: используем price вместо monthly_rent
                bedrooms=bedrooms,
                bathrooms=None,  # Пока не извлекаем из JSON
                property_type=property_type,
                url=url,
                image_url=image_urls[0] if image_urls else None,  # Исправлено: используем image_url вместо images
                description=None,
                area=self._extract_area_from_address(title),
                posted_date=date_published  # Исправлено: используем posted_date вместо date_published
            )
            
            logger.debug(f"Создано объявление: {title} - {price}")
            return property_obj
            
        except Exception as e:
            logger.error(f"Ошибка парсинга объявления из JSON: {e}")
            return None
    
    def _parse_bedrooms_from_json(self, bedrooms_str: str) -> int:
        """Парсит количество спален из JSON строки"""
        try:
            # Ищем числа в строке типа "1, 2, 3 & 5 bed" или "3 Bed"
            numbers = re.findall(r'\d+', bedrooms_str)
            if numbers:
                # Берем первое число как основное количество спален
                return int(numbers[0])
        except (ValueError, AttributeError):
            pass
        return 1  # По умолчанию
    
    async def search_properties_json(self, filters: SearchFilters, max_pages: int = 5) -> List[Property]:
        """Поиск объявлений с использованием JSON API (новый метод)"""
        properties = []
        seen_ids: Set[str] = set()
        
        logger.info(f"Starting JSON search with filters: city={filters.city}, max_price={filters.max_price}, min_bedrooms={filters.min_bedrooms}")
        
        # Создаем HTTP session для requests
        async with aiohttp.ClientSession() as session:
            for page in range(1, max_pages + 1):
                try:
                    url = self._build_search_url(filters, page)
                    logger.info(f"Processing page {page}: {url}")
                    
                    # Делаем HTTP запрос с реалистичными заголовками
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
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
                    
                    # Небольшая задержка
                    await asyncio.sleep(1)
                    
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                            logger.error(f"HTTP ошибка {response.status} для страницы {page}")
                            continue
                        
                        html_content = await response.text()
                        logger.info(f"Получено {len(html_content)} символов HTML для страницы {page}")
                        
                        # Извлекаем и парсим JSON данные
                        page_properties = self.extract_json_data(html_content)
                        
                        if not page_properties:
                            logger.info(f"Нет объявлений на странице {page}, останавливаем пагинацию")
                            break
                        
                        # Фильтруем дубликаты
                        new_properties = []
                        for prop in page_properties:
                            if prop and prop.id not in seen_ids:
                                seen_ids.add(prop.id)
                                new_properties.append(prop)
                        
                        properties.extend(new_properties)
                        logger.info(f"Добавлено {len(new_properties)} новых объявлений со страницы {page}")
                        
                        # Обновляем статистику
                        self.stats['total_pages_processed'] += 1
                        self.stats['successful_parses'] += len(new_properties)
                        
                except Exception as e:
                    logger.error(f"Ошибка обработки страницы {page}: {e}")
                    continue
        
        logger.info(f"JSON поиск завершен. Найдено {len(properties)} уникальных объявлений")
        return properties
    
    def _build_search_url(self, filters: SearchFilters, page: int = 1) -> str:
        """Построение URL для поиска с фильтрами"""
        # Используем корректную структуру URL для daft.ie
        city_normalized = filters.city.lower().replace(" ", "-")
        if "dublin" in city_normalized:
            # Формат: /dublin-city/houses или /dublin-city/apartments
            base_search_url = f"{self.search_url}/dublin-city/houses"
        else:
            base_search_url = f"{self.search_url}/{city_normalized}/houses"
        
        # Параметры запроса с правильными названиями
        params = {
            "rentalPrice_to": str(filters.max_price),
            "numBeds_from": str(filters.min_bedrooms),
            "pageSize": "20",  # Важный параметр для получения всех результатов
        }
        
        # Добавляем пагинацию только если не первая страница
        if page > 1:
            params["page"] = str(page)
        
        # Добавляем районы если указаны
        if filters.areas:
            # Для Dublin районы указываются как dublin-1, dublin-2 etc
            area_params = []
            for area in filters.areas:
                if area.lower().startswith("dublin"):
                    # Dublin 1 -> dublin-1
                    area_num = area.lower().replace("dublin ", "")
                    area_params.append(f"dublin-{area_num}")
                else:
                    area_params.append(area.lower().replace(" ", "-"))
            
            if area_params:
                params["area"] = ",".join(area_params)
        
        url = f"{base_search_url}?{urlencode(params)}"
        logger.debug(f"Built search URL: {url}")
        return url
    
    async def _get_page_content(self, url: str) -> Optional[str]:
        """Получение содержимого страницы с улучшенной обработкой ошибок"""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Navigating to: {url} (attempt {attempt + 1})")
                
                # Добавляем случайную задержку для имитации человеческого поведения
                if attempt > 0:
                    await asyncio.sleep(self.retry_delay + random.uniform(1, 3))
                
                # Переходим на страницу
                response = await self.page.goto(
                    url, 
                    wait_until='networkidle', 
                    timeout=self.page_timeout
                )
                
                if response and response.status == 200:
                    # Ждем загрузки контента
                    await self.page.wait_for_timeout(3000)
                    
                    # Получаем HTML
                    content = await self.page.content()
                    logger.debug(f"Successfully loaded page: {len(content)} characters")
                    return content
                elif response and response.status == 403:
                    logger.warning(f"403 Forbidden for {url}, attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        # Увеличиваем задержку при 403
                        await asyncio.sleep(5 + attempt * 2)
                        continue
                else:
                    logger.warning(f"Failed to load {url}, status: {response.status if response else 'None'}")
                    
            except Exception as e:
                logger.error(f"Error loading page {url} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                    
        logger.error(f"Failed to load {url} after {self.max_retries} attempts")
        return None
    
    def _parse_price(self, price_text: str) -> Optional[int]:
        """Извлечение цены из текста"""
        try:
            # Ищем число с символом €
            price_match = re.search(r'€([\d,]+)', price_text.replace(" ", ""))
            if price_match:
                price_str = price_match.group(1).replace(",", "")
                return int(price_str)
        except (ValueError, AttributeError):
            pass
        
        logger.debug(f"Could not parse price from: {price_text}")
        return None
    
    def _parse_bedrooms(self, bedrooms_text: str) -> int:
        """Извлечение количества спален с улучшенной валидацией"""
        try:
            # Ищем "Studio" или число + "bed"
            if "studio" in bedrooms_text.lower():
                return 0
            
            # Ищем различные варианты записи количества спален
            bed_patterns = [
                r'(\d+)\s*bed',           # "3 bed", "3bed"
                r'(\d+)\s*-?\s*bed',      # "3-bed"
                r'(\d+)\s*br\b',          # "3 br", "3br"
                r'(\d+)\s*bedroom',       # "3 bedroom"
                r'bed\s*(\d+)',           # "bed 3"
                r'(\d+)\s*b\b',           # "3 b" (осторожно с этим паттерном)
            ]
            
            for pattern in bed_patterns:
                bed_match = re.search(pattern, bedrooms_text.lower())
                if bed_match:
                    bedrooms = int(bed_match.group(1))
                    # Валидация: реалистичное количество спален (1-10)
                    if 1 <= bedrooms <= 10:
                        return bedrooms
                    elif bedrooms == 0:
                        return 0  # studio
                    else:
                        logger.debug(f"Unrealistic bedroom count {bedrooms}, skipping")
                        continue
                
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error parsing bedrooms: {e}")
            
        logger.debug(f"Could not parse bedrooms from: {bedrooms_text}")
        return 1  # Возвращаем 1 по умолчанию вместо 0
    
    def _parse_bathrooms(self, bathrooms_text: str) -> Optional[int]:
        """Извлечение количества ванных"""
        try:
            bath_match = re.search(r'(\d+)\s*bath', bathrooms_text.lower())
            if bath_match:
                return int(bath_match.group(1))
        except (ValueError, AttributeError):
            pass
        return None
    
    def _extract_area_from_address(self, address: str) -> Optional[str]:
        """Извлечение района из адреса"""
        try:
            # Ищем Dublin X в адресе
            dublin_match = re.search(r'Dublin\s+(\d+[WwEe]?)', address)
            if dublin_match:
                return f"Dublin {dublin_match.group(1)}"
            
            # Ищем Co. Dublin
            if "Co. Dublin" in address:
                return "Co. Dublin"
                
        except Exception:
            pass
        return None
    
    def _parse_property_from_element(self, element_html: str) -> Optional[Property]:
        """Парсинг объявления из HTML элемента с улучшенной логикой"""
        try:
            soup = BeautifulSoup(element_html, 'html.parser')
            
            # Ищем ссылку на объявление
            link_element = soup.find("a", href=True)
            if not link_element:
                return None
            
            property_url = link_element.get("href")
            if not property_url or not any(pattern in property_url for pattern in ["/for-rent/", "/property-for-rent/"]):
                return None
            
            # Генерируем ID из URL (более надежно)
            url_parts = property_url.split("/")
            property_id = None
            for part in reversed(url_parts):
                if part and part != "for-rent" and not part.startswith("?"):
                    property_id = part
                    break
            
            if not property_id:
                property_id = str(hash(property_url))[:10]
            
            # Полный URL
            if property_url.startswith("http"):
                full_url = property_url
            else:
                full_url = urljoin(self.base_url, property_url)
            
            # Извлекаем данные из текста элемента
            element_text = soup.get_text()
            
            # Заголовок - улучшенное извлечение
            title = None
            title_selectors = ["h1", "h2", "h3", "h4", "[data-testid*='title']", ".title", ".property-title"]
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element and title_element.get_text(strip=True):
                    title = title_element.get_text(strip=True)
                    break
            
            if not title:
                # Пробуем извлечь заголовок из текста ссылки
                title = link_element.get_text(strip=True)[:100]
            
            if not title or len(title) < 5:
                title = "Property"
            
            # Адрес - улучшенное извлечение
            address = "Dublin"
            address_patterns = [
                r'([^,\n]*Dublin[^,\n]*(?:\d+[WwEe]?)?[^,\n]*)',
                r'([A-Z][a-z]+ \d+[WwEe]?, Dublin[^,\n]*)',
                r'([A-Z][a-z]+, Dublin[^,\n]*)',
            ]
            
            for pattern in address_patterns:
                address_match = re.search(pattern, element_text)
                if address_match:
                    candidate_address = address_match.group(1).strip()
                    if len(candidate_address) > len(address):
                        address = candidate_address
                    break
            
            # Цена - улучшенное извлечение
            price = None
            price_patterns = [
                r'€([\d,]+)\s*(?:per|/)?(?:\s*month)?',
                r'([\d,]+)\s*€\s*(?:per|/)?(?:\s*month)?',
                r'€\s*([\d,]+)',
                r'Price:\s*€([\d,]+)',
            ]
            
            for pattern in price_patterns:
                price_matches = re.findall(pattern, element_text, re.IGNORECASE)
                for price_text in price_matches:
                    parsed_price = self._parse_price(f"€{price_text}")
                    if parsed_price and 500 <= parsed_price <= 10000:  # Разумные пределы
                        price = parsed_price
                        break
                if price:
                    break
            
            if not price:
                logger.debug(f"No valid price found for property: {title}")
                return None
            
            # Количество спален - используем улучшенный метод
            bedrooms = self._parse_bedrooms(element_text)
            
            # Количество ванных
            bathrooms = self._parse_bathrooms(element_text)
            
            # Тип недвижимости - улучшенное определение
            property_type = "apartment"  # по умолчанию
            type_keywords = {
                "house": ["house", "townhouse", "terrace", "detached", "semi-detached"],
                "apartment": ["apartment", "flat", "penthouse"],
                "studio": ["studio"],
                "duplex": ["duplex"],
            }
            
            element_text_lower = element_text.lower()
            for prop_type, keywords in type_keywords.items():
                if any(keyword in element_text_lower for keyword in keywords):
                    property_type = prop_type
                    break
            
            # Изображение - улучшенное извлечение
            image_url = None
            img_selectors = ["img[src*='daft']", "img[data-src]", "img[src]", "[style*='background-image']"]
            for selector in img_selectors:
                img_element = soup.select_one(selector)
                if img_element:
                    src = img_element.get("src") or img_element.get("data-src")
                    if src:
                        if src.startswith("http"):
                            image_url = src
                        elif src.startswith("/"):
                            image_url = urljoin(self.base_url, src)
                        break
            
            # Район
            area = self._extract_area_from_address(address)
            
            property_obj = Property(
                id=property_id,
                title=title[:200],
                address=address[:200],
                price=price,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                property_type=property_type,
                url=full_url,
                image_url=image_url,
                description=None,
                area=area,
                posted_date=datetime.now()
            )
            
            logger.debug(f"Parsed property: {property_obj.title} - {property_obj.format_price()} - {property_obj.bedrooms} bed")
            return property_obj
            
        except Exception as e:
            logger.error(f"Error parsing property element: {e}")
            return None
    
    async def search_properties(self, filters: SearchFilters, max_pages: int = 5) -> List[Property]:
        """Поиск объявлений с фильтрами (обновленный метод с JSON парсингом)"""
        logger.info(f"Используем JSON подход для парсинга")
        return await self.search_properties_json(filters, max_pages)
        
        # Старый код поиска объявлений удален - теперь используется JSON подход
    
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
