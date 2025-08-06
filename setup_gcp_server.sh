#!/bin/bash

echo "🔧 НАСТРОЙКА GCP СЕРВЕРА ДЛЯ DAFT-BOT"
echo "====================================="

# Проверяем что мы на GCP
if ! curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/hostname > /dev/null; then
    echo "❌ Этот скрипт должен запускаться на GCP сервере"
    exit 1
fi

echo "✅ Обнаружен GCP сервер"

echo ""
echo "📦 1. Обновление системы..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget nginx htop

echo ""
echo "👤 2. Настройка пользователя botuser..."
if ! id "botuser" &>/dev/null; then
    sudo useradd -m -s /bin/bash botuser
    sudo usermod -aG sudo botuser
    echo "✅ Пользователь botuser создан"
else
    echo "✅ Пользователь botuser уже существует"
fi

echo ""
echo "📂 3. Создание структуры директорий..."
sudo -u botuser mkdir -p /home/botuser/daft-property-bot
sudo -u botuser mkdir -p /home/botuser/daft-property-bot/logs

echo ""
echo "🔍 4. Проверка доступности daft.ie..."
DAFT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://www.daft.ie/)
if [ "$DAFT_STATUS" = "200" ]; then
    echo "✅ daft.ie доступен (статус: $DAFT_STATUS)"
    echo "🎉 НЕТ БЛОКИРОВКИ! Можно использовать реальный парсер"
else
    echo "❌ daft.ie недоступен (статус: $DAFT_STATUS)"
    echo "⚠️ Возможна блокировка IP"
fi

echo ""
echo "🌐 5. Информация о сервере:"
echo "Внешний IP: $(curl -s https://httpbin.org/ip | grep -o '[0-9.]*')"
echo "Внутренний IP: $(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip)"
echo "Зона: $(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/zone | cut -d/ -f4)"
echo "Тип машины: $(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/machine-type | cut -d/ -f4)"

echo ""
echo "🔐 6. Настройка firewall (если нужно)..."
# Проверяем открыты ли нужные порты
if sudo ufw status | grep -q "Status: active"; then
    echo "UFW активен, добавляем правила..."
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8080/tcp
else
    echo "UFW не активен, пропускаем настройку"
fi

echo ""
echo "📋 7. Следующие шаги:"
echo "1. Скопировать архив проекта: scp daft-bot-backup-*.tar.gz botuser@GCP_IP:/home/botuser/"
echo "2. Распаковать: tar -xzf daft-bot-backup-*.tar.gz"
echo "3. Склонировать репозиторий: git clone https://github.com/SharonLewislxz48/daft-property-bot.git"
echo "4. Настроить окружение: python3 -m venv .venv && source .venv/bin/activate"
echo "5. Установить зависимости: pip install -r requirements.txt"
echo "6. Скопировать конфиги: cp bot_config.json daft-property-bot/"
echo "7. Запустить тест: python3 production_parser.py"

echo ""
echo "✅ GCP сервер готов к установке daft-bot!"

# Создаем информационный файл
sudo -u botuser tee /home/botuser/server_info.txt > /dev/null << EOF
GCP Server Information
=====================
External IP: $(curl -s https://httpbin.org/ip | grep -o '[0-9.]*')
Internal IP: $(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip)
Zone: $(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/zone | cut -d/ -f4)
Machine Type: $(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/machine-type | cut -d/ -f4)
Setup Date: $(date)
Daft.ie Status: $DAFT_STATUS
EOF

echo "📄 Информация сохранена в /home/botuser/server_info.txt"
