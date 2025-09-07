# Dockerfile (Финальная и правильная версия)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 1. Устанавливаем системные зависимости, ВКЛЮЧАЯ Node.js
# Это нужно, чтобы в контейнере были команды 'npm' и 'node'
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    netcat-openbsd && \
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Копируем файлы зависимостей Python и устанавливаем их
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 3. Копируем ВСЕ файлы проекта, включая вашу локальную, РАБОЧУЮ папку node_modules
# Важно, чтобы 'node_modules' уже существовала в корне вашего проекта перед сборкой
COPY . .

# 4. Собираем CSS, используя Node.js из образа и зависимости из скопированной node_modules
RUN npm run css:build

# Команда по умолчанию
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "wsgi:app"]