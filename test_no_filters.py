#!/usr/bin/env python3
"""
Тест парсера без фильтров для получения максимума данных
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def test_without_filters():
    """Тест парсера без фильтров"""
    print("🔍 Тестируем парсер БЕЗ фильтров...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-IE,en;q=0.9',
        'Referer': 'https://www.daft.ie/'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Тестируем разные URL
        urls_to_test = [
            "https://www.daft.ie/property-for-rent/dublin",  # Без фильтров
            "https://www.daft.ie/for-rent/dublin",           # Альтернативный URL
            "https://www.daft.ie/property-for-rent/ireland/dublin",  # Полный путь
        ]
        
        for url in urls_to_test:
            print(f"\n🌐 Тестируем URL: {url}")
            
            try:
                async with session.get(url) as response:
                    print(f"📊 Статус: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        print(f"📄 Размер контента: {len(content)} символов")
                        
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Ищем ссылки на объявления
                        links = soup.find_all('a', href=True)
                        property_links = []
                        
                        for link in links:
                            href = link.get('href', '')
                            
                            if '/for-rent/' in href:
                                if any(prop_type in href for prop_type in ['apartment', 'studio', 'flat']):
                                    if re.search(r'/\d+$', href):
                                        full_url = href if href.startswith('http') else f"https://www.daft.ie{href}"
                                        property_links.append(full_url)
                        
                        unique_links = list(set(property_links))
                        print(f"🔗 Найдено ссылок на объявления: {len(unique_links)}")
                        
                        if unique_links:
                            print("✅ УСПЕХ! Найдены ссылки:")
                            for i, link in enumerate(unique_links[:5]):
                                print(f"  {i+1}. {link}")
                            
                            # Тестируем первую ссылку
                            if unique_links:
                                test_link = unique_links[0]
                                print(f"\n🔗 Тестируем первую ссылку: {test_link}")
                                
                                async with session.get(test_link) as prop_response:
                                    if prop_response.status == 200:
                                        prop_content = await prop_response.text()
                                        prop_soup = BeautifulSoup(prop_content, 'html.parser')
                                        
                                        title_elem = prop_soup.find('title')
                                        if title_elem:
                                            title = title_elem.get_text().replace(' is for rent on Daft.ie', '')
                                            print(f"📰 Заголовок: {title}")
                                            
                                            # Ищем цену
                                            price_elements = prop_soup.find_all(string=lambda text: text and '€' in text and 'month' in text)
                                            if price_elements:
                                                print(f"💰 Цена: {price_elements[0].strip()}")
                                        
                                        print("✅ Ссылка РАБОТАЕТ!")
                                        return True
                        else:
                            print("⚠️ Ссылки на объявления не найдены")
                    
            except Exception as e:
                print(f"❌ Ошибка для {url}: {e}")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_without_filters())
    
    if success:
        print(f"\n🎉 ТЕСТ БЕЗ ФИЛЬТРОВ УСПЕШЕН!")
    else:
        print(f"\n⚠️ Нужно попробовать другие методы")
