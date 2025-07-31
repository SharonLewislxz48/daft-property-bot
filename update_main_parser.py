#!/usr/bin/env python3
"""
Обновленный парсер daft.ie с использованием Playwright для получения полных результатов поиска
"""

import asyncio
import re
from typing import List, Dict, Any
from playwright.async_api import async_playwright
import json
import datetime
import aiohttp
from bs4 import BeautifulSoup

class DaftPlaywrightParser:
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        self.session = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_search_results(self, min_bedrooms: int = 3, max_price: int = 2500, location: str = "dublin") -> List[Dict[str, Any]]:
        """
        Получает результаты поиска с использованием Playwright для обхода JavaScript
        """
        print(f"🔍 Поиск объявлений: {min_bedrooms}+ спален, до €{max_price} в {location}")
        
        # Формируем URL с фильтрами
        search_url = f"{self.base_url}/property-for-rent/{location}?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}"
        print(f"🌐 URL поиска: {search_url}")
        
        results = []
        
        async with async_playwright() as p:
            # Запускаем браузер в headless режиме
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # Переходим на страницу поиска
                await page.goto(search_url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)  # Ждем загрузки JavaScript
                
                # Получаем количество результатов
                try:
                    results_count_element = await page.wait_for_selector('h1[data-testid="search-h1"]', timeout=5000)
                    results_text = await results_count_element.text_content()
                    results_count = re.search(r'(\d+)', results_text)
                    total_results = int(results_count.group(1)) if results_count else 0
                    print(f"📊 Найдено результатов: {total_results}")
                except:
                    print("⚠️ Не удалось получить количество результатов")
                    total_results = 0

                # Ищем ссылки на объявления (универсальный метод)
                property_links = await page.query_selector_all('a[href*="/for-rent/"]')
                print(f"🔗 Найдено ссылок на объявления: {len(property_links)}")
                
                # Извлекаем уникальные ссылки
                unique_links = set()
                for link in property_links:
                    href = await link.get_attribute('href')
                    if href and '/for-rent/' in href and href not in unique_links:
                        if href.startswith('/'):
                            href = self.base_url + href
                        unique_links.add(href)
                
                print(f"🏠 Уникальных объявлений: {len(unique_links)}")
                
                # Обрабатываем первые 10 объявлений для демонстрации
                for i, url in enumerate(list(unique_links)[:10]):
                    print(f"📝 Обрабатываем объявление {i+1}/10: {url}")
                    property_data = await self.parse_property_details(url, page)
                    if property_data:
                        results.append(property_data)
                        print(f"✅ Найдено: {property_data['title']} - €{property_data.get('price', 'N/A')}")
                
            except Exception as e:
                print(f"❌ Ошибка при поиске: {e}")
                
            finally:
                await browser.close()
        
        return results

    async def parse_property_details(self, url: str, page) -> Dict[str, Any]:
        """
        Парсит детали объявления
        """
        try:
            await page.goto(url, wait_until='networkidle', timeout=20000)
            await page.wait_for_timeout(1000)
            
            # Получаем заголовок
            title = ""
            try:
                title_element = await page.query_selector('h1')
                if title_element:
                    title = await title_element.text_content()
                    title = title.strip()
            except:
                pass
                
            # Извлекаем данные из JSON на странице
            property_data = {
                'url': url,
                'title': title,
                'price': None,
                'bedrooms': None,
                'property_type': None,
                'location': None,
                'description': None,
                'parsed_at': datetime.datetime.now().isoformat()
            }
            
            # Ищем JSON данные в скрипте страницы
            try:
                script_content = await page.content()
                # Ищем JSON с данными объявления
                json_match = re.search(r'"listing":\s*({.*?"nonFormatted".*?})', script_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    # Очищаем JSON от возможных проблем
                    json_str = re.sub(r'("price":\s*)"([^"]*)"', r'\1\2', json_str)  # Убираем кавычки у цены
                    
                    try:
                        listing_data = json.loads(json_str)
                        
                        # Извлекаем цену
                        if 'nonFormatted' in listing_data and 'price' in listing_data['nonFormatted']:
                            property_data['price'] = listing_data['nonFormatted']['price']
                        elif 'price' in listing_data:
                            # Пытаемся извлечь цену из строки
                            price_str = listing_data['price']
                            price_match = re.search(r'€([\d,]+)', price_str)
                            if price_match:
                                property_data['price'] = int(price_match.group(1).replace(',', ''))
                        
                        # Извлекаем количество спален
                        if 'numBedrooms' in listing_data:
                            bedrooms_str = listing_data['numBedrooms']
                            if bedrooms_str:
                                # Извлекаем числа из строки типа "1, 2 & 3 bed"
                                bed_numbers = re.findall(r'(\d+)', bedrooms_str)
                                if bed_numbers:
                                    property_data['bedrooms'] = max([int(x) for x in bed_numbers])
                        
                        # Другие поля
                        property_data['property_type'] = listing_data.get('propertyType', '')
                        property_data['description'] = listing_data.get('description', '')[:500]  # Обрезаем описание
                        
                        # Локация из заголовка
                        if title:
                            location_match = re.search(r'Dublin\s+\d+|Dublin\s+\w+', title)
                            if location_match:
                                property_data['location'] = location_match.group()
                                
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Ошибка парсинга JSON: {e}")
                        
            except Exception as e:
                print(f"⚠️ Ошибка извлечения данных: {e}")
            
            return property_data
            
        except Exception as e:
            print(f"❌ Ошибка парсинга {url}: {e}")
            return None

    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Форматирует результаты для вывода
        """
        if not results:
            return "❌ Объявления не найдены"
        
        output = [f"🏠 Найдено {len(results)} объявлений:\n"]
        
        for i, prop in enumerate(results, 1):
            price_str = f"€{prop['price']}" if prop['price'] else "Цена не указана"
            bedrooms_str = f"{prop['bedrooms']} спален" if prop['bedrooms'] else "Спальни не указаны"
            
            output.append(f"{i}. {prop['title']}")
            output.append(f"   💰 {price_str} | 🛏️ {bedrooms_str}")
            output.append(f"   📍 {prop.get('location', 'Локация не указана')}")
            output.append(f"   🔗 {prop['url']}")
            output.append("")
        
        return "\n".join(output)

async def main():
    """
    Основная функция для тестирования обновленного парсера
    """
    print("🚀 Запуск обновленного парсера Daft.ie с Playwright")
    print("=" * 60)
    
    async with DaftPlaywrightParser() as parser:
        # Ищем 3+ спальни до €2500 в Дублине
        results = await parser.get_search_results(
            min_bedrooms=3,
            max_price=2500,
            location="dublin"
        )
        
        # Выводим результаты
        formatted_output = parser.format_results(results)
        print("\n" + "=" * 60)
        print("📋 РЕЗУЛЬТАТЫ ПОИСКА")
        print("=" * 60)
        print(formatted_output)
        
        # Сохраняем в файл
        with open('daft_results_playwright.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"💾 Результаты сохранены в daft_results_playwright.json")

if __name__ == "__main__":
    asyncio.run(main())
