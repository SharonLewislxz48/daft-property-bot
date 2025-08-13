#!/bin/bash

# Скрипт для обновления бота на сервере с поддержкой ветки enhanced-bot-v2.0
echo "🚀 Начинаем обновление бота на сервере..."

# Переходим в директорию проекта
cd /home/ubuntu/daft-property-bot

# Останавливаем текущие контейнеры
echo "⏹️ Останавливаем контейнеры..."
docker-compose down

# Получаем последние изменения из правильной ветки
echo "📥 Получаем обновления из GitHub (ветка enhanced-bot-v2.0)..."
git fetch origin
git checkout enhanced-bot-v2.0
git pull origin enhanced-bot-v2.0

# Пересобираем и перезапускаем контейнеры
echo "🔄 Пересобираем Docker контейнеры..."
docker-compose up -d --build

# Ждем немного для запуска
sleep 10

# Проверяем статус
echo "✅ Проверяем статус контейнеров..."
docker-compose ps

# Проверяем логи бота
echo "📋 Последние логи бота:"
docker-compose logs --tail=20 bot

echo "🎉 Обновление завершено!"
echo "📊 Для просмотра логов используйте: docker-compose logs -f bot"
