#!/bin/bash

# Comprehensive Code Validation Script
# Validates all services for enterprise-grade deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}QuidPath Enterprise Code Validation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check Python code
check_python_service() {
    local service_name=$1
    local service_path=$2
    
    echo -e "${YELLOW}Checking $service_name...${NC}"
    cd "$service_path"
    
    # Check if Python files exist
    if ! find . -name "*.py" -not -path "*/venv/*" -not -path "*/.venv/*" -not -path "*/node_modules/*" | grep -q .; then
        echo -e "${YELLOW}No Python files found in $service_name${NC}"
        cd - > /dev/null
        return
    fi
    
    # Black formatting check
    echo -n "  Black formatting: "
    if python -m black --check --quiet . 2>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${YELLOW}NEEDS FORMATTING${NC}"
        echo "    Running black formatter..."
        python -m black . --quiet 2>/dev/null || true
        ((WARNINGS++))
    fi
    
    # isort check
    echo -n "  Import sorting: "
    if python -m isort --check-only --quiet . 2>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${YELLOW}NEEDS SORTING${NC}"
        echo "    Running isort..."
        python -m isort . --quiet 2>/dev/null || true
        ((WARNINGS++))
    fi
    
    # Flake8 critical errors
    echo -n "  Flake8 critical: "
    if python -m flake8 . --select=E9,F63,F7,F82 --count --quiet 2>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC}"
        python -m flake8 . --select=E9,F63,F7,F82 --show-source 2>/dev/null || true
        ((ERRORS++))
    fi
    
    # Flake8 style warnings
    echo -n "  Flake8 style: "
    local flake8_count=$(python -m flake8 . --count --exit-zero --max-line-length=127 2>/dev/null | tail -1)
    if [ "$flake8_count" -eq 0 ] 2>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${YELLOW}$flake8_count warnings${NC}"
        ((WARNINGS++))
    fi
    
    # Bandit security scan
    echo -n "  Security scan: "
    if python -m bandit -r . -ll --quiet 2>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${YELLOW}WARNINGS${NC}"
        python -m bandit -r . -ll 2>/dev/null | grep -A 5 "Issue:" || true
        ((WARNINGS++))
    fi
    
    cd - > /dev/null
    echo ""
}

# Function to check JavaScript/TypeScript code
check_javascript_service() {
    local service_name=$1
    local service_path=$2
    
    echo -e "${YELLOW}Checking $service_name...${NC}"
    cd "$service_path"
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        echo -e "${YELLOW}No package.json found in $service_name${NC}"
        cd - > /dev/null
        return
    fi
    
    # ESLint check
    echo -n "  ESLint: "
    if npm run lint --silent 2>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${YELLOW}WARNINGS${NC}"
        ((WARNINGS++))
    fi
    
    # TypeScript check
    echo -n "  TypeScript: "
    if npx tsc --noEmit --skipLibCheck 2>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${YELLOW}TYPE ERRORS${NC}"
        ((WARNINGS++))
    fi
    
    # npm audit
    echo -n "  npm audit: "
    local audit_result=$(npm audit --json 2>/dev/null | grep -o '"vulnerabilities":{[^}]*}' || echo '{}')
    if echo "$audit_result" | grep -q '"critical":0,"high":0'; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${YELLOW}VULNERABILITIES${NC}"
        npm audit 2>/dev/null | grep -A 3 "Severity:" || true
        ((WARNINGS++))
    fi
    
    cd - > /dev/null
    echo ""
}

# Check Backend
if [ -d "quidpath-backend" ]; then
    check_python_service "Backend" "quidpath-backend"
else
    echo -e "${RED}Backend directory not found${NC}"
    ((ERRORS++))
fi

# Check Billing
if [ -d "billing" ]; then
    check_python_service "Billing Service" "billing"
else
    echo -e "${RED}Billing directory not found${NC}"
    ((ERRORS++))
fi

# Check Tazama
if [ -d "tazama-ai-microservice" ]; then
    check_python_service "Tazama AI" "tazama-ai-microservice"
else
    echo -e "${RED}Tazama directory not found${NC}"
    ((ERRORS++))
fi

# Check Frontend
if [ -d "quidpath-erp-frontend" ]; then
    check_javascript_service "Frontend" "quidpath-erp-frontend"
else
    echo -e "${RED}Frontend directory not found${NC}"
    ((ERRORS++))
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    echo -e "${GREEN}Code is ready for deployment.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}$WARNINGS warning(s) found.${NC}"
    echo -e "${YELLOW}Code is acceptable but could be improved.${NC}"
    exit 0
else
    echo -e "${RED}$ERRORS error(s) found.${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}$WARNINGS warning(s) also found.${NC}"
    fi
    echo -e "${RED}Fix errors before deployment.${NC}"
    exit 1
fi
