#!/bin/bash

# 🚀 Enhanced Bot v2.0 - Deployment Script
# Скрипт для развертывания бота на сервере

set -e  # Остановить выполнение при ошибке

echo "🚀 РАЗВЕРТЫВАНИЕ ENHANCED BOT V2.0"
echo "=================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверяем аргументы
if [ $# -eq 0 ]; then
    echo "Использование: $0 <production|staging|local>"
    echo "  production - развертывание на продакшен сервере"
    echo "  staging    - развертывание на тестовом сервере"
    echo "  local      - локальное развертывание для тестов"
    exit 1
fi

ENVIRONMENT=$1
REPO_URL="https://github.com/SharonLewislxz48/daft-property-bot.git"
BRANCH="enhanced-bot-v2.0"
APP_DIR="/opt/daft-property-bot"
SERVICE_NAME="daftbot"
USER="daftbot"

print_status "Развертывание окружения: $ENVIRONMENT"

# 1. Обновление системы
print_status "Обновление системы..."
sudo apt update && sudo apt upgrade -y

# 2. Установка зависимостей
print_status "Установка системных зависимостей..."
sudo apt install -y python3 python3-pip python3-venv git nginx supervisor sqlite3 curl

# 3. Установка Playwright dependencies
print_status "Установка Playwright зависимостей..."
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# 4. Создание пользователя для приложения
if ! id "$USER" &>/dev/null; then
    print_status "Создание пользователя $USER..."
    sudo useradd -r -s /bin/bash -d $APP_DIR $USER
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
else
    print_success "Пользователь $USER уже существует"
fi

# 5. Клонирование/обновление репозитория
print_status "Получение кода из репозитория..."
if [ -d "$APP_DIR/.git" ]; then
    print_status "Обновление существующего репозитория..."
    sudo -u $USER git -C $APP_DIR fetch origin
    sudo -u $USER git -C $APP_DIR checkout $BRANCH
    sudo -u $USER git -C $APP_DIR pull origin $BRANCH
else
    print_status "Клонирование репозитория..."
    sudo -u $USER git clone -b $BRANCH $REPO_URL $APP_DIR
fi

# 6. Создание виртуального окружения
print_status "Создание виртуального окружения..."
sudo -u $USER python3 -m venv $APP_DIR/.venv

# 7. Установка Python зависимостей
print_status "Установка Python зависимостей..."
sudo -u $USER $APP_DIR/.venv/bin/pip install --upgrade pip
sudo -u $USER $APP_DIR/.venv/bin/pip install -r $APP_DIR/requirements.txt

# 8. Установка Playwright браузеров
print_status "Установка Playwright браузеров..."
sudo -u $USER $APP_DIR/.venv/bin/playwright install chromium

# 9. Создание директорий для данных и логов
print_status "Создание директорий..."
sudo -u $USER mkdir -p $APP_DIR/data
sudo -u $USER mkdir -p $APP_DIR/logs

# 10. Настройка конфигурации в зависимости от окружения
print_status "Настройка конфигурации для $ENVIRONMENT..."

case $ENVIRONMENT in
    "production")
        CONFIG_FILE="$APP_DIR/bot_config.json"
        ;;
    "staging")
        CONFIG_FILE="$APP_DIR/bot_config_staging.json"
        ;;
    "local")
        CONFIG_FILE="$APP_DIR/bot_config_local.json"
        ;;
esac

# Создаем шаблон конфигурации если не существует
if [ ! -f "$CONFIG_FILE" ]; then
    print_warning "Конфигурационный файл не найден. Создаем шаблон..."
    sudo -u $USER cat > $CONFIG_FILE << 'EOF'
{
    "telegram": {
        "bot_token": "YOUR_BOT_TOKEN_HERE",
        "group_id": -1002819366953
    },
    "database": {
        "path": "data/enhanced_bot.db"
    },
    "logging": {
        "level": "INFO",
        "file": "logs/enhanced_bot.log"
    },
    "parser": {
        "max_pages": 3,
        "max_results": 100,
        "timeout": 30000
    }
}
EOF
    print_error "⚠️  ВАЖНО: Отредактируйте $CONFIG_FILE и добавьте ваш bot_token!"
fi

