#!/bin/bash

# Скрипт для обновления бота на сервере
echo "🚀 Начинаем обновление бота на сервере..."

# Переходим в директорию проекта
cd /home/ubuntu/daft-property-bot

# Получаем последние изменения
echo "📥 Получаем обновления из GitHub..."
git pull origin main

# Пересобираем и перезапускаем контейнеры
echo "🔄 Пересобираем Docker контейнеры..."
docker-compose down
docker-compose up -d --build

# Проверяем статус
echo "✅ Проверяем статус контейнеров..."
docker-compose ps

echo "🎉 Обновление завершено!"
