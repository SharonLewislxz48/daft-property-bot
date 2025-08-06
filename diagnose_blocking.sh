#!/bin/bash

echo "🔍 ДИАГНОСТИКА БЛОКИРОВКИ DAFT.IE"
echo "================================="

echo ""
echo "📍 1. Проверяем IP адрес сервера:"
curl -s https://httpbin.org/ip

echo ""
echo "📡 2. Проверяем доступность daft.ie:"
curl -I -s -w "HTTP Status: %{http_code}\nTotal time: %{time_total}s\n" https://www.daft.ie/

echo ""
echo "🌍 3. Проверяем через разные User-Agent:"
echo "Chrome:"
curl -I -s -w "HTTP Status: %{http_code}\n" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36" https://www.daft.ie/

echo "Firefox:"
curl -I -s -w "HTTP Status: %{http_code}\n" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0" https://www.daft.ie/

echo "Safari:"
curl -I -s -w "HTTP Status: %{http_code}\n" -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15" https://www.daft.ie/

echo ""
echo "🕸️ 4. Проверяем robots.txt:"
curl -s https://www.daft.ie/robots.txt | head -20

echo ""
echo "🔄 5. Тестируем другие домены:"
echo "Ping google.com:"
ping -c 2 google.com

echo ""
echo "📊 РЕЗУЛЬТАТ ДИАГНОСТИКИ:"
echo "Если все запросы возвращают 403 - IP заблокирован"
echo "Если ping работает, но daft.ie нет - блокировка специфична для daft.ie"
