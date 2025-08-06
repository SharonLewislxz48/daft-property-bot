#!/bin/bash

echo "🔍 ДИАГНОСТИКА: ЧТО ИЗМЕНИЛОСЬ В ПАРСЕРЕ"
echo "========================================"

echo ""
echo "📊 1. Проверяем какой парсер использовался раньше на сервере..."

# Проверяем что в оригинальном backup файле
if [ -f "production_parser_original_backup.py" ]; then
    echo ""
    echo "🔍 2. Анализ оригинального парсера:"
    echo "Размер файла: $(wc -l < production_parser_original_backup.py) строк"
    echo ""
    echo "Использует ли Playwright:"
    if grep -q "playwright" production_parser_original_backup.py; then
        echo "✅ ДА - использует Playwright (браузер)"
        grep -n "playwright\|async_playwright\|browser" production_parser_original_backup.py | head -5
    else
        echo "❌ НЕТ - не использует Playwright"
    fi
    
    echo ""
    echo "Использует ли aiohttp:"
    if grep -q "aiohttp" production_parser_original_backup.py; then
        echo "✅ ДА - использует aiohttp"
        grep -n "aiohttp\|ClientSession" production_parser_original_backup.py | head -3
    else
        echo "❌ НЕТ - не использует aiohttp"
    fi
    
    echo ""
    echo "Использует ли requests:"
    if grep -q "requests" production_parser_original_backup.py; then
        echo "✅ ДА - использует requests"
        grep -n "requests\|get\|post" production_parser_original_backup.py | head -3
    else
        echo "❌ НЕТ - не использует requests"
    fi
else
    echo "❌ Файл production_parser_original_backup.py не найден"
fi

echo ""
echo "🔍 3. Анализ текущего парсера (после изменений):"
if [ -f "production_parser.py" ]; then
    echo "Размер файла: $(wc -l < production_parser.py) строк"
    echo ""
    echo "Использует ли aiohttp:"
    if grep -q "aiohttp" production_parser.py; then
        echo "✅ ДА - использует aiohttp (HTTP клиент)"
    else
        echo "❌ НЕТ - не использует aiohttp"
    fi
    
    echo ""
    echo "Использует ли Playwright:"
    if grep -q "playwright" production_parser.py; then
        echo "✅ ДА - использует Playwright"
    else
        echo "❌ НЕТ - НЕ использует Playwright (вот проблема!)"
    fi
fi

echo ""
echo "🔍 4. Выводы:"
echo "Если оригинальный парсер использовал Playwright, а новый aiohttp - это объясняет блокировку!"
echo ""
echo "📋 Playwright vs aiohttp:"
echo "✅ Playwright = Настоящий браузер Chrome (выглядит как человек)"
echo "❌ aiohttp = HTTP клиент (выглядит как бот)"
echo ""
echo "💡 РЕШЕНИЕ: Вернуться к Playwright парсеру!"

echo ""
echo "🚀 5. План исправления:"
echo "1. Протестировать Playwright парсер на сервере"
echo "2. Если работает - заменить текущий парсер"
echo "3. Перезапустить бота с браузерным парсингом"
