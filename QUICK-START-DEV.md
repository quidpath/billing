# Quick Start - Development Environment

## Prerequisites
- Docker Desktop installed and running
- Git Bash or PowerShell (Windows) or Terminal (Linux/Mac)

## Start All Services (Recommended)

### Windows
```bash
.\start-all-dev.bat
```

### Linux/Mac
```bash
chmod +x start-all-dev.sh
./start-all-dev.sh
```

This script will:
1. Create shared Docker network
2. Stop any existing containers
3. Build and start all services (Backend, Billing, Tazama)
4. Run database migrations
5. Create admin superusers

## Access Admin Panels

After services start (wait 1-2 minutes), access:

- **Backend Admin**: http://localhost:8000/admin
- **Billing Admin**: http://localhost:8002/admin
- **Tazama Admin**: http://localhost:8001/admin

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

## Troubleshooting

### Admin Panel Not Loading

1. **Check if containers are running:**
   ```bash
   docker ps
   ```
   You should see: `django-backend-dev`, `billing-backend-dev`, `tazama-ai-backend-dev`

2. **Check service logs:**
   ```bash
   docker logs django-backend-dev
   docker logs billing-backend-dev
   docker logs tazama-ai-backend-dev
   ```

3. **Run diagnostic script:**
   ```bash
   .\check-dev-services.bat
   ```

4. **Manually create superusers:**
   ```bash
   .\create-superusers.bat
   ```

### Port Already in Use

If you get "port already in use" error:

1. **Stop existing containers:**
   ```bash
   cd quidpath-backend
   docker compose -f docker-compose.dev.yml down
   cd ../billing
   docker compose -f docker-compose.dev.yml down
   cd ../tazama-ai-microservice
   docker compose -f docker-compose.dev.yml down
   ```

2. **Check what's using the port:**
   ```bash
   netstat -ano | findstr :8000
   netstat -ano | findstr :8002
   netstat -ano | findstr :8001
   ```

3. **Kill the process or change port in docker-compose.dev.yml**

### Database Connection Error

1. **Wait for database to initialize** (15-30 seconds after starting)

2. **Restart the service:**
   ```bash
   cd quidpath-backend
   docker compose -f docker-compose.dev.yml restart
   ```

3. **Check database logs:**
   ```bash
   docker logs postgres_dev
   docker logs postgres_billing_dev
   docker logs postgres_tazama_dev
   ```

### Cannot Login to Admin

1. **Verify superuser exists:**
   ```bash
   docker exec django-backend-dev python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.filter(username='admin').exists())"
   ```

2. **Create superuser manually:**
   ```bash
   docker exec -it django-backend-dev python manage.py createsuperuser
   ```

3. **Reset admin password:**
   ```bash
   docker exec -it django-backend-dev python manage.py changepassword admin
   ```

## Manual Commands

### Start Individual Service

```bash
cd quidpath-backend
docker compose -f docker-compose.dev.yml up -d --build

cd billing
docker compose -f docker-compose.dev.yml up -d --build

cd tazama-ai-microservice
docker compose -f docker-compose.dev.yml up -d --build
```

### Stop Individual Service

```bash
cd quidpath-backend
docker compose -f docker-compose.dev.yml down
```

### View Logs (Follow Mode)

```bash
docker logs -f django-backend-dev
docker logs -f billing-backend-dev
docker logs -f tazama-ai-backend-dev
```

### Run Migrations

```bash
docker exec django-backend-dev python manage.py migrate
docker exec billing-backend-dev python manage.py migrate
docker exec tazama-ai-backend-dev python manage.py migrate
```

### Access Django Shell

```bash
docker exec -it django-backend-dev python manage.py shell
docker exec -it billing-backend-dev python manage.py shell
docker exec -it tazama-ai-backend-dev python manage.py shell
```

### Rebuild Containers

```bash
cd quidpath-backend
docker compose -f docker-compose.dev.yml up -d --build --force-recreate
```

## Service URLs

| Service | URL | Admin Panel |
|---------|-----|-------------|
| Backend | http://localhost:8000 | http://localhost:8000/admin |
| Billing | http://localhost:8002 | http://localhost:8002/admin |
| Tazama AI | http://localhost:8001 | http://localhost:8001/admin |

## Database Ports

| Service | Port | Database Name |
|---------|------|---------------|
| Backend | 5432 | devdb |
| Billing | 5433 | billing_devdb |
| Tazama | 5434 | tazama_devdb |

**Database Credentials:**
- Username: `devuser`
- Password: `devpass`

## Development Workflow

1. **Start services** using `start-all-dev.bat`
2. **Make code changes** (hot reload enabled)
3. **View logs** to debug issues
4. **Run tests** in containers
5. **Stop services** when done

## Common Issues

### "Cannot connect to Docker daemon"
- Make sure Docker Desktop is running
- Restart Docker Desktop

### "Network quidpath_network not found"
- Run: `docker network create quidpath_network`

### "Container name already in use"
- Run: `docker rm -f django-backend-dev billing-backend-dev tazama-ai-backend-dev`

### "Permission denied" (Linux/Mac)
- Run: `chmod +x start-all-dev.sh`

## Next Steps

Once all services are running:

1. Access admin panels and verify login works
2. Create test data (users, corporates, subscriptions)
3. Test API endpoints
4. Develop new features
5. Run tests before committing

## Support

If you encounter issues:
1. Check container logs
2. Verify all containers are running
3. Check database connections
4. Restart services
5. Rebuild containers if needed

Happy coding!
