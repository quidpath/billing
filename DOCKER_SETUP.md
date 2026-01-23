# Docker Setup Instructions

## What Was Fixed

1. **Environment Variables**: Fixed the missing `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` variables by moving them directly into the `docker-compose.dev.yml` file instead of relying on a separate `.env.dev` file.

2. **Dependencies Added**:
   - `whitenoise>=6.5.0` - For serving static files (including admin panel CSS/JS)
   - `psycopg2-binary>=2.9.0` - PostgreSQL adapter for Python

3. **Static Files Configuration**: 
   - WhiteNoise is already configured in `base.py` settings
   - Static files will be collected automatically on container startup

4. **Superuser Auto-Creation**:
   - Created management command `create_superuser` to automatically create admin user
   - Updated `start.sh` to run this command on startup

5. **Port Mapping**: Fixed port mapping to `8002:8002` for proper access

## How to Use

### 1. Build and Start Containers

```bash
# Build the containers (first time or after dependency changes)
docker compose -f docker-compose.dev.yml build

# Start the containers
docker compose -f docker-compose.dev.yml up
```

### 2. Access the Application

- **API Base URL**: http://localhost:8002/
- **Admin Panel**: http://localhost:8002/admin/
- **Admin Credentials**:
  - Username: `admin`
  - Password: `admin123`

### 3. Change Superuser Credentials (Optional)

Edit the environment variables in `docker-compose.dev.yml`:

```yaml
environment:
  DJANGO_SUPERUSER_USERNAME: your_username
  DJANGO_SUPERUSER_EMAIL: your_email@example.com
  DJANGO_SUPERUSER_PASSWORD: your_secure_password
```

Then rebuild and restart:

```bash
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up --build
```

### 4. View Logs

```bash
# All services
docker compose -f docker-compose.dev.yml logs -f

# Just the web service
docker compose -f docker-compose.dev.yml logs -f web

# Just the database
docker compose -f docker-compose.dev.yml logs -f db
```

### 5. Stop Containers

```bash
# Graceful shutdown
docker compose -f docker-compose.dev.yml down

# Remove volumes (WARNING: deletes database data)
docker compose -f docker-compose.dev.yml down -v
```

### 6. Execute Commands in Running Container

```bash
# Django shell
docker compose -f docker-compose.dev.yml exec web python manage.py shell

# Create migrations
docker compose -f docker-compose.dev.yml exec web python manage.py makemigrations

# Run migrations
docker compose -f docker-compose.dev.yml exec web python manage.py migrate

# Create another superuser manually
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

## Database Access

**Connection Details**:
- Host: `localhost` (from host machine) or `db` (from web container)
- Port: `5433` (mapped from container's 5432)
- Database: `billing_devdb`
- Username: `devuser`
- Password: `devpass`

**Connect with psql**:
```bash
psql -h localhost -p 5433 -U devuser -d billing_devdb
# Password: devpass
```

## Troubleshooting

### Static Files Not Loading in Admin Panel

If admin panel looks broken (no styling):

1. Exec into container and collect static files manually:
```bash
docker compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput
```

2. Restart the container:
```bash
docker compose -f docker-compose.dev.yml restart web
```

### Database Connection Issues

Check if the database is ready:
```bash
docker compose -f docker-compose.dev.yml logs db
```

The database should show: `database system is ready to accept connections`

### Port Already in Use

If port 8002 is already in use, change it in `docker-compose.dev.yml`:
```yaml
ports:
  - "8003:8002"  # Change 8003 to any available port
```

### Reset Everything

To start fresh:
```bash
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up
```

## Environment Variables Reference

All environment variables are now in `docker-compose.dev.yml`. Key variables:

- `DEBUG`: Set to "True" for development
- `SECRET_KEY`: Django secret key (change in production)
- `DATABASE_URL`: PostgreSQL connection string
- `DJANGO_SUPERUSER_USERNAME`: Admin username (default: admin)
- `DJANGO_SUPERUSER_EMAIL`: Admin email
- `DJANGO_SUPERUSER_PASSWORD`: Admin password (default: admin123)
- `PESAWAY_TEST_MODE`: Set to "true" for test mode

## Next Steps

1. ✅ Containers are configured and ready
2. ✅ Admin panel accessible at http://localhost:8002/admin/
3. ✅ Static files configured with WhiteNoise
4. ✅ Superuser auto-created on startup
5. Configure Pesaway payment gateway credentials in the environment variables
6. Add your business logic and models
7. Test the payment integration

## Production Deployment

For production, use `docker-compose.yml` instead and ensure:
- Change `SECRET_KEY` to a secure random value
- Set `DEBUG=False`
- Configure proper `ALLOWED_HOSTS`
- Use strong database credentials
- Enable SSL for database connections
- Set up proper domain and HTTPS


