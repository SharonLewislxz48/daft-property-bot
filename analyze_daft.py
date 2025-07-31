#!/usr/bin/env python3
"""
Анализатор структуры страницы daft.ie для поиска реальных объявлений
"""
import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
import re

async def analyze_daft_structure():
    """Анализ структуры страницы daft.ie"""
    print("🔍 Анализируем структуру страницы daft.ie...")
    
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
                    
                    # Анализируем script теги
                    print("\n📄 Анализ script тегов:")
                    scripts = soup.find_all('script')
                    for i, script in enumerate(scripts[:10]):  # Первые 10
                        script_content = script.string or ""
                        if len(script_content) > 100:
                            print(f"Script {i+1}: {len(script_content)} символов")
                            
                            # Ищем упоминания о недвижимости
                            if any(keyword in script_content.lower() for keyword in ['property', 'listing', 'rent', 'apartment']):
                                print(f"  ✅ Содержит данные о недвижимости")
                                
                                # Показываем начало контента
                                print(f"  Начало: {script_content[:200]}...")
                                
                                # Ищем JSON структуры
                                json_patterns = [
                                    r'window\.__NEXT_DATA__\s*=\s*({.+?});',
                                    r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                                    r'"listings":\s*\[',
                                    r'"properties":\s*\[',
                                    r'"results":\s*\['
                                ]
                                
                                for pattern in json_patterns:
                                    matches = re.findall(pattern, script_content)
                                    if matches:
                                        print(f"  🎯 Найден паттерн: {pattern}")
                    
                    # Анализируем ссылки
                    print("\n🔗 Анализ ссылок:")
                    links = soup.find_all('a', href=True)
                    property_links = []
                    
                    for link in links:
                        href = link.get('href', '')
                        if '/for-rent/' in href and any(word in href for word in ['apartment', 'house', 'studio']):
                            full_url = href if href.startswith('http') else f"https://www.daft.ie{href}"
                            property_links.append(full_url)
                    
                    print(f"Найдено {len(property_links)} ссылок на объявления:")
                    for i, link in enumerate(property_links[:5]):
                        print(f"  {i+1}. {link}")
                    
                    # Анализируем data-testid атрибуты
                    print("\n🏷️ Анализ data-testid атрибутов:")
                    testid_elements = soup.find_all(attrs={"data-testid": True})
                    for elem in testid_elements[:10]:
                        testid = elem.get('data-testid')
                        if 'property' in testid.lower() or 'listing' in testid.lower():
                            print(f"  ✅ {testid}: {elem.name}")
                    
                    # Анализируем классы
                    print("\n🎨 Анализ CSS классов:")
                    all_elements = soup.find_all(class_=True)
                    property_classes = set()
                    
                    for elem in all_elements:
                        classes = elem.get('class', [])
                        for cls in classes:
                            if any(keyword in cls.lower() for keyword in ['property', 'listing', 'card', 'item']):
                                property_classes.add(cls)
                    
                    print(f"Найдено {len(property_classes)} классов связанных с недвижимостью:")
                    for cls in list(property_classes)[:10]:
                        print(f"  • {cls}")
                    
                    return True
                    
                else:
                    print(f"❌ Ошибка: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(analyze_daft_structure())
