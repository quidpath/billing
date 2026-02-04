@echo off
REM Quick diagnostic script for development services

echo ========================================
echo Development Services Diagnostic
echo ========================================
echo.

echo Checking Docker...
docker --version
echo.

echo Checking running containers...
docker ps
echo.

echo Checking all containers (including stopped)...
docker ps -a
echo.

echo Checking networks...
docker network ls | findstr quidpath
echo.

echo ========================================
echo Container Logs (last 20 lines)
echo ========================================
echo.

echo Backend Logs:
echo ----------------------------------------
docker logs --tail 20 django-backend-dev 2>&1
echo.

echo Billing Logs:
echo ----------------------------------------
docker logs --tail 20 billing-backend-dev 2>&1
echo.

echo Tazama Logs:
echo ----------------------------------------
docker logs --tail 20 tazama-ai-backend-dev 2>&1
echo.

echo ========================================
echo Health Check
echo ========================================
echo.

echo Testing Backend (localhost:8000)...
curl -s http://localhost:8000/admin/ >nul 2>&1 && echo Backend: OK || echo Backend: FAILED
echo.

echo Testing Billing (localhost:8002)...
curl -s http://localhost:8002/admin/ >nul 2>&1 && echo Billing: OK || echo Billing: FAILED
echo.

echo Testing Tazama (localhost:8001)...
curl -s http://localhost:8001/admin/ >nul 2>&1 && echo Tazama: OK || echo Tazama: FAILED
echo.

echo ========================================
echo Diagnostic Complete
echo ========================================
pause
