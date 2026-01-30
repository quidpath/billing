@echo off
REM Diagnostic Script - Identify and report issues with the deployment

echo ==========================================
echo 🔍 QuidPath Services Diagnostic Tool
echo ==========================================
echo.

set ISSUES_FOUND=0

REM Check Docker is running
echo [1/10] Checking Docker...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Docker is not running or not installed
    set /a ISSUES_FOUND+=1
) else (
    echo ✓ Docker is running
)
echo.

REM Check shared network exists
echo [2/10] Checking shared network...
docker network inspect quidpath_network >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ Shared network 'quidpath_network' does not exist
    echo   Fix: docker network create quidpath_network
    set /a ISSUES_FOUND+=1
) else (
    echo ✓ Shared network exists
)
echo.

REM Check Main Backend container
echo [3/10] Checking Main Backend container...
docker ps --filter "name=django-backend" --format "{{.Names}}" | findstr "django-backend" >nul
if %errorlevel% neq 0 (
    echo ✗ Main Backend container is not running
    echo   Fix: cd quidpath-backend ^&^& docker compose up -d
    set /a ISSUES_FOUND+=1
) else (
    echo ✓ Main Backend container is running
)
echo.

REM Check Billing container
echo [4/10] Checking Billing container...
docker ps --filter "name=billing-backend" --format "{{.Names}}" | findstr "billing-backend" >nul
if %errorlevel% neq 0 (
    echo ✗ Billing container is not running
    echo   Fix: cd billing ^&^& docker compose up -d
    set /a ISSUES_FOUND+=1
) else (
    echo ✓ Billing container is running
)
echo.

REM Check Tazama AI container
echo [5/10] Checking Tazama AI container...
docker ps --filter "name=tazama-ai-backend" --format "{{.Names}}" | findstr "tazama-ai-backend" >nul
if %errorlevel% neq 0 (
    echo ✗ Tazama AI container is not running
    echo   Fix: cd tazama-ai-microservice ^&^& docker compose up -d
    set /a ISSUES_FOUND+=1
) else (
    echo ✓ Tazama AI container is running
)
echo.

REM Check Main Backend database
echo [6/10] Checking Main Backend database...
docker ps --filter "name=postgres_prod" --format "{{.Names}}" | findstr "postgres_prod" >nul
if %errorlevel% neq 0 (
    echo ✗ Main Backend database is not running
    set /a ISSUES_FOUND+=1
) else (
    echo ✓ Main Backend database is running
)
echo.

REM Check Billing database
echo [7/10] Checking Billing database...
docker ps --filter "name=postgres_billing_prod" --format "{{.Names}}" | findstr "postgres_billing_prod" >nul
if %errorlevel% neq 0 (
    echo ✗ Billing database is not running
    set /a ISSUES_FOUND+=1
) else (
    echo ✓ Billing database is running
)
echo.

REM Check Tazama database
echo [8/10] Checking Tazama database...
docker ps --filter "name=tazama_postgres" --format "{{.Names}}" | findstr "tazama_postgres" >nul
if %errorlevel% neq 0 (
    echo ✗ Tazama database is not running
    set /a ISSUES_FOUND+=1
) else (
    echo ✓ Tazama database is running
)
echo.

REM Check port availability
echo [9/10] Checking port availability...
netstat -an | findstr ":8000.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo ✓ Port 8000 is in use (Main Backend)
) else (
    echo ✗ Port 8000 is not in use
    set /a ISSUES_FOUND+=1
)

netstat -an | findstr ":8002.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo ✓ Port 8002 is in use (Billing)
) else (
    echo ✗ Port 8002 is not in use
    set /a ISSUES_FOUND+=1
)

netstat -an | findstr ":8001.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo ✓ Port 8001 is in use (Tazama AI)
) else (
    echo ✗ Port 8001 is not in use
    set /a ISSUES_FOUND+=1
)
echo.

REM Check service health
echo [10/10] Checking service health...
curl -s -f http://localhost:8000/api/auth/health/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Main Backend is healthy
) else (
    echo ✗ Main Backend health check failed
    set /a ISSUES_FOUND+=1
)

curl -s -f http://localhost:8002/api/billing/health/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Billing Service is healthy
) else (
    echo ✗ Billing Service health check failed
    set /a ISSUES_FOUND+=1
)

curl -s -f http://localhost:8001/api/tazama/ >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Tazama AI is healthy
) else (
    echo ✗ Tazama AI health check failed
    set /a ISSUES_FOUND+=1
)
echo.

REM Summary
echo ==========================================
echo 📊 Diagnostic Summary
echo ==========================================
if %ISSUES_FOUND% equ 0 (
    echo ✅ No issues found! All services are running correctly.
) else (
    echo ⚠️  Found %ISSUES_FOUND% issue(s)
    echo.
    echo Recommended actions:
    echo 1. Check the specific errors above
    echo 2. View logs: docker compose logs -f
    echo 3. Try redeploying: deploy-all-production.bat
    echo 4. For billing password issues: fix-billing-password.bat
)
echo.

REM Show recent errors from logs
echo ==========================================
echo 📜 Recent Errors (Last 20 lines)
echo ==========================================
echo.
echo Main Backend:
cd quidpath-backend
docker compose logs --tail=20 backend 2>nul | findstr /i "error fail exception"
cd ..
echo.

echo Billing:
cd billing
docker compose logs --tail=20 backend 2>nul | findstr /i "error fail exception"
cd ..
echo.

echo Tazama AI:
cd tazama-ai-microservice
docker compose logs --tail=20 web 2>nul | findstr /i "error fail exception"
cd ..
echo.

pause
