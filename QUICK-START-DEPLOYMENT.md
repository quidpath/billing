# QuidPath Quick Start Deployment Guide

## Prerequisites Check

Before starting, ensure you have:
- [ ] Ubuntu/Debian server with root access
- [ ] Docker and Docker Compose installed
- [ ] Nginx installed
- [ ] Certbot installed
- [ ] Domains pointing to your server IP:
  - api.quidpath.com
  - quidpath.com
  - www.quidpath.com
  - billing.quidpath.com
  - ai.quidpath.com

## Step 1: Generate All Secrets (5 minutes)

Run this script to generate all required secrets:

```bash
cat > /root/generate-secrets.sh << 'EOF'
#!/bin/bash
echo "========================================="
echo "QuidPath Production Secrets"
echo "========================================="
echo ""
echo "COPY THESE VALUES TO YOUR .env FILES"
echo ""
echo "# Use SAME value for all services:"
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)"
echo ""
echo "# Use SAME value for Main Backend and Billing:"
echo "BILLING_WEBHOOK_SECRET=$(openssl rand -hex 32)"
echo ""
echo "# Service API Keys (match between services):"
echo "BILLING_SERVICE_API_KEY=$(openssl rand -hex 32)"
echo "TAZAMA_SERVICE_API_KEY=$(openssl rand -hex 32)"
echo ""
echo "# Django Secret Keys (DIFFERENT for each service):"
echo "MAIN_DJANGO_SECRET=$(openssl rand -hex 32)"
echo "BILLING_DJANGO_SECRET=$(openssl rand -hex 32)"
echo "TAZAMA_DJANGO_SECRET=$(openssl rand -hex 32)"
echo ""
echo "# Database Passwords (DIFFERENT for each service):"
echo "MAIN_DB_PASSWORD=$(openssl rand -base64 24)"
echo "BILLING_DB_PASSWORD=$(openssl rand -base64 24)"
echo "TAZAMA_DB_PASSWORD=$(openssl rand -base64 24)"
echo ""
echo "========================================="
echo "SAVE THESE VALUES SECURELY!"
echo "========================================="
EOF

chmod +x /root/generate-secrets.sh
/root/generate-secrets.sh > /root/secrets.txt
cat /root/secrets.txt
```

**IMPORTANT**: Save the output to a secure location!

## Step 2: Create .env Files (10 minutes)

### Main Backend

```bash
cat > /root/quidpath-deployment/backend/.env << 'EOF'
# Database
DATABASE_URL=postgresql://quidpath_user:PASTE_MAIN_DB_PASSWORD@db:5432/quidpath_db
POSTGRES_DB=quidpath_db
POSTGRES_USER=quidpath_user
POSTGRES_PASSWORD=PASTE_MAIN_DB_PASSWORD

# Django
DEBUG=False
DJANGO_SETTINGS_MODULE=quidpath_backend.settings.prod
SECRET_KEY=PASTE_MAIN_DJANGO_SECRET
ALLOWED_HOSTS=api.quidpath.com,quidpath.com,www.quidpath.com
CSRF_TRUSTED_ORIGINS=https://quidpath.com,https://www.quidpath.com,https://*.quidpath.com

# Email
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# JWT (SAME for all services)
JWT_SECRET_KEY=PASTE_JWT_SECRET_KEY

# Service API Keys
BILLING_SERVICE_API_KEY=PASTE_BILLING_SERVICE_API_KEY
TAZAMA_SERVICE_API_KEY=PASTE_TAZAMA_SERVICE_API_KEY

# Webhook
BILLING_WEBHOOK_SECRET=PASTE_BILLING_WEBHOOK_SECRET

# Services
BILLING_SERVICE_URL=http://billing-backend:8000/api/billing
EOF
```

### Billing Service

```bash
cat > /root/quidpath-deployment/billing/.env << 'EOF'
# Django
DJANGO_SETTINGS_MODULE=billing_service.settings.prod
SECRET_KEY=PASTE_BILLING_DJANGO_SECRET
DEBUG=False
ALLOWED_HOSTS=billing.quidpath.com,api.quidpath.com
CSRF_TRUSTED_ORIGINS=https://quidpath.com,https://www.quidpath.com,https://*.quidpath.com

# Database
POSTGRES_DB=billing_prod
POSTGRES_USER=billing_user
POSTGRES_PASSWORD=PASTE_BILLING_DB_PASSWORD
DATABASE_URL=postgresql://billing_user:PASTE_BILLING_DB_PASSWORD@db:5432/billing_prod

# JWT (SAME as Main Backend)
JWT_SECRET_KEY=PASTE_JWT_SECRET_KEY

# Service API Key (SAME as Main Backend BILLING_SERVICE_API_KEY)
SERVICE_API_KEY=PASTE_BILLING_SERVICE_API_KEY

# Main Backend
ERP_BACKEND_URL=http://django-backend:8000

# Webhook (SAME as Main Backend)
BILLING_WEBHOOK_SECRET=PASTE_BILLING_WEBHOOK_SECRET

# Cache
USER_CACHE_TTL=3600
CORPORATE_CACHE_TTL=86400

# Server
PORT=8000
WORKERS=4
EOF
```

### Tazama AI

