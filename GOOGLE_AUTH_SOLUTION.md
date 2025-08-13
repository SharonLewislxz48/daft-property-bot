# Решение проблемы с Google авторизацией на Daft.ie

## Проблема ❌
Google блокирует автоматизированные браузеры (Playwright/Selenium) с сообщением:
```
Возможно, этот браузер или приложение небезопасны. Подробнее…
Попробуйте сменить браузер. Если вы уже используете поддерживаемый браузер, повторите попытку входа ещё раз.
```

## Решения ✅

### 1. Автоматическое извлечение cookies (Рекомендуется)
```bash
python3 extract_cookies.py
```

**Пошаговая инструкция:**
1. Откройте обычный браузер (Chrome/Firefox)
2. Перейдите на https://www.daft.ie/login
3. Войдите через Google OAuth
4. Убедитесь, что авторизация успешна
5. Закройте браузер
6. Запустите `extract_cookies.py`
7. Cookies автоматически сохранятся для автоматизации

**Преимущества:**
- ✅ Полностью автоматический процесс
- ✅ Работает с Chrome, Chromium, Firefox
- ✅ Поддержка Linux/macOS/Windows
- ✅ Безопасное извлечение без ручного копирования

### 2. Улучшенный браузер с обходом детекции
Обновленный скрипт включает:
- Удаление webdriver property
- Настройка user-agent
- Отключение автоматизационных флагов
- Эмуляция обычного браузера

### 3. Fallback на внешний браузер
При блокировке автоматически предлагается:
- Открытие входа в системном браузере
- Импорт cookies из системного браузера
- Ручной ввод cookies при необходимости

### 4. Полный обход Google OAuth
Используйте только email/пароль:
- Выберите "Нет" при предложении Google
- Введите учетные данные Daft.ie напрямую
- Работает если у вас есть отдельный пароль для Daft.ie

## Диагностика и устранение неполадок

### Проверка cookies
```bash
# Проверить наличие cookies
ls -la daft_cookies.json

# Посмотреть содержимое cookies
python3 -c "import json; print(json.load(open('daft_cookies.json'))[:3])"

# Очистить cookies для нового извлечения
rm -f daft_cookies.json
```

### Проверка браузера
```bash
# Тест авторизации с диагностикой
python3 test_daft_login.py

# Просмотр скриншота страницы входа
xdg-open daft_login_page.png
```

### Ручное извлечение cookies
Если автоматическое извлечение не работает:

1. Откройте браузер и войдите на Daft.ie
2. Нажмите F12 → Application → Cookies → daft.ie
3. Скопируйте важные cookies (session, auth, token)
4. Запустите автоматизацию и вставьте при запросе

## Команды для быстрого решения

```bash
# Полная очистка и новое извлечение
rm -f daft_credentials.json daft_cookies.json
python3 extract_cookies.py
python3 telegram_daft_automation.py

# Тест без извлечения cookies
python3 test_daft_login.py

# Принудительное использование email/пароль
# (выберите "Нет" при вопросе о Google)
python3 telegram_daft_automation.py
```

## Технические детали

### Селекторы Google авторизации
Скрипт ищет следующие элементы:
```python
google_selectors = [
    'button:has-text("Google")',
    'button:has-text("Continue with Google")',
    '[data-testid="google-login"]',
    'button[class*="google"]',
    '.google-signin-button',
    'a[href*="google"]'
]
```

### Настройки браузера для обхода детекции
```python
args = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-extensions',
    '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
]
```

### Поддерживаемые браузеры для извлечения cookies
- ✅ Google Chrome
- ✅ Chromium  
- ✅ Firefox
- ✅ Chrome Beta
- ✅ Snap Chromium

**Проблема полностью решена с множественными fallback методами! 🎉**
