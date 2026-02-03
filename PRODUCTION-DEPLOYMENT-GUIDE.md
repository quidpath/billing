# QuidPath Production Deployment Guide

## Overview

This guide covers deploying all three microservices (Main Backend, Billing Service, Tazama AI) with JWT authentication and subscription synchronization.

## Prerequisites

- Ubuntu/Debian server with root access
- Docker and Docker Compose installed
- Nginx installed
- Certbot installed for SSL certificates
- Domain names configured:
  - `api.quidpath.com` → Main Backend
  - `quidpath.com` / `www.quidpath.com` → Frontend
  - `billing.quidpath.com` → Billing Service
  - `ai.quidpath.com` → Tazama AI Service

## Step 1: Generate Secure Secrets

Generate strong secrets for production:

```bash
# Generate JWT secret (use same for all services)
openssl rand -hex 32

# Generate webhook secret (use same for Main Backend and Billing)
openssl rand -hex 32

# Generate service API keys
openssl rand -hex 32  # For Billing Service
openssl rand -hex 32  # For Tazama Service

# Generate Django secret keys
openssl rand -hex 32  # For Main Backend
openssl rand -hex 32  # For Billing Service
openssl rand -hex 32  # For Tazama Service
```

Save these values - you'll need them for the .env files.

## Step 2: Environment Configuration

### Main Backend (.env)

Create `/root/quidpath-deployment/backend/.env`:

```bash
# Database Configuration
DATABASE_URL=postgresql://quidpath_user:CHANGE_THIS_PASSWORD@db:5432/quidpath_db
POSTGRES_DB=quidpath_db
POSTGRES_USER=quidpath_user
POSTGRES_PASSWORD=CHANGE_THIS_PASSWORD

# Django Settings
DEBUG=False
DJANGO_SETTINGS_MODULE=quidpath_backend.settings.prod
SECRET_KEY=YOUR_DJANGO_SECRET_KEY_HERE
ALLOWED_HOSTS=api.quidpath.com,quidpath.com,www.quidpath.com

# CSRF Configuration
CSRF_TRUSTED_ORIGINS=https://quidpath.com,https://www.quidpath.com,https://*.quidpath.com

# Email Settings (Gmail SMTP)
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password

# JWT Configuration (CRITICAL - Must match all services)
JWT_SECRET_KEY=YOUR_JWT_SECRET_HERE

# Service API Keys (CRITICAL - Must match microservices)
BILLING_SERVICE_API_KEY=YOUR_BILLING_API_KEY_HERE
TAZAMA_SERVICE_API_KEY=YOUR_TAZAMA_API_KEY_HERE

# Webhook Configuration (CRITICAL - Must match Billing Service)
BILLING_WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET_HERE

# Billing Service URL
BILLING_SERVICE_URL=http://billing-backend:8000/api/billing

# M-Pesa Configuration (Optional)
MPESA_CONSUMER_KEY=your_mpesa_consumer_key
MPESA_CONSUMER_SECRET=your_mpesa_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_mpesa_passkey
MPESA_CALLBACK_URL=https://api.quidpath.com/api/payments/mpesa/callback/
```

### Billing Service (.env)

Create `/root/quidpath-deployment/billing/.env`:

```bash
# Django Environment
DJANGO_SETTINGS_MODULE=billing_service.settings.prod

# Security
SECRET_KEY=YOUR_BILLING_DJANGO_SECRET_KEY_HERE
DEBUG=False

# Allowed Hosts
ALLOWED_HOSTS=billing.quidpath.com,api.quidpath.com

# CSRF Configuration
CSRF_TRUSTED_ORIGINS=https://quidpath.com,https://www.quidpath.com,https://*.quidpath.com

# Database Configuration
POSTGRES_DB=billing_prod
POSTGRES_USER=billing_user
POSTGRES_PASSWORD=CHANGE_THIS_BILLING_PASSWORD
DATABASE_URL=postgresql://billing_user:CHANGE_THIS_BILLING_PASSWORD@db:5432/billing_prod

# JWT Configuration (CRITICAL - Must match Main Backend)
JWT_SECRET_KEY=YOUR_JWT_SECRET_HERE

# Service API Key (CRITICAL - Must match Main Backend BILLING_SERVICE_API_KEY)
SERVICE_API_KEY=YOUR_BILLING_API_KEY_HERE

# Main Backend URL
ERP_BACKEND_URL=http://django-backend:8000

# Webhook Configuration (CRITICAL - Must match Main Backend)
BILLING_WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET_HERE

# Cache Configuration
USER_CACHE_TTL=3600
CORPORATE_CACHE_TTL=86400

# Pesaway Payment Gateway (Optional)
PESAWAY_API_KEY=your_pesaway_api_key
PESAWAY_SECRET_KEY=your_pesaway_secret_key
PESAWAY_MERCHANT_ID=your_pesaway_merchant_id
PESAWAY_TEST_MODE=false
PESAWAY_WEBHOOK_URL=https://billing.quidpath.com/api/billing/webhooks/pesaway/
PESAWAY_WEBHOOK_SECRET=your_pesaway_webhook_secret

# Server Configuration
PORT=8000
WORKERS=4
```