# 11. Создание systemd сервиса
print_status "Создание systemd сервиса..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Daft Property Bot Enhanced v2.0
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/.venv/bin
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/enhanced_main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 12. Инициализация базы данных
print_status "Инициализация базы данных..."
sudo -u $USER $APP_DIR/.venv/bin/python -c "
import sys
sys.path.append('$APP_DIR')
import asyncio
from database.enhanced_database import EnhancedDatabase

async def init_db():
    db = EnhancedDatabase('$APP_DIR/data/enhanced_bot.db')
    await db.init_database()
    print('База данных инициализирована')

asyncio.run(init_db())
"

# 13. Настройка прав доступа
print_status "Настройка прав доступа..."
sudo chown -R $USER:$USER $APP_DIR
sudo chmod +x $APP_DIR/enhanced_main.py

# 14. Обновление systemd и запуск сервиса
print_status "Регистрация и запуск сервиса..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# 15. Проверка статуса
sleep 3
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    print_success "✅ Сервис $SERVICE_NAME успешно запущен!"
    sudo systemctl status $SERVICE_NAME --no-pager -l
else
    print_error "❌ Ошибка запуска сервиса $SERVICE_NAME"
    sudo journalctl -u $SERVICE_NAME --no-pager -l -n 20
    exit 1
fi

# 16. Создание скриптов управления
print_status "Создание скриптов управления..."

# Скрипт для управления ботом
sudo tee $APP_DIR/manage_bot.sh > /dev/null << 'EOF'
#!/bin/bash
# Скрипт управления ботом

SERVICE_NAME="daftbot"

case $1 in
    "start")
        echo "🚀 Запуск бота..."
        sudo systemctl start $SERVICE_NAME
        ;;
    "stop")
        echo "🛑 Остановка бота..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    "restart")
        echo "🔄 Перезапуск бота..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    "status")
        echo "📊 Статус бота:"
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    "logs")
        echo "📋 Логи бота:"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    "update")
        echo "🔄 Обновление бота..."
        cd /opt/daft-property-bot
        sudo -u daftbot git pull origin enhanced-bot-v2.0
        sudo -u daftbot .venv/bin/pip install -r requirements.txt
        sudo systemctl restart $SERVICE_NAME
        echo "✅ Бот обновлен и перезапущен"
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update}"
        echo "  start   - запустить бота"
        echo "  stop    - остановить бота"
        echo "  restart - перезапустить бота"
        echo "  status  - показать статус"
        echo "  logs    - показать логи в реальном времени"
        echo "  update  - обновить код и перезапустить"
        ;;
esac
EOF

sudo chmod +x $APP_DIR/manage_bot.sh
sudo ln -sf $APP_DIR/manage_bot.sh /usr/local/bin/manage-daftbot

print_success "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo ""
echo "📋 ИНФОРМАЦИЯ:"
echo "  • Приложение установлено в: $APP_DIR"
echo "  • Сервис: $SERVICE_NAME"
echo "  • Конфигурация: $CONFIG_FILE"
echo "  • Логи: $APP_DIR/logs/"
echo "  • База данных: $APP_DIR/data/"
echo ""
echo "🔧 УПРАВЛЕНИЕ:"
echo "  • Статус:      sudo systemctl status $SERVICE_NAME"
echo "  • Запуск:      sudo systemctl start $SERVICE_NAME"
echo "  • Остановка:   sudo systemctl stop $SERVICE_NAME"
echo "  • Перезапуск:  sudo systemctl restart $SERVICE_NAME"
echo "  • Логи:        sudo journalctl -u $SERVICE_NAME -f"
echo "  • Управление:  manage-daftbot {start|stop|restart|status|logs|update}"
echo ""
echo "⚠️  НЕ ЗАБУДЬТЕ:"
echo "  1. Отредактировать $CONFIG_FILE"
echo "  2. Добавить telegram bot_token"
echo "  3. Перезапустить сервис после настройки"
echo ""

if [ "$ENVIRONMENT" = "production" ]; then
    print_warning "🔐 Для продакшена рекомендуется:"
    echo "  • Настроить файрвол (ufw)"
    echo "  • Настроить SSL сертификаты"
    echo "  • Настроить мониторинг"
    echo "  • Настроить бэкапы базы данных"
fi
