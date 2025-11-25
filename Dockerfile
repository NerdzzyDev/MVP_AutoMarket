# Dockerfile
FROM python:3.13-slim

# Работаем в директории приложения
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

COPY alembic_migrate.sh /alembic_migrate.sh
RUN chmod +x /alembic_migrate.sh

# Указываем порт uvicorn
EXPOSE 8081

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081", "--reload"]
