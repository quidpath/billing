# Production Deployment Steps

## Quick Deployment Guide for Fixed Issues

### Prerequisites
- SSH access to production server
- Docker and Docker Compose installed
- Production `.env` files configured

---

## 🚀 Step-by-Step Deployment

### Step 1: Backup Current State
```bash
# SSH into production server
ssh user@your-production-server

# Backup current containers (optional)
cd /root/quidpath-deployment/billing
docker compose logs > backup-logs-$(date +%Y%m%d).txt
```

### Step 2: Pull Latest Code
```bash
# Navigate to billing service
cd /root/quidpath-deployment/billing

# Pull latest changes
git pull origin main  # or your production branch
```

### Step 3: Verify .env Configuration
```bash
# Check that BILLING_SERVICE_URL is correct in main backend
grep "BILLING_SERVICE_URL" /root/quidpath-deployment/backend/.env

# Should output:
# BILLING_SERVICE_URL=http://billing-backend:8000/api/billing
```

### Step 4: Rebuild Billing Service
```bash
cd /root/quidpath-deployment/billing

# Stop current service
docker compose down

# Rebuild with no cache (to ensure PyJWT is installed)
docker compose build --no-cache

# Start service
docker compose up -d

# Check logs
docker compose logs -f
```

### Step 5: Verify Billing Service is Running
```bash
# Check container status
docker ps | grep billing

# Check logs for errors
docker logs billing-backend --tail 50

# Test health endpoint (should return 401 - auth required)
docker exec billing-backend curl -I http://localhost:8000/api/billing/health/
```

### Step 6: Restart Main Backend (if needed)
```bash
cd /root/quidpath-deployment/backend

# Restart to pick up any changes
docker compose restart backend

# Check logs
docker logs django-backend --tail 50
```

### Step 7: Verify Inter-Service Communication
```bash
# Test connection from main backend to billing service
docker exec django-backend python -c "
import requests
try:
    r = requests.get('http://billing-backend:8000/api/billing/health/', timeout=5)
    print(f'✅ Connection successful! Status: {r.status_code}')
    if r.status_code == 401:
        print('✅ Auth is working (401 expected)')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

### Step 8: Verify Network Configuration
```bash
# Check both services are on the same network
docker network inspect quidpath_network | grep -A 5 "Containers"

# Should show both:
# - billing-backend
# - django-backend
```

---

## ✅ Success Indicators

You should see:
- ✅ Billing service container running
- ✅ No errors in logs about `jwt` module
- ✅ No errors about `LocalMemoryCache`
- ✅ Database connection successful
- ✅ Health endpoint returns 401 (auth required)
- ✅ Main backend can connect to billing service

---

## 🔍 Troubleshooting

### Issue: "No module named 'jwt'"
**Solution:** Rebuild with `--no-cache` flag
```bash
docker compose build --no-cache
docker compose up -d
```

### Issue: "LocalMemoryCache not found"
**Solution:** Code should already be fixed. If still seeing this:
```bash
# Check the settings file
docker exec billing-backend cat /app/billing_service/settings/base.py | grep LocMemCache
```

### Issue: "could not translate host name 'db'"
**Solution:** Database host is now configurable
```bash
# Check if DB_HOST is set (should not be needed)
docker exec billing-backend env | grep DB_HOST

# If needed, add to .env:
# DB_HOST=db
```

### Issue: Connection refused from main backend
**Solution:** Verify network and port
```bash
# Check network
docker network inspect quidpath_network

# Verify billing service is listening
docker exec billing-backend netstat -tlnp | grep 8000

# Check environment variable in main backend
docker exec django-backend env | grep BILLING_SERVICE_URL
```

---

## 🔄 Rollback Plan

If something goes wrong:
```bash
cd /root/quidpath-deployment/billing

# Stop new version
docker compose down

# Checkout previous version
git checkout <previous-commit-hash>

# Rebuild and start
docker compose build
docker compose up -d
```

---

## 📊 Monitoring After Deployment

### Check Logs Continuously
```bash
# Billing service
docker logs -f billing-backend

# Main backend
docker logs -f django-backend
```

### Monitor Resource Usage
```bash
docker stats billing-backend django-backend
```

### Test API Endpoints
```bash
# From outside (with proper auth token)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.quidpath.com/api/billing/health/
```

---

## 📝 Post-Deployment Checklist

- [ ] Billing service container is running
- [ ] No errors in billing service logs
- [ ] Database connection successful
- [ ] PyJWT module loaded successfully
- [ ] Cache backend working (no LocalMemoryCache errors)
- [ ] Main backend can connect to billing service
- [ ] Both services on quidpath_network
- [ ] Health endpoints responding
- [ ] API endpoints working with authentication
- [ ] No performance degradation

---

## 🎯 Expected Behavior

### Development
- Port 8002 (host) → 8000 (container)
- Container name: `billing-backend-dev`
- Network: `quidpath_network`

### Production
- Port 8002 (host) → 8000 (container)
- Container name: `billing-backend`
- Network: `quidpath_network`

### Both Environments
- Health endpoint requires auth (401 response)
- JWT tokens validated
- Inter-service communication working
- Database connections stable

---

## 🆘 Support

If issues persist:
1. Check all logs: `docker compose logs`
2. Verify environment variables: `docker exec billing-backend env`
3. Test database connection: `docker exec billing-backend python manage.py check --database default`
4. Review network: `docker network inspect quidpath_network`
