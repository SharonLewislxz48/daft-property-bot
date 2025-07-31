#!/bin/bash

# 🏠 Daft.ie Property Bot - Installation Script

set -e

echo "🏠 Daft.ie Property Bot Installation"
echo "===================================="

# Проверка системы
echo "🔍 Checking system requirements..."

# Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION found"

# Pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

# Git
if ! command -v git &> /dev/null; then
    echo "❌ Git is required but not installed"
    exit 1
fi

echo "✅ All system requirements met"

# Создание виртуального окружения
echo ""
echo "📦 Setting up virtual environment..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Активация виртуального окружения
source venv/bin/activate
echo "✅ Virtual environment activated"

# Установка зависимостей
echo ""
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Установка Playwright
echo ""
echo "🎭 Installing Playwright browser..."
playwright install chromium

# Создание директорий
echo ""
echo "📁 Creating directories..."
mkdir -p data logs
touch logs/.gitkeep

# Настройка .env
echo ""
echo "⚙️ Setting up configuration..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo ""
    echo "🔧 IMPORTANT: Edit .env file with your Telegram token:"
    echo "   nano .env"
    echo ""
    echo "Add your bot token from @BotFather:"
    echo "   TELEGRAM_TOKEN=your_bot_token_here"
else
    echo "✅ .env file already exists"
fi

# Проверка Docker (опционально)
echo ""
echo "🐳 Checking Docker (optional)..."
if command -v docker &> /dev/null; then
    echo "✅ Docker found - you can use 'make start' for containerized deployment"
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose found"
    else
        echo "⚠️ Docker Compose not found - install for easy deployment"
    fi
else
    echo "⚠️ Docker not found - you can still run with Python directly"
fi

# Финальные инструкции
echo ""
echo "🎉 Installation completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Telegram token:"
echo "   nano .env"
echo ""
echo "2. Start the bot:"
echo "   # With Docker (recommended):"
echo "   make start"
echo ""
echo "   # Or with Python directly:"
echo "   source venv/bin/activate"
echo "   python3 main.py"
echo ""
echo "3. Find your bot in Telegram and send /start"
echo ""
echo "📚 See USER_GUIDE.md for detailed usage instructions"
