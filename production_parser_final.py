#!/usr/bin/env python3
"""
Финальный продакшн парсер daft.ie с улучшенной обработкой
"""

import asyncio
import re
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
import json
import datetime

class AdvancedDaftParser:
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        
    async def search_properties(self, search_url: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Поиск недвижимости с браузерной автоматизацией"""
        print(f"🌐 URL: {search_url}")
        
        async with async_playwright() as p:
            # Запускаем браузер
            browser = await p.chromium.launch(headless=True)
            
            # Создаем контекст с настройками
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Загружаем страницу поиска
                print("📄 Загружаем страницу поиска...")
                await page.goto(search_url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Получаем общее количество результатов
                total_count = await self._get_results_count(page)
                print(f"📊 Доступно объявлений: {total_count}")
                
                # Собираем ссылки на объявления
                property_urls = await self._collect_property_urls(page)
                print(f"🔗 Найдено ссылок: {len(property_urls)}")
                
                # Ограничиваем количество
                urls_to_process = property_urls[:limit]
                print(f"📝 Будем обрабатывать: {len(urls_to_process)} объявлений")
                
                # Парсим каждое объявление
                results = []
                for i, url in enumerate(urls_to_process, 1):
                    print(f"  {i}/{len(urls_to_process)}: {self._get_property_name(url)}")
                    
                    property_data = await self._parse_property(page, url)
                    if property_data:
                        results.append(property_data)
                        self._print_property_summary(property_data)
                    else:
                        print("    ❌ Не удалось получить данные")
                
                return results
                
            except Exception as e:
                print(f"❌ Ошибка поиска: {e}")
                return []
                
            finally:
                await browser.close()
    
    async def _get_results_count(self, page) -> int:
        """Получает общее количество результатов поиска"""
        try:
            h1_element = await page.wait_for_selector('h1', timeout=5000)
            h1_text = await h1_element.text_content()
            count_match = re.search(r'(\d+)', h1_text or '')
            return int(count_match.group(1)) if count_match else 0
        except:
            return 0
    
    async def _collect_property_urls(self, page) -> List[str]:
        """Собирает все ссылки на объявления со страницы"""
        try:
            property_links = await page.query_selector_all('a[href*="/for-rent/"]')
            
            unique_urls = set()
            for link in property_links:
                href = await link.get_attribute('href')
                if href and '/for-rent/' in href and href not in unique_urls:
                    if href.startswith('/'):
                        href = self.base_url + href
                    unique_urls.add(href)
            
            return list(unique_urls)
        except:
            return []
    
    def _get_property_name(self, url: str) -> str:
        """Извлекает читаемое имя из URL"""
        try:
            parts = url.split('/')
            if len(parts) > 3:
                name = parts[-1].replace('-', ' ')
                return name[:40] + '...' if len(name) > 40 else name
        except:
            pass
        return url[-40:]
    
    async def _parse_property(self, page, url: str) -> Optional[Dict[str, Any]]:
        """Парсит данные одного объявления"""
        try:
            # Переходим на страницу объявления
            await page.goto(url, wait_until='networkidle', timeout=15000)
            await page.wait_for_timeout(2000)
            
            # Получаем содержимое страницы
            page_content = await page.content()
            
            return {
                'url': url,
                'title': await self._extract_title(page),
                'price': await self._extract_price(page, page_content),
                'bedrooms': await self._extract_bedrooms(page, page_content),
                'property_type': self._extract_property_type(page_content),
                'location': await self._extract_location(page),
                'description': self._extract_description(page_content),
                'posted_date': self._extract_posted_date(page_content)
            }
            
        except Exception as e:
            print(f"    ❌ Ошибка парсинга {url}: {e}")
            return None
    
    async def _extract_title(self, page) -> Optional[str]:
        """Извлекает заголовок объявления"""
        try:
            title_selectors = ['h1', '.TitleBlock_title', '[data-testid="title"]']
            
            for selector in title_selectors:
                element = await page.query_selector(selector)
                if element:
                    title = await element.text_content()
                    return title.strip() if title else None
        except:
            pass
        return None
    
    async def _extract_price(self, page, page_content: str) -> Optional[int]:
        """Извлекает цену из разных источников на странице"""
        # Пробуем селекторы
        price_selectors = [
            '[data-testid="price"]',
            '.TitleBlock_price',
            'span:has-text("€")',
            '.price'
        ]
        
        for selector in price_selectors:
            try:
                price_element = await page.query_selector(selector)
                if price_element:
                    price_text = await price_element.text_content()
                    price_match = re.search(r'€([\d,]+)', price_text or '')
                    if price_match:
                        return int(price_match.group(1).replace(',', ''))
            except:
                continue
        
        # Ищем в JSON данных
        try:
            json_match = re.search(r'"price":\s*(\d+)', page_content)
            if json_match:
                return int(json_match.group(1))
        except:
            pass
        
        return None
    
    async def _extract_bedrooms(self, page, page_content: str) -> Optional[int]:
        """Извлекает количество спален с улучшенной логикой"""
        # Сначала ищем в JSON данных
        try:
            # Ищем в structured data
            json_match = re.search(r'"numBedrooms":\s*"([^"]*)"', page_content)
            if json_match:
                bedrooms_text = json_match.group(1)
                
                # Если это просто число
                if bedrooms_text.isdigit():
                    return int(bedrooms_text)
                
                # Если это диапазон или список (например "1, 2 & 3 bed")
                bed_numbers = re.findall(r'(\d+)', bedrooms_text)
                if bed_numbers:
                    # Берем максимальное значение из найденных
                    return max([int(x) for x in bed_numbers])
        except:
            pass
        
        # Ищем в селекторах на странице
        try:
            bed_selectors = [
                '[data-testid="bed-bath"]',
                '.property-details',
                '.TitleBlock_meta'
            ]
            
            for selector in bed_selectors:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    bed_match = re.search(r'(\d+)\s*bed', text or '', re.IGNORECASE)
                    if bed_match:
                        return int(bed_match.group(1))
        except:
            pass
        
        # Последний шанс - ищем в тексте страницы
        try:
            bed_match = re.search(r'(\d+)\s*bedroom', page_content, re.IGNORECASE)
            if bed_match:
                bedrooms = int(bed_match.group(1))
                # Проверяем разумность (не больше 10 спален)
                if 1 <= bedrooms <= 10:
                    return bedrooms
        except:
            pass
        
        return None
    
    async def _extract_location(self, page) -> Optional[str]:
        """Извлекает местоположение"""
        try:
            title_element = await page.query_selector('h1')
            if title_element:
                title = await title_element.text_content()
                location_match = re.search(r'Dublin\s+\d+|Dublin\s+\w+', title or '')
                if location_match:
                    return location_match.group()
        except:
            pass
        return None
    
    def _extract_property_type(self, page_content: str) -> str:
        """Извлекает тип недвижимости"""
        try:
            # Ищем в JSON данных
            type_match = re.search(r'"@type":\s*"([^"]*)"', page_content)
            if type_match:
                return type_match.group(1)
            
            # Ищем в тексте
            if 'apartment' in page_content.lower():
                return 'Apartment'
            elif 'house' in page_content.lower():
                return 'House'
            elif 'studio' in page_content.lower():
                return 'Studio'
        except:
            pass
        return 'Unknown'
    
    def _extract_description(self, page_content: str, max_length: int = 200) -> str:
        """Извлекает описание объявления"""
        try:
            # Ищем в JSON данных
            desc_match = re.search(r'"description":\s*"([^"]*)"', page_content)
            if desc_match:
                desc = desc_match.group(1)
                if len(desc) > max_length:
                    desc = desc[:max_length] + '...'
                return desc
        except:
            pass
        return 'No description'
    
    def _extract_posted_date(self, page_content: str) -> str:
        """Извлекает дату публикации"""
        try:
            # Ищем различные форматы дат
            date_patterns = [
                r'"datePublished":\s*"([^"]*)"',
                r'"date":\s*"([^"]*)"',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{4}-\d{2}-\d{2})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, page_content)
                if match:
                    return match.group(1)
        except:
            pass
        return 'Unknown'
    
    def _print_property_summary(self, prop: Dict[str, Any]):
        """Выводит краткую информацию об объявлении"""
        title = prop.get('title', 'Без названия')[:50]
        price = f"€{prop['price']}" if prop.get('price') else 'Цена не указана'
        beds = f"{prop['bedrooms']} спален" if prop.get('bedrooms') else 'Спальни не указаны'
        print(f"    ✅ {title} - {price}, {beds}")
    
    def format_results(self, results: List[Dict[str, Any]], show_details: bool = True) -> str:
        """Форматирует результаты для вывода"""
        if not results:
            return "❌ Объявления не найдены"
        
        output = [f"🏠 НАЙДЕНО {len(results)} ОБЪЯВЛЕНИЙ:\n"]
        
        for i, prop in enumerate(results, 1):
            price_str = f"€{prop['price']}" if prop['price'] else "Цена не указана"
            bedrooms_str = f"{prop['bedrooms']} спален" if prop['bedrooms'] else "Спальни не указаны"
            type_str = prop.get('property_type', 'Тип не указан')
            location_str = prop.get('location', 'Локация не указана')
            
            output.append(f"{i}. {prop['title']}")
            output.append(f"   💰 {price_str} | 🛏️ {bedrooms_str} | 🏠 {type_str}")
            output.append(f"   📍 {location_str}")
            
            if show_details:
                output.append(f"   🔗 {prop['url']}")
            
            output.append("")
        
        return "\n".join(output)
    
    def get_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Возвращает статистику по результатам"""
        if not results:
            return {}
        
        prices = [prop['price'] for prop in results if prop.get('price')]
        bedrooms = [prop['bedrooms'] for prop in results if prop.get('bedrooms')]
        
        stats = {
            'total_count': len(results),
            'with_price': len(prices),
            'with_bedrooms': len(bedrooms)
        }
        
        if prices:
            stats.update({
                'avg_price': sum(prices) / len(prices),
                'min_price': min(prices),
                'max_price': max(prices)
            })
        
        if bedrooms:
            stats.update({
                'avg_bedrooms': sum(bedrooms) / len(bedrooms),
                'min_bedrooms': min(bedrooms),
                'max_bedrooms': max(bedrooms)
            })
        
        return stats

async def main():
    """Основная функция для тестирования"""
    print("🚀 ADVANCED DAFT.IE PARSER")
    print("=" * 50)
    
    parser = AdvancedDaftParser()
    
    # URL для поиска 3+ спален до €2500 в Дублине
    search_url = "https://www.daft.ie/property-for-rent/dublin?rentalPrice_to=2500&numBeds_from=3"
    
    print(f"🎯 ПОИСК: 3+ спален до €2500 в Дублине")
    print(f"🔗 URL: {search_url}")
    print()
    
    # Выполняем поиск
    start_time = datetime.datetime.now()
    results = await parser.search_properties(search_url, limit=15)
    duration = (datetime.datetime.now() - start_time).total_seconds()
    
    # Выводим результаты
    print("\n" + "=" * 50)
    print("📋 РЕЗУЛЬТАТЫ ПОИСКА")
    print("=" * 50)
    
    formatted_output = parser.format_results(results)
    print(formatted_output)
    
    # Статистика
    print("=" * 50)
    print(f"⏱️  Время выполнения: {duration:.1f} секунд")
    print(f"📊 Найдено объявлений: {len(results)}")
    
    if results:
        stats = parser.get_statistics(results)
        if stats.get('avg_price'):
            print(f"💰 Средняя цена: €{stats['avg_price']:.0f}")
        if stats.get('avg_bedrooms'):
            print(f"🛏️  Среднее количество спален: {stats['avg_bedrooms']:.1f}")
    
    # Сохраняем результаты
    filename = f'daft_advanced_search_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Результаты сохранены в {filename}")

if __name__ == "__main__":
    asyncio.run(main())
