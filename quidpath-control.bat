@echo off
REM QuidPath Master Control Script
REM One script to rule them all

:menu
cls
echo ==========================================
echo 🎮 QuidPath Master Control Panel
echo ==========================================
echo.
echo 1. Deploy All Services (Fresh Start)
echo 2. Fix Billing Password Issue
echo 3. Test All Services
echo 4. Diagnose Issues
echo 5. View Logs (All Services)
echo 6. View Logs (Main Backend)
echo 7. View Logs (Billing)
echo 8. View Logs (Tazama AI)
echo 9. Restart All Services
echo 10. Stop All Services
echo 11. Start All Services
echo 12. Backup All Databases
echo 13. Show Service Status
echo 14. Open Documentation
echo 15. Exit
echo.
set /p choice="Enter your choice (1-15): "

if "%choice%"=="1" goto deploy
if "%choice%"=="2" goto fix_billing
if "%choice%"=="3" goto test
if "%choice%"=="4" goto diagnose
if "%choice%"=="5" goto logs_all
if "%choice%"=="6" goto logs_main
if "%choice%"=="7" goto logs_billing
if "%choice%"=="8" goto logs_tazama
if "%choice%"=="9" goto restart_all
if "%choice%"=="10" goto stop_all
if "%choice%"=="11" goto start_all
if "%choice%"=="12" goto backup
if "%choice%"=="13" goto status
if "%choice%"=="14" goto docs
if "%choice%"=="15" goto end

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:deploy
cls
echo ==========================================
echo 🚀 Deploying All Services
echo ==========================================
call deploy-all-production.bat
pause
goto menu

:fix_billing
cls
echo ==========================================
echo 🔧 Fixing Billing Password Issue
echo ==========================================
call fix-billing-password.bat
pause
goto menu

:test
cls
echo ==========================================
echo 🧪 Testing All Services
echo ==========================================
call test-services.bat
pause
goto menu

:diagnose
cls
echo ==========================================
echo 🔍 Diagnosing Issues
echo ==========================================
call diagnose-issues.bat
pause
goto menu

:logs_all
cls
echo ==========================================
echo 📜 Viewing All Logs (Press Ctrl+C to stop)
echo ==========================================
echo.
echo Main Backend:
cd quidpath-backend
start cmd /k "docker compose logs -f backend"
cd ..
echo.
echo Billing:
cd billing
start cmd /k "docker compose logs -f backend"
cd ..
echo.
echo Tazama AI:
cd tazama-ai-microservice
start cmd /k "docker compose logs -f web"
cd ..
echo.
echo Logs opened in separate windows
pause
goto menu

:logs_main
cls
echo ==========================================
echo 📜 Main Backend Logs (Press Ctrl+C to stop)
echo ==========================================
cd quidpath-backend
docker compose logs -f backend
cd ..
pause
goto menu

:logs_billing
cls
echo ==========================================
echo 📜 Billing Logs (Press Ctrl+C to stop)
echo ==========================================
cd billing
docker compose logs -f backend
cd ..
pause
goto menu

:logs_tazama
cls
echo ==========================================
echo 📜 Tazama AI Logs (Press Ctrl+C to stop)
echo ==========================================
cd tazama-ai-microservice
docker compose logs -f web
cd ..
pause
goto menu

:restart_all
cls
echo ==========================================
echo 🔄 Restarting All Services
echo ==========================================
echo.
echo Restarting Main Backend...
cd quidpath-backend
docker compose restart
cd ..
echo.
echo Restarting Billing...
cd billing
docker compose restart
cd ..
echo.
echo Restarting Tazama AI...
cd tazama-ai-microservice
docker compose restart
cd ..
echo.
echo ✅ All services restarted
pause
goto menu

:stop_all
cls
echo ==========================================
echo ⏹️  Stopping All Services
echo ==========================================
echo.
echo Stopping Main Backend...
cd quidpath-backend
docker compose down
cd ..
echo.
echo Stopping Billing...
cd billing
docker compose down
cd ..
echo.
echo Stopping Tazama AI...
cd tazama-ai-microservice
docker compose down
cd ..
echo.
echo ✅ All services stopped
pause
goto menu

:start_all
cls
echo ==========================================
echo ▶️  Starting All Services
echo ==========================================
echo.
echo Starting Main Backend...
cd quidpath-backend
docker compose up -d
cd ..
echo.
echo Starting Billing...
cd billing
docker compose up -d
cd ..
echo.
echo Starting Tazama AI...
cd tazama-ai-microservice
docker compose up -d
cd ..
echo.
echo ✅ All services started
echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul
echo.
echo Testing services...
curl -s -o nul -w "Main Backend: %%{http_code}\n" http://localhost:8000/api/auth/health/
curl -s -o nul -w "Billing: %%{http_code}\n" http://localhost:8002/api/billing/health/
curl -s -o nul -w "Tazama AI: %%{http_code}\n" http://localhost:8001/api/tazama/
pause
goto menu

:backup
cls
echo ==========================================
echo 💾 Backing Up All Databases
echo ==========================================
echo.
set timestamp=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%
echo Creating backups with timestamp: %timestamp%
echo.

echo Backing up Main Backend database...
cd quidpath-backend
docker compose exec -T db pg_dump -U quidpath_user quidpath_db > ..\backups\main_%timestamp%.sql
cd ..
echo ✓ Main Backend backed up

echo Backing up Billing database...
cd billing
docker compose exec -T db pg_dump -U billing_user billing_prod > ..\backups\billing_%timestamp%.sql
cd ..
echo ✓ Billing backed up

echo Backing up Tazama AI database...
cd tazama-ai-microservice
docker compose exec -T db pg_dump -U tazama_user tazama_db > ..\backups\tazama_%timestamp%.sql
cd ..
echo ✓ Tazama AI backed up

echo.
echo ✅ All databases backed up to 'backups' folder
pause
goto menu

:status
cls
echo ==========================================
echo 📊 Service Status
echo ==========================================
echo.
echo Docker Containers:
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo Network Configuration:
docker network inspect quidpath_network --format "{{range .Containers}}{{.Name}}: {{.IPv4Address}}\n{{end}}" 2>nul
echo.
echo Service Health:
curl -s -o nul -w "Main Backend (8000): %%{http_code}\n" http://localhost:8000/api/auth/health/
curl -s -o nul -w "Billing (8002): %%{http_code}\n" http://localhost:8002/api/billing/health/
curl -s -o nul -w "Tazama AI (8001): %%{http_code}\n" http://localhost:8001/api/tazama/
echo.
pause
goto menu

:docs
cls
echo ==========================================
echo 📚 Opening Documentation
echo ==========================================
echo.
echo 1. Deployment Guide
echo 2. Quick Reference
echo 3. Changes Summary
echo 4. Back to Main Menu
echo.
set /p doc_choice="Enter your choice (1-4): "

if "%doc_choice%"=="1" start DEPLOYMENT-GUIDE.md
if "%doc_choice%"=="2" start QUICK-REFERENCE.md
if "%doc_choice%"=="3" start CHANGES-SUMMARY.md
if "%doc_choice%"=="4" goto menu

goto docs

:end
cls
echo ==========================================
echo 👋 Thank you for using QuidPath Control
echo ==========================================
echo.
echo Service URLs:
echo   Main Backend:    http://localhost:8000
echo   Billing Service: http://localhost:8002
echo   Tazama AI:       http://localhost:8001
echo.
echo Admin Credentials: admin / admin123
echo.
exit /b
