#!/usr/bin/env python3
"""
Простой тест соединения с daft.ie
"""
import asyncio
import aiohttp

async def test_connection():
    print("🌐 Тестируем соединение с daft.ie...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    
    urls_to_test = [
        "https://www.daft.ie",
        "https://www.daft.ie/property-for-rent/dublin",
        "https://daft.ie",
    ]
    
    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as session:
        for url in urls_to_test:
            try:
                print(f"\n🔗 Тестируем: {url}")
                
                async with session.get(url) as response:
                    print(f"📊 Статус: {response.status}")
                    print(f"🌐 URL после редиректов: {response.url}")
                    
                    if response.status == 200:
                        content = await response.text()
                        print(f"📄 Размер контента: {len(content)} символов")
                        
                        if 'daft' in content.lower():
                            print("✅ Содержимое выглядит как daft.ie")
                        else:
                            print("⚠️ Содержимое не похоже на daft.ie")
                    else:
                        print(f"❌ Ошибка: {response.status}")
                        
            except asyncio.TimeoutError:
                print(f"⏰ Таймаут для {url}")
            except Exception as e:
                print(f"❌ Ошибка для {url}: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