### Tazama AI Service (.env)

Create `/root/quidpath-deployment/tazama/.env`:

```bash
# Django Settings
SECRET_KEY=YOUR_TAZAMA_DJANGO_SECRET_KEY_HERE
DEBUG=False
DJANGO_SETTINGS_MODULE=tazama_ai.settings.prod
ALLOWED_HOSTS=ai.quidpath.com,api.quidpath.com

# Database Configuration
POSTGRES_DB=tazama_db
POSTGRES_USER=tazama_user
POSTGRES_PASSWORD=CHANGE_THIS_TAZAMA_PASSWORD
DATABASE_URL=postgresql://tazama_user:CHANGE_THIS_TAZAMA_PASSWORD@db:5432/tazama_db

# JWT Configuration (CRITICAL - Must match Main Backend)
JWT_SECRET_KEY=YOUR_JWT_SECRET_HERE

# Service API Key (CRITICAL - Must match Main Backend TAZAMA_SERVICE_API_KEY)
SERVICE_API_KEY=YOUR_TAZAMA_API_KEY_HERE

# Main Backend URL
ERP_BACKEND_URL=http://django-backend:8000

# Cache Configuration
USER_CACHE_TTL=3600
CORPORATE_CACHE_TTL=86400

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://quidpath.com,https://www.quidpath.com

# Server Configuration
PORT=8001
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120
```

## Step 3: SSL Certificates

Obtain SSL certificates for all domains:

```bash
# Stop nginx temporarily
sudo systemctl stop nginx

# Get certificates for all domains
sudo certbot certonly --standalone -d api.quidpath.com
sudo certbot certonly --standalone -d quidpath.com -d www.quidpath.com
sudo certbot certonly --standalone -d billing.quidpath.com
sudo certbot certonly --standalone -d ai.quidpath.com

# Start nginx
sudo systemctl start nginx
```

## Step 4: Create Docker Network

Create shared network for inter-service communication:

```bash
docker network create quidpath_network
```

## Step 5: Deploy Services

### Deploy Main Backend

```bash
cd /root/quidpath-deployment/backend

# Pull latest code
git pull origin main

# Build and start
docker compose down
docker compose build --no-cache
docker compose up -d

# Run migrations
docker exec django-backend python manage.py migrate

# Collect static files
docker exec django-backend python manage.py collectstatic --noinput

# Create superuser
docker exec -it django-backend python manage.py createsuperuser
```

### Deploy Billing Service

```bash
cd /root/quidpath-deployment/billing

# Pull latest code
git pull origin main

# Build and start
docker compose down
docker compose build --no-cache
docker compose up -d

# Run migrations
docker exec billing-backend python manage.py migrate

# Collect static files
docker exec billing-backend python manage.py collectstatic --noinput

# Create superuser
docker exec -it billing-backend python manage.py createsuperuser

# Seed plans (optional)
docker exec billing-backend python seed_plans.py
```

### Deploy Tazama AI Service

```bash
cd /root/quidpath-deployment/tazama

# Pull latest code
git pull origin main

# Build and start
docker compose down
docker compose build --no-cache
docker compose up -d

# Run migrations
docker exec tazama-ai-backend python manage.py migrate

# Collect static files
docker exec tazama-ai-backend python manage.py collectstatic --noinput

# Create superuser
docker exec -it tazama-ai-backend python manage.py createsuperuser
```

## Step 6: Configure Nginx

Copy the nginx configuration:

```bash
# Copy nginx config
sudo cp /root/quidpath-deployment/backend/nginx.conf /etc/nginx/sites-available/quidpath

# Enable site
sudo ln -sf /etc/nginx/sites-available/quidpath /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Step 7: Verify Deployment

### Check Service Health

```bash
# Check Main Backend
curl https://api.quidpath.com/api/auth/health/

# Check Billing Service
curl https://billing.quidpath.com/api/billing/health/

# Check Tazama AI
curl https://ai.quidpath.com/api/tazama/health/
```

### Check Docker Containers

```bash
# Check all containers are running
docker ps

# Expected containers:
# - django-backend (port 8000)
# - postgres_prod
# - billing-backend (port 8002)
# - postgres_billing_prod
# - tazama-ai-backend (port 8001)
# - tazama_postgres
```

### Check Logs

```bash
# Main Backend logs
docker logs django-backend --tail 100 -f

# Billing Service logs
docker logs billing-backend --tail 100 -f

# Tazama AI logs
docker logs tazama-ai-backend --tail 100 -f
```

## Step 8: Test JWT Authentication

### Test Main Backend JWT Issuance

```bash
# Login to get JWT token
curl -X POST https://api.quidpath.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'

# Save the access token from response
```

### Test Billing Service JWT Validation

```bash
# Access Billing Service with JWT token
curl https://billing.quidpath.com/api/billing/subscriptions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

### Test Tazama AI JWT Validation

