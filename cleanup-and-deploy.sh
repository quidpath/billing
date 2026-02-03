#!/bin/bash

# QuidPath Production Cleanup and Deployment Script
# This script removes all .md files, removes emojis, and deploys all services

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}QuidPath Production Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as correct user
if [ "$USER" != "quidpath" ]; then
    echo -e "${RED}Please run as quidpath user${NC}"
    echo "Switch user: su - quidpath"
    exit 1
fi

# Navigate to deployment directory
cd ~/quidpath-deployment

echo -e "${YELLOW}Step 1: Cleaning up documentation files...${NC}"
# Remove all .md files except README.md in root
find . -type f -name "*.md" ! -name "README.md" -delete
echo -e "${GREEN}Documentation files removed${NC}"

echo ""
echo -e "${YELLOW}Step 2: Creating Docker network...${NC}"
docker network create quidpath_network 2>/dev/null || echo "Network already exists"

echo ""
echo -e "${YELLOW}Step 3: Deploying Backend...${NC}"
cd ~/quidpath-deployment/backend
git pull origin main || echo "Using local version"
docker compose down
docker compose build --no-cache
docker compose up -d
sleep 15
docker exec django-backend python manage.py migrate --noinput
docker exec django-backend python manage.py collectstatic --noinput
echo -e "${GREEN}Backend deployed${NC}"

echo ""
echo -e "${YELLOW}Step 4: Deploying Billing Service...${NC}"
cd ~/quidpath-deployment/billing
git pull origin main || echo "Using local version"
docker compose down
docker compose build --no-cache
docker compose up -d
sleep 15
docker exec billing-backend python manage.py migrate --noinput
docker exec billing-backend python manage.py collectstatic --noinput
echo -e "${GREEN}Billing Service deployed${NC}"

echo ""
echo -e "${YELLOW}Step 5: Deploying Tazama AI...${NC}"
cd ~/quidpath-deployment/tazama
git pull origin main || echo "Using local version"
docker compose down
docker compose build --no-cache
docker compose up -d
sleep 15
docker exec tazama-ai-backend python manage.py migrate --noinput
docker exec tazama-ai-backend python manage.py collectstatic --noinput
echo -e "${GREEN}Tazama AI deployed${NC}"

echo ""
echo -e "${YELLOW}Step 6: Deploying Frontend...${NC}"
cd ~/quidpath-deployment/frontend
git pull origin main || echo "Using local version"
docker compose down
docker compose build --no-cache
docker compose up -d
sleep 10
echo -e "${GREEN}Frontend deployed${NC}"

echo ""
echo -e "${YELLOW}Step 7: Reloading Nginx...${NC}"
sudo nginx -t && sudo systemctl reload nginx
echo -e "${GREEN}Nginx reloaded${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Health Check${NC}"
echo -e "${GREEN}========================================${NC}"

sleep 5

echo -n "Backend: "
if curl -s -f http://localhost:8000/api/auth/health/ > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
fi

echo -n "Billing: "
if curl -s -f http://localhost:8002/api/billing/health/ > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
fi

echo -n "Tazama: "
if curl -s -f http://localhost:8001/api/tazama/health/ > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
fi

echo -n "Frontend: "
if curl -s -f http://localhost:3000/ > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Public URLs:"
echo "  - Frontend: https://quidpath.com"
echo "  - Backend API: https://api.quidpath.com"
echo "  - Billing: https://billing.quidpath.com"
echo "  - Tazama AI: https://ai.quidpath.com"
