# Quidpath Billing Microservice

**Complete subscription management system for Quidpath ERP** - Similar to how Netflix, Odoo, or Acumatica manage customer billing. Companies **cannot use Quidpath without an active subscription or trial**.

## 🎯 What This Does

This billing microservice ensures that:
- ✅ Every company gets a **30-day free trial** when they register
- ✅ Companies **cannot access Quidpath** without an active subscription or trial
- ✅ All **invoices are tracked** and accessible to companies
- ✅ **Payment processing** is handled securely via Pesaway (M-Pesa & Card)
- ✅ **Email notifications** keep companies informed
- ✅ **Access control** is enforced at the middleware level

## 🚀 Quick Start

### Start Services
```bash
# 1. Start Billing Service
cd e:\billing
docker compose -f docker-compose.dev.yml up

# 2. Start Main Backend (in another terminal)
cd e:\quidpath-backend
python manage.py runserver 8000
```

### Access Points
- **Billing API:** http://localhost:8002/api/billing/
- **Admin Panel:** http://localhost:8002/admin/ (admin/admin123)
- **Main Backend:** http://localhost:8000/
- **Integration API:** http://localhost:8000/api/billing/

### Test It
```bash
# Create a trial
curl -X POST http://localhost:8002/api/billing/trials/create/ \
  -H "Content-Type: application/json" \
  -d '{"corporate_id": "uuid", "corporate_name": "Test", "plan_tier": "starter"}'

# Check access
curl -X POST http://localhost:8002/api/billing/access/check/ \
  -H "Content-Type: application/json" \
  -d '{"corporate_id": "uuid"}'
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[QUICK_START.md](QUICK_START.md)** | Get started in 3 steps |
| **[BILLING_INTEGRATION_GUIDE.md](BILLING_INTEGRATION_GUIDE.md)** | Complete integration guide |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System architecture diagrams |
| **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** | Summary of features |
| **[DOCKER_SETUP.md](DOCKER_SETUP.md)** | Docker configuration |

## ✨ Features

### Subscription Management
- **Plans**: Starter, Professional, Enterprise tiers
- **Billing Cycles**: Monthly, Quarterly, Yearly
- **Add-ons**: Additional users, storage, features
- **Promotions**: Discount codes with validation

### Trial Management
- **30-Day Free Trial** for all new companies
- **Automatic Expiration** tracking
- **Email Reminders** (7, 3 days before expiry)
- **Seamless Conversion** to paid subscription

### Invoice Management
- **Automatic Generation** on subscription events
- **Line Item Breakdown** (plan, add-ons, tax, discounts)
- **Due Date Tracking** with reminders
- **Payment History** with receipts

### Payment Processing
- **M-Pesa Integration** via Pesaway
- **Card Payments** (Visa, Mastercard)
- **Webhook Handling** for payment confirmation
- **Secure Processing** with signature verification

### Access Control
- **Middleware-based** enforcement
- **Real-time Checks** on every request
- **Fail-open Design** for reliability
- **Grace Periods** (configurable)

### Notifications
- **Invoice Created** - When new invoice is generated
- **Payment Confirmed** - On successful payment
- **Invoice Reminders** - 7, 3, 1 days before due
- **Trial Expiring** - 7, 3 days before expiry

## 🏗️ Architecture

```
Frontend → Main Backend (Port 8000)
              ↓
        SubscriptionMiddleware
              ↓
        Check Access Control
              ↓
    Billing Microservice (Port 8002)
              ↓
        Trial/Subscription Check
              ↓
    Return: has_access = true/false
