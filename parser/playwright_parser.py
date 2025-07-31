import asyncio
import logging
import re
import random
from typing import List, Optional, Dict, Set
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
            params["from"] = str((page - 1) * 20)
        
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
        """Поиск объявлений с фильтрами"""
        properties = []
        seen_ids: Set[str] = set()
        
        # Статистика
        total_found = 0
        successful_parses = 0
        failed_parses = 0
        
        logger.info(f"Starting search with filters: city={filters.city}, max_price={filters.max_price}, min_bedrooms={filters.min_bedrooms}, areas={filters.areas}")
        
        for page in range(1, max_pages + 1):
            try:
                url = self._build_search_url(filters, page)
                logger.info(f"Processing page {page}: {url}")
                
                html_content = await self._get_page_content(url)
                
                if not html_content:
                    logger.warning(f"No content received for page {page}")
                    continue
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Улучшенный поиск элементов объявлений
                property_links = []
                
                # Ищем все ссылки на объявления
                all_links = soup.find_all("a", href=True)
                for link in all_links:
                    href = link.get("href")
                    if href and ("/for-rent/" in href or "/property-for-rent/" in href):
                        # Проверяем, что это не навигационная ссылка
                        if not any(nav in href for nav in ["/page/", "/search/", "?from=", "#"]):
                            property_links.append(link)
                
                logger.info(f"Found {len(property_links)} property links on page {page}")
                total_found += len(property_links)
                
                if len(property_links) == 0:
                    logger.info(f"No properties found on page {page}, stopping pagination")
                    break
                
                # Парсим каждое объявление
                page_properties = []
                for link in property_links:
                    try:
                        # Получаем контейнер с информацией об объявлении
                        container = link
                        # Поднимаемся до контейнера с полной информацией
                        for _ in range(5):
                            parent = container.find_parent()
                            if parent and (parent.name in ['div', 'article', 'li'] or 
                                         'property' in parent.get('class', []) if parent.get('class') else False):
                                container = parent
                            else:
                                break
                        
                        property_obj = self._parse_property_from_element(str(container))
                        if property_obj and property_obj.id not in seen_ids:
                            # Проверяем фильтры
                            if self._matches_filters(property_obj, filters):
                                page_properties.append(property_obj)
                                seen_ids.add(property_obj.id)
                                successful_parses += 1
                            else:
                                logger.debug(f"Property {property_obj.title} filtered out")
                        elif property_obj:
                            logger.debug(f"Duplicate property: {property_obj.id}")
                        else:
                            failed_parses += 1
                            
                    except Exception as e:
                        logger.debug(f"Error parsing individual property: {e}")
                        failed_parses += 1
                        continue
                
                properties.extend(page_properties)
                logger.info(f"Page {page}: {len(page_properties)} valid properties found, {len(page_properties)} added")
                
                # Если на странице мало объявлений, возможно это последняя страница
                if len(property_links) < 10:
                    logger.info(f"Few properties on page {page}, likely last page")
                    break
                
                # Задержка между страницами
                await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error processing page {page}: {e}")
                failed_parses += 1
                continue
        
        # Финальная статистика
        success_rate = (successful_parses / total_found * 100) if total_found > 0 else 0
        logger.info(f"Search completed:")
        logger.info(f"  Total property links found: {total_found}")
        logger.info(f"  Successfully parsed: {successful_parses}")
        logger.info(f"  Failed to parse: {failed_parses}")
        logger.info(f"  Success rate: {success_rate:.1f}%")
        logger.info(f"  Unique properties returned: {len(properties)}")
        
        return properties
    
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
