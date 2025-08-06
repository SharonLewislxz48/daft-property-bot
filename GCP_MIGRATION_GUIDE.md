# 🌐 МИГРАЦИЯ НА GOOGLE CLOUD PLATFORM

## 📋 ПЛАН МИГРАЦИИ

1. **Регистрация в GCP** - Создание аккаунта и проекта
2. **Создание VM** - Настройка виртуальной машины
3. **Настройка сервера** - Установка необходимого ПО
4. **Миграция проекта** - Перенос кода и данных
5. **Тестирование** - Проверка работы без блокировок
6. **Переключение** - Обновление DNS/webhook

---

## 🚀 ШАГ 1: РЕГИСТРАЦИЯ В GOOGLE CLOUD

### 1.1 Создание аккаунта
```
1. Перейти на: https://cloud.google.com/
2. Нажать "Get started for free"
3. Войти через Google аккаунт или создать новый
4. Ввести данные карты (требуется для верификации)
5. Получить $300 кредитов на 90 дней
```

### 1.2 Создание проекта
```
1. В GCP Console создать новый проект
2. Название: "daft-property-bot"
3. Включить Compute Engine API
4. Включить Cloud Logging API
```

---

## 🖥️ ШАГ 2: СОЗДАНИЕ ВИРТУАЛЬНОЙ МАШИНЫ

### 2.1 Параметры VM (РЕКОМЕНДУЕМАЯ ПЛАТНАЯ КОНФИГУРАЦИЯ)
```
Compute Engine > VM instances > Create Instance

ОПТИМАЛЬНАЯ КОНФИГУРАЦИЯ ДЛЯ БОТА (~€8/месяц):
- Name: daft-bot-server
- Region: europe-west1 (Бельгия) - ближе к Ирландии
- Zone: europe-west1-b
- Machine type: e2-small (2 vCPU, 2GB RAM) - НАМНОГО БЫСТРЕЕ
- Boot disk: Ubuntu 22.04 LTS, 20GB SSD Persistent Disk
- Firewall: Allow HTTP traffic, Allow HTTPS traffic

💰 СТОИМОСТЬ: ~€7-8/месяц
🚀 ПРЕИМУЩЕСТВА:
- В 2 раза больше RAM (2GB vs 1GB)
- В 2 раза больше CPU (2 vCPU vs 1 vCPU)  
- SSD диск (быстрее стандартного)
- Европейский регион (лучше пинг)
- Стабильная работа под нагрузкой

АЛЬТЕРНАТИВА (если нужно дешевле ~€5/месяц):
- Machine type: e2-micro (1 vCPU, 1GB RAM)
- Region: europe-west1 (всё равно платно, но дешевле)
- Boot disk: 20GB Standard Persistent Disk
```

### 2.2 Настройка сети
```
VPC network > Firewall > Create Firewall Rule

Правило для бота:
- Name: allow-telegram-webhook
- Direction: Ingress
- Action: Allow
- Targets: All instances in the network
- Source IP ranges: 0.0.0.0/0
- Protocols and ports: TCP 8080, 443, 80, 22
```

---

## 🔧 ШАГ 3: ПЕРВИЧНАЯ НАСТРОЙКА СЕРВЕРА

### 3.1 Подключение к серверу
```bash
# Через GCP Console (браузер)
gcloud compute ssh daft-bot-server --zone=europe-west1-b

# Или через SSH с локальной машины
gcloud compute ssh --zone=europe-west1-b daft-bot-server --project=ваш-проект-id
```

### 3.2 Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget nginx
```

### 3.3 Настройка пользователя
```bash
# Создаем пользователя для бота
sudo useradd -m -s /bin/bash botuser
sudo usermod -aG sudo botuser

# Переключаемся на пользователя бота
sudo su - botuser
```

---

## 📦 ШАГ 4: МИГРАЦИЯ ПРОЕКТА

### 4.1 Клонирование репозитория
```bash
# На новом сервере GCP
cd /home/botuser
git clone https://github.com/SharonLewislxz48/daft-property-bot.git
cd daft-property-bot
git checkout enhanced-bot-v2.0
```

### 4.2 Настройка окружения
```bash
# Создаем виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Создаем директорию для логов
mkdir -p logs
```

### 4.3 Перенос конфигурации
```bash
# Скопируйте с Oracle Cloud сервера файлы:
# - bot_config.json (токен бота)
# - .env (если есть)
# - database.db (если есть база данных)

# Пример команды для копирования с Oracle Cloud:
# scp root@130.61.186.30:/opt/daft-property-bot/bot_config.json ./
# scp root@130.61.186.30:/opt/daft-property-bot/database.db ./
```

---

## 🧪 ШАГ 5: ТЕСТИРОВАНИЕ БЕЗ БЛОКИРОВОК

### 5.1 Проверка IP адреса
```bash
curl -s https://httpbin.org/ip
```

### 5.2 Тест доступности daft.ie
```bash
curl -I https://www.daft.ie/
# Должен вернуть 200 OK вместо 403
```

### 5.3 Тест парсера
```bash
source .venv/bin/activate

