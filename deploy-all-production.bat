@echo off
REM Production Deployment Script for QuidPath Multi-Service Architecture
REM This script deploys the main backend and all microservices with shared authentication

echo ==========================================
echo 🚀 QuidPath Production Deployment
echo ==========================================
echo.

REM Step 1: Create shared Docker network
echo ==========================================
echo 📡 Step 1: Setting up shared network
echo ==========================================
docker network inspect quidpath_network >nul 2>&1
if %errorlevel% equ 0 (
    echo ℹ Network 'quidpath_network' already exists
) else (
    docker network create quidpath_network
    echo ✓ Created shared network 'quidpath_network'
)
echo.

REM Step 2: Deploy Main Backend (QuidPath)
echo ==========================================
echo 🏢 Step 2: Deploying Main Backend
echo ==========================================
cd quidpath-backend

echo ℹ Stopping existing containers...
docker compose down

echo ℹ Building and starting main backend...
docker compose up -d --build

echo ℹ Waiting for database to be ready...
timeout /t 10 /nobreak >nul

echo ℹ Running migrations...
docker compose exec -T backend python manage.py migrate --noinput

echo ℹ Creating superuser (if not exists)...
echo from django.contrib.auth import get_user_model > temp_superuser.py
echo User = get_user_model() >> temp_superuser.py
echo if not User.objects.filter(username='admin').exists(): >> temp_superuser.py
echo     User.objects.create_superuser('admin', 'admin@quidpath.com', 'admin123') >> temp_superuser.py
echo     print("Superuser created successfully") >> temp_superuser.py
echo else: >> temp_superuser.py
echo     print("Superuser already exists") >> temp_superuser.py
docker compose exec -T backend python manage.py shell < temp_superuser.py
del temp_superuser.py

echo ℹ Collecting static files...
docker compose exec -T backend python manage.py collectstatic --noinput

echo ✓ Main backend deployed successfully
cd ..
echo.

REM Step 3: Deploy Billing Microservice
echo ==========================================
echo 💳 Step 3: Deploying Billing Microservice
echo ==========================================
cd billing

echo ℹ Stopping existing containers...
docker compose down

echo ℹ Building and starting billing service...
docker compose up -d --build

echo ℹ Waiting for database to be ready...
timeout /t 10 /nobreak >nul

echo ℹ Running migrations for billing database...
docker compose exec -T backend python manage.py migrate --database=default --noinput

echo ℹ Running migrations for shared auth database...
docker compose exec -T backend python manage.py migrate --database=auth_db --noinput

echo ℹ Collecting static files...
docker compose exec -T backend python manage.py collectstatic --noinput

echo ✓ Billing microservice deployed successfully
cd ..
echo.

REM Step 4: Deploy Tazama AI Microservice
echo ==========================================
echo 🤖 Step 4: Deploying Tazama AI Microservice
echo ==========================================
cd tazama-ai-microservice

echo ℹ Stopping existing containers...
docker compose down

echo ℹ Building and starting Tazama AI service...
docker compose up -d --build

echo ℹ Waiting for database to be ready...
timeout /t 10 /nobreak >nul

echo ℹ Running migrations for Tazama database...
docker compose exec -T web python manage.py migrate --database=default --noinput

echo ℹ Running migrations for shared auth database...
docker compose exec -T web python manage.py migrate --database=auth_db --noinput

echo ℹ Collecting static files...
docker compose exec -T web python manage.py collectstatic --noinput

echo ✓ Tazama AI microservice deployed successfully
cd ..
echo.

REM Step 5: Verify all services
echo ==========================================
echo 🔍 Step 5: Verifying Services
echo ==========================================
echo.

echo Checking service health...
echo.

curl -f http://localhost:8000/api/auth/health/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Main Backend (Port 8000): Running
) else (
    echo ✗ Main Backend (Port 8000): Not responding
)

curl -f http://localhost:8002/api/billing/health/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Billing Service (Port 8002): Running
) else (
    echo ✗ Billing Service (Port 8002): Not responding
)

curl -f http://localhost:8001/api/tazama/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Tazama AI Service (Port 8001): Running
) else (
    echo ✗ Tazama AI Service (Port 8001): Not responding
)

echo.
echo ==========================================
echo ✅ Deployment Complete!
echo ==========================================
echo.
echo Service URLs:
echo   Main Backend:    http://localhost:8000
echo   Billing Service: http://localhost:8002
echo   Tazama AI:       http://localhost:8001
echo.
echo Admin Panel:
echo   URL: http://localhost:8000/admin/
echo   Username: admin
echo   Password: admin123
echo.
echo Note: All services share the same authentication database.
echo You can log into any admin panel with the same credentials.
echo.
pause
