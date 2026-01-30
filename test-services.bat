@echo off
REM Service Testing Script - Verify all services are working correctly

echo ==========================================
echo 🧪 Testing QuidPath Services
echo ==========================================
echo.

REM Test Main Backend
echo Testing Main Backend (Port 8000)...
curl -s -o nul -w "Status: %%{http_code}\n" http://localhost:8000/api/auth/health/
if %errorlevel% equ 0 (
    echo ✓ Main Backend is responding
) else (
    echo ✗ Main Backend is not responding
)
echo.

REM Test Billing Service
echo Testing Billing Service (Port 8002)...
curl -s -o nul -w "Status: %%{http_code}\n" http://localhost:8002/api/billing/health/
if %errorlevel% equ 0 (
    echo ✓ Billing Service is responding
) else (
    echo ✗ Billing Service is not responding
)
echo.

REM Test Tazama AI
echo Testing Tazama AI Service (Port 8001)...
curl -s -o nul -w "Status: %%{http_code}\n" http://localhost:8001/api/tazama/
if %errorlevel% equ 0 (
    echo ✓ Tazama AI is responding
) else (
    echo ✗ Tazama AI is not responding
)
echo.

REM Check Docker containers
echo ==========================================
echo 📦 Docker Container Status
echo ==========================================
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

REM Check Docker network
echo ==========================================
echo 📡 Network Configuration
echo ==========================================
docker network inspect quidpath_network --format "{{range .Containers}}{{.Name}}: {{.IPv4Address}}\n{{end}}"
echo.

REM Check database connections
echo ==========================================
echo 💾 Database Connections
echo ==========================================

echo Main Backend Database:
docker compose -f quidpath-backend/docker-compose.yml exec -T db psql -U quidpath_user -d quidpath_db -c "SELECT version();" 2>nul
if %errorlevel% equ 0 (
    echo ✓ Main database is accessible
) else (
    echo ✗ Main database connection failed
)
echo.

echo Billing Database:
docker compose -f billing/docker-compose.yml exec -T db psql -U billing_user -d billing_prod -c "SELECT version();" 2>nul
if %errorlevel% equ 0 (
    echo ✓ Billing database is accessible
) else (
    echo ✗ Billing database connection failed
)
echo.

echo Tazama Database:
docker compose -f tazama-ai-microservice/docker-compose.yml exec -T db psql -U tazama_user -d tazama_db -c "SELECT version();" 2>nul
if %errorlevel% equ 0 (
    echo ✓ Tazama database is accessible
) else (
    echo ✗ Tazama database connection failed
)
echo.

echo ==========================================
echo ✅ Testing Complete
echo ==========================================
echo.
pause
