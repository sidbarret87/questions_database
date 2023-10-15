#создание миграции
alembic revision --autogenerate -m "create question table"


# Запуск Alembic миграций
alembic upgrade head


# Запуск приложения
uvicorn main:app --host 0.0.0.0 --port 80