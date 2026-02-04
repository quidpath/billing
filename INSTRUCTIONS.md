# Development Environment Setup Instructions

## Current Status

All configuration files have been updated and fixed:

### Fixed Issues:
1. ✅ Tazama settings module corrected (was using `settings.dev`, now uses `settings`)
2. ✅ Removed auth_db configuration from Tazama (services are now independent)
3. ✅ All ALLOWED_HOSTS configured correctly for localhost access
4. ✅ JWT middleware configured to allow admin panel access
5. ✅ All docker-compose.dev.yml files properly configured
6. ✅ Database ports properly mapped (5432, 5433, 5434)

## What You Need to Do

### Step 1: Start All Services

Open PowerShell or CMD in the root directory (where all 4 folders are) and run:

```bash
cd billing
.\start-all-dev.bat
```

**What this does:**
- Creates shared Docker network `quidpath_network`
- Stops any existing containers
- Builds and starts all 3 services (Backend, Billing, Tazama)
- Waits for databases to initialize
- Runs migrations on all services
- Creates admin superusers (username: admin, password: admin123)

**Expected output:**
- You should see services starting
- Migrations running
- Superusers being created
- Final message: "Ready to develop!"

### Step 2: Verify Services Are Running

Run the diagnostic script:

```bash
.\check-dev-services.bat
```

**What to look for:**
- All 3 containers should be running: `django-backend-dev`, `billing-backend-dev`, `tazama-ai-backend-dev`
- Health checks should show: Backend: OK, Billing: OK, Tazama: OK

### Step 3: Test Admin Access

Run the test script:

```bash
.\test-admin-access.bat
```

**What this does:**
- Tests HTTP status of all admin panels
- Opens admin panels in your browser

**Expected status codes:**
- 200 or 302 = Working correctly
- 000 = Service not responding (wait longer or check logs)
- 500 = Server error (check logs)

### Step 4: Login to Admin Panels

The script will open these URLs in your browser:
- http://localhost:8000/admin (Backend)
- http://localhost:8002/admin (Billing)
- http://localhost:8001/admin (Tazama)

**Login credentials:**
- Username: `admin`
- Password: `admin123`

## If Admin Panels Don't Load

### Option 1: Check Container Logs

```bash
docker logs django-backend-dev
docker logs billing-backend-dev
docker logs tazama-ai-backend-dev
```

Look for errors like:
- Database connection errors
- Migration errors
- Port binding errors

### Option 2: Manually Create Superusers

If you can access the admin panel but can't login:

```bash
.\create-superusers.bat
```

### Option 3: Restart Services

```bash
cd quidpath-backend
docker compose -f docker-compose.dev.yml restart

cd ../billing
docker compose -f docker-compose.dev.yml restart

cd ../tazama-ai-microservice
docker compose -f docker-compose.dev.yml restart
```

### Option 4: Full Rebuild

If nothing works, do a full rebuild:

```bash
cd quidpath-backend
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d --build

cd ../billing
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d --build

cd ../tazama-ai-microservice
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d --build
```

Then wait 30 seconds and run migrations:

```bash
docker exec django-backend-dev python manage.py migrate
docker exec billing-backend-dev python manage.py migrate
docker exec tazama-ai-backend-dev python manage.py migrate
```

Then create superusers:

```bash
.\create-superusers.bat
```

## Common Issues and Solutions

### Issue: "Port already in use"

**Solution:**
```bash
# Stop all containers
docker compose -f docker-compose.dev.yml down

# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :8002
netstat -ano | findstr :8001

# Kill the process or change port in docker-compose.dev.yml
```

### Issue: "Cannot connect to database"

**Solution:**
- Wait 30 seconds for database to initialize
- Check database logs: `docker logs postgres_dev`
- Restart service: `docker compose -f docker-compose.dev.yml restart`

### Issue: "relation 'auth_user' does not exist"

