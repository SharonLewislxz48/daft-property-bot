#!/usr/bin/env python3
"""
Детальный анализ HTML страницы daft.ie для поиска правильных селекторов
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def detailed_html_analysis():
    """Детальный анализ HTML для поиска объявлений"""
    
    url = "https://www.daft.ie/property-for-rent/dublin?rentalPrice_to=2500&numBeds_from=3"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    print(f"🔍 Детальный анализ страницы:")
    print(f"URL: {url}")
    print("="*80)
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print(f"📄 Размер страницы: {len(content):,} символов")
                    
                    # 1. Ищем все ссылки
                    all_links = soup.find_all('a')
                    print(f"🔗 Всего ссылок на странице: {len(all_links)}")
                    
                    # 2. Фильтруем ссылки по паттернам
                    for_rent_links = [link for link in all_links if link.get('href') and 'for-rent' in link.get('href')]
                    print(f"🏠 Ссылок с 'for-rent': {len(for_rent_links)}")
                    
                    # 3. Показываем примеры найденных ссылок
                    print(f"\n📋 Первые 10 ссылок с 'for-rent':")
                    for i, link in enumerate(for_rent_links[:10]):
                        href = link.get('href')
                        text = link.get_text().strip()[:50]
                        print(f"  {i+1}. {href} | {text}...")
                    
                    # 4. Ищем другие возможные селекторы
                    print(f"\n🔍 Поиск альтернативных селекторов:")
                    
                    # Ищем по data атрибутам
                    data_elements = soup.find_all(attrs={"data-testid": True})
                    print(f"📊 Элементов с data-testid: {len(data_elements)}")
                    
                    # Показываем уникальные data-testid
                    testids = set([elem.get('data-testid') for elem in data_elements[:20]])
                    for testid in sorted(testids):
                        print(f"  • data-testid='{testid}'")
                    
                    # 5. Ищем по классам
                    elements_with_class = soup.find_all(class_=True)
                    classes = set()
                    for elem in elements_with_class[:50]:
                        if elem.get('class'):
                            classes.update(elem.get('class'))
                    
                    print(f"\n🎨 Частые классы CSS:")
                    common_classes = [cls for cls in classes if any(word in cls.lower() for word in ['card', 'item', 'property', 'listing'])]
                    for cls in sorted(common_classes)[:10]:
                        print(f"  • {cls}")
                    
                    # 6. Ищем JSON данные
                    scripts = soup.find_all('script')
                    print(f"\n📜 Script тегов: {len(scripts)}")
                    
                    for i, script in enumerate(scripts):
                        if script.string and ('property' in script.string.lower() or 'listing' in script.string.lower()):
                            content_preview = script.string[:200].replace('\n', ' ')
                            print(f"  Script {i}: {content_preview}...")
                    
                    # 7. Поиск индикаторов количества результатов
                    page_text = soup.get_text()
                    result_indicators = []
                    
                    lines = page_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ('result' in line.lower() or 'found' in line.lower() or 'property' in line.lower()):
                            if any(char.isdigit() for char in line) and len(line) < 100:
                                result_indicators.append(line)
                    
                    print(f"\n📈 Индикаторы результатов:")
                    for indicator in result_indicators[:5]:
                        print(f"  • {indicator}")
                        
                else:
                    print(f"❌ Ошибка: {response.status}")
                    
        except Exception as e:
            print(f"❌ Исключение: {e}")

if __name__ == "__main__":
    asyncio.run(detailed_html_analysis())
