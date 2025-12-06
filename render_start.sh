#!/bin/bash
set -e

echo "=== Starting PokeTD Application ==="
echo "Database URL: $DATABASE_URL"

# Инициализация базы данных
echo "Initializing database..."
python -c "
import sys
sys.path.append('/opt/render/project/src')
from backend.create_tables import init_db
init_db()
"

echo "✓ Database initialized"

# Запуск приложения
echo "Starting application..."
exec gunicorn backend.app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:10000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -