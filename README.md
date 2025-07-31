# 🏠 Daft.ie Property Bot

🤖 **Автоматический мониторинг недвижимости в Ирландии**

Telegram бот для поиска и мониторинга объявлений на Daft.ie - крупнейшем сайте недвижимости Ирландии.

## ✨ **Возможности**

- 🔍 **Автоматический поиск** по 100+ локациям Ирландии
- 📱 **Удобный Telegram интерфейс** с интуитивной навигацией
- ⚙️ **Гибкие настройки**: регионы, цена, количество спален
- � **Аналитика и статистика** поиска
- 🚀 **Быстрое развертывание** с Docker

## 🗺️ **География поиска**

- **🏙️ Дублин**: 62 района (Dublin 1-24, Rathmines, Clontarf, etc.)
- **🌆 Крупные города**: Cork, Galway, Belfast, Limerick, Waterford
- **�️ Все графства**: 32 графства Ирландии и Северной Ирландии
- **⭐ Готовые комбинации**: студенческие районы, деловые центры

## 🚀 **Быстрый старт**

### 1️⃣ **Скачать проект**
```bash
git clone https://github.com/your-username/daftparser.git
cd daftparser
```

### 2️⃣ **Настроить токен**
```bash
cp .env.example .env
nano .env  # Добавьте TELEGRAM_TOKEN=your_bot_token
```

### 3️⃣ **Запустить**
```bash
# Автоматический режим
./run.sh

# Или с Make
make start
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Установка Playwright (для парсинга динамического контента)
```bash
playwright install chromium
```

### 4. Настройка переменных окружения
Создайте файл `.env` и заполните его:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
CHAT_ID=your_chat_id_here
ADMIN_USER_ID=your_admin_user_id_here
```

### 5. Создание бота в Telegram
1. Найдите @BotFather в Telegram
2. Выполните команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте токен в `.env` файл

### 6. Получение Chat ID
1. Добавьте бота в группу
2. Отправьте любое сообщение в группу
3. Перейдите по ссылке: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Найдите chat_id в ответе и добавьте в `.env`

## Запуск

### Разработка
```bash
python main.py
```

### Продакшн (с systemd)
```bash
sudo cp daftbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable daftbot
sudo systemctl start daftbot
```

## Команды бота

### Настройка фильтров
- `/add_area Dublin 1` - добавить район для поиска
- `/remove_area Dublin 6` - удалить район из поиска
- `/list_areas` - показать текущие районы
- `/set_city Dublin` - установить город для поиска
- `/set_max_price 2500` - установить максимальную цену
- `/set_min_bedrooms 3` - установить минимальное количество спален

### Управление
- `/status` - показать текущие настройки
- `/start_monitoring` - запустить мониторинг
- `/stop_monitoring` - остановить мониторинг
- `/help` - показать помощь

## Структура проекта
```
daftparser/
├── main.py              # Главный файл приложения
├── bot/
│   ├── __init__.py
│   ├── handlers.py      # Обработчики команд Telegram
│   └── keyboards.py     # Клавиатуры для бота
├── parser/
│   ├── __init__.py
│   ├── daft_parser.py   # Парсер сайта daft.ie
│   └── models.py        # Модели данных
├── database/
│   ├── __init__.py
│   ├── database.py      # Работа с SQLite
│   └── models.py        # Модели базы данных
├── config/
│   ├── __init__.py
│   └── settings.py      # Настройки приложения
├── utils/
│   ├── __init__.py
│   └── helpers.py       # Вспомогательные функции
├── requirements.txt
├── .env.example
├── daftbot.service      # Systemd сервис
└── README.md
```

## Автозапуск на Ubuntu

### 1. Создание systemd сервиса
```bash
sudo nano /etc/systemd/system/daftbot.service
```

### 2. Содержимое сервиса (см. daftbot.service)

### 3. Активация сервиса
```bash
sudo systemctl daemon-reload
sudo systemctl enable daftbot
sudo systemctl start daftbot
sudo systemctl status daftbot
```

## Логи
```bash
# Просмотр логов
sudo journalctl -u daftbot -f

# Логи за последний час
sudo journalctl -u daftbot --since "1 hour ago"
```

## Автор
Создано для автоматизации поиска жилья в Дублине через daft.ie
