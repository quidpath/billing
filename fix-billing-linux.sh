#!/bin/bash

# Fix Billing Service on Linux
set -e

echo "=========================================="
echo "🔧 Fixing Billing Service"
echo "=========================================="
echo ""

# Step 1: Check if shared network exists
echo "[1/6] Checking shared network..."
if docker network inspect quidpath_network >/dev/null 2>&1; then
    echo "✓ Network 'quidpath_network' exists"
else
    echo "Creating shared network..."
    docker network create quidpath_network
    echo "✓ Network created"
fi
echo ""

# Step 2: Check if main backend is running
echo "[2/6] Checking main backend..."
if docker ps --filter "name=django-backend" --format "{{.Names}}" | grep -q "django-backend"; then
    echo "✓ Main backend is running"
    
    # Check if it's on the shared network
    if docker network inspect quidpath_network --format '{{range .Containers}}{{.Name}}{{"\n"}}{{end}}' | grep -q "django-backend"; then
        echo "✓ Main backend is on shared network"
    else
        echo "⚠ Main backend is not on shared network, connecting..."
        docker network connect quidpath_network django-backend 2>/dev/null || echo "Already connected or failed"
    fi
else
    echo "⚠ Main backend is not running"
    echo "  You may need to start it first: cd ~/quidpath-deployment/quidpath-backend && docker compose up -d"
fi
echo ""

# Step 3: Check if postgres_prod is accessible
echo "[3/6] Checking main database..."
if docker ps --filter "name=postgres_prod" --format "{{.Names}}" | grep -q "postgres_prod"; then
    echo "✓ Main database is running"
    
    # Check if it's on the shared network
    if docker network inspect quidpath_network --format '{{range .Containers}}{{.Name}}{{"\n"}}{{end}}' | grep -q "postgres_prod"; then
        echo "✓ Main database is on shared network"
    else
        echo "⚠ Main database is not on shared network, connecting..."
        docker network connect quidpath_network postgres_prod 2>/dev/null || echo "Already connected or failed"
    fi
else
    echo "⚠ Main database is not running"
    echo "  You need to start the main backend first!"
fi
echo ""

# Step 4: Stop billing service
echo "[4/6] Stopping billing service..."
cd ~/quidpath-deployment/billing
docker compose down
echo "✓ Billing service stopped"
echo ""

# Step 5: Rebuild and start billing service
echo "[5/6] Starting billing service..."
docker compose up -d --build
echo "✓ Billing service started"
echo ""

# Step 6: Wait and check logs
echo "[6/6] Waiting for service to initialize..."
sleep 15

echo ""
echo "=========================================="
echo "📊 Service Status"
echo "=========================================="
docker ps --filter "name=billing-backend" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "=========================================="
echo "📜 Recent Logs"
echo "=========================================="
docker logs billing-backend --tail 30

echo ""
echo "=========================================="
echo "🔍 Network Connectivity"
echo "=========================================="
echo "Containers on quidpath_network:"
docker network inspect quidpath_network --format '{{range .Containers}}  - {{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'

echo ""
echo "=========================================="
if docker ps --filter "name=billing-backend" --filter "status=running" --format "{{.Names}}" | grep -q "billing-backend"; then
    echo "✅ Billing service is running!"
    echo ""
    echo "Test the service:"
    echo "  curl http://localhost:8002/api/billing/health/"
else
    echo "❌ Billing service is not running properly"
    echo ""
    echo "Check logs with:"
    echo "  docker logs billing-backend"
    echo ""
    echo "Or run the diagnostic:"
    echo "  bash check-billing-logs.sh"
fi
echo ""
