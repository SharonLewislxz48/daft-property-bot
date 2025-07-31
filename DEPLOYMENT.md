# 🚀 Deployment Guide - Daft.ie Property Bot

Подробное руководство по развертыванию бота на различных платформах.

## 📋 **Предварительные требования**

### 🔧 **Системные требования**
- **ОС**: Linux (Ubuntu 20.04+), macOS, Windows 10+
- **RAM**: Минимум 512MB, рекомендуется 1GB+
- **Диск**: 2GB свободного места
- **Сеть**: Стабильное интернет-соединение

### 📱 **Telegram Bot Token**
1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Укажите имя и username бота
4. Сохраните полученный токен

---

## 🐳 **Docker развертывание (Рекомендуется)**

### 🚀 **Быстрый старт**
```bash
# 1. Скачать проект
git clone <your-repo-url>
cd daftparser

# 2. Настроить токен
cp .env.example .env
nano .env  # Добавить TELEGRAM_TOKEN

# 3. Запустить
docker-compose up -d
```

### 🔧 **Детальная настройка**

#### 📝 **1. Конфигурация .env**
```bash
# Основные настройки
TELEGRAM_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
DATABASE_PATH=./data/enhanced_bot.db
LOG_LEVEL=INFO

# Продакшн настройки
BROWSER_HEADLESS=true
MAX_CONCURRENT_REQUESTS=3
REQUEST_DELAY=1.5
```

#### 🏗️ **2. Сборка и запуск**
```bash
# Сборка образа
docker-compose build

# Запуск в фоне
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f daftparser-bot
```

#### 🔄 **3. Управление**
```bash
# Рестарт
docker-compose restart

# Остановка
docker-compose down

# Обновление
git pull
docker-compose build --no-cache
docker-compose up -d
```

---

## 🐍 **Python развертывание**

### 🔧 **Автоматическая установка**
```bash
# Запустить скрипт установки
./install.sh

# Следовать инструкциям
```

### 🛠️ **Ручная установка**

#### 📦 **1. Создание виртуального окружения**
```bash
# Python 3.11+
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

#### 📚 **2. Установка зависимостей**
```bash
# Базовые зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Playwright браузер
playwright install chromium
```

#### ⚙️ **3. Настройка**
```bash
# Конфигурация
cp .env.example .env
nano .env

# Создание директорий
mkdir -p data logs
```

#### 🚀 **4. Запуск**
```bash
# Разработка
python3 main.py

# Продакшн с логированием
python3 main.py > logs/bot.log 2>&1 &
```

---

## ☁️ **Облачное развертывание**

### 🚀 **Railway**
```bash
# 1. Подключить GitHub репозиторий
# 2. Добавить переменные окружения:
TELEGRAM_TOKEN=your_token
PYTHONPATH=/app

# 3. Railway автоматически деплоит
```

### 🟣 **Heroku**
```bash
# Создать Procfile
echo "worker: python3 main.py" > Procfile

# Деплой
heroku create your-bot-name
heroku config:set TELEGRAM_TOKEN=your_token
git push heroku main
```

### 🌊 **DigitalOcean App Platform**
```yaml
# app.yaml
name: daftparser-bot
services:
- name: bot
  source_dir: /
  github:
    repo: your-username/daftparser
    branch: main
  run_command: python3 main.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: TELEGRAM_TOKEN
    value: your_token
```

---

## 🖥️ **VPS/Сервер развертывание**

### 🐧 **Ubuntu Server**

#### 🔧 **1. Подготовка системы**
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3 python3-pip python3-venv git docker.io docker-compose

# Настройка Docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

#### 📥 **2. Развертывание проекта**
```bash
# Клонирование
cd /opt
sudo git clone <your-repo> daftparser
sudo chown -R $USER:$USER daftparser
cd daftparser

# Настройка
cp .env.example .env
nano .env  # Добавить токен

# Запуск
docker-compose up -d
```

#### 🔄 **3. Автозапуск (systemd)**
```bash
# Копирование сервиса
sudo cp deploy/daftparser-bot.service /etc/systemd/system/

# Редактирование пути
sudo nano /etc/systemd/system/daftparser-bot.service
# Изменить WorkingDirectory=/opt/daftparser

# Включение автозапуска
sudo systemctl daemon-reload
sudo systemctl enable daftparser-bot
sudo systemctl start daftparser-bot

# Проверка статуса
sudo systemctl status daftparser-bot
```

### 🔐 **Nginx Reverse Proxy (для webhook)**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /webhook {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔐 **Безопасность**

### 🛡️ **Базовые меры**
```bash
# Firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Создание отдельного пользователя
sudo useradd -m -s /bin/bash botuser
sudo usermod -aG docker botuser

# Ограничение ресурсов Docker
# docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

### 🔑 **Переменные окружения**
```bash
# Никогда не коммитьте .env!
echo ".env" >> .gitignore

# Для продакшн используйте:
export TELEGRAM_TOKEN="your_token"
export DATABASE_PATH="/secure/path/bot.db"
```

---

## 📊 **Мониторинг**

### 📈 **Логирование**
```bash
# Просмотр логов Docker
docker-compose logs -f --tail=100

# Ротация логов
# docker-compose.yml:
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 🔔 **Алерты**
```bash
# Healthcheck в docker-compose.yml
healthcheck:
  test: ["CMD", "python3", "-c", "import requests; requests.get('http://localhost:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 📊 **Метрики**
```bash
# Системные ресурсы
docker stats daftparser_bot

# Размер базы данных
ls -lh data/enhanced_bot.db

# Логи ошибок
grep -i error logs/bot.log
```

---

## 🔄 **Обновление**

### 🐳 **Docker обновление**
```bash
# Обновление кода
git pull

# Пересборка и перезапуск
docker-compose build --no-cache
docker-compose up -d

# Проверка
docker-compose logs -f
```

### 🐍 **Python обновление**
```bash
# Обновление кода
git pull

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Рестарт сервиса
sudo systemctl restart daftparser-bot
```

---

## 🧪 **Тестирование**

### ✅ **Проверка развертывания**
```bash
# Тест импортов
make test

# Проверка конфигурации
python3 -c "
from config.settings import TELEGRAM_TOKEN
print('✅ Config OK' if TELEGRAM_TOKEN else '❌ No token')
"

# Тест подключения к Telegram
python3 -c "
import asyncio
from aiogram import Bot
from config.settings import TELEGRAM_TOKEN

async def test():
    bot = Bot(TELEGRAM_TOKEN)
    me = await bot.get_me()
    print(f'✅ Bot connected: @{me.username}')
    await bot.session.close()

asyncio.run(test())
"
```

---

## 🆘 **Траблшутинг**

### ❌ **Частые проблемы**

#### 🔐 **Неверный токен**
```
ERROR: Unauthorized
```
**Решение**: Проверить TELEGRAM_TOKEN в .env

#### 🌐 **Сетевые проблемы**
```
ERROR: Connection timeout
```
**Решение**: Проверить интернет, настроить прокси

#### 💾 **Проблемы с БД**
```
ERROR: Database locked
```
**Решение**: Остановить все процессы, проверить права доступа

#### 🎭 **Playwright ошибки**
```
ERROR: Browser not found
```
**Решение**: `playwright install chromium`

### 📞 **Получение помощи**
- 📚 Проверить [USER_GUIDE.md](USER_GUIDE.md)
- 🐛 Создать Issue на GitHub
- 📝 Приложить логи и конфигурацию

---

**🎉 Успешного развертывания! 🏠🇮🇪**