```

**Key Components:**
1. **Main Backend**: Hosts SubscriptionMiddleware that checks access
2. **Billing Service**: Manages subscriptions, invoices, payments
3. **PostgreSQL**: Stores all billing data
4. **Pesaway**: Payment gateway for M-Pesa and cards

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams.

## 🔌 API Endpoints

### Access Control (Critical)
```
POST /api/billing/access/check/
```
Returns whether a company has access to Quidpath.

### Subscription Management
```
GET  /api/billing/plans/
POST /api/billing/trials/create/
POST /api/billing/subscriptions/create/
POST /api/billing/subscriptions/status/
```

### Invoice & Payment
```
POST /api/billing/invoices/
POST /api/billing/payments/initiate/
POST /api/billing/payments/webhook/
```

### Main Backend Integration
```
GET  /api/billing/status/        (authenticated)
GET  /api/billing/invoices/      (authenticated)
POST /api/billing/subscribe/     (authenticated)
POST /api/billing/payment/initiate/ (authenticated)
```

## 🔐 Security Features

- **Corporate ID Validation** - UUID format verification
- **Data Isolation** - Companies can only access their own data
- **Webhook Security** - HMAC signature verification
- **JWT Authentication** - For main backend integration
- **Fail-open Design** - System stays available if billing service is down

## 🛠️ Technology Stack

- **Framework**: Django 4.2+ & Django REST Framework
- **Database**: PostgreSQL 15
- **Payment Gateway**: Pesaway (M-Pesa & Card)
- **Static Files**: WhiteNoise
- **Containerization**: Docker & Docker Compose
- **Email**: SMTP (Gmail/AWS SES)

## 📦 Installation

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for main backend)
- PostgreSQL client (optional)

### Setup
```bash
# 1. Clone repository (already done)
cd e:\billing

# 2. Build and start services
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up

# 3. Access admin panel
# http://localhost:8002/admin/
# Username: admin
# Password: admin123
```

### Configuration

Environment variables are set in `docker-compose.dev.yml`:
```yaml
DATABASE_URL: postgresql://devuser:devpass@db:5432/billing_devdb
DJANGO_SUPERUSER_USERNAME: admin
DJANGO_SUPERUSER_PASSWORD: admin123
PESAWAY_TEST_MODE: true
```

For production, update these values securely.

## 🧪 Testing

### Manual Testing
1. Start both services (billing + main backend)
2. Register a company in main backend
3. Create trial via billing API
4. Login to main backend
5. Try accessing protected endpoints
6. Verify access is granted/denied based on subscription status

### Integration Testing
```bash
# Run tests in billing service
docker compose -f docker-compose.dev.yml exec web python manage.py test

# Run tests in main backend
cd e:\quidpath-backend
python manage.py test
```

## 📊 Monitoring

### Health Checks
```bash
# Billing service
curl http://localhost:8002/api/billing/plans/

# Database
docker compose -f docker-compose.dev.yml exec db pg_isready -U devuser
```

### Logs
```bash
# View all logs
docker compose -f docker-compose.dev.yml logs -f

# View specific service
docker compose -f docker-compose.dev.yml logs -f web
```

## 🚨 Troubleshooting

### Service Won't Start
```bash
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up
```

### Admin Panel No Styles
```bash
docker compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.dev.yml restart web
```

### Access Always Denied
- Check if trial/subscription exists in database
- Verify corporate_id is valid UUID
- Check billing service logs

See [QUICK_START.md](QUICK_START.md) for more troubleshooting tips.

## 🎯 Production Checklist

- [ ] Change default admin credentials
- [ ] Set strong SECRET_KEY
- [ ] Configure real Pesaway credentials
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable database SSL
- [ ] Set up HTTPS for webhooks
- [ ] Configure SMTP for emails
- [ ] Set up monitoring/alerting
- [ ] Configure backups
- [ ] Test payment webhooks with real transactions

## 🤝 Contributing

This is a proprietary system for Quidpath. For internal development:
1. Create feature branch
2. Test thoroughly
3. Update documentation
4. Submit for review

## 📄 License

© 2026 Quidpath. All rights reserved.

---

**Need Help?**
- Check the [Integration Guide](BILLING_INTEGRATION_GUIDE.md)
- Review [Architecture Diagrams](ARCHITECTURE.md)
- See [Quick Start](QUICK_START.md)


