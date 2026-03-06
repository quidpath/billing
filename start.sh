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

# Load .env but do NOT overwrite variables already set by Docker/compose/deploy.
# This ensures stage deploy (DATABASE_URL, DJANGO_SETTINGS_MODULE, etc.) wins over a prod .env on the server.
if [ -f .env ]; then
  echo "Loading environment variables from .env (deploy-set vars are preserved)"
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      value="${value#\'}"; value="${value%\'}"
      value="${value#\"}"; value="${value%\"}"
      # Only set if not already set (e.g. by compose from deploy secrets)
      if [[ -z "${!key:-}" ]]; then
        export "$key=$value"
      fi
    fi
  done < .env
fi

# Detect Python interpreter
PYTHON=$(command -v python3 || command -v python)

if [ -z "$PYTHON" ]; then
  echo "ERROR: No Python interpreter found in PATH"
  exit 1
fi

echo " Using Python at: $PYTHON"

echo " Running makemigrations..."
$PYTHON manage.py makemigrations --noinput

echo " Running migrations..."
$PYTHON manage.py migrate --database=default --noinput

echo " Collecting static files..."
$PYTHON manage.py collectstatic --noinput

echo " Creating superuser (if not exists)..."
$PYTHON manage.py create_superuser

echo "Starting Gunicorn server..."
exec gunicorn billing_service.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-2} \
    --timeout 120
