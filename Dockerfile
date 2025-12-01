# Dockerfile
FROM python:3.13-slim

# Работаем в директории приложения
WORKDIR /app

# 1️⃣ Копируем только файл зависимостей
COPY requirements.txt .

# 2️⃣ Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 3️⃣ Копируем весь код приложения
COPY ./app ./app
COPY alembic_migrate.sh /alembic_migrate.sh
RUN chmod +x /alembic_migrate.sh

# 4️⃣ Указываем порт uvicorn
EXPOSE 8081

# 5️⃣ Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081", "--reload"]
