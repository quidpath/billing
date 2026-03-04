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

# Load environment variables from .env without sourcing (avoids shell interpreting $()& etc.)
if [ -f .env ]; then
  echo "Loading environment variables from .env"
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      # Strip surrounding single or double quotes so JWT_SECRET_KEY etc. work
      value="${value#\'}"; value="${value%\'}"
      value="${value#\"}"; value="${value%\"}"
      export "$key=$value"
    fi
  done < .env
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