**Solution:**
- Run migrations: `docker exec django-backend-dev python manage.py migrate`
- Check migrations status: `docker exec django-backend-dev python manage.py showmigrations`

### Issue: "CSRF verification failed"

**Solution:**
- Clear browser cookies
- Try incognito/private mode
- Check ALLOWED_HOSTS in .env.dev includes localhost

### Issue: "Admin panel shows 404"

**Solution:**
- Verify URL is correct: http://localhost:8000/admin/ (note the trailing slash)
- Check container is running: `docker ps`
- Check logs: `docker logs django-backend-dev`

## Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                  quidpath_network                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Backend    │  │   Billing    │  │   Tazama     │ │
│  │ localhost:   │  │ localhost:   │  │ localhost:   │ │
│  │   8000       │  │   8002       │  │   8001       │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │          │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐ │
│  │ PostgreSQL   │  │ PostgreSQL   │  │ PostgreSQL   │ │
│  │ Port: 5432   │  │ Port: 5433   │  │ Port: 5434   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Development Workflow

1. **Start services**: `.\start-all-dev.bat`
2. **Make code changes**: Files are mounted as volumes (hot reload)
3. **View logs**: `docker logs -f django-backend-dev`
4. **Run tests**: `docker exec django-backend-dev python manage.py test`
5. **Access shell**: `docker exec -it django-backend-dev python manage.py shell`
6. **Stop services**: `docker compose -f docker-compose.dev.yml down`

## Useful Commands

### View All Running Containers
```bash
docker ps
```

### View Logs (Follow Mode)
```bash
docker logs -f django-backend-dev
docker logs -f billing-backend-dev
docker logs -f tazama-ai-backend-dev
```

### Access Django Shell
```bash
docker exec -it django-backend-dev python manage.py shell
docker exec -it billing-backend-dev python manage.py shell
docker exec -it tazama-ai-backend-dev python manage.py shell
```

### Run Migrations
```bash
docker exec django-backend-dev python manage.py migrate
docker exec billing-backend-dev python manage.py migrate
docker exec tazama-ai-backend-dev python manage.py migrate
```

### Create Superuser
```bash
docker exec -it django-backend-dev python manage.py createsuperuser
docker exec -it billing-backend-dev python manage.py createsuperuser
docker exec -it tazama-ai-backend-dev python manage.py createsuperuser
```

### Stop All Services
```bash
docker compose -f docker-compose.dev.yml down
```

### Rebuild Containers
```bash
docker compose -f docker-compose.dev.yml up -d --build --force-recreate
```

### Clean Up Everything
```bash
docker compose -f docker-compose.dev.yml down -v
docker system prune -a
```

## Next Steps

Once all services are running and admin panels are accessible:

1. ✅ Verify you can login to all 3 admin panels
2. ✅ Create test data (users, corporates, subscriptions)
3. ✅ Test API endpoints
4. ✅ Test inter-service communication
5. ✅ Develop new features
6. ✅ Run tests before committing

## Files Reference

- `start-all-dev.bat` - Main startup script
- `check-dev-services.bat` - Diagnostic script
- `test-admin-access.bat` - Test admin panels
- `create-superusers.bat` - Create admin users
- `QUICK-START-DEV.md` - Quick start guide
- `DEV-ENVIRONMENT-GUIDE.txt` - Detailed guide
- `START-HERE.txt` - Quick reference

## Support

If you encounter issues not covered here:

1. Check Docker Desktop is running
2. Check container logs for errors
3. Verify ports are not in use
4. Try full rebuild with `-v` flag
5. Check .env.dev files are correct

## Summary

**To get started right now:**

1. Open PowerShell/CMD
2. Navigate to billing folder
3. Run: `.\start-all-dev.bat`
4. Wait 1-2 minutes
5. Run: `.\test-admin-access.bat`
6. Login with admin/admin123

That's it! You should now have all services running with accessible admin panels.
