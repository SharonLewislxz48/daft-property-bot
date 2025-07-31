#!/usr/bin/env python3
"""
Анализ структуры страницы Daft.ie
"""
import asyncio
import aiohttp
import random
from bs4 import BeautifulSoup

async def analyze_daft_page():
    """Анализируем структуру страницы Daft.ie"""
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    url = "https://www.daft.ie/property-for-rent/dublin?rentalPrice_to=3000&numBeds_from=2"
    
    print("🔍 Анализируем структуру страницы Daft.ie...")
    print("=" * 50)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        await asyncio.sleep(2)  # Задержка
        
        async with session.get(url) as response:
            print(f"📊 Status: {response.status}")
            print(f"📏 Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
            
            html = await response.text()
            print(f"📄 HTML Length: {len(html)} characters")
            
            # Анализируем содержимое
            soup = BeautifulSoup(html, 'html.parser')
            
            # Проверяем наличие JavaScript-контента
            scripts = soup.find_all('script')
            print(f"📜 JavaScript blocks: {len(scripts)}")
            
            # Ищем признаки React/SPA приложения
            react_indicators = [
                'react', 'ReactDOM', '__NEXT_DATA__', 'window.__APP_STATE__',
                'application/json', 'hydrate', 'clientside'
            ]
            
            for indicator in react_indicators:
                if indicator in html:
                    print(f"🔧 Found SPA indicator: {indicator}")
            
            # Проверяем заголовок страницы
            title = soup.find('title')
            if title:
                print(f"📰 Page title: {title.get_text()}")
            
            # Ищем основной контент
            content_selectors = [
                'main', '[role="main"]', '#main', '.main-content',
                '[data-testid]', '[class*="result" i]', '[class*="listing" i]'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"📦 Found {len(elements)} elements with selector: {selector}")
                    if len(elements) < 10:  # Показываем только если их немного
                        for elem in elements[:3]:
                            classes = elem.get('class', [])
                            test_id = elem.get('data-testid', '')
                            print(f"   - Classes: {classes}, TestID: {test_id}")
            
            # Проверяем наличие ошибок или блокировок
            error_indicators = [
                'blocked', 'forbidden', 'access denied', 'cloudflare',
                'bot protection', 'security check', 'captcha'
            ]
            
            html_lower = html.lower()
            for indicator in error_indicators:
                if indicator in html_lower:
                    print(f"🚫 Found blocking indicator: {indicator}")
            
            # Сохраняем часть HTML для анализа
            print("\n📝 Sample HTML structure:")
            print("-" * 30)
            
            # Ищем JSON данные
            script_tags = soup.find_all('script', type='application/json')
            if script_tags:
                print(f"🔍 Found {len(script_tags)} JSON script tags")
                for i, tag in enumerate(script_tags[:2]):
                    content = tag.string or tag.get_text()
                    if content and len(content) > 100:
                        print(f"   JSON {i+1}: {content[:200]}...")
            
            # Ищем __NEXT_DATA__ (Next.js)
            next_data_script = soup.find('script', string=lambda text: text and '__NEXT_DATA__' in text)
            if next_data_script:
                print("🎯 Found __NEXT_DATA__ - это Next.js приложение")
                content = next_data_script.string
                if 'properties' in content or 'listings' in content:
                    print("✅ JSON содержит данные об объявлениях!")

if __name__ == "__main__":
    asyncio.run(analyze_daft_page())
