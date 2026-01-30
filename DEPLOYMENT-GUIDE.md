# QuidPath Multi-Service Production Deployment Guide

## Architecture Overview

This system consists of three interconnected services:

1. **Main Backend** (`quidpath-backend`) - Port 8000
   - Core ERP functionality
   - Shared authentication database
   - User management

2. **Billing Microservice** (`billing`) - Port 8002
   - Payment processing
   - Subscription management
   - Pesaway integration

3. **Tazama AI Microservice** (`tazama-ai-microservice`) - Port 8001
   - AI-powered fraud detection
   - Transaction analysis

## Shared Authentication

All three services share a single authentication database (`quidpath_db`) hosted in the main backend. This means:

- ✅ Create a superuser once in the main backend
- ✅ Use the same credentials to log into all admin panels
- ✅ Users are synchronized across all services
- ✅ No need to create separate users for each service

### Database Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Shared Network                            │
│                  (quidpath_network)                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐│
│  │  Main Backend    │  │  Billing Service │  │  Tazama AI ││
│  │  (Port 8000)     │  │  (Port 8002)     │  │ (Port 8001)││
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬─────┘│
│           │                     │                     │      │
│           │                     │                     │      │
│  ┌────────▼─────────┐  ┌───────▼──────────┐ ┌───────▼─────┐│
│  │  postgres_prod   │  │postgres_billing  │ │tazama_postgres││
│  │  (quidpath_db)   │  │  (billing_prod)  │ │ (tazama_db) ││
│  │  [SHARED AUTH]   │  │                  │ │             ││
│  └──────────────────┘  └──────────────────┘ └─────────────┘│
│           ▲                     ▲                     ▲      │
│           │                     │                     │      │
│           └─────────────────────┴─────────────────────┘      │
│                    All services read auth from here          │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Docker and Docker Compose installed
- Ports 8000, 8001, 8002 available
- Sufficient disk space for databases

## Quick Start (Windows)

### Option 1: Full Deployment

```batch
deploy-all-production.bat
```

This will:
1. Create shared Docker network
2. Deploy main backend with database
3. Deploy billing microservice
4. Deploy Tazama AI microservice
5. Run all migrations
6. Create superuser (admin/admin123)
7. Verify all services

### Option 2: Fix Billing Password Issue Only

If you're experiencing the password authentication error:

```batch
fix-billing-password.bat
```

This will:
1. Stop billing containers
2. Remove old database volume
3. Start fresh with correct password
4. Run migrations

## Quick Start (Linux/Mac)

```bash
chmod +x deploy-all-production.sh
sudo ./deploy-all-production.sh
```

## Manual Deployment

### Step 1: Create Shared Network

```bash
docker network create quidpath_network
```

### Step 2: Deploy Main Backend

```bash
cd quidpath-backend
docker compose down
docker compose up -d --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py collectstatic --noinput
```

### Step 3: Deploy Billing Service

```bash
cd ../billing
docker compose down
docker compose up -d --build
docker compose exec backend python manage.py migrate --database=default
docker compose exec backend python manage.py migrate --database=auth_db
docker compose exec backend python manage.py collectstatic --noinput
```

### Step 4: Deploy Tazama AI

```bash
cd ../tazama-ai-microservice
docker compose down
docker compose up -d --build
docker compose exec web python manage.py migrate --database=default
docker compose exec web python manage.py migrate --database=auth_db
docker compose exec web python manage.py collectstatic --noinput
```

## Accessing the Services

### Admin Panels

- **Main Backend**: http://localhost:8000/admin/
- **Billing Service**: http://localhost:8002/admin/
- **Tazama AI**: http://localhost:8001/admin/

**Default Credentials** (all services):
- Username: `admin`
- Password: `admin123`

⚠️ **Change these credentials in production!**

### API Endpoints

- **Main Backend**: http://localhost:8000/api/
- **Billing Service**: http://localhost:8002/api/billing/
- **Tazama AI**: http://localhost:8001/api/tazama/

### Health Checks

```bash
# Main Backend
curl http://localhost:8000/api/auth/health/

# Billing Service
curl http://localhost:8002/api/billing/health/

# Tazama AI
curl http://localhost:8001/api/tazama/
```

## Troubleshooting

### Password Authentication Failed

**Error**: `FATAL: password authentication failed for user "billing_user"`

