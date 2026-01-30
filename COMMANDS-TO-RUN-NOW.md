# 🚀 Commands to Run Right Now

## Your Current Situation

Your billing-backend is restarting continuously. Here's how to fix it:

## Option 1: Quick Fix (30 seconds)

Copy and paste these commands into your terminal:

```bash
# Create shared network
docker network create quidpath_network 2>/dev/null || echo "Network exists"

# Connect main backend to shared network
docker network connect quidpath_network django-backend 2>/dev/null || echo "Already connected"
docker network connect quidpath_network postgres_prod 2>/dev/null || echo "Already connected"

# Restart billing service
cd ~/quidpath-deployment/billing
docker compose restart

# Wait and check
sleep 15
docker logs billing-backend --tail 30
```

## Option 2: Automated Fix (1 minute)

```bash
cd ~/quidpath-deployment
chmod +x connect-networks.sh fix-billing-linux.sh
bash fix-billing-linux.sh
```

## Option 3: Manual Step-by-Step (2 minutes)

```bash
# 1. Create network
docker network create quidpath_network

# 2. Connect main backend
docker network connect quidpath_network django-backend
docker network connect quidpath_network postgres_prod

# 3. Stop billing
cd ~/quidpath-deployment/billing
docker compose down

# 4. Start billing
docker compose up -d

# 5. Check status
sleep 15
docker ps --filter "name=billing-backend"
docker logs billing-backend --tail 50
```

## Check If It Worked

```bash
# Should show "running" status
docker ps --filter "name=billing-backend"

# Should return HTTP 200
curl http://localhost:8002/api/billing/health/
```

## If Still Not Working

Run the diagnostic:

```bash
cd ~/quidpath-deployment/billing
chmod +x quick-diagnose.sh
bash quick-diagnose.sh
```

Then look at the output and:

### If you see "could not translate host name postgres_prod"
```bash
docker network connect quidpath_network postgres_prod
cd ~/quidpath-deployment/billing
docker compose restart
```

### If you see "password authentication failed"
```bash
cd ~/quidpath-deployment/billing
nano .env
# Change POSTGRES_PASSWORD to: BillingSecure2026ChangeThis
# Save (Ctrl+X, Y, Enter)
docker compose down
docker compose up -d
```

### If you see "relation does not exist"
```bash
docker exec billing-backend python manage.py migrate --database=default
docker exec billing-backend python manage.py migrate --database=auth_db
```

## Verify All Services

Once billing is working:

```bash
# Check all containers
docker ps

# Test all services
curl http://localhost:8000/api/auth/health/      # Main backend
curl http://localhost:8002/api/billing/health/   # Billing
curl http://localhost:8001/api/tazama/           # Tazama AI
```

## Access Admin Panels

- Main: http://YOUR_SERVER_IP:8000/admin/
- Billing: http://YOUR_SERVER_IP:8002/admin/
- Tazama: http://YOUR_SERVER_IP:8001/admin/

Login: `admin` / `admin123`

## Next Steps

1. ✅ Fix billing service (you're doing this now)
2. ✅ Verify all three services work
3. ✅ Test shared authentication (login to all admin panels)
4. 🔐 Change default passwords
5. 🔐 Update production credentials
6. 🌐 Configure Nginx and SSL

## Need More Help?

See detailed guides:
- `LINUX-FIX-GUIDE.md` - Comprehensive Linux troubleshooting
- `DEPLOYMENT-GUIDE.md` - Full deployment documentation
- `QUICK-REFERENCE.md` - Command reference

---

**Start here:** Run Option 1 (Quick Fix) above! 👆
