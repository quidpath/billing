# QuidPath Services - Quick Reference Card

## 🚀 Quick Commands

### Deploy Everything
```batch
deploy-all-production.bat
```

### Fix Billing Password Issue
```batch
fix-billing-password.bat
```

### Test All Services
```batch
test-services.bat
```

## 🌐 Service URLs

| Service | URL | Admin Panel |
|---------|-----|-------------|
| Main Backend | http://localhost:8000 | http://localhost:8000/admin/ |
| Billing | http://localhost:8002 | http://localhost:8002/admin/ |
| Tazama AI | http://localhost:8001 | http://localhost:8001/admin/ |

## 🔑 Default Credentials

**Username:** `admin`  
**Password:** `admin123`

⚠️ Works for all three admin panels!

## 📊 Database Info

| Service | Database | User | Host |
|---------|----------|------|------|
| Main Backend | quidpath_db | quidpath_user | postgres_prod |
| Billing | billing_prod | billing_user | postgres_billing_prod |
| Tazama AI | tazama_db | tazama_user | tazama_postgres |
| **Shared Auth** | quidpath_db | quidpath_user | postgres_prod |

## 🔧 Common Commands

### View Logs
```batch
REM All services
docker compose logs -f

REM Specific service
docker compose logs -f backend

REM Last 100 lines
docker compose logs --tail=100 backend
```

### Restart Services
```batch
REM Main Backend
cd quidpath-backend
docker compose restart

REM Billing
cd billing
docker compose restart

REM Tazama AI
cd tazama-ai-microservice
docker compose restart
```

### Run Migrations
```batch
REM Main Backend
cd quidpath-backend
docker compose exec backend python manage.py migrate

REM Billing (both databases)
cd billing
docker compose exec backend python manage.py migrate --database=default
docker compose exec backend python manage.py migrate --database=auth_db

REM Tazama AI (both databases)
cd tazama-ai-microservice
docker compose exec web python manage.py migrate --database=default
docker compose exec web python manage.py migrate --database=auth_db
```

### Create Superuser
```batch
REM Only needed for main backend
cd quidpath-backend
docker compose exec backend python manage.py createsuperuser
```

### Access Database Shell
```batch
REM Main Backend
cd quidpath-backend
docker compose exec db psql -U quidpath_user -d quidpath_db

REM Billing
cd billing
docker compose exec db psql -U billing_user -d billing_prod

REM Tazama AI
cd tazama-ai-microservice
docker compose exec db psql -U tazama_user -d tazama_db
```

### Backup Databases
```batch
REM Main Backend
cd quidpath-backend
docker compose exec db pg_dump -U quidpath_user quidpath_db > backup_main.sql

REM Billing
cd billing
docker compose exec db pg_dump -U billing_user billing_prod > backup_billing.sql

REM Tazama AI
cd tazama-ai-microservice
docker compose exec db pg_dump -U tazama_user tazama_db > backup_tazama.sql
```

### Stop All Services
```batch
cd quidpath-backend
docker compose down

cd ..\billing
docker compose down

cd ..\tazama-ai-microservice
docker compose down
```

### Start All Services
```batch
cd quidpath-backend
docker compose up -d

cd ..\billing
docker compose up -d

cd ..\tazama-ai-microservice
docker compose up -d
```

## 🐛 Troubleshooting

### Password Authentication Failed
```batch
fix-billing-password.bat
```

### Service Not Responding
```batch
REM Check if container is running
docker ps

REM Check logs
docker compose logs backend

REM Restart service
docker compose restart backend
```

### Database Connection Issues
```batch
REM Check database is ready
docker compose exec db pg_isready -U <username> -d <database>

REM Check network
docker network inspect quidpath_network
```

### Port Already in Use
```batch
REM Find process using port
netstat -ano | findstr :8000

REM Kill process
taskkill /PID <PID> /F
```

## 📝 Environment Files

### Main Backend (.env)
```env
POSTGRES_DB=quidpath_db
POSTGRES_USER=quidpath_user
POSTGRES_PASSWORD=eDgDiAcayFqcPpXjThL6Ak668
```

### Billing (.env)
```env
POSTGRES_DB=billing_prod
POSTGRES_USER=billing_user
POSTGRES_PASSWORD=BillingSecure2026ChangeThis

AUTH_POSTGRES_DB=quidpath_db
AUTH_POSTGRES_USER=quidpath_user
AUTH_POSTGRES_PASSWORD=eDgDiAcayFqcPpXjThL6Ak668
AUTH_POSTGRES_HOST=postgres_prod
```

### Tazama AI (.env)
```env
POSTGRES_DB=tazama_db
POSTGRES_USER=tazama_user
POSTGRES_PASSWORD=tazama_pass123

AUTH_POSTGRES_DB=quidpath_db
AUTH_POSTGRES_USER=quidpath_user
AUTH_POSTGRES_PASSWORD=eDgDiAcayFqcPpXjThL6Ak668
AUTH_POSTGRES_HOST=postgres_prod
```

## 🔍 Health Checks

```batch
REM Main Backend
curl http://localhost:8000/api/auth/health/

REM Billing
curl http://localhost:8002/api/billing/health/

REM Tazama AI
curl http://localhost:8001/api/tazama/
```

## 📦 Docker Network

All services must be on the `quidpath_network`:

```batch
REM Create network
docker network create quidpath_network

REM Inspect network
docker network inspect quidpath_network

REM List containers on network
docker network inspect quidpath_network --format "{{range .Containers}}{{.Name}}\n{{end}}"
```

## 🎯 Quick Fixes

### Reset Everything
```batch
REM Stop all
cd quidpath-backend && docker compose down
cd ..\billing && docker compose down
cd ..\tazama-ai-microservice && docker compose down

REM Remove volumes (⚠️ deletes all data)
docker volume prune -f

REM Redeploy
cd ..
deploy-all-production.bat
```

### Update Code
```batch
REM Pull latest code
git pull

REM Rebuild and restart
docker compose up -d --build
```

### Clear Logs
```batch
REM Truncate logs
docker compose logs --tail=0 -f
```

## 📞 Support

For detailed documentation, see `DEPLOYMENT-GUIDE.md`
