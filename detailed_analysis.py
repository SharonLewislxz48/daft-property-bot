#!/usr/bin/env python3
"""
Детальный анализатор ссылок daft.ie
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def detailed_link_analysis():
    """Детальный анализ ссылок на странице"""
    print("🔍 Детальный анализ ссылок на daft.ie...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-IE,en;q=0.9',
        'Referer': 'https://www.google.ie/'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        url = "https://www.daft.ie/property-for-rent/dublin"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    print(f"✅ Получили контент: {len(content)} символов")
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Анализируем ВСЕ ссылки
                    print("\n🔗 Анализ ВСЕХ ссылок:")
                    links = soup.find_all('a', href=True)
                    
                    property_patterns = [
                        r'/for-rent/',
                        r'/apartment',
                        r'/house',
                        r'/studio',
                        r'/\d+$'  # Заканчивается на число
                    ]
                    
                    for pattern in property_patterns:
                        print(f"\n📋 Ссылки с паттерном '{pattern}':")
                        matching_links = []
                        
                        for link in links:
                            href = link.get('href', '')
                            if re.search(pattern, href):
                                full_url = href if href.startswith('http') else f"https://www.daft.ie{href}"
                                matching_links.append(full_url)
                        
                        unique_links = list(set(matching_links))
                        print(f"  Найдено {len(unique_links)} уникальных ссылок")
                        
                        for i, link in enumerate(unique_links[:5]):
                            print(f"    {i+1}. {link}")
                        
                        if len(unique_links) > 5:
                            print(f"    ... и ещё {len(unique_links)-5} ссылок")
                    
                    # Специальный поиск объявлений
                    print(f"\n🎯 Специальный поиск объявлений:")
                    property_links = []
                    
                    for link in links:
                        href = link.get('href', '')
                        
                        # Различные варианты ссылок на объявления
                        if any(pattern in href for pattern in ['/for-rent/', '/to-rent/', '/rental/']):
                            if any(prop_type in href for prop_type in ['apartment', 'house', 'studio', 'flat']):
                                if re.search(r'/\d+$', href):  # Заканчивается на ID
                                    full_url = href if href.startswith('http') else f"https://www.daft.ie{href}"
                                    property_links.append(full_url)
                    
                    print(f"Найдено {len(property_links)} ссылок на объявления:")
                    for i, link in enumerate(property_links[:10]):
                        print(f"  {i+1}. {link}")
                    
                    # Сохраняем примеры ссылок для тестирования
                    if property_links:
                        print(f"\n📝 Сохраняем первые 5 ссылок для тестирования...")
                        with open('/home/barss/PycharmProjects/daftparser/test_links.txt', 'w') as f:
                            for link in property_links[:5]:
                                f.write(link + '\n')
                        print("✅ Ссылки сохранены в test_links.txt")
                    
                    return property_links
                    
                else:
                    print(f"❌ Ошибка: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return []

if __name__ == "__main__":
    links = asyncio.run(detailed_link_analysis())
