#!/bin/bash
set -e

# Wait for database to be ready (if using external database)
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database..."
    python << EOF
import sys
import time
import os
from urllib.parse import urlparse
import socket

db_url = os.getenv('DATABASE_URL', '')
if db_url:
    parsed = urlparse(db_url)
    host = parsed.hostname
    port = parsed.port or 5432
    
    for i in range(30):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                print(f"Database at {host}:{port} is ready")
                sys.exit(0)
        except Exception as e:
            pass
        time.sleep(1)
    
    print(f"Warning: Could not connect to database at {host}:{port}")
    sys.exit(0)
EOF
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files (includes frontend build)
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Seed templates if needed (idempotent)
echo "Seeding templates..."
python manage.py seed_templates || true

# Start services based on CMD
if [ "$1" = "server" ]; then
    echo "Starting Django server..."
    exec python manage.py runserver 0.0.0.0:8000
elif [ "$1" = "worker" ]; then
    echo "Starting Celery worker..."
    exec celery -A backend.celery_app worker -l info
elif [ "$1" = "both" ]; then
    echo "Starting both Django server and Celery worker..."
    # Start celery in background
    celery -A backend.celery_app worker -l info &
    # Start django in foreground
    exec python manage.py runserver 0.0.0.0:8000
else
    exec "$@"
fi

