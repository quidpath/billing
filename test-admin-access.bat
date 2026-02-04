@echo off
REM Test if admin panels are accessible

echo ========================================
echo Testing Admin Panel Access
echo ========================================
echo.

echo Testing Backend Admin (http://localhost:8000/admin/)...
curl -s -o nul -w "Status: %%{http_code}\n" http://localhost:8000/admin/
echo.

echo Testing Billing Admin (http://localhost:8002/admin/)...
curl -s -o nul -w "Status: %%{http_code}\n" http://localhost:8002/admin/
echo.

echo Testing Tazama Admin (http://localhost:8001/admin/)...
curl -s -o nul -w "Status: %%{http_code}\n" http://localhost:8001/admin/
echo.

echo ========================================
echo Status Code Guide:
echo   200 = OK (Admin panel accessible)
echo   302 = Redirect (Admin panel working, redirecting to login)
echo   000 = Service not responding
echo   500 = Server error (check logs)
echo ========================================
echo.

echo Opening admin panels in browser...
start http://localhost:8000/admin/
timeout /t 2 /nobreak >nul
start http://localhost:8002/admin/
timeout /t 2 /nobreak >nul
start http://localhost:8001/admin/
echo.

echo Admin panels should now be open in your browser.
echo Login with: admin / admin123
echo.
pause
