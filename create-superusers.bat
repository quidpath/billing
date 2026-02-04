@echo off
REM Manually create superusers for all services

echo ========================================
echo Creating Superusers
echo ========================================
echo.

echo Creating Backend superuser...
docker exec -it django-backend-dev python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@quidpath.com', 'admin123'); print('Backend superuser ready')"
echo.

echo Creating Billing superuser...
docker exec -it billing-backend-dev python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@billing.com', 'admin123'); print('Billing superuser ready')"
echo.

echo Creating Tazama superuser...
docker exec -it tazama-ai-backend-dev python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@tazama.com', 'admin123'); print('Tazama superuser ready')"
echo.

echo ========================================
echo Superusers Created!
echo ========================================
echo.
echo You can now login with:
echo   Username: admin
echo   Password: admin123
echo.
pause
