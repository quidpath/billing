#!/bin/bash

echo "=========================================="
echo "🔍 Quick Billing Diagnosis"
echo "=========================================="
echo ""

echo "1. Container Status:"
docker ps -a --filter "name=billing-backend" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "2. Last 30 log lines:"
echo "---"
docker logs billing-backend --tail 30 2>&1
echo "---"
echo ""

echo "3. Network connectivity:"
echo "Can billing-backend reach postgres_prod?"
docker exec billing-backend ping -c 2 postgres_prod 2>&1 || echo "❌ Cannot reach postgres_prod"
echo ""

echo "Can billing-backend reach postgres_billing_prod?"
docker exec billing-backend ping -c 2 postgres_billing_prod 2>&1 || echo "❌ Cannot reach postgres_billing_prod"
echo ""

echo "4. Environment check:"
docker exec billing-backend env | grep -E "(AUTH_POSTGRES|POSTGRES_)" | sort
echo ""

echo "5. Containers on shared network:"
docker network inspect quidpath_network --format '{{range .Containers}}  - {{.Name}}{{"\n"}}{{end}}' 2>&1
echo ""