```bash
cat > /root/quidpath-deployment/tazama/.env << 'EOF'
# Django
SECRET_KEY=PASTE_TAZAMA_DJANGO_SECRET
DEBUG=False
DJANGO_SETTINGS_MODULE=tazama_ai.settings.prod
ALLOWED_HOSTS=ai.quidpath.com,api.quidpath.com

# Database
POSTGRES_DB=tazama_db
POSTGRES_USER=tazama_user
POSTGRES_PASSWORD=PASTE_TAZAMA_DB_PASSWORD
DATABASE_URL=postgresql://tazama_user:PASTE_TAZAMA_DB_PASSWORD@db:5432/tazama_db

# JWT (SAME as Main Backend)
JWT_SECRET_KEY=PASTE_JWT_SECRET_KEY

# Service API Key (SAME as Main Backend TAZAMA_SERVICE_API_KEY)
SERVICE_API_KEY=PASTE_TAZAMA_SERVICE_API_KEY

# Main Backend
ERP_BACKEND_URL=http://django-backend:8000

# Cache
USER_CACHE_TTL=3600
CORPORATE_CACHE_TTL=86400

# CORS
CORS_ALLOWED_ORIGINS=https://quidpath.com,https://www.quidpath.com

# Server
PORT=8001
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120
EOF
```

**Now replace all PASTE_* placeholders with values from /root/secrets.txt**

## Step 3: Obtain SSL Certificates (5 minutes)

```bash
# Stop nginx
sudo systemctl stop nginx

# Get certificates
sudo certbot certonly --standalone -d api.quidpath.com
sudo certbot certonly --standalone -d quidpath.com -d www.quidpath.com
sudo certbot certonly --standalone -d billing.quidpath.com
sudo certbot certonly --standalone -d ai.quidpath.com

# Start nginx
sudo systemctl start nginx
```

## Step 4: Configure Nginx (2 minutes)

```bash
# Copy nginx config
sudo cp /root/quidpath-deployment/backend/nginx.conf /etc/nginx/sites-available/quidpath

# Enable site
sudo ln -sf /etc/nginx/sites-available/quidpath /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## Step 5: Run Pre-Deployment Check (2 minutes)

```bash
# Make script executable
chmod +x /root/quidpath-deployment/pre-deployment-check.sh

# Run check
/root/quidpath-deployment/pre-deployment-check.sh
```

**Fix any errors before proceeding!**

## Step 6: Deploy All Services (10 minutes)

```bash
# Make deployment script executable
chmod +x /root/quidpath-deployment/deploy-all-services.sh

# Run deployment
/root/quidpath-deployment/deploy-all-services.sh
```

## Step 7: Create Superusers (5 minutes)

```bash
# Main Backend
docker exec -it django-backend python manage.py createsuperuser

# Billing Service
docker exec -it billing-backend python manage.py createsuperuser

# Tazama AI
docker exec -it tazama-ai-backend python manage.py createsuperuser
```

## Step 8: Verify Deployment (5 minutes)

### Check Services

```bash
# Check containers
docker ps

# Check health endpoints
curl https://api.quidpath.com/api/auth/health/
curl https://billing.quidpath.com/api/billing/health/
curl https://ai.quidpath.com/api/tazama/health/
```

### Test JWT Authentication

```bash
# Login to Main Backend
curl -X POST https://api.quidpath.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'

# Save the access token and test Billing Service
curl https://billing.quidpath.com/api/billing/plans/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Test Subscription Webhook

```bash
# Check logs for webhook activity
docker logs billing-backend | grep -i webhook
docker logs django-backend | grep -i webhook
```

## Step 9: Seed Initial Data (Optional, 5 minutes)

```bash
# Seed billing plans
docker exec billing-backend python seed_plans.py

# Seed payment methods
docker exec billing-backend python seed_payment_methods.py
```

## Step 10: Setup Monitoring (5 minutes)

```bash
# Create health check script
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

# Test it
/root/health-check.sh
```

## Troubleshooting

### Service Not Starting

```bash
# Check logs
docker logs <container-name> --tail 100

# Check environment
docker exec <container-name> env | grep -E "JWT|SECRET|DATABASE"

# Restart
docker compose restart
```

### JWT Authentication Failing

```bash
# Verify JWT secrets match
docker exec django-backend env | grep JWT_SECRET_KEY
docker exec billing-backend env | grep JWT_SECRET_KEY
docker exec tazama-ai-backend env | grep JWT_SECRET_KEY

# All three should output the SAME value
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

## Total Time: ~50 minutes

## Next Steps

1. Configure automated backups
2. Set up monitoring and alerting
3. Configure log aggregation
4. Test subscription creation flow
5. Test payment processing
6. Configure rate limiting
7. Set up staging environment
8. Implement CI/CD pipelines

## Support

For detailed information, see:
- `PRODUCTION-DEPLOYMENT-GUIDE.md` - Complete deployment guide
- `.env.production.template` - Environment variable reference
- `billing/.kiro/specs/microservices-authentication/` - JWT auth documentation
- `billing/.kiro/specs/subscription-sync/` - Subscription sync documentation

## Security Reminders

- [ ] All secrets are strong (32+ characters)
- [ ] JWT_SECRET_KEY is the same across all services
- [ ] BILLING_WEBHOOK_SECRET matches in Main Backend and Billing
- [ ] Service API keys match between services
- [ ] DEBUG=False in all .env files
- [ ] Database passwords are unique and strong
- [ ] SSL certificates are valid
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] Secrets file (/root/secrets.txt) is secured or deleted
