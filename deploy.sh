#!/bin/bash
# Billing Service Deployment Script

set -e

echo "Deploying Billing Service..."

# Stop existing containers
docker compose down

# Clear database if needed (uncomment for fresh start)
# sudo rm -rf /mnt/ebs/postgres_data/*

# Build and start
docker compose up -d --build

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 20

# Show status
docker ps --filter "name=billing"

# Show logs
echo ""
echo "Recent logs:"
docker logs billing-backend --tail 30

echo ""
echo "Deployment complete!"
echo "Access admin at: http://localhost:8002/admin/"
