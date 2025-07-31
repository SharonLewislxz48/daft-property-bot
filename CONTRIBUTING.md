# 🤝 Contributing to Daft.ie Property Bot

Спасибо за интерес к улучшению проекта! 🎉

## 🚀 **Быстрый старт**

### 1️⃣ **Fork и клонирование**
```bash
# Fork репозиторий на GitHub
git clone https://github.com/YOUR_USERNAME/daftparser.git
cd daftparser
```

### 2️⃣ **Настройка окружения**
```bash
# Автоматическая установка
./install.sh

# Или вручную
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 3️⃣ **Настройка бота**
```bash
cp .env.example .env
# Добавьте свой TELEGRAM_TOKEN
```

## 🔄 **Процесс разработки**

### 📋 **1. Создание Issue**
- 🐛 **Bug Report** - для сообщения об ошибках
- ✨ **Feature Request** - для предложений новых функций
- 📚 **Documentation** - для улучшения документации

### 🌿 **2. Создание ветки**
```bash
git checkout -b feature/new-awesome-feature
# или
git checkout -b bugfix/fix-important-bug
```

### 💻 **3. Разработка**
```bash
# Разработка с автоперезагрузкой
make dev

# Тестирование
make test

# Проверка стиля кода
python -m py_compile bot/*.py
```

### 📤 **4. Отправка изменений**
```bash
git add .
git commit -m "✨ Add awesome new feature"
git push origin feature/new-awesome-feature
```

### 🔄 **5. Pull Request**
- Используйте шаблон PR
- Опишите изменения подробно
- Приложите скриншоты (если есть UI изменения)

## 📝 **Стиль кода**

### 🐍 **Python**
- **PEP 8** стиль кодирования
- **Type hints** для новых функций
- **Docstrings** для публичных методов
- **Async/await** для асинхронных операций

```python
async def search_properties(
    self, 
    regions: List[str], 
    max_price: int = 2500
) -> List[Property]:
    """
    Поиск объявлений недвижимости.
    
    Args:
        regions: Список регионов для поиска
        max_price: Максимальная цена
        
    Returns:
        Список найденных объявлений
    """
    # Ваш код здесь
```

### 🤖 **Telegram Bot**
- **Обработка ошибок** во всех handlers
- **Cooldown** между сообщениями
- **Markdown escaping** для текста
- **Логирование** операций

```python
async def callback_handler(self, callback: CallbackQuery):
    """Обработчик callback запросов"""
    try:
        # Сразу отвечаем на callback
        await callback.answer()
        
        # Ваша логика здесь
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.answer("❌ Произошла ошибка")
```

## 🧪 **Тестирование**

### ✅ **Обязательные проверки**
```bash
# Импорт модулей
make test

# Синтаксис Python
python -m py_compile bot/*.py parser/*.py

# Docker сборка
docker build -t test-bot .
```

### 🔍 **Ручное тестирование**
1. Запустите бота: `make dev`
2. Протестируйте новую функцию в Telegram
3. Проверьте логи на ошибки
4. Убедитесь, что старые функции работают

## 📊 **Структура проекта**

```
daftparser/
├── bot/                    # Telegram бот
│   ├── bot.py             # Основная логика
│   ├── bot_handlers.py    # Дополнительные обработчики
│   └── keyboards.py       # Клавиатуры
├── parser/                # Парсер недвижимости
│   ├── production_parser.py
│   └── models.py
├── database/              # База данных
│   └── database.py
├── config/                # Конфигурация
│   ├── settings.py
│   └── regions.py
├── tests/                 # Тесты (TODO)
├── docs/                  # Документация
└── deploy/                # Развертывание
```

## 🎯 **Приоритетные области**

### 🔥 **Высокий приоритет**
- 🐛 **Исправление багов** в парсере
- 🚀 **Оптимизация производительности**
- 🔒 **Улучшение безопасности**
- 📱 **UX/UI улучшения бота**

### 🌟 **Средний приоритет**
- ✨ **Новые функции поиска**
- 📊 **Расширение аналитики**
- 🗺️ **Добавление новых регионов**
- 🔔 **Улучшение уведомлений**

### 💡 **Низкий приоритет**
- 📚 **Улучшение документации**
- 🧪 **Добавление тестов**
- 🎨 **Косметические изменения**

## 🆘 **Получение помощи**

### 💬 **Коммуникация**
- **Issues** - для обсуждения багов и функций
- **Discussions** - для общих вопросов
- **Email** - для приватных вопросов

### 📚 **Ресурсы**
- [USER_GUIDE.md](USER_GUIDE.md) - руководство пользователя
- [DEPLOYMENT.md](DEPLOYMENT.md) - развертывание
- [aiogram docs](https://docs.aiogram.dev/) - Telegram Bot API
- [Playwright docs](https://playwright.dev/python/) - веб-автоматизация

## 🎉 **Признание**

Все contributors будут добавлены в:
- **README.md** - список участников
- **CHANGELOG.md** - история изменений
- **GitHub Contributors** - автоматически

## 📄 **Лицензия**

Участвуя в проекте, вы соглашаетесь с тем, что ваши вклады будут лицензированы под [MIT License](LICENSE).

---

**Спасибо за участие в развитии проекта! 🏠🇮🇪**
