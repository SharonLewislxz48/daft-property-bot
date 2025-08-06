#!/bin/bash

echo "🌐 ПОДГОТОВКА К МИГРАЦИИ НА GOOGLE CLOUD"
echo "========================================="

echo ""
echo "📋 1. Создаем архив текущего проекта для переноса:"
tar -czf daft-bot-backup-$(date +%Y%m%d).tar.gz \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    bot_config.json \
    database.db \
    enhanced_main.py \
    production_parser_original_backup.py \
    parser/ \
    bot/ \
    *.md \
    *.txt \
    *.py \
    *.json

echo "✅ Архив создан: daft-bot-backup-$(date +%Y%m%d).tar.gz"

echo ""
echo "📝 2. Сохраняем текущую конфигурацию:"
echo "Токен бота:"
if [ -f "bot_config.json" ]; then
    cat bot_config.json | grep -o '"bot_token": "[^"]*"'
else
    echo "❌ bot_config.json не найден"
fi

echo ""
echo "IP текущего сервера Oracle Cloud:"
curl -s https://httpbin.org/ip

echo ""
echo "📊 3. Информация для переноса:"
echo "- Операционная система: $(lsb_release -d | cut -f2)"
echo "- Python версия: $(python3 --version)"
echo "- Размер проекта: $(du -sh . | cut -f1)"

echo ""
echo "🔗 4. Следующие шаги:"
echo "1. Перейти на https://cloud.google.com/"
echo "2. Создать аккаунт и проект"
echo "3. Создать VM e2-micro в europe-west1"
echo "4. Скачать архив на новый сервер"
echo "5. Запустить setup_gcp_server.sh"

echo ""
echo "📁 Файлы готовы к переносу:"
ls -lh daft-bot-backup-*.tar.gz

echo ""
echo "🚀 Готово к миграции на Google Cloud!"
