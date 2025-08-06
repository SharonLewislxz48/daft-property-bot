#!/bin/bash

echo "🚨 КРИТИЧЕСКОЕ РЕШЕНИЕ: ВРЕМЕННАЯ ЗАМЕНА ПАРСЕРА"
echo "================================================"

echo ""
echo "Проблема: daft.ie блокирует Oracle Cloud IP адреса"
echo "Решение: Временно используем тестовые данные для проверки бота"

echo ""
echo "1. Создаем резервную копию:"
cp production_parser.py production_parser_original_backup.py
echo "✅ Создана резервная копия production_parser_original_backup.py"

echo ""
echo "2. Заменяем парсер на версию с обходом:"
cp production_parser_proxy.py production_parser.py
echo "✅ Заменен production_parser.py"

echo ""
echo "3. Заменяем в папке parser/:"
cp production_parser_proxy.py parser/production_parser.py
echo "✅ Заменен parser/production_parser.py"

echo ""
echo "4. Тестируем новый парсер:"
python3 production_parser.py

echo ""
echo "5. Перезапускаем бота:"
sudo systemctl restart daftbot

echo ""
echo "6. Проверяем статус:"
sudo systemctl status daftbot --no-pager -l

echo ""
echo "✅ ВРЕМЕННОЕ РЕШЕНИЕ АКТИВИРОВАНО"
echo ""
echo "⚠️  ВНИМАНИЕ:"
echo "   - Бот будет возвращать тестовые данные"
echo "   - Это решение ТОЛЬКО для проверки работоспособности"
echo "   - Для продакшена нужно решить проблему с IP блокировкой"
echo ""
echo "💡 ПОСТОЯННЫЕ РЕШЕНИЯ:"
echo "   1. Использовать VPN/прокси сервер"
echo "   2. Сменить хостинг (не Oracle Cloud)"
echo "   3. Использовать платные прокси API"
echo "   4. Связаться с daft.ie для разблокировки IP"
