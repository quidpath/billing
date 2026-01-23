# Quick Start Guide

## 🚀 Start in 3 Steps

### Step 1: Start Billing Service
```bash
cd e:\billing
docker compose -f docker-compose.dev.yml up
```
✅ Wait for: `database system is ready to accept connections`

### Step 2: Start Main Backend
```bash
cd e:\quidpath-backend
python manage.py runserver 8000
```

### Step 3: Test Access
```bash
# Admin Panel (Billing Service)
http://localhost:8002/admin/
Username: admin
Password: admin123

# Main Backend API
http://localhost:8000/api/
```

## 🧪 Quick Test

### 1. Create a Trial
```bash
curl -X POST http://localhost:8002/api/billing/trials/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "corporate_id": "123e4567-e89b-12d3-a456-426614174000",
    "corporate_name": "Test Corp",
    "plan_tier": "starter"
  }'
```

### 2. Check Access
```bash
curl -X POST http://localhost:8002/api/billing/access/check/ \
  -H "Content-Type: application/json" \
  -d '{
    "corporate_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

Expected response:
```json
{
  "success": true,
  "has_access": true,
  "access_type": "trial",
  "trial": {
    "days_remaining": 30
  }
}
```

## 📍 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Billing API | http://localhost:8002/api/billing/ | Billing operations |
| Billing Admin | http://localhost:8002/admin/ | Manage subscriptions |
| Main Backend | http://localhost:8000/ | ERP API |
| Billing Integration | http://localhost:8000/api/billing/ | Proxied endpoints |

## 🔑 Default Credentials

**Billing Admin:**
- Username: `admin`
- Password: `admin123`

⚠️ **Change these immediately in production!**

## 📊 Check Status

### Billing Service Health
```bash
curl http://localhost:8002/api/billing/plans/
```

### Database Connection
```bash
docker compose -f docker-compose.dev.yml exec db psql -U devuser -d billing_devdb -c "SELECT COUNT(*) FROM billing_plan;"
```

### Main Backend Middleware
```bash
# Make authenticated request to any protected endpoint
# Should check subscription status automatically
```

## 🛠️ Common Commands

### Billing Service

**View Logs:**
```bash
docker compose -f docker-compose.dev.yml logs -f web
```

**Restart:**
```bash
docker compose -f docker-compose.dev.yml restart web
```

**Shell Access:**
```bash
docker compose -f docker-compose.dev.yml exec web python manage.py shell
```

**Run Migrations:**
```bash
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
```

**Create Superuser (manual):**
```bash
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### Database

**Access PostgreSQL:**
```bash
docker compose -f docker-compose.dev.yml exec db psql -U devuser -d billing_devdb
```

**Backup Database:**
```bash
docker compose -f docker-compose.dev.yml exec db pg_dump -U devuser billing_devdb > backup.sql
```

## 🔍 Verify Integration

### 1. Check Middleware is Active
Look for this in main backend startup:
```
System check identified no issues (0 silenced).
Starting development server at http://127.0.0.1:8000/
```

### 2. Test Protected Endpoint
```bash
# Login first
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user@company.com", "password": "password"}'

# Use JWT token in protected request
curl http://localhost:8000/api/accounting/accounts/ \
  -H "Authorization: Bearer <your_jwt_token>"
```

If subscription expired:
```json
{
  "success": false,
  "error": "subscription_required",
  "message": "Trial period has expired. Please subscribe to continue using Quidpath.",
  "reason": "trial_expired"
}
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port
netstat -ano | findstr :8002

# Kill process (Windows)
taskkill /PID <process_id> /F
```

### Database Errors
```bash
# Reset database
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up
```

### Billing Service Can't Start
```bash
# Rebuild without cache
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up
```

### Static Files Missing
```bash
docker compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.dev.yml restart web
```

## 📖 Full Documentation

- **Complete Guide:** `BILLING_INTEGRATION_GUIDE.md`
- **Integration Summary:** `INTEGRATION_SUMMARY.md`
- **Docker Setup:** `DOCKER_SETUP.md`
- **Changes Made:** `CHANGES_SUMMARY.md`

## ✅ Success Checklist

- [ ] Billing service running on port 8002
- [ ] Main backend running on port 8000
- [ ] Can access admin panel at http://localhost:8002/admin/
- [ ] Can create trial via API
- [ ] Access check returns correct status
- [ ] Middleware blocks expired subscriptions
- [ ] Can view plans via API
- [ ] Database persists data between restarts

## 🎯 Next Actions

1. ✅ **Test with Real Company Data**
   - Register a real company in main backend
   - Create trial for that company
   - Test access control

2. ✅ **Configure Payments**
   - Get Pesaway test credentials
   - Update environment variables
   - Test payment flow

3. ✅ **Setup Email Notifications**
   - Configure SMTP settings
   - Test invoice emails
   - Test payment confirmations

4. ✅ **Production Preparation**
   - Change admin password
   - Update SECRET_KEY
   - Configure proper domains
   - Set up SSL certificates

## 💡 Tips

- **Development:** Keep both services running in separate terminals
- **Debugging:** Check logs in real-time with `-f` flag
- **Testing:** Use the admin panel to verify data
- **Performance:** Add Redis caching for access checks in production

## 🚨 Important Notes

⚠️ **This is a development setup**
- Default credentials are insecure
- DEBUG mode is enabled
- Test mode for payment gateway
- No SSL/HTTPS configured

🔒 **For production:**
- Change all default credentials
- Set DEBUG=False
- Configure real payment credentials
- Enable HTTPS
- Set up proper monitoring

---

**Ready to go!** 🎉

Start the services and begin testing. For detailed information, see `BILLING_INTEGRATION_GUIDE.md`.


