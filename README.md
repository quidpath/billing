# Billing Service

Independent billing microservice for QuidPath ERP.

## Quick Start

```bash
# Start the service
docker compose up -d

# Check logs
docker logs billing-backend

# Create superuser
docker exec billing-backend python manage.py createsuperuser

# Access admin
http://localhost:8002/admin/
```

## Environment Variables

See `.env` file for configuration.

## Database

Uses its own PostgreSQL database (billing_prod).
