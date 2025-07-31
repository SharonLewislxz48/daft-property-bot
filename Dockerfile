FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Playwright браузеры
RUN playwright install chromium
RUN playwright install-deps chromium

# Копируем весь проект
COPY . .

# Создаем директории для данных
RUN mkdir -p data logs

# Устанавливаем права
RUN chmod +x run.sh

# Порт (если нужен webhook)
EXPOSE 8000

# Запуск
CMD ["python3", "main.py"]
