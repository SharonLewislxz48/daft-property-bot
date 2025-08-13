#!/usr/bin/env python3
"""
Утилита для извлечения cookies Daft.ie из системного браузера
Обходит проблему блокировки Google OAuth в автоматизированных браузерах
"""

import sqlite3
import json
import os
import shutil
from pathlib import Path
import platform

def extract_chrome_cookies():
    """Извлечение cookies из Chrome/Chromium"""
    system = platform.system()
    
    if system == "Linux":
        chrome_paths = [
            Path.home() / ".config/google-chrome/Default/Cookies",
            Path.home() / ".config/chromium/Default/Cookies",
            Path.home() / "snap/chromium/common/chromium/Default/Cookies",
            Path.home() / ".config/google-chrome-beta/Default/Cookies"
        ]
    elif system == "Darwin":  # macOS
        chrome_paths = [
            Path.home() / "Library/Application Support/Google/Chrome/Default/Cookies",
            Path.home() / "Library/Application Support/Chromium/Default/Cookies"
        ]
    elif system == "Windows":
        chrome_paths = [
            Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Cookies",
            Path.home() / "AppData/Local/Chromium/User Data/Default/Cookies"
        ]
    else:
        print(f"❌ Неподдерживаемая система: {system}")
        return None
    
    for chrome_path in chrome_paths:
        if chrome_path.exists():
            try:
                print(f"🔍 Проверяем {chrome_path}")
                
                # Копируем файл cookies
                temp_cookies = "/tmp/temp_cookies.db"
                shutil.copy2(chrome_path, temp_cookies)
                
                conn = sqlite3.connect(temp_cookies)
                cursor = conn.cursor()
                
                # Извлекаем cookies для daft.ie
                cursor.execute("""
                    SELECT name, value, domain, path, expires_utc, is_secure, is_httponly
                    FROM cookies 
                    WHERE host_key LIKE '%daft.ie%'
                    ORDER BY creation_utc DESC
                """)
                
                rows = cursor.fetchall()
                conn.close()
                os.remove(temp_cookies)
                
                if rows:
                    cookies = []
                    for row in rows:
                        cookie = {
                            'name': row[0],
                            'value': row[1],
                            'domain': row[2] if row[2].startswith('.') else f".{row[2]}",
                            'path': row[3],
                            'expires': row[4] if row[4] > 0 else -1,
                            'secure': bool(row[5]),
                            'httpOnly': bool(row[6])
                        }
                        cookies.append(cookie)
                    
                    print(f"✅ Найдено {len(cookies)} cookies из {chrome_path}")
                    return cookies
                
            except Exception as e:
                print(f"❌ Ошибка обработки {chrome_path}: {e}")
                continue
    
    return None

def extract_firefox_cookies():
    """Извлечение cookies из Firefox"""
    try:
        system = platform.system()
        
        if system == "Linux":
            firefox_dir = Path.home() / ".mozilla/firefox"
        elif system == "Darwin":
            firefox_dir = Path.home() / "Library/Application Support/Firefox/Profiles"
        elif system == "Windows":
            firefox_dir = Path.home() / "AppData/Roaming/Mozilla/Firefox/Profiles"
        else:
            return None
        
        if not firefox_dir.exists():
            return None
        
        # Находим профиль по умолчанию
        profiles = list(firefox_dir.glob("*.default*"))
        if not profiles:
            profiles = list(firefox_dir.glob("*"))
        
        for profile in profiles:
            cookies_db = profile / "cookies.sqlite"
            if cookies_db.exists():
                try:
                    temp_cookies = "/tmp/temp_firefox_cookies.db"
                    shutil.copy2(cookies_db, temp_cookies)
                    
                    conn = sqlite3.connect(temp_cookies)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT name, value, host, path, expiry, isSecure, isHttpOnly
                        FROM moz_cookies 
                        WHERE host LIKE '%daft.ie%'
                        ORDER BY creationTime DESC
                    """)
                    
                    rows = cursor.fetchall()
                    conn.close()
                    os.remove(temp_cookies)
                    
                    if rows:
                        cookies = []
                        for row in rows:
                            cookie = {
                                'name': row[0],
                                'value': row[1],
                                'domain': row[2] if row[2].startswith('.') else f".{row[2]}",
                                'path': row[3],
                                'expires': row[4] if row[4] else -1,
                                'secure': bool(row[5]),
                                'httpOnly': bool(row[6])
                            }
                            cookies.append(cookie)
                        
                        print(f"✅ Найдено {len(cookies)} cookies из Firefox")
                        return cookies
                
                except Exception as e:
                    print(f"❌ Ошибка обработки Firefox cookies: {e}")
                    continue
        
        return None
        
    except Exception as e:
        print(f"❌ Ошибка извлечения Firefox cookies: {e}")
        return None

def save_cookies_for_automation(cookies):
    """Сохранение cookies для использования в автоматизации"""
    if not cookies:
        return False
    
    # Сохраняем в формате, понятном Playwright
    output_file = "daft_cookies.json"
    
    try:
        with open(output_file, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print(f"💾 Cookies сохранены в {output_file}")
        print(f"📊 Всего cookies: {len(cookies)}")
        
        # Показываем основные cookies
        auth_cookies = [c for c in cookies if 'auth' in c['name'].lower() or 'session' in c['name'].lower() or 'token' in c['name'].lower()]
        if auth_cookies:
            print("🔑 Найдены потенциальные cookies авторизации:")
            for cookie in auth_cookies[:3]:  # Показываем первые 3
                print(f"   - {cookie['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения cookies: {e}")
        return False

def main():
    """Основная функция"""
    print("🍪 Извлечение cookies Daft.ie из браузера")
    print("=" * 50)
    
    print("\n⚠️  ВАЖНО: Перед запуском этого скрипта:")
    print("1. Откройте Daft.ie в браузере")
    print("2. Войдите в свой аккаунт через Google")
    print("3. Убедитесь, что авторизация успешна")
    print("4. Закройте браузер")
    
    input("\nНажмите Enter когда будете готовы...")
    
    # Пробуем Chrome/Chromium
    print("\n🔍 Поиск cookies в Chrome/Chromium...")
    cookies = extract_chrome_cookies()
    
    if not cookies:
        print("\n🔍 Поиск cookies в Firefox...")
        cookies = extract_firefox_cookies()
    
    if cookies:
        success = save_cookies_for_automation(cookies)
        if success:
            print("\n🎉 Готово! Теперь можно запускать автоматизацию:")
            print("python3 telegram_daft_automation.py")
        else:
            print("\n❌ Не удалось сохранить cookies")
    else:
        print("\n❌ Cookies не найдены")
        print("\nВозможные причины:")
        print("- Вы не вошли в аккаунт Daft.ie")
        print("- Используется другой браузер")
        print("- Cookies были очищены")
        print("\nРешение:")
        print("1. Откройте браузер")
        print("2. Войдите на daft.ie через Google")
        print("3. Запустите скрипт снова")

if __name__ == "__main__":
    main()
