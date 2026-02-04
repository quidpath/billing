#!/bin/bash

# Start All Development Services Script
# This script starts Backend, Billing, and Tazama AI services

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Starting QuidPath Development Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create shared network if it doesn't exist
echo -e "${YELLOW}Creating shared Docker network...${NC}"
docker network create quidpath_network 2>/dev/null || echo "Network already exists"
echo ""

# Stop any existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
cd quidpath-backend && docker compose -f docker-compose.dev.yml down 2>/dev/null || true
cd ../billing && docker compose -f docker-compose.dev.yml down 2>/dev/null || true
cd ../tazama-ai-microservice && docker compose -f docker-compose.dev.yml down 2>/dev/null || true
cd ..
echo ""

# Start Backend
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Backend Service${NC}"
echo -e "${GREEN}========================================${NC}"
cd quidpath-backend
docker compose -f docker-compose.dev.yml up -d --build
echo -e "${GREEN}Backend starting...${NC}"
echo ""

# Start Billing
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Billing Service${NC}"
echo -e "${GREEN}========================================${NC}"
cd ../billing
docker compose -f docker-compose.dev.yml up -d --build
echo -e "${GREEN}Billing starting...${NC}"
echo ""

# Start Tazama AI
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Tazama AI Service${NC}"
echo -e "${GREEN}========================================${NC}"
cd ../tazama-ai-microservice
docker compose -f docker-compose.dev.yml up -d --build
echo -e "${GREEN}Tazama AI starting...${NC}"
cd ..
echo ""

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start (30 seconds)...${NC}"
sleep 30

# Run migrations and create superusers
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setting Up Services${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${YELLOW}Backend: Running migrations...${NC}"
docker exec django-backend-dev python manage.py migrate --noinput 2>/dev/null || echo "Migrations already applied"

echo -e "${YELLOW}Backend: Creating superuser...${NC}"
docker exec django-backend-dev python manage.py shell << 'EOF' 2>/dev/null || true
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@quidpath.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
EOF

echo ""
echo -e "${YELLOW}Billing: Running migrations...${NC}"
docker exec billing-backend-dev python manage.py migrate --noinput 2>/dev/null || echo "Migrations already applied"

echo -e "${YELLOW}Billing: Creating superuser...${NC}"
docker exec billing-backend-dev python manage.py shell << 'EOF' 2>/dev/null || true
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@billing.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
EOF

echo ""
echo -e "${YELLOW}Tazama AI: Running migrations...${NC}"
docker exec tazama-ai-backend-dev python manage.py migrate --noinput 2>/dev/null || echo "Migrations already applied"

echo -e "${YELLOW}Tazama AI: Creating superuser...${NC}"
docker exec tazama-ai-backend-dev python manage.py shell << 'EOF' 2>/dev/null || true
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@tazama.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
EOF

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All Services Started!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${BLUE}Service URLs:${NC}"
echo -e "  Backend:    ${GREEN}http://localhost:8000${NC}"
echo -e "  Backend Admin: ${GREEN}http://localhost:8000/admin${NC}"
echo -e "  Billing:    ${GREEN}http://localhost:8002${NC}"
echo -e "  Billing Admin: ${GREEN}http://localhost:8002/admin${NC}"
echo -e "  Tazama AI:  ${GREEN}http://localhost:8001${NC}"
echo -e "  Tazama Admin: ${GREEN}http://localhost:8001/admin${NC}"
echo ""

echo -e "${BLUE}Admin Credentials:${NC}"
echo -e "  Username: ${GREEN}admin${NC}"
echo -e "  Password: ${GREEN}admin123${NC}"
echo ""

echo -e "${BLUE}Useful Commands:${NC}"
echo -e "  View logs:     ${YELLOW}docker logs -f <container-name>${NC}"
echo -e "  Stop all:      ${YELLOW}docker compose -f docker-compose.dev.yml down${NC}"
echo -e "  Restart:       ${YELLOW}docker compose -f docker-compose.dev.yml restart${NC}"
echo ""

echo -e "${BLUE}Container Names:${NC}"
echo -e "  - django-backend-dev"
echo -e "  - billing-backend-dev"
echo -e "  - tazama-ai-backend-dev"
echo ""

echo -e "${GREEN}Ready to develop!${NC}"
