#!/usr/bin/env python3
"""
Тестирование поиска на daft.ie с использованием Playwright
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def test_daft_with_playwright():
    """Тестируем поиск на daft.ie с браузером"""
    
    async with async_playwright() as p:
        # Запускаем браузер
        browser = await p.chromium.launch(headless=True)  # headless=False для отладки
        page = await browser.new_page()
        
        # Настраиваем User-Agent
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        print("🔍 Тестируем поиск 3+ спальни до €2500 с Playwright")
        print("="*60)
        
        # URL с фильтрами
        url = "https://www.daft.ie/property-for-rent/dublin?rentalPrice_to=2500&numBeds_from=3"
        print(f"🌐 Переходим на: {url}")
        
        try:
            # Переходим на страницу
            await page.goto(url, wait_until='networkidle')
            
            # Ждем загрузки контента
            await page.wait_for_timeout(3000)  # 3 секунды
            
            print(f"✅ Страница загружена")
            
            # Получаем заголовок страницы
            title = await page.title()
            print(f"📄 Заголовок: {title}")
            
            # Ищем количество результатов
            page_text = await page.inner_text('body')
            
            # Ищем индикаторы результатов
            result_patterns = [
                r'(\d+)\s+propert(?:y|ies)\s+found',
                r'(\d+)\s+result',
                r'showing\s+(\d+)',
                r'(\d+)\s+properties\s+to\s+rent'
            ]
            
            for pattern in result_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    print(f"📊 Найдено результатов: {matches[0]}")
                    break
            
            # Ищем ссылки на объявления разными способами
            
            # Способ 1: По href содержащим for-rent
            links1 = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a[href*="for-rent"]'));
                return links
                    .map(link => link.href)
                    .filter(href => href.includes('/for-rent/') && href.split('/').length >= 6)
                    .slice(0, 10);
            }''')
            
            print(f"\n🔗 Способ 1 - ссылки с 'for-rent': {len(links1)}")
            for i, link in enumerate(links1[:3]):
                print(f"  {i+1}. {link}")
            
            # Способ 2: По data-testid
            links2 = await page.evaluate('''() => {
                const elements = document.querySelectorAll('[data-testid*="property"], [data-testid*="listing"], [data-testid*="card"]');
                const links = [];
                elements.forEach(el => {
                    const link = el.querySelector('a') || el.closest('a');
                    if (link && link.href.includes('for-rent')) {
                        links.push(link.href);
                    }
                });
                return [...new Set(links)].slice(0, 10);
            }''')
            
            print(f"\n🔗 Способ 2 - через data-testid: {len(links2)}")
            for i, link in enumerate(links2[:3]):
                print(f"  {i+1}. {link}")
            
            # Способ 3: Поиск по классам
            links3 = await page.evaluate('''() => {
                const selectors = [
                    '[class*="card"] a[href*="for-rent"]',
                    '[class*="property"] a[href*="for-rent"]', 
                    '[class*="listing"] a[href*="for-rent"]',
                    '[class*="item"] a[href*="for-rent"]'
                ];
                
                const links = [];
                selectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        if (el.href && el.href.includes('/for-rent/')) {
                            links.push(el.href);
                        }
                    });
                });
                
                return [...new Set(links)].slice(0, 10);
            }''')
            
            print(f"\n🔗 Способ 3 - через классы: {len(links3)}")
            for i, link in enumerate(links3[:3]):
                print(f"  {i+1}. {link}")
            
            # Способ 4: Универсальный поиск всех ссылок
            all_property_links = await page.evaluate('''() => {
                const allLinks = document.querySelectorAll('a');
                const propertyLinks = [];
                
                allLinks.forEach(link => {
                    const href = link.href;
                    if (href && href.includes('/for-rent/') && href.split('/').length >= 6) {
                        // Проверяем что это не навигационная ссылка
                        if (!href.includes('?') || href.includes('/property-for-rent/')) {
                            propertyLinks.push(href);
                        }
                    }
                });
                
                return [...new Set(propertyLinks)];
            }''')
            
            print(f"\n🔗 Способ 4 - универсальный: {len(all_property_links)}")
            for i, link in enumerate(all_property_links[:5]):
                print(f"  {i+1}. {link}")
            
            # Проверяем одно объявление
            if all_property_links:
                test_link = all_property_links[0]
                print(f"\n🧪 Тестируем первое найденное объявление:")
                print(f"🔗 {test_link}")
                
                await page.goto(test_link, wait_until='networkidle')
                await page.wait_for_timeout(2000)
                
                # Получаем заголовок объявления
                property_title = await page.title()
                print(f"📄 Заголовок: {property_title}")
                
                # Ищем цену
                price_text = await page.evaluate('''() => {
                    const priceElements = document.querySelectorAll('*');
                    for (let el of priceElements) {
                        const text = el.textContent;
                        if (text && text.includes('€') && text.includes('month')) {
                            return text.trim();
                        }
                    }
                    return 'Цена не найдена';
                }''')
                
                print(f"💰 Цена: {price_text}")
                
                # Проверяем количество спален в заголовке
                if '3 bed' in property_title.lower() or '3 bedroom' in property_title.lower():
                    print(f"✅ Подтверждено: 3+ спальни в заголовке")
                elif 'bed' in property_title.lower():
                    print(f"🔍 Найдено упоминание спален: {property_title}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_daft_with_playwright())
