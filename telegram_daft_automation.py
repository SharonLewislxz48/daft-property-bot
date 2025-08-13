#!/usr/bin/env python3
"""
Автоматизация отправки заявок на объявления Daft.ie из Telegram
Использует Playwright для веб-автоматизации и pyautogui для работы с Telegram
"""

import asyncio
import re
import time
import json
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

import pyautogui
import pyperclip
from playwright.async_api import async_playwright, Page, Browser
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import requests
from io import BytesIO

@dataclass
class PropertyListing:
    """Данные об объявлении недвижимости"""
    title: str
    address: str
    price: str
    bedrooms: str
    url: str
    user: str

class DaftAutomation:
    """Класс для автоматизации работы с Daft.ie"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.credentials_file = "daft_credentials.json"
        self.cookies_file = "daft_cookies.json"
        
    async def init_browser(self):
        """Инициализация браузера"""
        self.playwright = await async_playwright().start()
        
        # Настройки для обхода защиты Google
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Показываем браузер для контроля
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions-except',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        # Создаем контекст с дополнительными настройками
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='Europe/Dublin'
        )
        
        # Удаляем webdriver property для обхода детекции
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Переопределяем plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Переопределяем languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        self.page = await context.new_page()
        
        # Загружаем cookies если есть
        await self.load_cookies()
        
    async def close_browser(self):
        """Закрытие браузера"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def load_cookies(self):
        """Загрузка сохраненных cookies"""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                await self.page.context.add_cookies(cookies)
                print("✅ Cookies загружены")
            except Exception as e:
                print(f"❌ Ошибка загрузки cookies: {e}")
    
    async def save_cookies(self):
        """Сохранение cookies"""
        try:
            cookies = await self.page.context.cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            print("✅ Cookies сохранены")
        except Exception as e:
            print(f"❌ Ошибка сохранения cookies: {e}")
    
    def load_credentials(self) -> Optional[Dict[str, str]]:
        """Загрузка учетных данных"""
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Ошибка загрузки credentials: {e}")
        return None
    
    def save_credentials(self, email: str, password: str):
        """Сохранение учетных данных"""
        try:
            credentials = {"email": email, "password": password}
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f)
            print("✅ Учетные данные сохранены")
        except Exception as e:
            print(f"❌ Ошибка сохранения credentials: {e}")
    
    async def login_to_daft(self) -> bool:
        """Вход в аккаунт Daft.ie"""
        try:
            # Переходим на страницу входа
            await self.page.goto('https://www.daft.ie/login')
            await self.page.wait_for_load_state('networkidle')
            
            # Проверяем, не залогинены ли уже
            if await self.page.locator('[data-testid="user-menu"]').count() > 0:
                print("✅ Уже авторизованы")
                return True
            
            # Проверяем доступные методы авторизации
            google_button_selectors = [
                'button:has-text("Google")',
                'button:has-text("Continue with Google")',
                '[data-testid="google-login"]',
                'button[class*="google"]',
                '.google-signin-button'
            ]
            
            # Ищем кнопку входа через Google
            google_button = None
            for selector in google_button_selectors:
                if await self.page.locator(selector).count() > 0:
                    google_button = self.page.locator(selector).first
                    break
            
            # Если есть кнопка Google, предлагаем выбор
            if google_button:
                auth_method = messagebox.askyesnocancel(
                    "Метод авторизации",
                    "Найдена авторизация через Google.\n\n"
                    "Да - войти через Google\n"
                    "Нет - войти через email/пароль\n"
                    "Отмена - пропустить авторизацию"
                )
                
                if auth_method is None:  # Отмена
                    return False
                elif auth_method:  # Да - Google
                    return await self._login_with_google(google_button)
                # Нет - продолжаем с обычной авторизацией
            
            # Обычная авторизация через email/пароль
            return await self._login_with_email_password()
            
        except Exception as e:
            print(f"❌ Ошибка входа в Daft.ie: {e}")
            return False
    
    async def _login_with_google(self, google_button) -> bool:
        """Авторизация через Google"""
        try:
            print("🔑 Авторизация через Google...")
            
            # Показываем предупреждение о Google блокировке
            choice = messagebox.askyesnocancel(
                "Авторизация через Google",
                "Google может блокировать автоматизированные браузеры.\n\n"
                "Да - Попробовать автоматическую авторизацию\n"
                "Нет - Открыть в обычном браузере\n"
                "Отмена - Пропустить авторизацию"
            )
            
            if choice is None:  # Отмена
                return False
            elif choice is False:  # Нет - обычный браузер
                return await self._login_with_external_browser()
            
            # Да - пробуем автоматическую авторизацию
            await google_button.click()
            
            # Ждем перенаправления
            await self.page.wait_for_timeout(3000)
            
            # Проверяем, не заблокировал ли Google
            page_content = await self.page.content()
            if "небезопасн" in page_content.lower() or "unsafe" in page_content.lower() or "blocked" in page_content.lower():
                print("❌ Google заблокировал автоматизированный браузер")
                messagebox.showwarning(
                    "Google блокировка",
                    "Google заблокировал автоматизированный браузер.\n"
                    "Попробуем альтернативный метод..."
                )
                return await self._login_with_external_browser()
            
            # Показываем инструкцию пользователю
            messagebox.showinfo(
                "Авторизация через Google",
                "Завершите авторизацию через Google в браузере.\n\n"
                "После успешной авторизации нажмите OK."
            )
            
            # Ждем возвращения на Daft.ie
            max_attempts = 60  # 60 секунд ожидания
            for attempt in range(max_attempts):
                await self.page.wait_for_timeout(1000)
                
                current_url = self.page.url
                if 'daft.ie' in current_url:
                    if await self.page.locator('[data-testid="user-menu"]').count() > 0:
                        print("✅ Успешная авторизация через Google")
                        await self.save_cookies()
                        return True
            
            print("⏱️ Таймаут авторизации через Google")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка авторизации через Google: {e}")
            return await self._login_with_external_browser()
    
    async def _login_with_external_browser(self) -> bool:
        """Авторизация через внешний браузер"""
        try:
            print("🌐 Открытие авторизации в обычном браузере...")
            
            # Открываем страницу входа в системном браузере
            import webbrowser
            webbrowser.open('https://www.daft.ie/login')
            
            messagebox.showinfo(
                "Авторизация в браузере",
                "1. Войдите в аккаунт Daft.ie в открывшемся браузере\n"
                "2. После успешного входа скопируйте cookies\n"
                "3. Нажмите OK когда будете готовы"
            )
            
            # Предлагаем импорт cookies из системного браузера
            import_cookies = messagebox.askyesno(
                "Импорт cookies",
                "Попробовать автоматически импортировать cookies из Chrome/Firefox?"
            )
            
            if import_cookies:
                success = await self._import_system_cookies()
                if success:
                    return True
            
            # Ручной ввод cookies
            cookie_string = simpledialog.askstring(
                "Ввод cookies",
                "Скопируйте cookies из браузера\n"
                "(F12 -> Application -> Cookies -> daft.ie):",
                show='*'
            )
            
            if cookie_string:
                success = await self._parse_and_set_cookies(cookie_string)
                if success:
                    print("✅ Cookies успешно импортированы")
                    return True
            
            print("❌ Не удалось импортировать cookies")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка авторизации через внешний браузер: {e}")
            return False
    
    async def _import_system_cookies(self) -> bool:
        """Импорт cookies из системного браузера"""
        try:
            # Попытка импорта из Chrome
            import sqlite3
            import os
            from pathlib import Path
            
            chrome_paths = [
                Path.home() / ".config/google-chrome/Default/Cookies",
                Path.home() / ".config/chromium/Default/Cookies",
                Path.home() / "snap/chromium/common/chromium/Default/Cookies"
            ]
            
            for chrome_path in chrome_paths:
                if chrome_path.exists():
                    try:
                        # Копируем файл cookies (Chrome блокирует прямой доступ)
                        temp_cookies = "/tmp/temp_cookies.db"
                        import shutil
                        shutil.copy2(chrome_path, temp_cookies)
                        
                        conn = sqlite3.connect(temp_cookies)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT name, value, domain, path, expires_utc, is_secure, is_httponly
                            FROM cookies 
                            WHERE host_key LIKE '%daft.ie%'
                        """)
                        
                        rows = cursor.fetchall()
                        if rows:
                            cookies = []
                            for row in rows:
                                cookie = {
                                    'name': row[0],
                                    'value': row[1],
                                    'domain': row[2],
                                    'path': row[3],
                                    'expires': row[4],
                                    'secure': bool(row[5]),
                                    'httpOnly': bool(row[6])
                                }
                                cookies.append(cookie)
                            
                            await self.page.context.add_cookies(cookies)
                            conn.close()
                            os.remove(temp_cookies)
                            
                            # Проверяем авторизацию
                            await self.page.goto('https://www.daft.ie')
                            await self.page.wait_for_load_state('networkidle')
                            
                            if await self.page.locator('[data-testid="user-menu"]').count() > 0:
                                await self.save_cookies()
                                return True
                        
                        conn.close()
                        os.remove(temp_cookies)
                        
                    except Exception as e:
                        print(f"Ошибка импорта из {chrome_path}: {e}")
                        continue
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка импорта системных cookies: {e}")
            return False
    
    async def _parse_and_set_cookies(self, cookie_string: str) -> bool:
        """Парсинг и установка cookies из строки"""
        try:
            # Простой парсинг cookies в формате "name=value; name2=value2"
            cookies = []
            
            for cookie_pair in cookie_string.split(';'):
                cookie_pair = cookie_pair.strip()
                if '=' in cookie_pair:
                    name, value = cookie_pair.split('=', 1)
                    cookies.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.daft.ie',
                        'path': '/'
                    })
            
            if cookies:
                await self.page.context.add_cookies(cookies)
                
                # Проверяем авторизацию
                await self.page.goto('https://www.daft.ie')
                await self.page.wait_for_load_state('networkidle')
                
                if await self.page.locator('[data-testid="user-menu"]').count() > 0:
                    await self.save_cookies()
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка парсинга cookies: {e}")
            return False
    
    async def _login_with_email_password(self) -> bool:
        """Обычная авторизация через email/пароль"""
        try:
            # Проверяем наличие полей для ввода
            email_selectors = [
                '[data-testid="email"]',
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email" i]'
            ]
            
            password_selectors = [
                '[data-testid="password"]',
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password" i]'
            ]
            
            submit_selectors = [
                '[data-testid="sign-in"]',
                'button[type="submit"]',
                'button:has-text("Sign in")',
                'button:has-text("Login")',
                'button:has-text("Log in")'
            ]
            
            # Находим поля ввода
            email_field = None
            for selector in email_selectors:
                if await self.page.locator(selector).count() > 0:
                    email_field = self.page.locator(selector).first
                    break
            
            password_field = None
            for selector in password_selectors:
                if await self.page.locator(selector).count() > 0:
                    password_field = self.page.locator(selector).first
                    break
            
            submit_button = None
            for selector in submit_selectors:
                if await self.page.locator(selector).count() > 0:
                    submit_button = self.page.locator(selector).first
                    break
            
            if not email_field or not password_field:
                print("❌ Не найдены поля для ввода email/пароля")
                return False
            
            # Загружаем или запрашиваем учетные данные
            credentials = self.load_credentials()
            if not credentials:
                email = simpledialog.askstring("Вход в Daft.ie", "Введите email:")
                password = simpledialog.askstring("Вход в Daft.ie", "Введите пароль:", show='*')
                if not email or not password:
                    return False
                self.save_credentials(email, password)
                credentials = {"email": email, "password": password}
            
            # Заполняем форму входа
            await email_field.fill(credentials['email'])
            await password_field.fill(credentials['password'])
            
            if submit_button:
                await submit_button.click()
            else:
                # Пробуем нажать Enter
                await password_field.press('Enter')
            
            # Ожидаем успешного входа
            user_menu_selectors = [
                '[data-testid="user-menu"]',
                '.user-menu',
                '[data-testid="account-menu"]',
                'button:has-text("Account")',
                'button:has-text("Profile")'
            ]
            
            for selector in user_menu_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    print("✅ Успешный вход через email/пароль")
                    await self.save_cookies()
                    return True
                except:
                    continue
            
            print("❌ Не удалось подтвердить успешный вход")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка входа через email/пароль: {e}")
            return False
    
    async def open_property_listing(self, url: str) -> bool:
        """Открытие объявления в браузере"""
        try:
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            
            # Проверяем, что страница загрузилась корректно
            title_selector = '[data-testid="address"]'
            if await self.page.locator(title_selector).count() > 0:
                print(f"✅ Объявление открыто: {url}")
                return True
            else:
                print(f"❌ Не удалось загрузить объявление: {url}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка открытия объявления: {e}")
            return False
    
    async def send_application(self) -> bool:
        """Отправка заявки на объявление"""
        try:
            # Ищем кнопку "Contact Agent" или "Apply"
            contact_selectors = [
                '[data-testid="contact-agent-button"]',
                'button:has-text("Contact")',
                'button:has-text("Apply")',
                'button:has-text("Get in touch")',
                '[data-testid="email-agent"]'
            ]
            
            contact_button = None
            for selector in contact_selectors:
                if await self.page.locator(selector).count() > 0:
                    contact_button = self.page.locator(selector).first
                    break
            
            if not contact_button:
                print("❌ Не найдена кнопка для отправки заявки")
                return False
            
            # Кликаем по кнопке
            await contact_button.click()
            await self.page.wait_for_timeout(2000)
            
            # Ищем форму для отправки сообщения
            message_selectors = [
                '[data-testid="message-textarea"]',
                'textarea[name="message"]',
                'textarea[placeholder*="message"]',
                'textarea'
            ]
            
            message_field = None
            for selector in message_selectors:
                if await self.page.locator(selector).count() > 0:
                    message_field = self.page.locator(selector).first
                    break
            
            if message_field:
                # Заполняем сообщение
                default_message = """Hello,

