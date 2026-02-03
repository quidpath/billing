#!/bin/bash
set -euo pipefail

echo "Starting Container"

# Path where manage.py lives inside the container
APP_DIR="/app"

if [ ! -f "$APP_DIR/manage.py" ]; then
  echo "ERROR: manage.py not found in $APP_DIR"
  exit 1
fi

cd "$APP_DIR"

# Load environment variables from .env if it exists
if [ -f .env ]; then
  echo "Loading environment variables from .env"
  set -o allexport
  . .env
  set +o allexport
fi

# Detect Python interpreter
PYTHON=$(command -v python3 || command -v python)

if [ -z "$PYTHON" ]; then
  echo "ERROR: No Python interpreter found in PATH"
  exit 1
fi

echo "Using Python at: $PYTHON"

echo "Running makemigrations..."
$PYTHON manage.py makemigrations --noinput

echo "Running migrations on default database only..."
$PYTHON manage.py migrate --database=default --noinput

echo "Collecting static files..."
$PYTHON manage.py collectstatic --noinput

echo "Creating superuser (if not exists)..."
$PYTHON manage.py create_superuser

echo "Starting Gunicorn server..."
exec gunicorn billing_service.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-2} \
    --timeout 120



