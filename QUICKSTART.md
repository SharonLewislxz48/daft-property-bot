# 🚀 Quick Start - Daft.ie Property Bot

**3 команды и ваш бот работает!** ⚡

## ⚡ **Супер-быстрый старт**

```bash
# 1. Скачать проект
git clone https://github.com/your-username/daftparser.git && cd daftparser

# 2. Настроить токен
cp .env.example .env && nano .env  # Добавить TELEGRAM_TOKEN

# 3. Запустить
./run.sh
```

**Готово!** 🎉 Найдите бота в Telegram и отправьте `/start`

---

## 🎯 **Варианты запуска**

### 🐳 **Docker (Рекомендуется)**
```bash
make start
# или
docker-compose up -d
```

### 🐍 **Python напрямую**
```bash
make install && make dev
```

### ☁️ **Облачные платформы**
- **Railway**: Просто подключите GitHub repo
- **Heroku**: `git push heroku main`
- **DigitalOcean**: App Platform ready

---

## 📋 **Что нужно**

### 🔑 **Обязательно**
- **Python 3.11+** или **Docker**
- **Telegram Bot Token** от [@BotFather](https://t.me/BotFather)

### 📱 **Получение токена**
1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Укажите имя бота: `Property Search Bot`
4. Username: `your_property_bot`
5. Скопируйте токен: `1234567890:ABC-DEF...`

---

## ⚙️ **Настройка .env**

```bash
# Обязательно
TELEGRAM_TOKEN=your_bot_token_here

# Опционально (есть значения по умолчанию)
DATABASE_PATH=./data/enhanced_bot.db
LOG_LEVEL=INFO
BROWSER_HEADLESS=true
```

---

## 🎮 **Первые команды**

После запуска найдите бота в Telegram:

```
/start          → Запуск и регистрация
⚙️ Настройки    → Выбор регионов и параметров
🔍 Разовый поиск → Найти объявления сейчас
▶️ Мониторинг   → Автоматическое отслеживание
```

---

## 🗺️ **Регионы для поиска**

- **🏙️ Дублин**: 62 района (Dublin 1-24, Rathmines, Clontarf...)
- **🌆 Города**: Cork, Galway, Belfast, Limerick, Waterford
- **🗺️ Графства**: Все 32 графства Ирландии
- **⭐ Готовые наборы**: Студенческие районы, деловые центры

---

## 🆘 **Проблемы?**

### ❌ **Частые ошибки**

**"Unauthorized"**
```bash
# Проверьте токен в .env
grep TELEGRAM_TOKEN .env
```

**"Module not found"**
```bash
# Установите зависимости
make install
```

**"Docker not found"**
```bash
# Используйте Python напрямую
make dev
```

### 📞 **Получить помощь**
- 📚 [USER_GUIDE.md](USER_GUIDE.md) - подробное руководство
- 🚀 [DEPLOYMENT.md](DEPLOYMENT.md) - развертывание
- 🐛 [Issues](https://github.com/your-username/daftparser/issues) - сообщить о проблеме

---

## 🎉 **Готово!**

Ваш бот должен быть активен в Telegram. Отправьте `/start` и начинайте поиск недвижимости в Ирландии! 🏠🇮🇪