**Solution**:
1. Run `fix-billing-password.bat` (Windows) or manually:
   ```bash
   cd billing
   docker compose down
   docker volume rm billing_postgres_data
   docker compose up -d --build
   ```

### Services Can't Communicate

**Error**: `could not translate host name "postgres_prod" to address`

**Solution**: Ensure all services are on the shared network:
```bash
docker network inspect quidpath_network
```

All containers should be listed. If not, redeploy with the deployment script.

### Database Connection Refused

**Solution**: Wait for databases to fully initialize:
```bash
docker compose logs db
```

Look for "database system is ready to accept connections"

### Port Already in Use

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**: Stop conflicting services:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

## Environment Variables

### Main Backend (.env)

```env
POSTGRES_DB=quidpath_db
POSTGRES_USER=quidpath_user
POSTGRES_PASSWORD=eDgDiAcayFqcPpXjThL6Ak668
DATABASE_URL=postgresql://quidpath_user:eDgDiAcayFqcPpXjThL6Ak668@db:5432/quidpath_db
```

### Billing Service (.env)

```env
# Own database
POSTGRES_DB=billing_prod
POSTGRES_USER=billing_user
POSTGRES_PASSWORD=BillingSecure2026ChangeThis

# Shared auth database
AUTH_POSTGRES_DB=quidpath_db
AUTH_POSTGRES_USER=quidpath_user
AUTH_POSTGRES_PASSWORD=eDgDiAcayFqcPpXjThL6Ak668
AUTH_POSTGRES_HOST=postgres_prod
```

### Tazama AI (.env)

```env
# Own database
POSTGRES_DB=tazama_db
POSTGRES_USER=tazama_user
POSTGRES_PASSWORD=tazama_pass123

# Shared auth database
AUTH_POSTGRES_DB=quidpath_db
AUTH_POSTGRES_USER=quidpath_user
AUTH_POSTGRES_PASSWORD=eDgDiAcayFqcPpXjThL6Ak668
AUTH_POSTGRES_HOST=postgres_prod
```

## Database Migrations

### Running Migrations

Each service has two databases:
1. **default**: Service-specific data
2. **auth_db**: Shared authentication (read-only for microservices)

```bash
# Main backend (creates auth tables)
docker compose exec backend python manage.py migrate

# Billing service
docker compose exec backend python manage.py migrate --database=default
docker compose exec backend python manage.py migrate --database=auth_db

# Tazama AI
docker compose exec web python manage.py migrate --database=default
docker compose exec web python manage.py migrate --database=auth_db
```

### Creating New Migrations

```bash
# Main backend
docker compose exec backend python manage.py makemigrations

# Billing service
docker compose exec backend python manage.py makemigrations

# Tazama AI
docker compose exec web python manage.py makemigrations
```

## Backup and Restore

### Backup Databases

```bash
# Main backend (includes auth)
docker compose exec db pg_dump -U quidpath_user quidpath_db > backup_main.sql

# Billing
docker compose exec db pg_dump -U billing_user billing_prod > backup_billing.sql

# Tazama AI
docker compose exec db pg_dump -U tazama_user tazama_db > backup_tazama.sql
```

### Restore Databases

```bash
# Main backend
docker compose exec -T db psql -U quidpath_user quidpath_db < backup_main.sql

# Billing
docker compose exec -T db psql -U billing_user billing_prod < backup_billing.sql

# Tazama AI
docker compose exec -T db psql -U tazama_user tazama_db < backup_tazama.sql
```

## Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

### Container Status

```bash
docker ps
```

### Resource Usage

```bash
docker stats
```

## Security Checklist

- [ ] Change default superuser password
- [ ] Update SECRET_KEY in all .env files
- [ ] Set DEBUG=False in production
- [ ] Configure proper ALLOWED_HOSTS
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable database backups
- [ ] Set up monitoring and alerts
- [ ] Review CORS settings
- [ ] Update Pesaway API credentials

## Production Deployment

For production deployment on a server:

1. Update `.env` files with production credentials
2. Configure domain names in ALLOWED_HOSTS
3. Set up Nginx reverse proxy
4. Configure SSL certificates (Let's Encrypt)
5. Set up automated backups
6. Configure monitoring (Prometheus/Grafana)
7. Set up log aggregation (ELK stack)

## Support

For issues or questions:
- Check logs: `docker compose logs -f`
- Verify network: `docker network inspect quidpath_network`
- Check database: `docker compose exec db psql -U <user> -d <database>`

## License

Proprietary - QuidPath ERP System
