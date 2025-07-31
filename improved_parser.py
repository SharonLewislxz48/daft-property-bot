#!/usr/bin/env python3
"""
Улучшенный парсер с исправленным извлечением цен и данных
"""

import asyncio
import re
from typing import List, Dict, Any
from playwright.async_api import async_playwright
import json
import datetime

class ImprovedDaftParser:
    def __init__(self):
        self.base_url = "https://www.daft.ie"
        
    async def get_search_results(self, min_bedrooms: int = 3, max_price: int = 2500, location: str = "dublin") -> List[Dict[str, Any]]:
        """
        Получает результаты поиска с улучшенным парсингом данных
        """
        print(f"🔍 Поиск объявлений: {min_bedrooms}+ спален, до €{max_price} в {location}")
        
        search_url = f"{self.base_url}/property-for-rent/{location}?rentalPrice_to={max_price}&numBeds_from={min_bedrooms}"
        print(f"🌐 URL поиска: {search_url}")
        
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                await page.goto(search_url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Получаем количество результатов
                try:
                    results_count_element = await page.wait_for_selector('h1[data-testid="search-h1"]', timeout=5000)
                    results_text = await results_count_element.text_content()
                    results_count = re.search(r'(\d+)', results_text)
                    total_results = int(results_count.group(1)) if results_count else 0
                    print(f"📊 Найдено результатов: {total_results}")
                except:
                    print("⚠️ Не удалось получить количество результатов")

                # Ищем карточки объявлений на странице поиска
                property_cards = await page.query_selector_all('[data-testid*="listing"]')
                print(f"🏠 Найдено карточек на странице: {len(property_cards)}")
                
                # Парсим данные прямо с страницы поиска
                for i, card in enumerate(property_cards[:10]):  # Берем первые 10
                    try:
                        property_data = await self.parse_search_card(card, page)
                        if property_data:
                            results.append(property_data)
                            price_str = f"€{property_data['price']}" if property_data['price'] else "Цена не указана"
                            bedrooms_str = f"{property_data['bedrooms']} спален" if property_data['bedrooms'] else "Спальни не указаны"
                            print(f"✅ {i+1}. {property_data['title']} - {price_str}, {bedrooms_str}")
                    except Exception as e:
                        print(f"⚠️ Ошибка парсинга карточки {i+1}: {e}")
                        continue
                
            except Exception as e:
                print(f"❌ Ошибка при поиске: {e}")
                
            finally:
                await browser.close()
        
        return results

    async def parse_search_card(self, card, page) -> Dict[str, Any]:
        """
        Парсит данные с карточки объявления на странице поиска
        """
        property_data = {
            'title': None,
            'price': None,
            'bedrooms': None,
            'property_type': None,
            'location': None,
            'url': None,
            'parsed_at': datetime.datetime.now().isoformat()
        }
        
        try:
            # Получаем ссылку
            link_element = await card.query_selector('a[href*="/for-rent/"]')
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    property_data['url'] = self.base_url + href if href.startswith('/') else href
            
            # Получаем заголовок
            title_selectors = [
                '[data-testid="listing-title"]',
                'h2 a',
                '.TitleBlock_address',
                'a[data-tracking="listing-title"]'
            ]
            
            for selector in title_selectors:
                try:
                    title_element = await card.query_selector(selector)
                    if title_element:
                        property_data['title'] = (await title_element.text_content()).strip()
                        break
                except:
                    continue
            
            # Получаем цену
            price_selectors = [
                '[data-testid="price"]',
                '.TitleBlock_price',
                '.SearchResult_price',
                '[class*="price"]'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = await card.query_selector(selector)
                    if price_element:
                        price_text = await price_element.text_content()
                        # Извлекаем числа из цены
                        price_match = re.search(r'€([\d,]+)', price_text)
                        if price_match:
                            property_data['price'] = int(price_match.group(1).replace(',', ''))
                            break
                except:
                    continue
            
            # Получаем количество спален и тип недвижимости
            details_selectors = [
                '[data-testid="bed-bath"]',
                '.TitleBlock_meta',
                '.SearchResult_propertyDetails',
                '[class*="bed"]'
            ]
            
            for selector in details_selectors:
                try:
                    details_element = await card.query_selector(selector)
                    if details_element:
                        details_text = await details_element.text_content()
                        
                        # Ищем количество спален
                        bed_match = re.search(r'(\d+)\s*bed', details_text, re.IGNORECASE)
                        if bed_match:
                            property_data['bedrooms'] = int(bed_match.group(1))
                        
                        # Ищем тип недвижимости
                        if 'apartment' in details_text.lower():
                            property_data['property_type'] = 'Apartment'
                        elif 'house' in details_text.lower():
                            property_data['property_type'] = 'House'
                        
                        if property_data['bedrooms']:  # Если нашли спальни, прерываем
                            break
                except:
                    continue
            
            # Если не нашли спальни в деталях, ищем в заголовке
            if not property_data['bedrooms'] and property_data['title']:
                bed_match = re.search(r'(\d+)\s*bed', property_data['title'], re.IGNORECASE)
                if bed_match:
                    property_data['bedrooms'] = int(bed_match.group(1))
            
            # Извлекаем локацию из заголовка
            if property_data['title']:
                location_match = re.search(r'Dublin\s+\d+|Dublin\s+\w+', property_data['title'])
                if location_match:
                    property_data['location'] = location_match.group()
            
            return property_data
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга карточки: {e}")
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
            type_str = prop.get('property_type', 'Тип не указан')
            
            output.append(f"{i}. {prop['title']}")
            output.append(f"   💰 {price_str} | 🛏️ {bedrooms_str} | 🏠 {type_str}")
            output.append(f"   📍 {prop.get('location', 'Локация не указана')}")
            output.append(f"   🔗 {prop['url']}")
            output.append("")
        
        return "\n".join(output)

async def main():
    """
    Основная функция для тестирования улучшенного парсера
    """
    print("🚀 Запуск улучшенного парсера Daft.ie")
    print("=" * 60)
    
    parser = ImprovedDaftParser()
    
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
    with open('daft_results_improved.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"💾 Результаты сохранены в daft_results_improved.json")

if __name__ == "__main__":
    asyncio.run(main())
