#!/bin/bash
set -e

echo "Ожидание запуска SQL Server..."

# Ждём пока SQL Server станет доступен (до 60 секунд)
for i in $(seq 1 30); do
    /opt/mssql-tools/bin/sqlcmd \
        -S "$DB_SERVER" \
        -U "$DB_USER" \
        -P "$DB_PASSWORD" \
        -Q "SELECT 1" \
        > /dev/null 2>&1 && break
    echo "SQL Server недоступен, попытка $i/30..."
    sleep 2
done

echo "SQL Server готов. Инициализация базы данных..."

/opt/mssql-tools/bin/sqlcmd \
    -S "$DB_SERVER" \
    -U "$DB_USER" \
    -P "$DB_PASSWORD" \
    -i /app/docker/init-db.sql \
    -b

echo "База данных инициализирована. Запуск приложения..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 app:app
