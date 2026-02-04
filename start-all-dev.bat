@echo off
REM Start All Development Services Script for Windows
REM This script starts Backend, Billing, and Tazama AI services

echo ========================================
echo Starting QuidPath Development Services
echo ========================================
echo.

REM Create shared network if it doesn't exist
echo Creating shared Docker network...
docker network create quidpath_network 2>nul
echo.

REM Stop any existing containers
echo Stopping existing containers...
cd quidpath-backend
docker compose -f docker-compose.dev.yml down 2>nul
cd ..\billing
docker compose -f docker-compose.dev.yml down 2>nul
cd ..\tazama-ai-microservice
docker compose -f docker-compose.dev.yml down 2>nul
cd ..
echo.

REM Start Backend
echo ========================================
echo Starting Backend Service
echo ========================================
cd quidpath-backend
docker compose -f docker-compose.dev.yml up -d --build
echo Backend starting...
echo.

REM Start Billing
echo ========================================
echo Starting Billing Service
echo ========================================
cd ..\billing
docker compose -f docker-compose.dev.yml up -d --build
echo Billing starting...
echo.

REM Start Tazama AI
echo ========================================
echo Starting Tazama AI Service
echo ========================================
cd ..\tazama-ai-microservice
docker compose -f docker-compose.dev.yml up -d --build
echo Tazama AI starting...
cd ..
echo.

REM Wait for databases to be ready
echo Waiting for databases to initialize (15 seconds)...
timeout /t 15 /nobreak >nul

REM Run migrations and create superusers
echo ========================================
echo Setting Up Services
echo ========================================
echo.

echo Backend: Waiting for service...
timeout /t 5 /nobreak >nul
echo Backend: Running migrations...
docker exec django-backend-dev python manage.py migrate --noinput
if errorlevel 1 (
    echo WARNING: Backend migrations may have failed. Check logs with: docker logs django-backend-dev
)

echo Backend: Creating superuser...
docker exec django-backend-dev python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@quidpath.com', 'admin123')"
if errorlevel 1 (
    echo WARNING: Backend superuser creation may have failed
)

echo.
echo Billing: Waiting for service...
timeout /t 5 /nobreak >nul
echo Billing: Running migrations...
docker exec billing-backend-dev python manage.py migrate --noinput
if errorlevel 1 (
    echo WARNING: Billing migrations may have failed. Check logs with: docker logs billing-backend-dev
)

echo Billing: Creating superuser...
docker exec billing-backend-dev python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@billing.com', 'admin123')"
if errorlevel 1 (
    echo WARNING: Billing superuser creation may have failed
)

echo.
echo Tazama AI: Waiting for service...
timeout /t 5 /nobreak >nul
echo Tazama AI: Running migrations...
docker exec tazama-ai-backend-dev python manage.py migrate --noinput
if errorlevel 1 (
    echo WARNING: Tazama migrations may have failed. Check logs with: docker logs tazama-ai-backend-dev
)

echo Tazama AI: Creating superuser...
docker exec tazama-ai-backend-dev python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@tazama.com', 'admin123')"
if errorlevel 1 (
    echo WARNING: Tazama superuser creation may have failed
)

echo.
echo ========================================
echo All Services Started!
echo ========================================
echo.

echo Service URLs:
echo   Backend:       http://localhost:8000
echo   Backend Admin: http://localhost:8000/admin
echo   Billing:       http://localhost:8002
echo   Billing Admin: http://localhost:8002/admin
echo   Tazama AI:     http://localhost:8001
echo   Tazama Admin:  http://localhost:8001/admin
echo.

echo Admin Credentials:
echo   Username: admin
echo   Password: admin123
echo.

echo Useful Commands:
echo   View logs:     docker logs -f container-name
echo   Stop all:      docker compose -f docker-compose.dev.yml down
echo   Restart:       docker compose -f docker-compose.dev.yml restart
echo.

echo Container Names:
echo   - django-backend-dev
echo   - billing-backend-dev
echo   - tazama-ai-backend-dev
echo.

echo Troubleshooting:
echo   If admin panels don't load:
echo   1. Run: .\check-dev-services.bat
echo   2. Check logs: docker logs django-backend-dev
echo   3. Recreate superusers: .\create-superusers.bat
echo   4. Restart services: docker compose -f docker-compose.dev.yml restart
echo.

echo Ready to develop!
pause