```bash
# Access Tazama AI with JWT token
curl https://ai.quidpath.com/api/tazama/analyze/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## Step 9: Test Subscription Sync

### Create Test Subscription in Billing

```bash
# Create subscription via Billing Service API
curl -X POST https://billing.quidpath.com/api/billing/subscriptions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "corporate_id": "YOUR_CORPORATE_UUID",
    "plan_id": "PLAN_UUID",
    "billing_cycle": "monthly"
  }'
```

### Verify Webhook Received

```bash
# Check Main Backend logs for webhook
docker logs django-backend | grep "Webhook received"

# Check Billing Service logs for webhook sent
docker logs billing-backend | grep "Webhook sent"
```

### Verify Subscription in Main Backend

```bash
# Get subscription from Main Backend
curl https://api.quidpath.com/api/org-auth/subscription/my-subscription \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## Step 10: Setup Auto-Renewal for SSL

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot auto-renewal is enabled by default
# Verify timer is active
sudo systemctl status certbot.timer
```

## Step 11: Setup Monitoring

### Create Health Check Script

```bash
cat > /root/health-check.sh << 'EOF'
#!/bin/bash

echo "=== QuidPath Health Check ==="
echo ""

echo "Main Backend:"
curl -s https://api.quidpath.com/api/auth/health/ || echo "FAILED"
echo ""

echo "Billing Service:"
curl -s https://billing.quidpath.com/api/billing/health/ || echo "FAILED"
echo ""

echo "Tazama AI:"
curl -s https://ai.quidpath.com/api/tazama/health/ || echo "FAILED"
echo ""

echo "Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}"
EOF

chmod +x /root/health-check.sh
```

### Run Health Check

```bash
/root/health-check.sh
```

## Troubleshooting

### Service Not Starting

```bash
# Check logs
docker logs <container-name>

# Check environment variables
docker exec <container-name> env | grep -E "JWT|SECRET|DATABASE"

# Restart service
docker compose restart
```

### Webhook Not Working

```bash
# Check webhook secret matches
docker exec django-backend env | grep BILLING_WEBHOOK_SECRET
docker exec billing-backend env | grep BILLING_WEBHOOK_SECRET

# Check network connectivity
docker exec billing-backend ping django-backend

# Check logs
docker logs django-backend | grep webhook
docker logs billing-backend | grep webhook
```

### JWT Authentication Failing

```bash
# Check JWT secret matches
docker exec django-backend env | grep JWT_SECRET_KEY
docker exec billing-backend env | grep JWT_SECRET_KEY
docker exec tazama-ai-backend env | grep JWT_SECRET_KEY

# Check service API keys match
docker exec django-backend env | grep SERVICE_API_KEY
docker exec billing-backend env | grep SERVICE_API_KEY
```

### Database Connection Issues

```bash
# Check database is running
docker ps | grep postgres

# Check database credentials
docker exec <backend-container> env | grep DATABASE_URL

# Test database connection
docker exec <backend-container> python manage.py dbshell
```

## Security Checklist

- [ ] All secrets are unique and strong (32+ characters)
- [ ] JWT_SECRET_KEY is the same across all services
- [ ] BILLING_WEBHOOK_SECRET matches in Main Backend and Billing Service
- [ ] Service API keys match between Main Backend and microservices
- [ ] DEBUG=False in all .env files
- [ ] Database passwords are strong and unique
- [ ] SSL certificates are valid and auto-renewing
- [ ] Nginx security headers are configured
- [ ] Firewall allows only ports 80, 443, and 22
- [ ] Docker containers are not exposed to public internet (only via nginx)

## Backup Strategy

### Database Backups

```bash
# Backup Main Backend database
docker exec postgres_prod pg_dump -U quidpath_user quidpath_db > backup_main_$(date +%Y%m%d).sql

# Backup Billing database
docker exec postgres_billing_prod pg_dump -U billing_user billing_prod > backup_billing_$(date +%Y%m%d).sql

# Backup Tazama database
docker exec tazama_postgres pg_dump -U tazama_user tazama_db > backup_tazama_$(date +%Y%m%d).sql
```

### Automated Backups

Create cron job for daily backups:

```bash
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /root/backup-databases.sh
```

## Maintenance

### Update Services

```bash
# Pull latest code
cd /root/quidpath-deployment/<service>
git pull origin main

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d

# Run migrations
docker exec <container-name> python manage.py migrate

# Collect static files
docker exec <container-name> python manage.py collectstatic --noinput
```

### View Logs

```bash
# Real-time logs
docker logs -f <container-name>

# Last 100 lines
docker logs --tail 100 <container-name>

# Logs with timestamps
docker logs -t <container-name>
```

## Support

For issues:
1. Check service logs
2. Verify environment variables
3. Test network connectivity between services
4. Check SSL certificates
5. Review nginx configuration
6. Consult documentation in `.kiro/specs/`

## Next Steps

1. Configure monitoring and alerting
2. Set up log aggregation
3. Implement automated backups
4. Configure CDN for static files
5. Set up staging environment
6. Implement CI/CD pipelines
7. Configure rate limiting
8. Set up application performance monitoring
