# Linux Server Fix Guide

## Current Issue

Your billing-backend container is restarting continuously. This is likely because:
1. The shared network `quidpath_network` doesn't exist, OR
2. The main backend's `postgres_prod` is not on the shared network, OR
3. There's a configuration issue preventing the billing service from connecting to the auth database

## Quick Fix (Recommended)

Run these commands on your Linux server:

```bash
# Step 1: Create shared network and connect all containers
cd ~/quidpath-deployment
chmod +x connect-networks.sh
bash connect-networks.sh

# Step 2: Restart billing service
cd ~/quidpath-deployment/billing
docker compose restart

# Step 3: Check if it's working
sleep 10
docker logs billing-backend --tail 50
```

## Detailed Fix

If the quick fix doesn't work, follow these steps:

### Step 1: Diagnose the Issue

```bash
cd ~/quidpath-deployment/billing
chmod +x quick-diagnose.sh
bash quick-diagnose.sh
```

This will show you:
- Container status
- Recent error logs
- Network connectivity
- Environment variables

### Step 2: Create Shared Network

```bash
docker network create quidpath_network
```

### Step 3: Connect Main Backend to Shared Network

```bash
# Connect main backend containers
docker network connect quidpath_network django-backend
docker network connect quidpath_network postgres_prod
```

### Step 4: Restart Billing Service

```bash
cd ~/quidpath-deployment/billing
docker compose down
docker compose up -d
```

### Step 5: Check Logs

```bash
# Wait for startup
sleep 15

# Check logs
docker logs billing-backend --tail 50

# Check if running
docker ps --filter "name=billing-backend"
```

## Verify Network Connectivity

Check that all containers are on the shared network:

```bash
docker network inspect quidpath_network --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'
```

You should see:
- django-backend
- postgres_prod
- billing-backend
- postgres_billing_prod

## Test Database Connectivity

From inside the billing container:

```bash
# Test connection to main auth database
docker exec billing-backend ping -c 2 postgres_prod

# Test connection to billing database
docker exec billing-backend ping -c 2 postgres_billing_prod
```

## Check Environment Variables

Verify the billing service has correct credentials:

```bash
docker exec billing-backend env | grep -E "(AUTH_POSTGRES|POSTGRES_|DATABASE_URL)"
```

Should show:
```
AUTH_POSTGRES_DB=quidpath_db
AUTH_POSTGRES_HOST=postgres_prod
AUTH_POSTGRES_PASSWORD=eDgDiAcayFqcPpXjThL6Ak668
AUTH_POSTGRES_USER=quidpath_user
DATABASE_URL=postgresql://billing_user:BillingSecure2026ChangeThis@postgres_billing_prod:5432/billing_prod
POSTGRES_DB=billing_prod
POSTGRES_PASSWORD=BillingSecure2026ChangeThis
POSTGRES_USER=billing_user
```

## Common Errors and Solutions

### Error: "could not translate host name postgres_prod"

**Solution**: Main backend database is not on shared network

```bash
docker network connect quidpath_network postgres_prod
cd ~/quidpath-deployment/billing
docker compose restart
```

### Error: "password authentication failed"

**Solution**: Check password in .env file

```bash
cd ~/quidpath-deployment/billing
cat .env | grep POSTGRES_PASSWORD
```

Should be: `POSTGRES_PASSWORD=BillingSecure2026ChangeThis` (no special characters)

If wrong, fix it:
```bash
nano .env
# Change the password
# Save and exit (Ctrl+X, Y, Enter)

# Restart
docker compose down
docker volume rm billing_postgres_data  # Remove old database
docker compose up -d
```

### Error: "relation does not exist"

**Solution**: Run migrations

```bash
docker exec billing-backend python manage.py migrate --database=default
docker exec billing-backend python manage.py migrate --database=auth_db
```

## Full Reset (Nuclear Option)

If nothing works, completely reset the billing service:

```bash
cd ~/quidpath-deployment/billing

# Stop and remove everything
docker compose down -v

# Remove the image
docker rmi billing-backend

# Rebuild and start
docker compose up -d --build

# Wait for startup
sleep 20

# Run migrations
docker exec billing-backend python manage.py migrate --database=default
docker exec billing-backend python manage.py migrate --database=auth_db

# Check logs
docker logs billing-backend --tail 50
```

## Automated Fix Script

Use the automated fix script:

```bash
cd ~/quidpath-deployment
chmod +x fix-billing-linux.sh
bash fix-billing-linux.sh
```

This script will:
1. Create/verify shared network
2. Connect main backend to network
3. Stop billing service
4. Rebuild and start billing service
5. Show status and logs

## Verify Everything Works

After fixing, verify all services:

```bash
# Check container status
docker ps

# Test main backend
curl http://localhost:8000/api/auth/health/

# Test billing service
curl http://localhost:8002/api/billing/health/

# Test Tazama AI
curl http://localhost:8001/api/tazama/
```

All should return HTTP 200.

## Access Admin Panels

Once working:
- Main Backend: http://YOUR_SERVER_IP:8000/admin/
- Billing: http://YOUR_SERVER_IP:8002/admin/
- Tazama AI: http://YOUR_SERVER_IP:8001/admin/

Login: admin / admin123

## Still Having Issues?

Run the comprehensive diagnostic:

```bash
cd ~/quidpath-deployment/billing
bash check-billing-logs.sh
```

This will show:
- Full logs
- Network configuration
- Database connectivity
- Environment variables

Then share the output for further troubleshooting.

## Production Deployment

Once everything works locally, for production:

1. Update .env files with production credentials
2. Set up Nginx reverse proxy
3. Configure SSL certificates
4. Set proper domain names in ALLOWED_HOSTS
5. Change default passwords

See DEPLOYMENT-GUIDE.md for full production setup.
