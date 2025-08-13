#!/bin/bash
# Скрипт установки зависимостей для автоматизации Daft.ie

echo "🚀 Установка зависимостей для автоматизации Daft.ie"
echo "=================================================="

# Проверка Ubuntu
if [[ ! -f /etc/lsb-release ]]; then
    echo "❌ Этот скрипт предназначен для Ubuntu"
    exit 1
fi

# Обновление системы
echo "📦 Обновление системы..."
sudo apt-get update

# Установка системных зависимостей
echo "🔧 Установка системных пакетов..."
sudo apt-get install -y \
    python3-pip \
    python3-tk \
    python3-dev \
    scrot \
    xsel \
    xclip \
    build-essential \
    libx11-dev \
    libxtst6 \
    libxrandr2 \
    libasound2-dev \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0

# Установка Python зависимостей
echo "🐍 Установка Python пакетов..."
pip3 install --user \
    playwright \
    pyautogui \
    pyperclip \
    pillow \
    requests

# Установка браузера для Playwright
echo "🌐 Установка Chromium для Playwright..."
python3 -m playwright install chromium
python3 -m playwright install-deps chromium

# Проверка установки
echo "✅ Проверка установки..."

# Проверка Python пакетов
python3 -c "
try:
    import playwright
    import pyautogui
    import pyperclip
    import PIL
    import requests
    import tkinter
    print('✅ Все Python пакеты установлены успешно')
except ImportError as e:
    print(f'❌ Ошибка импорта: {e}')
    exit(1)
"

# Проверка браузера
python3 -c "
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        browser.close()
    print('✅ Chromium работает корректно')
except Exception as e:
    print(f'❌ Ошибка Chromium: {e}')
"

# Настройка окружения
echo "⚙️ Настройка окружения..."

# Добавление переменных окружения
if ! grep -q "DISPLAY=:0" ~/.bashrc; then
    echo 'export DISPLAY=:0' >> ~/.bashrc
fi

# Создание директории для скриншотов
mkdir -p ~/screenshots

# Настройка прав доступа
sudo usermod -a -G input $USER

echo ""
echo "🎉 Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Перезагрузите систему или выполните: source ~/.bashrc"
echo "2. Убедитесь, что Telegram Desktop установлен и запущен"
echo "3. Запустите скрипт: python3 telegram_daft_automation.py"
echo ""
echo "⚠️ Важно:"
echo "- Убедитесь, что вы работаете в графическом окружении (не SSH)"
echo "- Telegram должен быть открыт на рабочем столе"
echo "- При первом запуске введите учетные данные Daft.ie"
echo ""
echo "🔧 Если возникнут проблемы:"
echo "- Проверьте DISPLAY: echo \$DISPLAY"
echo "- Перезагрузите систему"
echo "- Запустите: playwright install chromium"
