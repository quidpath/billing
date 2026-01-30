@echo off
REM Quick fix script for billing database password issue

echo ==========================================
echo 🔧 Fixing Billing Database Password
echo ==========================================
echo.

cd billing

echo Step 1: Stopping billing containers...
docker compose down
echo.

echo Step 2: Removing old database volume...
docker volume rm billing_postgres_data 2>nul
echo.

echo Step 3: Starting fresh with correct password...
docker compose up -d --build
echo.

echo Step 4: Waiting for database to initialize...
timeout /t 15 /nobreak >nul
echo.

echo Step 5: Running migrations...
docker compose exec -T backend python manage.py migrate --database=default --noinput
docker compose exec -T backend python manage.py migrate --database=auth_db --noinput
echo.

echo Step 6: Collecting static files...
docker compose exec -T backend python manage.py collectstatic --noinput
echo.

echo ==========================================
echo ✅ Billing service fixed!
echo ==========================================
echo.
echo The billing service should now be running on http://localhost:8002
echo.
pause
