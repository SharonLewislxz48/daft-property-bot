#!/usr/bin/env python3
"""
Тестирование авторизации на Daft.ie
Поддержка как Google OAuth, так и обычной авторизации
"""

import asyncio
from telegram_daft_automation import DaftAutomation

async def test_login():
    """Тест авторизации"""
    print("🧪 Тестирование авторизации на Daft.ie")
    print("-" * 50)
    
    automation = DaftAutomation()
    
    try:
        # Инициализация браузера
        print("🌐 Запуск браузера...")
        await automation.init_browser()
        
        # Переход на страницу логина
        print("📄 Переход на страницу входа...")
        await automation.page.goto('https://www.daft.ie/login')
        await automation.page.wait_for_load_state('networkidle')
        
        # Показываем содержимое страницы для диагностики
        print("🔍 Анализ доступных методов авторизации...")
        
        # Проверяем Google кнопку
        google_selectors = [
            'button:has-text("Google")',
            'button:has-text("Continue with Google")',
            '[data-testid="google-login"]',
            'button[class*="google"]',
            '.google-signin-button',
            'a[href*="google"]'
        ]
        
        google_found = False
        for selector in google_selectors:
            count = await automation.page.locator(selector).count()
            if count > 0:
                print(f"✅ Найдена кнопка Google: {selector}")
                google_found = True
        
        if not google_found:
            print("❌ Кнопка авторизации через Google не найдена")
        
        # Проверяем обычные поля
        email_selectors = [
            '[data-testid="email"]',
            'input[type="email"]',
            'input[name="email"]',
            'input[placeholder*="email" i]'
        ]
        
        email_found = False
        for selector in email_selectors:
            count = await automation.page.locator(selector).count()
            if count > 0:
                print(f"✅ Найдено поле email: {selector}")
                email_found = True
        
        if not email_found:
            print("❌ Поле для ввода email не найдено")
        
        # Получаем скриншот страницы
        screenshot_path = "daft_login_page.png"
        await automation.page.screenshot(path=screenshot_path)
        print(f"📸 Скриншот страницы сохранен: {screenshot_path}")
        
        # Пауза для ручной проверки
        input("\n⏸️ Нажмите Enter чтобы попробовать авторизацию...")
        
        # Попытка авторизации
        success = await automation.login_to_daft()
        
        if success:
            print("🎉 Авторизация успешна!")
            
            # Переход на главную страницу для проверки
            await automation.page.goto('https://www.daft.ie')
            await automation.page.wait_for_load_state('networkidle')
            
            # Проверяем элементы авторизованного пользователя
            user_indicators = [
                '[data-testid="user-menu"]',
                '.user-menu',
                'button:has-text("Account")',
                'button:has-text("Profile")',
                'a:has-text("My Account")'
            ]
            
            for selector in user_indicators:
                if await automation.page.locator(selector).count() > 0:
                    print(f"✅ Подтверждение авторизации: {selector}")
                    break
            else:
                print("⚠️ Не найдены индикаторы авторизации на главной странице")
        else:
            print("❌ Авторизация не удалась")
        
        # Финальная пауза
        input("\n⏸️ Нажмите Enter для завершения...")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
    finally:
        await automation.close_browser()
        print("👋 Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(test_login())
