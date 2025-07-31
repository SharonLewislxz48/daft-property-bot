#!/usr/bin/env python3
"""
Исследование правильных URL для поиска на daft.ie
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def test_search_urls():
    """Тестируем разные URL для поиска на daft.ie"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Разные варианты URL для поиска
    test_urls = [
        # Базовый поиск по Дублину
        ("Базовый поиск", "https://www.daft.ie/property-for-rent/dublin"),
        
        # С фильтром цены до 2500
        ("Цена до €2500", "https://www.daft.ie/property-for-rent/dublin?rentalPrice_to=2500"),
        
        # С фильтром спален от 3
        ("3+ спальни", "https://www.daft.ie/property-for-rent/dublin?numBeds_from=3"),
        
        # Комбинированный фильтр: 3+ спальни, до 2500
        ("3+ спальни до €2500", "https://www.daft.ie/property-for-rent/dublin?rentalPrice_to=2500&numBeds_from=3"),
        
        # Альтернативный синтаксис
        ("Альтернативный", "https://www.daft.ie/property-for-rent/dublin?rentalPrice_to=2500&numBeds=3"),
        
        # Поиск домов отдельно
        ("Дома 3+ спальни", "https://www.daft.ie/property-for-rent/dublin?rentalPrice_to=2500&numBeds_from=3&propertyType=house"),
        
        # Поиск квартир отдельно  
        ("Квартиры 3+ спальни", "https://www.daft.ie/property-for-rent/dublin?rentalPrice_to=2500&numBeds_from=3&propertyType=apartment"),
    ]
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for i, (name, url) in enumerate(test_urls):
            print(f"\n=== ТЕСТ {i+1}: {name} ===")
            print(f"URL: {url}")
            
            try:
                async with session.get(url) as response:
                    print(f"Статус: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        print(f"Размер ответа: {len(content):,} символов")
                        
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Ищем ссылки на объявления
                        links = soup.find_all('a', href=re.compile(r'/for-rent/'))
                        property_links = []
                        
                        for link in links:
                            href = link.get('href', '')
                            if '/for-rent/' in href and href.count('/') >= 4:
                                if not href.startswith('http'):
                                    href = 'https://www.daft.ie' + href
                                property_links.append(href)
                        
                        # Уникальные ссылки
                        unique_links = list(set(property_links))
                        print(f"Найдено уникальных объявлений: {len(unique_links)}")
                        
                        # Показываем первые 3 ссылки
                        for j, link in enumerate(unique_links[:3]):
                            print(f"  {j+1}. {link}")
                            
                        # Сохраняем лучший результат
                        if i == 3 and len(unique_links) > 0:  # Комбинированный фильтр
                            return unique_links
                            
                    else:
                        print(f"❌ Ошибка: {response.status}")
                        
            except Exception as e:
                print(f"❌ Исключение: {e}")
                
            await asyncio.sleep(1)  # Пауза между запросами

if __name__ == "__main__":
    asyncio.run(test_search_urls())
