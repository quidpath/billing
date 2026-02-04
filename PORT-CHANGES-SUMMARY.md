# Production Port Changes Summary

## ✅ Port Configuration Updated

**Date:** February 4, 2026  
**Reason:** Avoid port conflicts in production deployment

---

## 🔄 Port Changes

### Before (Conflicting)
```
Main Backend:  localhost:8000
Billing:       localhost:8002
Tazama:        localhost:8001
```

### After (No Conflicts)
```
Main Backend:  localhost:8004
Billing:       localhost:8005
Tazama:        localhost:8006
```

---

## 📋 Complete Port Mapping

### Application Services

| Service | Container | Internal Port | External Port | Access URL |
|---------|-----------|---------------|---------------|------------|
| Main Backend | django-backend | 8000 | 8004 | http://localhost:8004 |
| Billing | billing-backend | 8000 | 8005 | http://localhost:8005 |
| Tazama AI | tazama-ai-backend | 8001 | 8006 | http://localhost:8006 |

### Database Services

| Service | Container | Internal Port | External Port |
|---------|-----------|---------------|---------------|
| Main DB | postgres_prod | 5432 | 5432 |
| Billing DB | postgres_billing_prod | 5432 | 5433 |
| Tazama DB | tazama_postgres | 5432 | 5434 |

---

## 🔧 Files Modified

1. ✅ `quidpath-backend/docker-compose.yml` - Port 8000 → 8004
2. ✅ `billing/docker-compose.yml` - Port 8002 → 8005
3. ✅ `tazama-ai-microservice/docker-compose.yml` - Port 8001 → 8006

---

## ⚠️ IMPORTANT: No Environment Variable Changes Needed!

### Why?

Services communicate using **internal Docker network** with **internal ports**:

```bash
# These URLs remain UNCHANGED:
BILLING_SERVICE_URL=http://billing-backend:8000/api/billing
TAZAMA_SERVICE_URL=http://tazama-ai-backend:8001/api/tazama
ERP_BACKEND_URL=http://django-backend:8000
```

**External ports (8004, 8005, 8006) are only for:**
- Host machine access
- Nginx reverse proxy
- External monitoring tools

**Internal ports (8000, 8001) are used for:**
- Container-to-container communication
- Service discovery on Docker network
- Inter-service API calls

---

## 🚀 Deployment Steps

### 1. Stop All Services
```bash
cd ~/quidpath-deployment/backend
docker compose down

cd ~/quidpath-deployment/billing
docker compose down

cd ~/quidpath-deployment/tazama
docker compose down
```

### 2. Pull Latest Code
```bash
cd ~/quidpath-deployment/backend
git pull origin main

cd ~/quidpath-deployment/billing
git pull origin main

cd ~/quidpath-deployment/tazama
git pull origin main
```

### 3. Start Services (New Ports)
```bash
# Main Backend (port 8004)
cd ~/quidpath-deployment/backend
docker compose up -d --build

# Billing (port 8005)
cd ~/quidpath-deployment/billing
docker compose up -d --build

# Tazama (port 8006)
cd ~/quidpath-deployment/tazama
docker compose up -d --build
```

### 4. Verify All Services
```bash
# Check containers
docker ps | grep -E "django-backend|billing-backend|tazama-ai-backend"

# Test endpoints
curl -I http://localhost:8004/api/auth/health/
curl -I http://localhost:8005/api/billing/health/
curl -I http://localhost:8006/api/tazama/health/
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] All three containers running
- [ ] No "port already allocated" errors
- [ ] Main backend accessible on port 8004
- [ ] Billing accessible on port 8005
- [ ] Tazama accessible on port 8006
- [ ] Inter-service communication working (test with docker exec)
- [ ] All services on quidpath_network
- [ ] No errors in logs

### Test Inter-Service Communication

```bash
# From main backend to billing
docker exec django-backend curl -I http://billing-backend:8000/api/billing/health/
# Expected: 401 (auth required - connection working!)

# From main backend to tazama
docker exec django-backend curl -I http://tazama-ai-backend:8001/api/tazama/health/
# Expected: 401 or 200 (connection working!)
```

---

## 🌐 Nginx Configuration Update

If using nginx, update your configuration:

```nginx
# Main Backend API
location /api/ {
    proxy_pass http://127.0.0.1:8004;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Billing Service
location /api/billing/ {
    proxy_pass http://127.0.0.1:8005;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Tazama AI Service
location /api/tazama/ {
    proxy_pass http://127.0.0.1:8006;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Then reload nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔍 Troubleshooting

### Still Getting Port Conflicts?

```bash
# Check what's using the ports
sudo lsof -i :8004
sudo lsof -i :8005
sudo lsof -i :8006

# Find and stop conflicting containers
docker ps -a
docker stop <container-name>
docker rm <container-name>
```

### Services Can't Communicate?

```bash
# Verify network
docker network inspect quidpath_network

# Ensure all three containers are listed
# If not, recreate network:
docker network rm quidpath_network
docker network create quidpath_network

# Then restart all services
```

### Environment Variables Wrong?

```bash
# Check each service
docker exec django-backend env | grep -E "BILLING|TAZAMA"
docker exec billing-backend env | grep ERP_BACKEND
docker exec tazama-ai-backend env | grep ERP_BACKEND

# Should use internal ports (8000, 8001), NOT external (8004, 8005, 8006)
```

---

## 📝 Summary

✅ **External ports changed** to avoid conflicts:
- Main: 8000 → 8004
- Billing: 8002 → 8005
- Tazama: 8001 → 8006

✅ **Internal communication unchanged:**
- Services still use original ports (8000, 8001)
- No .env file changes needed
- Docker network handles routing

✅ **All services bound to 127.0.0.1:**
- Only accessible from localhost
- Use nginx for external access
- Secure by default

---

## 🎯 Quick Reference

```bash
# Access from host
curl http://localhost:8004/api/...  # Main Backend
curl http://localhost:8005/api/...  # Billing
curl http://localhost:8006/api/...  # Tazama

# Inter-service URLs (in .env files)
http://django-backend:8000          # Main Backend
http://billing-backend:8000         # Billing
http://tazama-ai-backend:8001       # Tazama
```

---

**Status:** ✅ Ready to deploy with new port configuration!
