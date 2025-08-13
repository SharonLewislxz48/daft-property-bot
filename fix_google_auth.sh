#!/bin/bash
# Быстрое решение проблемы блокировки Google на Daft.ie

echo "🔧 Решение проблемы Google блокировки"
echo "======================================"

echo ""
echo "❌ Проблема: Google блокирует автоматизированные браузеры"
echo "✅ Решение: Извлечение cookies из обычного браузера"
echo ""

echo "📋 Шаги для решения:"
echo "1. Откройте обычный браузер (Chrome/Firefox)"
echo "2. Войдите на https://www.daft.ie через Google"
echo "3. Убедитесь что авторизация успешна"
echo "4. Закройте браузер"
echo ""

read -p "👆 Выполнили шаги выше? (y/n): " confirm
if [[ $confirm != [yY] ]]; then
    echo "⏸️ Сначала выполните шаги выше, затем запустите скрипт снова"
    exit 1
fi

echo ""
echo "🔍 Извлечение cookies из браузера..."
python3 extract_cookies.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Готово! Запускаем автоматизацию..."
    echo ""
    python3 telegram_daft_automation.py
else
    echo ""
    echo "❌ Не удалось извлечь cookies"
    echo "🔧 Попробуйте альтернативный метод:"
    echo "   python3 telegram_daft_automation.py"
    echo "   (выберите 'Нет' при вопросе о Google авторизации)"
fi
