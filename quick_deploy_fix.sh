#!/bin/bash
# Скрипт быстрого деплоя исправлений на сервер

set -e

echo "🚀 ДЕПЛОЙ ИСПРАВЛЕНИЙ DAFT-PROPERTY-BOT"
echo "========================================"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📥 Получение последних изменений из Git...${NC}"
git pull origin enhanced-bot-v2.0

echo -e "${YELLOW}📦 Обновление зависимостей...${NC}"
source .venv/bin/activate
pip install -r requirements.txt

echo -e "${YELLOW}🔍 Проверка обновленного парсера...${NC}"
python3 -c "
import asyncio
from production_parser import ProductionDaftParser

async def test():
    parser = ProductionDaftParser()
    results = await parser.search_properties(min_bedrooms=3, max_price=2500, location='dublin-city', limit=3, max_pages=1)
    print(f'✅ Парсер работает: найдено {len(results)} объявлений')
    if results:
        print(f'📋 Пример: {results[0][\"title\"]} - €{results[0][\"price\"]}/мес')
    return len(results) > 0

success = asyncio.run(test())
if not success:
    print('❌ Парсер не работает')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Тест парсера пройден${NC}"
else
    echo -e "${RED}❌ Тест парсера провален${NC}"
    exit 1
fi

echo -e "${YELLOW}🤖 Перезапуск бота...${NC}"
if systemctl is-active --quiet daftbot.service; then
    echo "Останавливаем бота..."
    sudo systemctl stop daftbot.service
    sleep 3
fi

echo "Запускаем бота..."
sudo systemctl start daftbot.service
sleep 5

echo -e "${YELLOW}📊 Проверка статуса бота...${NC}"
if systemctl is-active --quiet daftbot.service; then
    echo -e "${GREEN}✅ Бот запущен успешно${NC}"
    
    echo -e "${YELLOW}📋 Последние логи бота:${NC}"
    sudo journalctl -u daftbot.service --no-pager -n 10
    
    echo ""
    echo -e "${GREEN}🎉 ДЕПЛОЙ ЗАВЕРШЕН УСПЕШНО!${NC}"
    echo "🔍 Проблема '0 объявлений' должна быть решена"
    echo "📊 Бот теперь использует JSON-парсинг с пагинацией"
    echo ""
    echo "📋 Для мониторинга используйте:"
    echo "   sudo journalctl -u daftbot.service -f"
    echo ""
    echo "🧪 Для тестирования отправьте команду /start боту"
    
else
    echo -e "${RED}❌ Ошибка запуска бота${NC}"
    echo "📋 Логи ошибок:"
    sudo journalctl -u daftbot.service --no-pager -n 20
    exit 1
fi
