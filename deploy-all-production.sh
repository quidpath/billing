#!/bin/bash

# Production Deployment Script for QuidPath Multi-Service Architecture
# This script deploys the main backend and all microservices with shared authentication

set -e  # Exit on any error

echo "=========================================="
echo "🚀 QuidPath Production Deployment"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run with sudo"
    exit 1
fi

# Step 1: Create shared Docker network
echo "=========================================="
echo "📡 Step 1: Setting up shared network"
echo "=========================================="
if docker network inspect quidpath_network >/dev/null 2>&1; then
    print_info "Network 'quidpath_network' already exists"
else
    docker network create quidpath_network
    print_success "Created shared network 'quidpath_network'"
fi
echo ""

# Step 2: Deploy Main Backend (QuidPath)
echo "=========================================="
echo "🏢 Step 2: Deploying Main Backend"
echo "=========================================="
cd quidpath-backend

print_info "Stopping existing containers..."
docker compose down

print_info "Building and starting main backend..."
docker compose up -d --build

print_info "Waiting for database to be ready..."
sleep 10

print_info "Running migrations..."
docker compose exec -T backend python manage.py migrate --noinput

print_info "Creating superuser (if not exists)..."
docker compose exec -T backend python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@quidpath.com', 'admin123')
    print("Superuser created successfully")
else:
    print("Superuser already exists")
EOF

print_info "Collecting static files..."
docker compose exec -T backend python manage.py collectstatic --noinput

print_success "Main backend deployed successfully"
cd ..
echo ""

# Step 3: Deploy Billing Microservice
echo "=========================================="
echo "💳 Step 3: Deploying Billing Microservice"
echo "=========================================="
cd billing

print_info "Stopping existing containers..."
docker compose down

print_info "Building and starting billing service..."
docker compose up -d --build

print_info "Waiting for database to be ready..."
sleep 10

print_info "Running migrations for billing database..."
docker compose exec -T backend python manage.py migrate --database=default --noinput

print_info "Running migrations for shared auth database..."
docker compose exec -T backend python manage.py migrate --database=auth_db --noinput

print_info "Collecting static files..."
docker compose exec -T backend python manage.py collectstatic --noinput

print_success "Billing microservice deployed successfully"
cd ..
echo ""

# Step 4: Deploy Tazama AI Microservice
echo "=========================================="
echo "🤖 Step 4: Deploying Tazama AI Microservice"
echo "=========================================="
cd tazama-ai-microservice

print_info "Stopping existing containers..."
docker compose down

print_info "Building and starting Tazama AI service..."
docker compose up -d --build

print_info "Waiting for database to be ready..."
sleep 10

print_info "Running migrations for Tazama database..."
docker compose exec -T web python manage.py migrate --database=default --noinput

print_info "Running migrations for shared auth database..."
docker compose exec -T web python manage.py migrate --database=auth_db --noinput

print_info "Collecting static files..."
docker compose exec -T web python manage.py collectstatic --noinput

print_success "Tazama AI microservice deployed successfully"
cd ..
echo ""

# Step 5: Verify all services
echo "=========================================="
echo "🔍 Step 5: Verifying Services"
echo "=========================================="

print_info "Checking service health..."
echo ""

# Check main backend
if curl -f http://localhost:8000/api/auth/health/ >/dev/null 2>&1; then
    print_success "Main Backend (Port 8000): Running"
else
    print_error "Main Backend (Port 8000): Not responding"
fi

# Check billing service
if curl -f http://localhost:8002/api/billing/health/ >/dev/null 2>&1; then
    print_success "Billing Service (Port 8002): Running"
else
    print_error "Billing Service (Port 8002): Not responding"
fi

# Check Tazama AI service
if curl -f http://localhost:8001/api/tazama/ >/dev/null 2>&1; then
    print_success "Tazama AI Service (Port 8001): Running"
else
    print_error "Tazama AI Service (Port 8001): Not responding"
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Service URLs:"
echo "  Main Backend:    http://localhost:8000"
echo "  Billing Service: http://localhost:8002"
echo "  Tazama AI:       http://localhost:8001"
echo ""
echo "Admin Panel:"
echo "  URL: http://localhost:8000/admin/"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Note: All services share the same authentication database."
echo "You can log into any admin panel with the same credentials."
echo ""
