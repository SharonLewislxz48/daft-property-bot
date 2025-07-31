#!/usr/bin/env python3
"""
Тест реальной ссылки daft.ie
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_real_link():
    """Тестируем реальную ссылку на объявление"""
    print("🔗 Тестируем реальную ссылку на объявление...")
    
    # Берем одну из найденных ссылок
    test_url = "https://www.daft.ie/for-rent/apartment-1-bed-apartment-eglinton-place-eglinton-road-dublin-4/5811432"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-IE,en;q=0.9',
        'Referer': 'https://www.daft.ie/'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            print(f"📋 Тестируем: {test_url}")
            
            async with session.get(test_url) as response:
                print(f"📊 Статус ответа: {response.status}")
                
                if response.status == 200:
                    content = await response.text()
                    print(f"✅ Страница загружена: {len(content)} символов")
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Извлекаем заголовок
                    title = soup.find('title')
                    if title:
                        print(f"📰 Заголовок: {title.get_text()}")
                    
                    # Ищем цену
                    price_elements = soup.find_all(text=lambda text: text and '€' in text)
                    if price_elements:
                        print(f"💰 Найдены цены: {price_elements[:3]}")
                    
                    # Проверяем что это реальная страница объявления
                    if 'apartment' in content.lower() or 'property' in content.lower():
                        print("✅ ПОДТВЕРЖДЕНО: Это реальная страница объявления!")
                        return True
                    else:
                        print("⚠️ Страница загружена, но не похожа на объявление")
                        return False
                        
                elif response.status == 404:
                    print("❌ 404 - Объявление не найдено (возможно удалено)")
                    return False
                else:
                    print(f"⚠️ Неожиданный статус: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_real_link())
    
    if success:
        print("\n🎉 ССЫЛКА РЕАЛЬНАЯ И РАБОТАЕТ!")
    else:
        print("\n⚠️ Проблемы со ссылкой")
