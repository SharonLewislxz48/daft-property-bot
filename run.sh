#!/bin/bash

# 🚀 Daft.ie Property Bot - Quick Start Script
echo "🏠 Starting Daft.ie Property Bot..."

# Проверяем .env файл
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Create .env file with your TELEGRAM_TOKEN"
    echo "Example: TELEGRAM_TOKEN=your_bot_token_here"
    exit 1
fi

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed!"
    echo "📥 Please install Docker first"
    exit 1
fi

# Создаем необходимые директории
mkdir -p data logs

# Проверяем токен в .env
if ! grep -q "TELEGRAM_TOKEN" .env; then
    echo "❌ TELEGRAM_TOKEN not found in .env"
    exit 1
fi

echo "✅ Environment check passed"

# Выбор режима запуска
echo ""
echo "🎯 Choose deployment mode:"
echo "1) 🐳 Docker Compose (Recommended)"
echo "2) 🐍 Direct Python"
echo "3) 🔧 Development mode"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "🐳 Starting with Docker Compose..."
        docker-compose up --build -d
        echo "✅ Bot started in background!"
        echo "📊 Check status: docker-compose logs -f"
        ;;
    2)
        echo "🐍 Starting with Python..."
        pip install -r requirements.txt
        playwright install chromium
        python3 main.py
        ;;
    3)
        echo "🔧 Development mode..."
        pip install -r requirements.txt
        playwright install chromium
        python3 -c "
import asyncio
from bot.bot import PropertyBot

async def main():
    bot = PropertyBot()
    print('🤖 Bot starting in development mode...')
    await bot.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Bot is running!"
echo "📱 Find your bot in Telegram and send /start"
