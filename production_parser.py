#!/usr/bin/env python3
"""
Готовый к продакшену парсер daft.ie с исправленной логикой спален
"""

import asyncio
import re
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
import json
import datetime
import logging
from pathlib import Path

class ProductionDaftParser:
    """
    Продакшен-готовый парсер для daft.ie с полной функциональностью
    """
    
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        
    async def search_properties(
        self, 
        min_bedrooms: int = 3, 
        max_price: int = 2500, 
        location: str = "dublin-city", 
        limit: int = 20,
        max_pages: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Ищет недвижимость на daft.ie с заданными параметрами
        
        Args:
            min_bedrooms: Минимальное количество спален
            max_price: Максимальная цена в евро
            location: Локация для поиска (dublin-city, cork, etc.)
            limit: Максимальное количество результатов
            max_pages: Максимальное количество страниц для просмотра
            
        Returns:
            Список словарей с данными о недвижимости
        """
        print(f"🔍 ПОИСК: {min_bedrooms}+ спален, до €{max_price}, {location} (до {max_pages} страниц)")
        
        # Увеличиваем pageSize для получения большего количества результатов на странице
        page_size = min(50, limit)  # максимум 50 на страницу
        
        async with async_playwright() as p:
            browser = None
            context = None
            page = None
            
            try:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox', 
                        '--disable-setuid-sandbox', 
                        '--disable-blink-features=AutomationControlled',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding'
                    ]
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                    }
                )
                
                page = await context.new_page()
                
                all_property_urls = []
                results = []
                
                # Просматриваем несколько страниц
                for page_num in range(max_pages):
                    search_url = f"{self.base_url}/property-for-rent/{location}/houses?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}&pageSize={page_size}&from={page_num * page_size}"
                    
                    # Загружаем страницу поиска
                    print(f"📄 Загружаем страницу {page_num + 1}/{max_pages}: {search_url}")
                    await page.goto(search_url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    if page_num == 0:
                        # Получаем общее количество результатов только на первой странице
                        total_count = await self._get_results_count(page)
                        print(f"📊 Доступно объявлений: {total_count}")
                    
                    # Собираем ссылки на объявления с текущей страницы
                    page_property_urls = await self._collect_property_urls(page)
                    print(f"🔗 Найдено ссылок на странице {page_num + 1}: {len(page_property_urls)}")
                    
                    if not page_property_urls:
                        print(f"❌ На странице {page_num + 1} не найдено объявлений, останавливаем поиск")
                        break
                    
                    all_property_urls.extend(page_property_urls)
                    
                    # Если уже собрали достаточно ссылок, останавливаемся
                    if len(all_property_urls) >= limit:
                        break
                
                # Ограничиваем количество
                urls_to_process = all_property_urls[:limit]
                print(f"📝 Всего собрано ссылок: {len(all_property_urls)}, будем обрабатывать: {len(urls_to_process)} объявлений")
                
                # Парсим каждое объявление с фильтрацией
                filtered_out = 0
                
                for i, url in enumerate(urls_to_process, 1):
                    print(f"  {i}/{len(urls_to_process)}: {self._get_property_name(url)}")
                    
                    property_data = await self._parse_property(page, url)
                    if property_data:
                        # ВАЖНО: Проверяем фильтры перед добавлением
                        if self._validate_property(property_data, min_bedrooms, max_price):
                            results.append(property_data)
                            self._print_property_summary(property_data)
                        else:
                            filtered_out += 1
                            print(f"    🚫 Отфильтровано: {property_data.get('bedrooms', '?')} спален, €{property_data.get('price', '?')}")
                    else:
                        print("    ❌ Не удалось получить данные")
                
                print(f"📊 Результат: {len(results)} подходящих, {filtered_out} отфильтрованных")
                return results
                
            except asyncio.CancelledError:
                print("🛑 Парсинг был отменен")
                raise  # Переподнимаем CancelledError для правильной обработки
                
            except Exception as e:
                print(f"❌ Ошибка поиска: {e}")
                return []
                
            finally:
                # Закрываем ресурсы в обратном порядке
                try:
                    if page:
                        await page.close()
                except:
                    pass
                    
                try:
                    if context:
                        await context.close()
                except:
                    pass
                    
                try:
                    if browser:
                        await browser.close()
                except:
                    pass
    
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
        """Извлекает краткое название из URL"""
        try:
            return url.split('/')[-2][:40] + "..." if len(url.split('/')[-2]) > 40 else url.split('/')[-2]
        except:
            return "unknown"
    
    async def _parse_property(self, page, url: str) -> Optional[Dict[str, Any]]:
        """Парсит отдельную страницу объявления"""
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(2000)
            
            # Получаем содержимое страницы для поиска данных
            page_content = await page.content()
            
            property_data = {
                'url': url,
                'title': None,
                'price': None,
                'bedrooms': None,
                'property_type': None,
                'location': None,
                'description': None,
                'parsed_at': datetime.datetime.now().isoformat()
            }
            
            # Извлекаем данные пошагово с обработкой ошибок
            try:
                property_data['title'] = await self._extract_title(page)
            except Exception as e:
                print(f"    ⚠️ Ошибка извлечения заголовка: {e}")
            
            try:
                property_data['price'] = await self._extract_price(page, page_content)
            except Exception as e:
                print(f"    ⚠️ Ошибка извлечения цены: {e}")
            
            try:
                property_data['bedrooms'] = await self._extract_bedrooms(page, page_content)
            except Exception as e:
                print(f"    ⚠️ Ошибка извлечения спален: {e}")
            
            try:
                property_data['property_type'] = self._extract_property_type(page_content)
                property_data['description'] = self._extract_description(page_content)
            except Exception as e:
                print(f"    ⚠️ Ошибка извлечения доп. данных: {e}")
            
            # Извлекаем локацию из заголовка
            if property_data['title']:
                property_data['location'] = self._extract_location_from_title(property_data['title'])
            
            # Проверяем, что получили основные данные
            if property_data['title'] or property_data['price']:
                return property_data
            
            return None
            
        except Exception as e:
            print(f"    ⚠️ Ошибка: {str(e)[:50]}...")
            return None
    
    async def _extract_title(self, page) -> Optional[str]:
        """Извлекает заголовок объявления"""
        try:
            title_element = await page.query_selector('h1')
            if title_element:
                title_text = await title_element.text_content()
                return title_text.strip() if title_text else None
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
    
    def _validate_property(self, property_data: Dict[str, Any], min_bedrooms: int, max_price: int) -> bool:
        """Валидация объявления по фильтрам и реалистичности данных"""
        
        # Проверяем наличие обязательных полей
        if not property_data.get('title') or not property_data.get('price'):
            return False
        
        # Проверяем цену
        price = property_data.get('price')
        if not price or price <= 0 or price > max_price:
            return False
        
        # Проверяем количество спален
        bedrooms = property_data.get('bedrooms')
        if bedrooms is None or bedrooms < min_bedrooms:
            return False
        
        # Проверяем реалистичность количества спален (не больше 10)
        if bedrooms > 10:
            return False
        
        # Проверяем реалистичность цены (не меньше €500 в месяц)
        if price < 500:
            return False
        
        # Проверяем что это не рекламное объявление
        title = property_data.get('title', '').lower()
        if any(keyword in title for keyword in ['advertisement', 'sponsored', 'promoted']):
            return False
        
        return True

    async def _extract_bedrooms(self, page, page_content: str) -> Optional[int]:
        """Извлекает количество спален с улучшенной логикой и валидацией"""
        
        # Список для сбора всех найденных значений
        found_bedrooms = []
        
        # 1. Ищем в JSON данных
        try:
            # Structured data
            json_match = re.search(r'"numBedrooms":\s*"?(\d+)"?', page_content)
            if json_match:
                bedrooms = int(json_match.group(1))
                if 0 <= bedrooms <= 10:  # Реалистичный диапазон
                    found_bedrooms.append(bedrooms)
        except:
            pass
        
        # 2. Ищем в селекторах на странице
        try:
            bed_selectors = [
                '[data-testid="bed-bath"]',
                '.property-details',
                '.TitleBlock_meta',
                '.BdRmBtListing',
                '[data-testid="beds"]'
            ]
            
            for selector in bed_selectors:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:  # Проверяем что text не None
                        # Ищем различные паттерны
                        patterns = [
                            r'(\d+)\s*bed',
                            r'(\d+)\s*bedroom',
                            r'(\d+)\s*br\b',
                            r'beds?\s*:\s*(\d+)',
                            r'(\d+)\s*-?\s*bed'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, text.lower())
                            for match in matches:
                                bedrooms = int(match)
                                if 0 <= bedrooms <= 10:
                                    found_bedrooms.append(bedrooms)
        except:
            pass
        
        # 3. Ищем в заголовке страницы
        try:
            title_element = await page.query_selector('h1')
            if title_element:
                title_text = await title_element.text_content()
                if title_text:  # Проверяем что title_text не None
                    patterns = [
                        r'(\d+)\s*bed',
                        r'(\d+)\s*bedroom',
                        r'studio'  # Отдельно обрабатываем studio
                    ]
                    
                    if 'studio' in title_text.lower():
                        found_bedrooms.append(0)
                    else:
                        for pattern in patterns[:2]:  # Только bed/bedroom паттерны
                            matches = re.findall(pattern, title_text.lower())
                            for match in matches:
                                bedrooms = int(match)
                                if 0 <= bedrooms <= 10:
                                    found_bedrooms.append(bedrooms)
        except:
            pass
        
        # 4. Последний шанс - ищем в тексте страницы (более осторожно)
        try:
            # Ищем только четкие упоминания
            bed_patterns = [
                r'(\d+)\s*bedroom\s*(?:house|apartment|flat)',
                r'(?:house|apartment|flat).*?(\d+)\s*bedroom',
                r'(\d+)\s*bed\s*(?:house|apartment|flat)',
            ]
            
            for pattern in bed_patterns:
                matches = re.findall(pattern, page_content.lower())
                for match in matches:
                    bedrooms = int(match)
                    if 0 <= bedrooms <= 10:
                        found_bedrooms.append(bedrooms)
        except:
            pass
        
        # Анализируем найденные значения
        if found_bedrooms:
            # Удаляем дубликаты и сортируем
            unique_bedrooms = list(set(found_bedrooms))
            
            # Если все значения одинаковые - берем его
            if len(unique_bedrooms) == 1:
                return unique_bedrooms[0]
            
            # Если есть разные значения, берем наиболее часто встречающееся
            from collections import Counter
            counter = Counter(found_bedrooms)
            most_common = counter.most_common(1)[0][0]
            
            # Дополнительная проверка: если наиболее частое значение кажется неразумным,
            # берем наименьшее разумное значение
            if most_common > 6:  # Очень много спален
                reasonable_values = [b for b in unique_bedrooms if 1 <= b <= 6]
                if reasonable_values:
                    return min(reasonable_values)
            
            return most_common
        
        # Если ничего не найдено, возвращаем None
        return None
    
    def _extract_property_type(self, page_content: str) -> Optional[str]:
        """Извлекает тип недвижимости"""
        try:
            type_match = re.search(r'"propertyType":\s*"([^"]*)"', page_content)
            if type_match:
                return type_match.group(1)
        except:
            pass
        return None
    
    def _extract_description(self, page_content: str, max_length: int = 200) -> Optional[str]:
        """Извлекает описание объявления"""
        try:
            desc_match = re.search(r'"description":\s*"([^"]*)"', page_content)
            if desc_match:
                description = desc_match.group(1)
                return description[:max_length] + "..." if len(description) > max_length else description
        except:
            pass
        return None
    
    def _extract_location_from_title(self, title: str) -> Optional[str]:
        """Извлекает локацию из заголовка"""
        try:
            location_match = re.search(r'Dublin\s+\d+|Dublin\s+\w+', title)
            if location_match:
                return location_match.group()
        except:
            pass
        return None
    
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
        
        valid_prices = [r['price'] for r in results if r['price']]
        valid_bedrooms = [r['bedrooms'] for r in results if r['bedrooms']]
        
        stats = {
            'total_count': len(results),
            'with_price': len(valid_prices),
            'with_bedrooms': len(valid_bedrooms)
        }
        
        if valid_prices:
            stats.update({
                'avg_price': sum(valid_prices) / len(valid_prices),
                'min_price': min(valid_prices),
                'max_price': max(valid_prices)
            })
        
        if valid_bedrooms:
            stats.update({
                'avg_bedrooms': sum(valid_bedrooms) / len(valid_bedrooms),
                'min_bedrooms': min(valid_bedrooms),
                'max_bedrooms': max(valid_bedrooms)
            })
        
        return stats

async def main():
    """Основная функция для демонстрации"""
    print("🚀 DAFT.IE PRODUCTION PARSER")
    print("=" * 50)
    
    parser = ProductionDaftParser()
    
    # Параметры поиска
    search_params = {
        'min_bedrooms': 3,
        'max_price': 2500,
        'location': 'dublin-city',  # Используем правильную локацию
        'limit': 20
    }
    
    print("🎯 ПАРАМЕТРЫ ПОИСКА:")
    for key, value in search_params.items():
        print(f"   {key}: {value}")
    print()
    
    # Выполняем поиск
    start_time = datetime.datetime.now()
    results = await parser.search_properties(**search_params)
    duration = (datetime.datetime.now() - start_time).total_seconds()
    
    # Выводим результаты
    print("\n" + "=" * 50)
    print("📋 РЕЗУЛЬТАТЫ")
    print("=" * 50)
    
    formatted_output = parser.format_results(results, show_details=False)
    print(formatted_output)
    
    # Статистика
    stats = parser.get_statistics(results)
    print("=" * 50)
    print("📊 СТАТИСТИКА")
    print("=" * 50)
    print(f"⏱️  Время выполнения: {duration:.1f} секунд")
    print(f"📊 Найдено объявлений: {stats.get('total_count', 0)}")
    
    if stats.get('avg_price'):
        print(f"💰 Средняя цена: €{stats['avg_price']:.0f}")
        print(f"💰 Диапазон цен: €{stats['min_price']} - €{stats['max_price']}")
    
    if stats.get('avg_bedrooms'):
        print(f"🛏️  Среднее кол-во спален: {stats['avg_bedrooms']:.1f}")
        print(f"🛏️  Диапазон спален: {stats['min_bedrooms']} - {stats['max_bedrooms']}")
    
    # Сохраняем результаты
    filename = f'daft_production_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'search_params': search_params,
            'results': results,
            'statistics': stats,
            'timestamp': datetime.datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Данные сохранены в {filename}")

if __name__ == "__main__":
    asyncio.run(main())
