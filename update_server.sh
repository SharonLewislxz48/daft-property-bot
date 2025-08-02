#!/bin/bash

# 🔄 Enhanced Bot v2.0 - Quick Update Script
# Скрипт быстрого обновления бота на сервере

set -e

echo "🔄 ОБНОВЛЕНИЕ ENHANCED BOT V2.0"
echo "==============================="

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Конфигурация
APP_DIR="/opt/daft-property-bot"
SERVICE_NAME="daftbot"
USER="daftbot"
BRANCH="enhanced-bot-v2.0"

# Проверяем права доступа
if [ "$EUID" -ne 0 ]; then
    echo "Пожалуйста, запустите скрипт с правами root (используйте sudo)"
    exit 1
fi

# Проверяем существование директории
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Директория $APP_DIR не найдена. Сначала выполните развертывание."
    exit 1
fi

print_status "Остановка сервиса..."
systemctl stop $SERVICE_NAME

print_status "Создание бэкапа базы данных..."
BACKUP_DIR="$APP_DIR/backups"
mkdir -p $BACKUP_DIR
if [ -f "$APP_DIR/data/enhanced_bot.db" ]; then
    cp "$APP_DIR/data/enhanced_bot.db" "$BACKUP_DIR/enhanced_bot_$(date +%Y%m%d_%H%M%S).db"
    print_success "Бэкап создан: $BACKUP_DIR/enhanced_bot_$(date +%Y%m%d_%H%M%S).db"
fi

print_status "Обновление кода из Git..."
cd $APP_DIR
sudo -u $USER git fetch origin
sudo -u $USER git checkout $BRANCH
sudo -u $USER git pull origin $BRANCH

print_status "Обновление Python зависимостей..."
sudo -u $USER $APP_DIR/.venv/bin/pip install --upgrade pip
sudo -u $USER $APP_DIR/.venv/bin/pip install -r requirements.txt

print_status "Обновление Playwright браузеров..."
sudo -u $USER $APP_DIR/.venv/bin/playwright install chromium

print_status "Проверка и обновление базы данных..."
sudo -u $USER $APP_DIR/.venv/bin/python -c "
import sys
sys.path.append('$APP_DIR')
import asyncio
from database.enhanced_database import EnhancedDatabase

async def update_db():
    db = EnhancedDatabase('$APP_DIR/data/enhanced_bot.db')
    await db.init_database()
    print('✅ База данных обновлена')

try:
    asyncio.run(update_db())
except Exception as e:
    print(f'⚠️ Предупреждение при обновлении БД: {e}')
"

print_status "Проверка конфигурации..."
if [ -f "$APP_DIR/bot_config.json" ]; then
    python3 -m json.tool "$APP_DIR/bot_config.json" > /dev/null
    print_success "Конфигурация корректна"
else
    print_warning "Конфигурационный файл не найден"
fi

print_status "Обновление прав доступа..."
chown -R $USER:$USER $APP_DIR
chmod +x $APP_DIR/enhanced_main.py

print_status "Перезагрузка systemd daemon..."
systemctl daemon-reload

print_status "Запуск сервиса..."
systemctl start $SERVICE_NAME
systemctl enable $SERVICE_NAME

# Ожидание запуска
sleep 5

print_status "Проверка статуса сервиса..."
if systemctl is-active --quiet $SERVICE_NAME; then
    print_success "✅ Сервис $SERVICE_NAME успешно обновлен и запущен!"
    
    echo ""
    echo "📊 СТАТУС СЕРВИСА:"
    systemctl status $SERVICE_NAME --no-pager -l
    
    echo ""
    echo "📋 ПОСЛЕДНИЕ ЛОГИ:"
    journalctl -u $SERVICE_NAME --no-pager -l -n 10
    
else
    echo "❌ Ошибка запуска сервиса $SERVICE_NAME"
    echo "📋 Логи ошибок:"
    journalctl -u $SERVICE_NAME --no-pager -l -n 20
    exit 1
fi

echo ""
print_success "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!"
echo ""
echo "📋 ИНФОРМАЦИЯ ОБ ОБНОВЛЕНИИ:"
echo "  • Время обновления: $(date)"
echo "  • Ветка: $BRANCH"
echo "  • Последний коммит: $(cd $APP_DIR && git log -1 --pretty=format:'%h - %s (%an, %ar)')"
echo "  • Статус сервиса: $(systemctl is-active $SERVICE_NAME)"
echo ""
echo "🔧 КОМАНДЫ ДЛЯ МОНИТОРИНГА:"
echo "  • Статус:    systemctl status $SERVICE_NAME"
echo "  • Логи:      journalctl -u $SERVICE_NAME -f"
echo "  • Управление: manage-daftbot {start|stop|restart|status|logs}"
echo ""

# Очистка старых бэкапов (оставляем только последние 10)
print_status "Очистка старых бэкапов..."
find $BACKUP_DIR -name "enhanced_bot_*.db" -type f | sort -r | tail -n +11 | xargs -r rm
print_success "Очистка завершена"