I am very interested in this property and would like to arrange a viewing at your earliest convenience. I am a reliable tenant with good references.

Please let me know when would be a good time for a viewing.

Best regards"""
                
                await message_field.fill(default_message)
                await self.page.wait_for_timeout(1000)
                
                # Ищем кнопку отправки
                send_selectors = [
                    'button:has-text("Send")',
                    'button:has-text("Submit")',
                    'button[type="submit"]',
                    '[data-testid="send-message"]'
                ]
                
                for selector in send_selectors:
                    if await self.page.locator(selector).count() > 0:
                        await self.page.locator(selector).first.click()
                        await self.page.wait_for_timeout(3000)
                        print("✅ Заявка отправлена")
                        return True
            
            print("❌ Не удалось найти форму для отправки заявки")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка отправки заявки: {e}")
            return False

class TelegramScanner:
    """Класс для сканирования сообщений в Telegram"""
    
    def __init__(self, chat_name: str = "Ирландия полная хуйня, уезжайте от сюда"):
        self.chat_name = chat_name
        self.property_pattern = re.compile(
            r'🏠\s+(.+?)\n\n📍\s+Адрес:\s+(.+?)\n💰\s+Цена:\s+(.+?)\n🛏️\s+Спальни:\s+(.+?)\n\n🔗\s+.*?\((https://www\.daft\.ie/[^)]+)\)\s*\n\n👤\s+От пользователя:\s+(.+)',
            re.MULTILINE | re.DOTALL
        )
    
    def parse_property_message(self, text: str) -> Optional[PropertyListing]:
        """Парсинг сообщения с объявлением"""
        match = self.property_pattern.search(text)
        if match:
            return PropertyListing(
                title=match.group(1).strip(),
                address=match.group(2).strip(),
                price=match.group(3).strip(),
                bedrooms=match.group(4).strip(),
                url=match.group(5).strip(),
                user=match.group(6).strip()
            )
        return None
    
    def get_selected_text(self) -> Optional[str]:
        """Получение выделенного текста из Telegram"""
        try:
            # Копируем выделенный текст
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            return pyperclip.paste()
        except Exception as e:
            print(f"❌ Ошибка получения текста: {e}")
            return None

class PropertyConfirmationDialog:
    """Диалог подтверждения для отправки заявки"""
    
    def __init__(self, property_listing: PropertyListing):
        self.property = property_listing
        self.result = False
        self.root = None
    
    def show_confirmation(self) -> bool:
        """Показ диалога подтверждения"""
        self.root = tk.Tk()
        self.root.title("Подтверждение отправки заявки")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Центрирование окна
        self.root.geometry("+{}+{}".format(
            (self.root.winfo_screenwidth() // 2) - 300,
            (self.root.winfo_screenheight() // 2) - 250
        ))
        
        # Информация об объявлении
        info_frame = tk.Frame(self.root, bg='white', relief='ridge', bd=2)
        info_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(info_frame, text="🏠 Объявление недвижимости", 
                font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
        
        # Детали объявления
        details = [
            ("🏠 Название:", self.property.title),
            ("📍 Адрес:", self.property.address),
            ("💰 Цена:", self.property.price),
            ("🛏️ Спальни:", self.property.bedrooms),
            ("👤 От пользователя:", self.property.user),
            ("🔗 URL:", self.property.url)
        ]
        
        for label, value in details:
            frame = tk.Frame(info_frame, bg='white')
            frame.pack(fill='x', padx=20, pady=5)
            
            tk.Label(frame, text=label, font=('Arial', 10, 'bold'), 
                    bg='white', anchor='w').pack(side='left')
            tk.Label(frame, text=value, font=('Arial', 10), 
                    bg='white', anchor='w', wraplength=400).pack(side='left', padx=(10, 0))
        
        # Кнопки
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="✅ Да, отправить заявку", 
                 command=self._on_yes, bg='#4CAF50', fg='white',
                 font=('Arial', 12, 'bold'), padx=20, pady=10).pack(side='left', padx=10)
        
        tk.Button(button_frame, text="❌ Нет, пропустить", 
                 command=self._on_no, bg='#f44336', fg='white',
                 font=('Arial', 12, 'bold'), padx=20, pady=10).pack(side='left', padx=10)
        
        tk.Button(button_frame, text="🌐 Открыть в браузере", 
                 command=self._open_browser, bg='#2196F3', fg='white',
                 font=('Arial', 12, 'bold'), padx=20, pady=10).pack(side='left', padx=10)
        
        # Запуск диалога
        self.root.protocol("WM_DELETE_WINDOW", self._on_no)
        self.root.mainloop()
        
        return self.result
    
    def _on_yes(self):
        """Обработчик кнопки 'Да'"""
        self.result = True
        self.root.destroy()
    
    def _on_no(self):
        """Обработчик кнопки 'Нет'"""
        self.result = False
        self.root.destroy()
    
    def _open_browser(self):
        """Открытие ссылки в браузере"""
        import webbrowser
        webbrowser.open(self.property.url)

async def main():
    """Основная функция"""
    print("🚀 Запуск автоматизации Daft.ie")
    print("📝 Инструкция:")
    print("1. Откройте Telegram и найдите нужный чат")
    print("2. Выделите сообщение с объявлением")
    print("3. Нажмите Enter в этом терминале")
    print("4. Следуйте инструкциям в диалоговых окнах")
    print("-" * 50)
    
    # Инициализация компонентов
    scanner = TelegramScanner()
    automation = DaftAutomation()
    
    try:
        # Инициализация браузера
        await automation.init_browser()
        
        # Попытка входа в аккаунт
        print("🔐 Проверка авторизации...")
        login_success = await automation.login_to_daft()
        if not login_success:
            print("⚠️ Авторизация пропущена или не удалась")
            print("💡 Вы сможете просматривать объявления, но отправка заявок может быть ограничена")
            
            continue_without_login = messagebox.askyesno(
                "Продолжить без авторизации?",
                "Авторизация не выполнена.\n\n"
                "Продолжить работу без авторизации?\n"
                "(Функциональность может быть ограничена)"
            )
            
            if not continue_without_login:
                return
        else:
            print("✅ Авторизация успешна")
        
        while True:
            input("\n🔍 Выделите сообщение в Telegram и нажмите Enter...")
            
            # Получение текста из Telegram
            text = scanner.get_selected_text()
            if not text:
                print("❌ Не удалось получить текст. Попробуйте еще раз.")
                continue
            
            # Парсинг объявления
            property_listing = scanner.parse_property_message(text)
            if not property_listing:
                print("❌ Сообщение не содержит объявление о недвижимости")
                print("Полученный текст:")
                print(text[:200] + "..." if len(text) > 200 else text)
                continue
            
            print(f"✅ Найдено объявление: {property_listing.title}")
            
            # Открытие объявления в браузере
            if not await automation.open_property_listing(property_listing.url):
                print("❌ Не удалось открыть объявление")
                continue
            
            # Показ диалога подтверждения
            dialog = PropertyConfirmationDialog(property_listing)
            if dialog.show_confirmation():
                print("📤 Отправка заявки...")
                
                if await automation.send_application():
                    print("🎉 Заявка успешно отправлена!")
                    messagebox.showinfo("Успех", "Заявка успешно отправлена!")
                else:
                    print("❌ Не удалось отправить заявку")
                    messagebox.showerror("Ошибка", "Не удалось отправить заявку")
            else:
                print("⏭️ Заявка пропущена")
            
            # Спрашиваем о продолжении
            continue_work = messagebox.askyesno("Продолжить", "Обработать еще одно объявление?")
            if not continue_work:
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Остановка по запросу пользователя")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
    finally:
        await automation.close_browser()
        print("👋 Работа завершена")

if __name__ == "__main__":
    # Проверка зависимостей
    try:
        import pyautogui
        import pyperclip
        import tkinter
        from playwright.async_api import async_playwright
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("📦 Установите зависимости:")
        print("pip install playwright pyautogui pyperclip pillow requests")
        print("playwright install chromium")
        exit(1)
    
    # Запуск
    asyncio.run(main())
