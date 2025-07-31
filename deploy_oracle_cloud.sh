#!/bin/bash

# 🌤️ Oracle Cloud Infrastructure Deployment Script
# Ubuntu 20.04/22.04 LTS

set -e

echo "🌤️ Deploying Daft Property Bot to Oracle Cloud..."
echo "=================================================="

# Проверка системы
echo "📋 System Information:"
lsb_release -a
echo ""

# Обновление системы
echo "🔄 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
echo "📦 Installing required packages..."
sudo apt install -y \
    git \
    curl \
    wget \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Установка Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "✅ Docker installed successfully!"
else
    echo "✅ Docker already installed"
fi

# Установка Docker Compose
echo "🔧 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed successfully!"
else
    echo "✅ Docker Compose already installed"
fi

# Клонирование репозитория
echo "📥 Cloning repository..."
cd /opt
sudo rm -rf daft-property-bot 2>/dev/null || true
sudo git clone https://github.com/SharonLewislxz48/daft-property-bot.git
sudo chown -R $USER:$USER daft-property-bot
cd daft-property-bot

# У нас уже есть все файлы, включая:
echo "✅ Project includes:"
echo "  • Docker configuration"
echo "  • Environment setup"
echo "  • Systemd services"  
echo "  • All dependencies"

# Создание .env файла
echo "⚙️ Creating environment configuration..."
cat > .env << 'EOF'
# 🤖 Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# 🔧 Application Settings
APP_ENV=production
LOG_LEVEL=INFO
MAX_PROPERTIES_PER_MESSAGE=5
REQUEST_DELAY=1.5

# 🐳 Docker Settings
COMPOSE_PROJECT_NAME=daft_bot
RESTART_POLICY=unless-stopped

# 🌐 Network Settings
EXPOSE_PORT=8000
HEALTH_CHECK_INTERVAL=30s

# 📊 Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
EOF

echo ""
echo "🔑 ВАЖНО! Отредактируйте файл .env:"
echo "sudo nano .env"
echo "Замените 'your_bot_token_here' на ваш реальный токен бота"
echo ""

# Настройка файрвола
echo "🔥 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw --force enable

# Создание systemd сервиса
echo "🚀 Creating systemd service..."
sudo tee /etc/systemd/system/daft-bot.service > /dev/null << 'EOF'
[Unit]
Description=Daft Property Bot
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/daft-property-bot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Включение сервиса
sudo systemctl daemon-reload
sudo systemctl enable daft-bot.service

echo ""
echo "🎉 Oracle Cloud deployment preparation completed!"
echo "=================================================="
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file: sudo nano .env"
echo "2. Add your Telegram bot token"
echo "3. Start the service: sudo systemctl start daft-bot"
echo "4. Check status: sudo systemctl status daft-bot"
echo "5. View logs: sudo docker-compose logs -f"
echo ""
echo "🔧 Useful commands:"
echo "• Restart bot: sudo systemctl restart daft-bot"
echo "• Stop bot: sudo systemctl stop daft-bot"
echo "• Update bot: cd /opt/daft-property-bot && git pull && sudo systemctl restart daft-bot"
echo ""
echo "🌐 Your bot will be available after configuration!"