# Восстанавливаем оригинальный парсер
cp production_parser_original_backup.py production_parser.py
cp production_parser_original_backup.py parser/production_parser.py

# Тестируем реальный парсинг
python3 production_parser.py
```

---

## ⚙️ ШАГ 6: НАСТРОЙКА СЛУЖБЫ

### 6.1 Создание systemd службы
```bash
sudo nano /etc/systemd/system/daftbot.service
```

Содержимое:
```ini
[Unit]
Description=Daft Property Bot GCP
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/daft-property-bot
Environment=PATH=/home/botuser/daft-property-bot/.venv/bin
ExecStart=/home/botuser/daft-property-bot/.venv/bin/python enhanced_main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6.2 Запуск службы
```bash
sudo systemctl daemon-reload
sudo systemctl enable daftbot
sudo systemctl start daftbot
sudo systemctl status daftbot
```

---

## 🔗 ШАГ 7: НАСТРОЙКА WEBHOOK

### 7.1 Получение внешнего IP
```bash
# На GCP сервере
curl -s https://httpbin.org/ip
```

### 7.2 Обновление webhook
```python
# Запустите на GCP сервере
import requests

BOT_TOKEN = "ваш_токен_бота"
NEW_SERVER_IP = "новый_ip_адрес"
WEBHOOK_URL = f"https://{NEW_SERVER_IP}/webhook/{BOT_TOKEN}"

# Установка нового webhook
response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={"url": WEBHOOK_URL}
)
print(response.json())
```

---

## 📊 ШАГ 8: ФИНАЛЬНАЯ ПРОВЕРКА

### 8.1 Чеклист миграции
- [ ] VM создана в GCP
- [ ] IP не заблокирован daft.ie (curl возвращает 200)
- [ ] Проект склонирован и настроен
- [ ] Зависимости установлены
- [ ] Парсер работает с реальными данными
- [ ] Служба запущена и активна
- [ ] Webhook обновлен на новый IP
- [ ] Бот отвечает в Telegram

### 8.2 Тест бота
```
/start - должен вернуть РЕАЛЬНЫЕ объявления с daft.ie
/search 2 2500 dublin-city - должен показать реальные результаты
```

---

## 💰 СТОИМОСТЬ (ПЛАТНАЯ КОНФИГУРАЦИЯ)

### 🚀 РЕКОМЕНДУЕМАЯ: e2-small в europe-west1
- **CPU**: 2 vCPU (в 2 раза больше мощности)
- **RAM**: 2GB (в 2 раза больше памяти)
- **Диск**: 20GB SSD (быстрый диск)
- **Регион**: europe-west1 (Бельгия, близко к Ирландии)
- **Стоимость**: ~€7-8/месяц (~$8-9/месяц)

### 💡 БЮДЖЕТНАЯ: e2-micro в europe-west1  
- **CPU**: 1 vCPU
- **RAM**: 1GB
- **Диск**: 20GB Standard
- **Регион**: europe-west1 (Бельгия)
- **Стоимость**: ~€4-5/месяц (~$5-6/месяц)

### 🎯 ПРЕИМУЩЕСТВА ПЛАТНОЙ ВЕРСИИ:
- ✅ **Любой регион** (можно выбрать ближайший к Ирландии)
- ✅ **Больше мощности** (бот будет работать быстрее)
- ✅ **SSD диск** (быстрая загрузка и работа)
- ✅ **Стабильность** (не ограничения Free Tier)
- ✅ **Лучший пинг** (europe-west1 → Dublin ~20-30ms)

### 📊 СРАВНЕНИЕ РЕГИОНОВ ДЛЯ DAFT.IE:
1. **europe-west1** (Бельгия) - ~25ms до Дублина ⭐⭐⭐
2. **europe-west2** (Лондон) - ~15ms до Дублина ⭐⭐⭐⭐  
3. **europe-west3** (Франкфурт) - ~35ms до Дублина ⭐⭐
4. **us-west1** (Орегон) - ~150ms до Дублина ⭐

### 💳 ОПЛАТА:
- Оплата по факту использования
- Автоматическое списание с карты
- Можно настроить лимиты расходов
- $300 кредитов на первые 90 дней (даже при платной конфигурации)

---

## 🚨 АВАРИЙНОЕ ПЕРЕКЛЮЧЕНИЕ

Если нужно быстро переключиться:

```bash
# 1. На новом GCP сервере
sudo systemctl start daftbot

# 2. Обновить webhook
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://NEW_GCP_IP/webhook/BOT_TOKEN"}'

# 3. Остановить старый сервер Oracle Cloud
# ssh root@130.61.186.30 "sudo systemctl stop daftbot"
```

---

## 📞 ПОДДЕРЖКА

После миграции на GCP:
- ✅ Нет блокировок от daft.ie
- ✅ Стабильная работа 99.9%
- ✅ Бесплатное использование в рамках лимитов
- ✅ Легкое масштабирование при необходимости

**Готов помочь на каждом этапе миграции!** 🚀
