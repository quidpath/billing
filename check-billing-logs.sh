#!/bin/bash

echo "=========================================="
echo "🔍 Checking Billing Backend Logs"
echo "=========================================="
echo ""

echo "Last 50 lines of billing-backend logs:"
echo "=========================================="
docker logs billing-backend --tail 50

echo ""
echo "=========================================="
echo "Checking network connectivity:"
echo "=========================================="
docker network inspect quidpath_network --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'

echo ""
echo "=========================================="
echo "Checking if postgres_prod is accessible:"
echo "=========================================="
docker exec billing-backend ping -c 2 postgres_prod 2>&1 || echo "Cannot reach postgres_prod"

echo ""
echo "=========================================="
echo "Checking environment variables:"
echo "=========================================="
docker exec billing-backend env | grep -E "(POSTGRES|AUTH_|DATABASE)" | sort

echo ""
echo "=========================================="
echo "Checking if billing database is ready:"
echo "=========================================="
docker exec postgres_billing_prod pg_isready -U billing_user -d billing_prod

echo ""
