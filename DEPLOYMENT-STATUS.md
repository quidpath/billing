# QuidPath Deployment Status

## Services Overview

### 1. Main Backend (quidpath-backend)
- **Port**: 8000
- **Database**: postgres_prod (quidpath_db)
- **User Model**: Authentication.CustomUser
- **Status**: Independent service with custom user model
- **CI/CD**: Comprehensive pipeline with code quality, security scans, and automated deployment
- **Features**: JWT authentication, subscription management, access control

### 2. Billing Service
- **Port**: 8002
- **Database**: postgres_billing_prod (billing_prod)
- **User Model**: Standard Django auth.User
- **Status**: Independent service with own database and users
- **CI/CD**: Comprehensive pipeline with code quality, security scans, and automated deployment
- **Features**: Subscription management, payment processing, webhook notifications

### 3. Tazama AI Service
- **Port**: 8001
- **Database**: tazama_postgres (tazama_db)
- **User Model**: Standard Django auth.User
- **Status**: Independent service with own database and users
- **CI/CD**: Comprehensive pipeline with code quality, security scans, and automated deployment
- **Features**: AI-powered fraud detection, transaction analysis

## Architecture

### Microservices Authentication
All services use JWT-based authentication for cross-service communication:
- Main Backend issues JWT tokens containing user_id, corporate_id, username, email, role
- Billing and Tazama services validate JWT tokens via middleware
- User data cached locally (1 hour TTL) for performance
- Corporate data cached locally (24 hours TTL)
- No database coupling between services

**Documentation**: `.kiro/specs/microservices-authentication/`

### Subscription Synchronization
Billing Service syncs subscription status to Main Backend via webhooks:
- Billing Service sends webhook events on subscription changes
- Main Backend stores subscription status for access control
- Webhooks secured with HMAC-SHA256 signatures
- Feature-based access control via decorators
- Grace period support for expired subscriptions

**Documentation**: `.kiro/specs/subscription-sync/`

## Deployment

Each service is completely independent:
- Separate databases
- Separate user management
- Separate superusers
- Communication via REST APIs and webhooks

### Deploy Billing Service

```bash
cd ~/quidpath-deployment/billing
bash deploy.sh
```

### Create Superusers

```bash
# Main Backend
docker exec django-backend python manage.py createsuperuser

# Billing
docker exec billing-backend python manage.py createsuperuser

# Tazama AI
docker exec tazama-ai-backend python manage.py createsuperuser
```

### Run Migrations

```bash
# Main Backend (includes subscription sync)
docker exec django-backend python manage.py migrate

# Billing
docker exec billing-backend python manage.py migrate

# Tazama AI
docker exec tazama-ai-backend python manage.py migrate
```

## Environment Variables

### Main Backend
```bash
JWT_SECRET_KEY=your-jwt-secret
BILLING_SERVICE_API_KEY=your-billing-api-key
TAZAMA_SERVICE_API_KEY=your-tazama-api-key
BILLING_WEBHOOK_SECRET=your-webhook-secret
BILLING_SERVICE_URL=http://billing-service:8002/api/billing
```

### Billing Service
```bash
JWT_SECRET_KEY=your-jwt-secret
SERVICE_API_KEY=your-billing-api-key
ERP_BACKEND_URL=http://django-backend:8000
BILLING_WEBHOOK_SECRET=your-webhook-secret
```

### Tazama AI Service
```bash
JWT_SECRET_KEY=your-jwt-secret
SERVICE_API_KEY=your-tazama-api-key
ERP_BACKEND_URL=http://django-backend:8000
```

## CI/CD Pipelines

All three services now have comprehensive CI/CD pipelines:

### Code Quality Checks
- **Black**: Code formatting validation
- **isort**: Import sorting validation
- **Flake8**: Linting and code style checks
- **mypy**: Type checking (optional)

### Security Scans
- **Bandit**: Python security vulnerability scanning
- **Safety**: Dependency vulnerability scanning
- **Trivy**: Docker image security scanning

### Django Checks
- System checks with deployment settings
- Migration validation
- Database connectivity tests

### Deployment
- Automated Docker image building
- Multi-platform support (linux/amd64, linux/arm64)
- Blue-green deployment strategy
- Health checks after deployment
- Automated database migrations
- Slack notifications

### Pipeline Files
- Main Backend: `.github/workflows/ci-cd-backend.yml`
- Billing Service: `.github/workflows/ci-cd-billing.yml`
- Tazama AI: `.github/workflows/ci-cd-tazama.yml`

## Code Quality Status

All services pass code quality checks:
- ✅ Black formatting
- ✅ isort import sorting
- ✅ Flake8 linting (no critical errors)
- ✅ Django system checks

## Network

All services connected via `quidpath_network` for inter-service communication.

## Clean Code

- No emojis in code
- Simple professional comments
- Production-ready configuration
- Proper error handling
- All code formatted and linted

## Features Implemented

### JWT Authentication System
- Token-based authentication across microservices
- User and corporate data caching
- Secure API key validation
- No database coupling

### Subscription Synchronization
- Real-time webhook notifications
- Subscription status tracking
- Feature-based access control
- Grace period support
- Manual sync fallback

### Access Control
- Subscription-based access control
- Feature-level permissions
- Plan-level restrictions
- Middleware enforcement
