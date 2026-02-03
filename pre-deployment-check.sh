#!/bin/bash

# Pre-Deployment Verification Script
# Checks all configuration before deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}QuidPath Pre-Deployment Check${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to check if value is placeholder
check_placeholder() {
    local value=$1
    local name=$2
    if [[ $value == *"CHANGE"* ]] || [[ $value == *"your_"* ]] || [[ $value == *"your-"* ]]; then
        echo -e "${RED}✗ $name contains placeholder value${NC}"
        ((ERRORS++))
        return 1
    else
        echo -e "${GREEN}✓ $name is configured${NC}"
        return 0
    fi
}

# Function to check if value is strong
check_strength() {
    local value=$1
    local name=$2
    local min_length=$3
    if [ ${#value} -lt $min_length ]; then
        echo -e "${YELLOW}⚠ $name is too short (minimum $min_length characters)${NC}"
        ((WARNINGS++))
        return 1
    else
        echo -e "${GREEN}✓ $name is strong${NC}"
        return 0
    fi
}

# Check Main Backend .env
echo -e "${YELLOW}Checking Main Backend configuration...${NC}"
if [ ! -f /root/quidpath-deployment/backend/.env ]; then
    echo -e "${RED}✗ Main Backend .env file not found${NC}"
    ((ERRORS++))
else
    source /root/quidpath-deployment/backend/.env
    
    check_placeholder "$SECRET_KEY" "Main Backend SECRET_KEY"
    check_strength "$SECRET_KEY" "Main Backend SECRET_KEY" 32
    
    check_placeholder "$JWT_SECRET_KEY" "JWT_SECRET_KEY"
    check_strength "$JWT_SECRET_KEY" "JWT_SECRET_KEY" 32
    
    check_placeholder "$BILLING_WEBHOOK_SECRET" "BILLING_WEBHOOK_SECRET"
    check_strength "$BILLING_WEBHOOK_SECRET" "BILLING_WEBHOOK_SECRET" 32
    
    check_placeholder "$BILLING_SERVICE_API_KEY" "BILLING_SERVICE_API_KEY"
    check_placeholder "$TAZAMA_SERVICE_API_KEY" "TAZAMA_SERVICE_API_KEY"
    
    check_placeholder "$POSTGRES_PASSWORD" "Main Backend POSTGRES_PASSWORD"
    check_strength "$POSTGRES_PASSWORD" "Main Backend POSTGRES_PASSWORD" 16
    
    if [ "$DEBUG" != "False" ]; then
        echo -e "${RED}✗ DEBUG is not set to False${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ DEBUG is False${NC}"
    fi
    
    MAIN_JWT=$JWT_SECRET_KEY
    MAIN_WEBHOOK=$BILLING_WEBHOOK_SECRET
    MAIN_BILLING_KEY=$BILLING_SERVICE_API_KEY
    MAIN_TAZAMA_KEY=$TAZAMA_SERVICE_API_KEY
fi

echo ""

# Check Billing Service .env
echo -e "${YELLOW}Checking Billing Service configuration...${NC}"
if [ ! -f /root/quidpath-deployment/billing/.env ]; then
    echo -e "${RED}✗ Billing Service .env file not found${NC}"
    ((ERRORS++))
else
    source /root/quidpath-deployment/billing/.env
    
    check_placeholder "$SECRET_KEY" "Billing SECRET_KEY"
    check_strength "$SECRET_KEY" "Billing SECRET_KEY" 32
    
    check_placeholder "$JWT_SECRET_KEY" "Billing JWT_SECRET_KEY"
    check_strength "$JWT_SECRET_KEY" "Billing JWT_SECRET_KEY" 32
    
    check_placeholder "$BILLING_WEBHOOK_SECRET" "Billing BILLING_WEBHOOK_SECRET"
    check_placeholder "$SERVICE_API_KEY" "Billing SERVICE_API_KEY"
    
    check_placeholder "$POSTGRES_PASSWORD" "Billing POSTGRES_PASSWORD"
    check_strength "$POSTGRES_PASSWORD" "Billing POSTGRES_PASSWORD" 16
    
    if [ "$DEBUG" != "False" ]; then
        echo -e "${RED}✗ DEBUG is not set to False${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ DEBUG is False${NC}"
    fi
    
    # Check if JWT secret matches Main Backend
    if [ "$JWT_SECRET_KEY" != "$MAIN_JWT" ]; then
        echo -e "${RED}✗ JWT_SECRET_KEY does not match Main Backend${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ JWT_SECRET_KEY matches Main Backend${NC}"
    fi
    
    # Check if webhook secret matches Main Backend
    if [ "$BILLING_WEBHOOK_SECRET" != "$MAIN_WEBHOOK" ]; then
        echo -e "${RED}✗ BILLING_WEBHOOK_SECRET does not match Main Backend${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ BILLING_WEBHOOK_SECRET matches Main Backend${NC}"
    fi
    
    # Check if service API key matches Main Backend
    if [ "$SERVICE_API_KEY" != "$MAIN_BILLING_KEY" ]; then
        echo -e "${RED}✗ SERVICE_API_KEY does not match Main Backend BILLING_SERVICE_API_KEY${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ SERVICE_API_KEY matches Main Backend${NC}"
    fi
fi

echo ""

# Check Tazama AI .env
echo -e "${YELLOW}Checking Tazama AI configuration...${NC}"
if [ ! -f /root/quidpath-deployment/tazama/.env ]; then
    echo -e "${RED}✗ Tazama AI .env file not found${NC}"
    ((ERRORS++))
else
    source /root/quidpath-deployment/tazama/.env
    
    check_placeholder "$SECRET_KEY" "Tazama SECRET_KEY"
    check_strength "$SECRET_KEY" "Tazama SECRET_KEY" 32
    
    check_placeholder "$JWT_SECRET_KEY" "Tazama JWT_SECRET_KEY"
    check_strength "$JWT_SECRET_KEY" "Tazama JWT_SECRET_KEY" 32
    
    check_placeholder "$SERVICE_API_KEY" "Tazama SERVICE_API_KEY"
    
    check_placeholder "$POSTGRES_PASSWORD" "Tazama POSTGRES_PASSWORD"
    check_strength "$POSTGRES_PASSWORD" "Tazama POSTGRES_PASSWORD" 16
    
    if [ "$DEBUG" != "False" ]; then
        echo -e "${RED}✗ DEBUG is not set to False${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ DEBUG is False${NC}"
    fi
    
    # Check if JWT secret matches Main Backend
    if [ "$JWT_SECRET_KEY" != "$MAIN_JWT" ]; then
        echo -e "${RED}✗ JWT_SECRET_KEY does not match Main Backend${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ JWT_SECRET_KEY matches Main Backend${NC}"
    fi
    
    # Check if service API key matches Main Backend
    if [ "$SERVICE_API_KEY" != "$MAIN_TAZAMA_KEY" ]; then
        echo -e "${RED}✗ SERVICE_API_KEY does not match Main Backend TAZAMA_SERVICE_API_KEY${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}✓ SERVICE_API_KEY matches Main Backend${NC}"
    fi
fi

echo ""

# Check Docker
echo -e "${YELLOW}Checking Docker installation...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
    docker --version
else
    echo -e "${RED}✗ Docker is not installed${NC}"
    ((ERRORS++))
fi

if command -v docker compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose is installed${NC}"
else
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    ((ERRORS++))
fi

echo ""

# Check Nginx
echo -e "${YELLOW}Checking Nginx installation...${NC}"
if command -v nginx &> /dev/null; then
    echo -e "${GREEN}✓ Nginx is installed${NC}"
    nginx -v
else
    echo -e "${RED}✗ Nginx is not installed${NC}"
    ((ERRORS++))
fi

echo ""

# Check SSL Certificates
echo -e "${YELLOW}Checking SSL certificates...${NC}"
if [ -f /etc/letsencrypt/live/api.quidpath.com/fullchain.pem ]; then
    echo -e "${GREEN}✓ SSL certificate for api.quidpath.com exists${NC}"
else
    echo -e "${YELLOW}⚠ SSL certificate for api.quidpath.com not found${NC}"
    ((WARNINGS++))
fi

if [ -f /etc/letsencrypt/live/billing.quidpath.com/fullchain.pem ]; then
    echo -e "${GREEN}✓ SSL certificate for billing.quidpath.com exists${NC}"
else
    echo -e "${YELLOW}⚠ SSL certificate for billing.quidpath.com not found${NC}"
    ((WARNINGS++))
fi

if [ -f /etc/letsencrypt/live/ai.quidpath.com/fullchain.pem ]; then
    echo -e "${GREEN}✓ SSL certificate for ai.quidpath.com exists${NC}"
else
    echo -e "${YELLOW}⚠ SSL certificate for ai.quidpath.com not found${NC}"
    ((WARNINGS++))
fi

echo ""

# Check Docker Network
echo -e "${YELLOW}Checking Docker network...${NC}"
if docker network ls | grep -q quidpath_network; then
    echo -e "${GREEN}✓ quidpath_network exists${NC}"
else
    echo -e "${YELLOW}⚠ quidpath_network does not exist (will be created during deployment)${NC}"
    ((WARNINGS++))
fi

echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Pre-Deployment Check Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready for deployment.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found. Review before deployment.${NC}"
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) found. Fix before deployment.${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) also found.${NC}"
    fi
    exit 1
fi
