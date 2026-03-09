

FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего кода приложения
COPY . .

# Создание директорий для данных и логов
RUN mkdir -p /app/data /app/logs

# Установка переменных окружения по умолчанию
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Команда по умолчанию
CMD ["python", "-m", "app.websocket.start_websocket"]
