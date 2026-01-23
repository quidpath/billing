@echo off
echo ========================================
echo  Starting Quidpath Billing Service
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found!
    echo Please copy .env.example to .env and configure it.
    echo.
    pause
    exit /b 1
)

REM Check if database exists
if not exist "db.sqlite3" (
    echo.
    echo [2/4] Database not found. Running migrations...
    python manage.py migrate
    
    echo.
    echo [3/4] Creating sample plans...
    python manage.py shell < seed_plans.py
    
    echo.
    echo [INFO] Database initialized successfully!
    echo [INFO] You may want to create a superuser:
    echo        python manage.py createsuperuser
    echo.
) else (
    echo [2/4] Database found. Skipping migrations.
    echo [3/4] Plans already seeded.
)

echo.
echo [4/4] Starting Django development server on port 8002...
echo.
echo ========================================
echo  Billing Service is starting...
echo  URL: http://localhost:8002
echo  Admin: http://localhost:8002/admin/
echo  API: http://localhost:8002/api/billing/
echo ========================================
echo.
echo Press CTRL+C to stop the server
echo.

python manage.py runserver 8002
