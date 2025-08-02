# 🚀 Развертывание Enhanced Bot v2.0 на сервере

## 📋 Варианты развертывания

### 1. 🔧 Прямое развертывание на сервере (рекомендуется)

#### Быстрое развертывание одной командой:
```bash
curl -fsSL https://raw.githubusercontent.com/SharonLewislxz48/daft-property-bot/enhanced-bot-v2.0/deploy_server.sh | sudo bash -s production
```

#### Пошаговое развертывание:

1. **Подготовка сервера**:
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Git
sudo apt install -y git curl

# Клонирование репозитория
git clone -b enhanced-bot-v2.0 https://github.com/SharonLewislxz48/daft-property-bot.git
cd daft-property-bot
```

2. **Запуск скрипта развертывания**:
```bash
chmod +x deploy_server.sh
sudo ./deploy_server.sh production
```

3. **Настройка конфигурации**:
```bash
# Редактирование конфигурации
sudo nano /opt/daft-property-bot/bot_config.json

# Добавьте ваш telegram bot_token и настройки
```

4. **Перезапуск после настройки**:
```bash
sudo systemctl restart daftbot
sudo systemctl status daftbot
```

### 2. 🐳 Docker развертывание

#### Требования:
- Docker и Docker Compose установлены на сервере

#### Развертывание:
```bash
# Клонирование репозитория
git clone -b enhanced-bot-v2.0 https://github.com/SharonLewislxz48/daft-property-bot.git
cd daft-property-bot

# Настройка конфигурации
cp bot_config_production.json bot_config.json
nano bot_config.json  # Добавьте ваш bot_token

# Создание директорий
mkdir -p data logs

# Запуск через Docker Compose
docker-compose -f docker-compose.enhanced.yml up -d

# Проверка статуса
docker-compose -f docker-compose.enhanced.yml ps
docker-compose -f docker-compose.enhanced.yml logs -f
```

## 📊 Управление ботом

### Systemd сервис (прямое развертывание):
```bash
# Статус сервиса
sudo systemctl status daftbot

# Запуск/остановка/перезапуск
sudo systemctl start daftbot
sudo systemctl stop daftbot
sudo systemctl restart daftbot

# Просмотр логов
sudo journalctl -u daftbot -f

# Быстрое управление
manage-daftbot status
manage-daftbot restart
manage-daftbot logs
manage-daftbot update
```

### Docker (контейнерное развертывание):
```bash
# Статус контейнера
docker-compose -f docker-compose.enhanced.yml ps

# Запуск/остановка/перезапуск
docker-compose -f docker-compose.enhanced.yml up -d
docker-compose -f docker-compose.enhanced.yml down
docker-compose -f docker-compose.enhanced.yml restart

# Просмотр логов
docker-compose -f docker-compose.enhanced.yml logs -f

# Обновление
docker-compose -f docker-compose.enhanced.yml pull
docker-compose -f docker-compose.enhanced.yml up -d --force-recreate
```

## 🔧 Конфигурация

### Основные настройки в `bot_config.json`:
```json
{
    "telegram": {
        "bot_token": "YOUR_BOT_TOKEN_HERE",
        "group_id": -1002819366953
    },
    "parser": {
        "max_pages": 3,
        "max_results": 100,
        "duplicate_filter_hours": 24
    },
    "limits": {
        "telegram_delay_seconds": 3
    }
}
```

## 📍 Пути и файлы

### Прямое развертывание:
- **Приложение**: `/opt/daft-property-bot/`
- **База данных**: `/opt/daft-property-bot/data/enhanced_bot.db`
- **Логи**: `/opt/daft-property-bot/logs/enhanced_bot.log`
- **Конфигурация**: `/opt/daft-property-bot/bot_config.json`
- **Сервис**: `systemctl status daftbot`

### Docker развертывание:
- **Данные**: `./data/enhanced_bot.db`
- **Логи**: `./logs/enhanced_bot.log`
- **Конфигурация**: `./bot_config.json`
- **Контейнер**: `docker ps | grep daft-property-bot`

## 🔍 Мониторинг и отладка

### Проверка работы бота:
```bash
# Проверка процесса
ps aux | grep enhanced_main

# Проверка логов
tail -f /opt/daft-property-bot/logs/enhanced_bot.log

# Проверка базы данных
sqlite3 /opt/daft-property-bot/data/enhanced_bot.db ".tables"
```

### Типичные проблемы:

1. **Бот не запускается**:
   - Проверьте bot_token в конфигурации
   - Проверьте логи: `sudo journalctl -u daftbot -n 50`

2. **Ошибки парсинга**:
   - Проверьте доступность интернета
   - Проверьте работу Playwright: `playwright --version`

3. **Проблемы с базой данных**:
   - Проверьте права доступа к директории `data/`
   - Проверьте целостность БД: `sqlite3 data/enhanced_bot.db "PRAGMA integrity_check;"`

## 🔄 Обновление

### Автоматическое обновление:
```bash
# Прямое развертывание
manage-daftbot update

# Docker
docker-compose -f docker-compose.enhanced.yml pull
docker-compose -f docker-compose.enhanced.yml up -d --force-recreate
```

### Ручное обновление:
```bash
# Остановка сервиса
sudo systemctl stop daftbot

# Обновление кода
cd /opt/daft-property-bot
sudo -u daftbot git pull origin enhanced-bot-v2.0

# Обновление зависимостей
sudo -u daftbot .venv/bin/pip install -r requirements.txt

# Запуск сервиса
sudo systemctl start daftbot
```

## 🔐 Безопасность (для продакшена)

```bash
# Настройка файрвола
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Создание бэкапов
crontab -e
# Добавить: 0 2 * * * cp /opt/daft-property-bot/data/enhanced_bot.db /backup/enhanced_bot_$(date +\%Y\%m\%d).db

# Мониторинг ресурсов
sudo apt install htop iotop
```

## ✅ Проверка успешного развертывания

1. Бот отвечает на команду `/start` в Telegram
2. Сервис активен: `systemctl is-active daftbot`
3. Логи не содержат критических ошибок
4. База данных содержит таблицы: `sqlite3 data/enhanced_bot.db ".tables"`
5. Парсер работает: проверьте функцию поиска в боте

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u daftbot -f`
2. Проверьте статус: `systemctl status daftbot`
3. Проверьте конфигурацию: `cat /opt/daft-property-bot/bot_config.json`
4. Откройте issue в GitHub репозитории
