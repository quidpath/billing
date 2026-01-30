#!/bin/bash

# Quick script to connect all containers to shared network

echo "=========================================="
echo "🔗 Connecting Services to Shared Network"
echo "=========================================="
echo ""

# Create network if it doesn't exist
echo "Creating/verifying shared network..."
docker network create quidpath_network 2>/dev/null || echo "Network already exists"
echo ""

# Connect main backend containers
echo "Connecting main backend containers..."
docker network connect quidpath_network django-backend 2>/dev/null && echo "✓ django-backend connected" || echo "  django-backend already connected or not running"
docker network connect quidpath_network postgres_prod 2>/dev/null && echo "✓ postgres_prod connected" || echo "  postgres_prod already connected or not running"
echo ""

# Connect billing containers
echo "Connecting billing containers..."
docker network connect quidpath_network billing-backend 2>/dev/null && echo "✓ billing-backend connected" || echo "  billing-backend already connected or not running"
docker network connect quidpath_network postgres_billing_prod 2>/dev/null && echo "✓ postgres_billing_prod connected" || echo "  postgres_billing_prod already connected or not running"
echo ""

# Connect Tazama containers
echo "Connecting Tazama containers..."
docker network connect quidpath_network tazama-ai-backend 2>/dev/null && echo "✓ tazama-ai-backend connected" || echo "  tazama-ai-backend already connected or not running"
docker network connect quidpath_network tazama_postgres 2>/dev/null && echo "✓ tazama_postgres connected" || echo "  tazama_postgres already connected or not running"
echo ""

echo "=========================================="
echo "📊 Network Status"
echo "=========================================="
echo "Containers on quidpath_network:"
docker network inspect quidpath_network --format '{{range .Containers}}  - {{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'

echo ""
echo "✅ Network connections updated!"
echo ""
echo "Now restart the billing service:"
echo "  cd ~/quidpath-deployment/billing"
echo "  docker compose restart"
echo ""
