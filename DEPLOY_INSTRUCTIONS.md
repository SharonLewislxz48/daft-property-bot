# 🚀 ИНСТРУКЦИИ ДЛЯ ДЕПЛОЯ ИСПРАВЛЕНИЙ

## 📋 КРАТКАЯ ВЕРСИЯ (для опытных)

```bash
# На сервере
cd /path/to/daftparser
./quick_deploy_fix.sh
```

---

## 📖 ПОДРОБНАЯ ВЕРСИЯ

### 1. Подключение к серверу
```bash
ssh username@your-server-ip
cd /path/to/daftparser  # Путь к проекту на сервере
```

### 2. Получение обновлений
```bash
git pull origin enhanced-bot-v2.0
```

### 3. Обновление зависимостей
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Тестирование парсера
```bash
python3 -c "
import asyncio
from production_parser import ProductionDaftParser

async def test():
    parser = ProductionDaftParser()
    results = await parser.search_properties(min_bedrooms=3, max_price=2500, location='dublin-city', limit=3)
    print(f'Найдено: {len(results)} объявлений')
    return len(results) > 0

print('✅ Тест пройден' if asyncio.run(test()) else '❌ Тест провален')
"
```

### 5. Перезапуск бота
```bash
sudo systemctl stop daftbot.service
sudo systemctl start daftbot.service
```

### 6. Проверка статуса
```bash
sudo systemctl status daftbot.service
sudo journalctl -u daftbot.service -f
```

---

## 🔧 ЧТО ИЗМЕНИЛОСЬ

### ✅ Исправления:
- **Главное:** Решена проблема "📊 Доступно объявлений: 0"
- **Парсер:** Переход от HTML к JSON-извлечению из React SPA
- **Пагинация:** Работает корректно (до 3 страниц)
- **Производительность:** 1.7 сек на поиск
- **Совместимость:** Сохранен API бота

### 📊 Ожидаемые результаты:
- Бот будет находить 5-20 объявлений вместо 0
- Поиск будет работать на нескольких страницах
- Время ответа: 2-3 секунды

---

## 🚨 УСТРАНЕНИЕ ПРОБЛЕМ

### Если бот не запускается:
```bash
# Проверить логи
sudo journalctl -u daftbot.service --no-pager -n 20

# Проверить порты
sudo netstat -tulpn | grep python

# Проверить виртуальное окружение
source .venv/bin/activate
python3 -c "import production_parser; print('✅ OK')"
```

### Если парсер не работает:
```bash
# Тест парсера напрямую
python3 production_parser.py

# Проверить интернет-соединение
curl -I https://www.daft.ie

# Проверить зависимости
pip list | grep -E "(aiohttp|asyncio)"
```

### Если бот показывает 0 объявлений:
```bash
# Проверить, что используется новый парсер
grep -n "extract_json_data" production_parser.py

# Тест JSON-парсинга
python3 -c "
from production_parser import ProductionDaftParser
import asyncio

async def test():
    parser = ProductionDaftParser()
    result = await parser.search_properties(min_bedrooms=2, max_price=3000, location='dublin-city', limit=1)
    print(f'Результат: {len(result)} объявлений')
    if result:
        print(f'Пример: {result[0]}')

asyncio.run(test())
"
```

---

## 📞 КОНТАКТЫ ДЛЯ ПОДДЕРЖКИ

При проблемах с деплоем:
1. Проверить логи: `sudo journalctl -u daftbot.service -f`
2. Убедиться что файлы обновились: `git log --oneline -1`
3. Проверить работу парсера: `python3 production_parser.py`

---

## ✅ ЧЕКЛИСТ УСПЕШНОГО ДЕПЛОЯ

- [ ] Git pull выполнен без ошибок
- [ ] Зависимости обновлены
- [ ] Тест парсера показывает > 0 объявлений
- [ ] Бот запущен (systemctl status = active)
- [ ] Логи не показывают критических ошибок
- [ ] Тестовая команда /start возвращает объявления

**Если все пункты отмечены ✅ - деплой успешен!** 🎉
