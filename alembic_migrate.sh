#!/bin/bash
#set -e

#echo "Running Alembic migrations..."
#alembic downgrade base
#alembic upgrade head
#alembic revision --autogenerate -m "create tables"
#alembic upgrade head
#echo "Migrations completed."

# Запуск приложения
exec uvicorn app.main:app --host 0.0.0.0 --port 8081
