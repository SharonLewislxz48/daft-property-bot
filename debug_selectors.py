#!/usr/bin/env python3
"""
Отладочный скрипт для изучения структуры страницы поиска daft.ie
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_page_structure():
    """
    Исследует структуру страницы поиска для поиска правильных селекторов
    """
    search_url = "https://www.daft.ie/property-for-rent/dublin?rentalPrice_to=2500&numBeds_from=3"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Headless для сервера
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            print(f"🌐 Переходим на: {search_url}")
            await page.goto(search_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(5000)  # Ждем загрузки
            
            print("🔍 Ищем все элементы с data-testid...")
            testid_elements = await page.query_selector_all('[data-testid]')
            print(f"Найдено элементов с data-testid: {len(testid_elements)}")
            
            # Получаем все data-testid
            testids = []
            for elem in testid_elements:
                testid = await elem.get_attribute('data-testid')
                if testid:
                    testids.append(testid)
            
            unique_testids = sorted(set(testids))
            print("📋 Уникальные data-testid:")
            for testid in unique_testids:
                print(f"  - {testid}")
            
            print("\n🔍 Ищем ссылки на объявления...")
            property_links = await page.query_selector_all('a[href*="/for-rent/"]')
            print(f"Найдено ссылок: {len(property_links)}")
            
            if property_links:
                print("📄 Первые 5 ссылок:")
                for i, link in enumerate(property_links[:5]):
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    print(f"  {i+1}. {href} - {text[:50]}...")
            
            print("\n🔍 Ищем элементы с классами, содержащими 'card' или 'listing'...")
            card_selectors = [
                '[class*="card"]',
                '[class*="listing"]',
                '[class*="Card"]',
                '[class*="Listing"]',
                '[class*="result"]',
                '[class*="Result"]'
            ]
            
            for selector in card_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"  {selector}: {len(elements)} элементов")
            
            print("\n🔍 Ищем элементы с ценами...")
            price_selectors = [
                '[class*="price"]',
                '[class*="Price"]',
                'span:has-text("€")',
                '*:has-text("€")'
            ]
            
            for selector in price_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"  {selector}: {len(elements)} элементов")
                        if len(elements) > 0:
                            first_text = await elements[0].text_content()
                            print(f"    Первый элемент: {first_text[:30]}...")
                except:
                    pass
            
            # Сохраняем HTML для анализа
            html_content = await page.content()
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("\n💾 HTML страницы сохранен в debug_page.html")
            
            print("\n⏸️ Ждем 10 секунд для ручного анализа...")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page_structure())
