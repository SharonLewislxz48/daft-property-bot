#!/usr/bin/env python3
"""
Продакшн-готовый парсер daft.ie с полной функциональностью:
- Обход всех страниц результатов
- Правильная логика извлечения спален
- Retry логика и обработка ошибок
- Логирование и статистика
- Валидация данных
"""

import asyncio
import re
import json
import datetime
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from playwright.async_api import async_playwright
import time

class ProductionDaftParser:
    """Продакшн-готовый парсер daft.ie"""
    
    def __init__(self, log_level: str = "INFO"):
        self.base_url = "https://www.daft.ie"
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Настройка логирования
        self._setup_logging(log_level)
        
        # Статистика
        self.stats = {
            'total_pages': 0,
            'total_links_found': 0,
            'total_processed': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'retries': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Настройки
        self.max_retries = 3
        self.retry_delay = 2
        self.page_timeout = 30000
        self.property_timeout = 15000
    
    def _setup_logging(self, level: str):
        """Настройка системы логирования"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # Создаем папку для логов
        Path("logs").mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format=log_format,
            handlers=[
                logging.FileHandler(f'logs/daft_parser_{datetime.datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    async def search_all_properties(
        self, 
        min_bedrooms: int = 3, 
        max_price: int = 2500, 
        location: str = "dublin",
        property_type: str = "all",  # "all", "houses", "apartments"
        max_pages: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Полный поиск с обходом всех страниц
        
        Args:
            min_bedrooms: Минимальное количество спален
            max_price: Максимальная цена в евро
            location: Локация для поиска
            property_type: Тип недвижимости ("all", "houses", "apartments")
            max_pages: Максимальное количество страниц для обхода
            
        Returns:
            Список словарей с данными о недвижимости
        """
        self.stats['start_time'] = datetime.datetime.now()
        print(f"🔍 Начинаем поиск: {min_bedrooms}+ спален, до €{max_price}, {location}")
        
        # Формируем правильный URL в зависимости от типа недвижимости
        if location.lower() == 'dublin':
            if property_type == "houses":
                base_search_url = f"{self.base_url}/property-for-rent/dublin-city/houses?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}&pageSize=20"
            elif property_type == "apartments":
                base_search_url = f"{self.base_url}/property-for-rent/dublin-city/apartments?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}&pageSize=20"
            else:  # all
                base_search_url = f"{self.base_url}/property-for-rent/dublin-city?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}&pageSize=20"
        else:
            # Для других городов используем общий формат
            if property_type == "houses":
                base_search_url = f"{self.base_url}/property-for-rent/{location}/houses?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}&pageSize=20"
            elif property_type == "apartments":
                base_search_url = f"{self.base_url}/property-for-rent/{location}/apartments?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}&pageSize=20"
            else:  # all
                base_search_url = f"{self.base_url}/property-for-rent/{location}?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}&pageSize=20"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Собираем все ссылки со всех страниц
                all_property_urls = await self._collect_all_property_urls(page, base_search_url, max_pages)
                self.logger.info(f"🔗 Всего найдено ссылок: {len(all_property_urls)}")
                
                # Парсим каждое объявление
                results = []
                for i, url in enumerate(all_property_urls, 1):
                    self.logger.info(f"📝 Обрабатываем {i}/{len(all_property_urls)}: {self._get_property_id(url)}")
                    
                    property_data = await self._parse_property_with_retry(page, url)
                    if property_data:
                        # Валидируем данные
                        if self._validate_property_data(property_data):
                            results.append(property_data)
                            self.stats['successful_parses'] += 1
                            self._log_property_summary(property_data)
                        else:
                            self.logger.warning(f"❌ Данные не прошли валидацию: {url}")
                            self.stats['failed_parses'] += 1
                    else:
                        self.stats['failed_parses'] += 1
                    
                    self.stats['total_processed'] += 1
                    
                    # Небольшая пауза между запросами
                    await asyncio.sleep(0.5)
                
                self.stats['end_time'] = datetime.datetime.now()
                self._log_final_statistics()
                
                return results
                
            except Exception as e:
                self.logger.error(f"❌ Критическая ошибка поиска: {e}")
                return []
                
            finally:
                await browser.close()
    
    async def _collect_all_property_urls(self, page, base_url: str, max_pages: int) -> List[str]:
        """Собирает ссылки со всех страниц результатов"""
        all_urls = set()
        current_page = 1
        
        while current_page <= max_pages:
            # Формируем URL для текущей страницы
            if current_page == 1:
                page_url = base_url
            else:
                # Добавляем параметр from для пагинации
                separator = "&" if "?" in base_url else "?"
                page_url = f"{base_url}{separator}from={(current_page-1)*20}"
            
            self.logger.info(f"📄 Загружаем страницу {current_page}: {page_url}")
            
            try:
                await page.goto(page_url, wait_until='networkidle', timeout=self.page_timeout)
                await page.wait_for_timeout(2000)
                
                # Проверяем количество результатов на первой странице
                if current_page == 1:
                    total_count = await self._get_results_count(page)
                    self.logger.info(f"📊 Общее количество объявлений: {total_count}")
                
                # Собираем ссылки на текущей странице
                page_urls = await self._collect_property_urls_on_page(page)
                
                if not page_urls:
                    self.logger.info(f"🔚 Больше нет объявлений на странице {current_page}")
                    break
                
                before_count = len(all_urls)
                all_urls.update(page_urls)
                new_urls = len(all_urls) - before_count
                
                self.logger.info(f"✅ Страница {current_page}: найдено {len(page_urls)} ссылок, новых: {new_urls}")
                self.stats['total_pages'] += 1
                
                # Если на странице меньше 20 объявлений, это последняя страница
                if len(page_urls) < 20:
                    self.logger.info(f"🔚 Последняя страница: {current_page}")
                    break
                
                current_page += 1
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка загрузки страницы {current_page}: {e}")
                break
        
        self.stats['total_links_found'] = len(all_urls)
        return list(all_urls)
    
    async def _collect_property_urls_on_page(self, page) -> List[str]:
        """Собирает ссылки на объявления с одной страницы"""
        try:
            # Ждем загрузки списка объявлений
            await page.wait_for_selector('a[href*="/for-rent/"]', timeout=10000)
            
            property_links = await page.query_selector_all('a[href*="/for-rent/"]')
            
            urls = []
            for link in property_links:
                href = await link.get_attribute('href')
                if href and '/for-rent/' in href:
                    # Исключаем ссылки на страницы поиска
                    if 'property-for-rent' not in href:
                        if href.startswith('/'):
                            href = self.base_url + href
                        urls.append(href)
            
            # Убираем дубликаты
            unique_urls = list(set(urls))
            return unique_urls
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сбора ссылок: {e}")
            return []
    
    async def _get_results_count(self, page) -> int:
        """Получает общее количество результатов поиска"""
        try:
            # Ищем элемент с количеством результатов
            selectors = [
                'h1',
                '[data-testid="results-count"]',
                '.SearchHeader__count'
            ]
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    text = await element.text_content()
                    if text:
                        count_match = re.search(r'(\d+)', text)
                        if count_match:
                            return int(count_match.group(1))
                except:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось получить количество результатов: {e}")
        
        return 0
    
    def _get_property_id(self, url: str) -> str:
        """Извлекает ID объявления из URL"""
        try:
            # Ищем ID в конце URL
            id_match = re.search(r'/(\d+)/?$', url)
            if id_match:
                return id_match.group(1)
            
            # Альтернативный способ - берем последнюю часть URL
            return url.split('/')[-1] if url.split('/')[-1] else url.split('/')[-2]
        except:
            return "unknown"
    
    async def _parse_property_with_retry(self, page, url: str) -> Optional[Dict[str, Any]]:
        """Парсит объявление с логикой повторных попыток"""
        for attempt in range(self.max_retries + 1):
            try:
                result = await self._parse_property(page, url)
                if result:
                    return result
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Попытка {attempt + 1} неудачна для {url}: {e}")
                
                if attempt < self.max_retries:
                    self.stats['retries'] += 1
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error(f"❌ Все попытки исчерпаны для {url}")
        
        return None
    
    async def _parse_property(self, page, url: str) -> Optional[Dict[str, Any]]:
        """Парсит отдельную страницу объявления"""
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=self.property_timeout)
            await page.wait_for_timeout(1500)
            
            # Получаем содержимое страницы
            page_content = await page.content()
            
            # Извлекаем данные
            property_data = {
                'url': url,
                'property_id': self._get_property_id(url),
                'title': await self._extract_title(page),
                'price': await self._extract_price(page, page_content),
                'bedrooms': await self._extract_bedrooms_improved(page, page_content),
                'bathrooms': await self._extract_bathrooms(page, page_content),
                'property_type': self._extract_property_type(page_content),
                'location': await self._extract_location(page),
                'description': self._extract_description(page_content),
                'features': await self._extract_features(page),
                'ber_rating': self._extract_ber_rating(page_content),
                'posted_date': self._extract_posted_date(page_content),
                'parsed_at': datetime.datetime.now().isoformat()
            }
            
            return property_data
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка парсинга {url}: {e}")
            raise
    
    async def _extract_title(self, page) -> Optional[str]:
        """Извлекает заголовок объявления"""
        selectors = [
            'h1',
            '[data-testid="title"]',
            '.TitleBlock__title'
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    title = await element.text_content()
                    if title and len(title.strip()) > 5:
                        return title.strip()
            except:
                continue
        
        return None
    
    async def _extract_price(self, page, page_content: str) -> Optional[int]:
        """Извлекает цену с улучшенной логикой"""
        # Пробуем селекторы на странице
        price_selectors = [
            '[data-testid="price"]',
            '.TitleBlock__price',
            '.PropertyMainInfo__price',
            'span:has-text("€")'
        ]
        
        for selector in price_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    price_text = await element.text_content()
                    if price_text:
                        # Ищем цену в формате €1,234 или €1234
                        price_match = re.search(r'€\s*([\d,]+)', price_text)
                        if price_match:
                            price_str = price_match.group(1).replace(',', '')
                            price = int(price_str)
                            # Проверяем разумность цены (от €100 до €10000)
                            if 100 <= price <= 10000:
                                return price
            except:
                continue
        
        # Ищем в JSON данных страницы
        try:
            json_patterns = [
                r'"price":\s*(\d+)',
                r'"rentalPrice":\s*(\d+)',
                r'"monthlyRent":\s*(\d+)'
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, page_content)
                if match:
                    price = int(match.group(1))
                    if 100 <= price <= 10000:
                        return price
        except:
            pass
        
        return None
    
    async def _extract_bedrooms_improved(self, page, page_content: str) -> Optional[int]:
        """Улучшенная логика извлечения количества спален"""
        
        # 1. Ищем в основных селекторах
        bed_selectors = [
            '[data-testid="bed-bath"]',
            '[data-testid="bedrooms"]', 
            '.PropertyDetailsList__item:has-text("bed")',
            '.TitleBlock__meta'
        ]
        
        for selector in bed_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        # Ищем "X bed" или "X bedroom"
                        bed_match = re.search(r'(\d+)\s*(?:bed|bedroom)', text.lower())
                        if bed_match:
                            bedrooms = int(bed_match.group(1))
                            # Проверяем разумность (от 1 до 10 спален)
                            if 1 <= bedrooms <= 10:
                                return bedrooms
            except:
                continue
        
        # 2. Ищем в JSON структурированных данных
        try:
            # Ищем точные поля для спален
            json_patterns = [
                r'"numberOfBedrooms":\s*(\d+)',
                r'"bedrooms":\s*(\d+)',
                r'"numBedrooms":\s*(\d+)',
                r'"bed":\s*(\d+)'
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, page_content)
                if match:
                    bedrooms = int(match.group(1))
                    if 1 <= bedrooms <= 10:
                        return bedrooms
        except:
            pass
        
        # 3. Ищем в тексте описания (осторожно, только если очень явно)
        try:
            # Ищем очень конкретные фразы
            description_patterns = [
                r'(\d+)\s*bedroom\s+(?:apartment|house|property)',
                r'this\s+(\d+)\s*bed',
                r'(\d+)\s*bed\s+(?:apartment|house|property)'
            ]
            
            for pattern in description_patterns:
                match = re.search(pattern, page_content.lower())
                if match:
                    bedrooms = int(match.group(1))
                    if 1 <= bedrooms <= 6:  # Более строгая проверка для текста
                        return bedrooms
        except:
            pass
        
        # 4. Последний шанс - ищем в мета-данных
        try:
            meta_match = re.search(r'content="(\d+)\s*bedroom', page_content, re.IGNORECASE)
            if meta_match:
                bedrooms = int(meta_match.group(1))
                if 1 <= bedrooms <= 10:
                    return bedrooms
        except:
            pass
        
        return None
    
    async def _extract_bathrooms(self, page, page_content: str) -> Optional[int]:
        """Извлекает количество ванных комнат"""
        # Ищем в селекторах
        bath_selectors = [
            '[data-testid="bed-bath"]',
            '[data-testid="bathrooms"]'
        ]
        
        for selector in bath_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        bath_match = re.search(r'(\d+)\s*(?:bath|bathroom)', text.lower())
                        if bath_match:
                            bathrooms = int(bath_match.group(1))
                            if 1 <= bathrooms <= 5:
                                return bathrooms
            except:
                continue
        
        # Ищем в JSON
        try:
            bath_patterns = [
                r'"numberOfBathrooms":\s*(\d+)',
                r'"bathrooms":\s*(\d+)',
                r'"bath":\s*(\d+)'
            ]
            
            for pattern in bath_patterns:
                match = re.search(pattern, page_content)
                if match:
                    bathrooms = int(match.group(1))
                    if 1 <= bathrooms <= 5:
                        return bathrooms
        except:
            pass
        
        return None
    
    async def _extract_location(self, page) -> Optional[str]:
        """Извлекает местоположение"""
        try:
            # Ищем в заголовке
            title_element = await page.query_selector('h1')
            if title_element:
                title = await title_element.text_content()
                if title:
                    # Ищем Dublin с номером или названием
                    location_patterns = [
                        r'Dublin\s+\d+',
                        r'Dublin\s+\w+',
                        r'Co\.\s*Dublin'
                    ]
                    
                    for pattern in location_patterns:
                        match = re.search(pattern, title, re.IGNORECASE)
                        if match:
                            return match.group()
        except:
            pass
        
        return None
    
    def _extract_property_type(self, page_content: str) -> Optional[str]:
        """Извлекает тип недвижимости"""
        try:
            # Ищем в JSON данных
            type_patterns = [
                r'"propertyType":\s*"([^"]*)"',
                r'"@type":\s*"([^"]*)"',
                r'"category":\s*"([^"]*)"'
            ]
            
            for pattern in type_patterns:
                match = re.search(pattern, page_content)
                if match:
                    prop_type = match.group(1)
                    if prop_type and prop_type.lower() not in ['breadcrumblist', 'webpage']:
                        return prop_type
            
            # Ищем ключевые слова в тексте
            if 'apartment' in page_content.lower():
                return 'Apartment'
            elif 'house' in page_content.lower():
                return 'House'
            elif 'studio' in page_content.lower():
                return 'Studio'
                
        except:
            pass
        
        return None
    
    def _extract_description(self, page_content: str, max_length: int = 300) -> Optional[str]:
        """Извлекает описание объявления"""
        try:
            # Ищем в JSON данных
            desc_patterns = [
                r'"description":\s*"([^"]*)"',
                r'"propertyDescription":\s*"([^"]*)"'
            ]
            
            for pattern in desc_patterns:
                match = re.search(pattern, page_content)
                if match:
                    description = match.group(1)
                    if description and len(description) > 20:
                        if len(description) > max_length:
                            description = description[:max_length] + "..."
                        return description
        except:
            pass
        
        return None
    
    async def _extract_features(self, page) -> List[str]:
        """Извлекает список особенностей недвижимости"""
        features = []
        
        try:
            # Ищем списки особенностей
            feature_selectors = [
                '.PropertyDetailsList__item',
                '.FeaturesList__item',
                '[data-testid="features"] li'
            ]
            
            for selector in feature_selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.text_content()
                    if text and len(text.strip()) > 2:
                        features.append(text.strip())
                        
                if features:  # Если нашли хотя бы одну особенность, останавливаемся
                    break
                    
        except:
            pass
        
        return features[:10]  # Ограничиваем количество особенностей
    
    def _extract_ber_rating(self, page_content: str) -> Optional[str]:
        """Извлекает BER рейтинг энергоэффективности"""
        try:
            ber_patterns = [
                r'"ber":\s*"([^"]*)"',
                r'"berRating":\s*"([^"]*)"',
                r'BER[:\s]+([A-G]\d*)',
                r'Energy Rating[:\s]+([A-G]\d*)'
            ]
            
            for pattern in ber_patterns:
                match = re.search(pattern, page_content, re.IGNORECASE)
                if match:
                    ber = match.group(1).strip()
                    if ber and len(ber) <= 3:
                        return ber
        except:
            pass
        
        return None
    
    def _extract_posted_date(self, page_content: str) -> Optional[str]:
        """Извлекает дату публикации"""
        try:
            date_patterns = [
                r'"datePublished":\s*"([^"]*)"',
                r'"postedDate":\s*"([^"]*)"',
                r'"listedDate":\s*"([^"]*)"'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, page_content)
                if match:
                    return match.group(1)
        except:
            pass
        
        return None
    
    def _validate_property_data(self, data: Dict[str, Any]) -> bool:
        """Валидирует данные объявления"""
        # Проверяем обязательные поля
        if not data.get('title') and not data.get('price'):
            return False
        
        # Проверяем разумность цены
        price = data.get('price')
        if price and (price < 100 or price > 10000):
            return False
        
        # Проверяем разумность количества спален
        bedrooms = data.get('bedrooms')
        if bedrooms and (bedrooms < 1 or bedrooms > 10):
            return False
        
        return True
    
    def _log_property_summary(self, prop: Dict[str, Any]):
        """Логирует краткую информацию об объявлении"""
        title = prop.get('title', 'Без названия')[:40]
        price = f"€{prop['price']}" if prop.get('price') else 'Цена не указана'
        bedrooms = f"{prop['bedrooms']} спален" if prop.get('bedrooms') else 'Спальни не указаны'
        location = prop.get('location', 'Локация не указана')
        
        self.logger.info(f"✅ {title} | {price} | {bedrooms} | {location}")
    
    def _log_final_statistics(self):
        """Логирует финальную статистику"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        self.logger.info("=" * 60)
        self.logger.info("📊 ФИНАЛЬНАЯ СТАТИСТИКА")
        self.logger.info("=" * 60)
        self.logger.info(f"⏱️  Время выполнения: {duration:.1f} секунд")
        self.logger.info(f"📄 Обработано страниц: {self.stats['total_pages']}")
        self.logger.info(f"🔗 Найдено ссылок: {self.stats['total_links_found']}")
        self.logger.info(f"📝 Обработано объявлений: {self.stats['total_processed']}")
        self.logger.info(f"✅ Успешно: {self.stats['successful_parses']}")
        self.logger.info(f"❌ Неудачно: {self.stats['failed_parses']}")
        self.logger.info(f"🔄 Повторных попыток: {self.stats['retries']}")
        
        if self.stats['total_processed'] > 0:
            success_rate = (self.stats['successful_parses'] / self.stats['total_processed']) * 100
            self.logger.info(f"📈 Процент успеха: {success_rate:.1f}%")
    
    def save_results(self, results: List[Dict[str, Any]], search_params: Dict[str, Any]) -> str:
        """Сохраняет результаты в JSON файл"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.results_dir / f"daft_results_{timestamp}.json"
        
        # Конвертируем datetime объекты в строки для JSON
        stats_copy = self.stats.copy()
        if stats_copy['start_time']:
            stats_copy['start_time'] = stats_copy['start_time'].isoformat()
        if stats_copy['end_time']:
            stats_copy['end_time'] = stats_copy['end_time'].isoformat()
        
        output_data = {
            'search_params': search_params,
            'statistics': stats_copy,
            'results_count': len(results),
            'results': results,
            'generated_at': datetime.datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"💾 Результаты сохранены в {filename}")
        return str(filename)
    
    def format_results_summary(self, results: List[Dict[str, Any]]) -> str:
        """Форматирует краткую сводку результатов"""
        if not results:
            return "❌ Объявления не найдены"
        
        # Статистика по ценам
        prices = [r['price'] for r in results if r.get('price')]
        bedrooms = [r['bedrooms'] for r in results if r.get('bedrooms')]
        
        summary = [
            f"🏠 НАЙДЕНО {len(results)} ОБЪЯВЛЕНИЙ",
            "",
            "💰 ЦЕНЫ:",
        ]
        
        if prices:
            summary.extend([
                f"   Средняя: €{sum(prices) / len(prices):.0f}",
                f"   Диапазон: €{min(prices)} - €{max(prices)}"
            ])
        
        if bedrooms:
            summary.extend([
                "",
                "🛏️ СПАЛЬНИ:",
                f"   Среднее: {sum(bedrooms) / len(bedrooms):.1f}",
                f"   Диапазон: {min(bedrooms)} - {max(bedrooms)}"
            ])
        
        # Топ-5 объявлений
        summary.extend([
            "",
            "🔝 ТОП-5 ОБЪЯВЛЕНИЙ:",
            ""
        ])
        
        for i, prop in enumerate(results[:5], 1):
            title = prop.get('title', 'Без названия')[:50]
            price = f"€{prop['price']}" if prop.get('price') else 'Цена не указана'
            beds = f"{prop['bedrooms']} спален" if prop.get('bedrooms') else 'Спальни не указаны'
            
            summary.append(f"{i}. {title}")
            summary.append(f"   💰 {price} | 🛏️ {beds}")
            summary.append("")
        
        return "\n".join(summary)

async def main():
    """Основная функция для демонстрации"""
    print("🚀 PRODUCTION DAFT.IE PARSER - ПОЛНАЯ ВЕРСИЯ")
    print("=" * 60)
    
    parser = ProductionDaftParser(log_level="INFO")
    
    # Параметры поиска
    search_params = {
        'min_bedrooms': 3,
        'max_price': 2500,
        'location': 'dublin',
        'property_type': 'houses',  # Используем houses как в примере пользователя
        'max_pages': 10  # Увеличиваем для полного обхода
    }
    
    print("🎯 ПАРАМЕТРЫ ПОИСКА:")
    for key, value in search_params.items():
        print(f"   {key}: {value}")
    print()
    
    # Выполняем поиск
    results = await parser.search_all_properties(**search_params)
    
    # Выводим результаты
    print("\n" + "=" * 60)
    print("📋 РЕЗУЛЬТАТЫ")
    print("=" * 60)
    
    summary = parser.format_results_summary(results)
    print(summary)
    
    # Сохраняем результаты
    filename = parser.save_results(results, search_params)
    print(f"\n💾 Подробные результаты сохранены в {filename}")

if __name__ == "__main__":
    asyncio.run(main())
