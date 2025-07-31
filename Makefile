# 🏠 Daft.ie Property Bot - Makefile

.PHONY: help build start stop restart logs install clean

# 🎯 Default target
help:
	@echo "🏠 Daft.ie Property Bot - Available commands:"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make install    - Install dependencies"
	@echo "  make start      - Start bot with Docker"
	@echo "  make dev        - Start in development mode"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  make build      - Build Docker image"
	@echo "  make up         - Start with docker-compose"
	@echo "  make down       - Stop docker-compose"
	@echo "  make restart    - Restart containers"
	@echo "  make logs       - Show logs"
	@echo ""
	@echo "🔧 Maintenance:"
	@echo "  make clean      - Clean up containers/images"
	@echo "  make update     - Update dependencies"
	@echo "  make test       - Run basic tests"

# 📦 Installation
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	playwright install chromium

# 🚀 Development mode
dev:
	@echo "🔧 Starting in development mode..."
	python3 main.py

# 🐳 Docker operations
build:
	@echo "🔨 Building Docker image..."
	docker-compose build

up:
	@echo "🚀 Starting with Docker Compose..."
	docker-compose up -d

down:
	@echo "⏹️ Stopping Docker Compose..."
	docker-compose down

start: up

stop: down

restart:
	@echo "🔄 Restarting..."
	docker-compose restart

logs:
	@echo "📊 Showing logs..."
	docker-compose logs -f

# 🔧 Maintenance
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down --volumes --remove-orphans
	docker system prune -f

update:
	@echo "🔄 Updating dependencies..."
	pip install -r requirements.txt --upgrade
	playwright install chromium

# 🧪 Testing
test:
	@echo "🧪 Running basic tests..."
	@python3 -c "\
import sys; \
import importlib.util; \
modules = ['bot.bot', 'parser.production_parser', 'database.database']; \
[print(f'✅ {m} - OK') if importlib.util.find_spec(m) else (print(f'❌ {m} - NOT FOUND'), sys.exit(1)) for m in modules]; \
print('🎉 All modules import successfully!');"

# 📊 Status check
status:
	@echo "📊 Checking status..."
	@docker-compose ps || echo "Docker Compose not running"

# 🗄️ Database backup
backup:
	@echo "💾 Creating database backup..."
	@timestamp=$$(date +%Y%m%d_%H%M%S) && \
	cp data/enhanced_bot.db "data/backup_enhanced_bot_$$timestamp.db" && \
	echo "✅ Backup created: backup_enhanced_bot_$$timestamp.db"
