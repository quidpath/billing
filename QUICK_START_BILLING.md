# Quick Start: Billing System with M-Pesa

Complete guide to get the billing system running in 15 minutes.

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
cd E:\billing
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in `E:\billing`:

```bash
# Django
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for quick start)
DATABASE_URL=sqlite:///db.sqlite3

# M-Pesa Sandbox (Get from https://developer.safaricom.co.ke/)
MPESA_TEST_MODE=true
MPESA_CONSUMER_KEY=your_sandbox_consumer_key
MPESA_CONSUMER_SECRET=your_sandbox_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_CALLBACK_URL=http://localhost:8002/api/billing/payments/webhook/mpesa/

# Paystack (Optional - for card payments)
PAYSTACK_TEST_MODE=true
PAYSTACK_PUBLIC_KEY=pk_test_xxx
PAYSTACK_SECRET_KEY=sk_test_xxx

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 3. Setup Database

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Seed Plans

```bash
python manage.py shell < seed_plans.py
```

### 5. Start Backend

```bash
python manage.py runserver 8002
```

Backend now running at: http://localhost:8002

### 6. Setup Frontend

```bash
cd E:\quidpath-erp-frontend

# Create .env.local
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/" > .env.local
echo "NEXT_PUBLIC_BILLING_SERVICE_URL=http://localhost:8002/api/billing" >> .env.local
echo "NEXT_PUBLIC_ENABLE_BILLING=true" >> .env.local
echo "NEXT_PUBLIC_ENABLE_FREE_TRIAL=true" >> .env.local
echo "NEXT_PUBLIC_FREE_TRIAL_DAYS=30" >> .env.local

# Install dependencies
npm install

# Start frontend
npm run dev
```

Frontend now running at: http://localhost:3000

---

## 📱 Setup M-Pesa Sandbox (5 minutes)

1. **Get Credentials:**
   - Go to: https://developer.safaricom.co.ke/
   - Sign up / Login
   - Create new app
   - Select "Lipa Na M-Pesa Online"
   - Copy Consumer Key and Consumer Secret

2. **Update .env:**
   ```bash
   MPESA_CONSUMER_KEY=your_actual_consumer_key
   MPESA_CONSUMER_SECRET=your_actual_consumer_secret
   ```

3. **Setup Callback (Optional for local testing):**
   ```bash
   # Install ngrok
   ngrok http 8002
   
   # Update .env with ngrok URL
   MPESA_CALLBACK_URL=https://your-ngrok-id.ngrok.io/api/billing/payments/webhook/mpesa/
   ```

---

## 🧪 Quick Test

### Test 1: Create Free Trial

```bash
curl -X POST http://localhost:8002/api/billing/trials/create/ \
-H "Content-Type: application/json" \
-d '{
  "corporate_id": "123e4567-e89b-12d3-a456-426614174000",
  "corporate_name": "Test Company",
  "plan_tier": "starter"
}'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "trial_id": "...",
    "corporate_id": "...",
    "status": "active",
    "days_remaining": 30,
    "end_date": "2024-XX-XX"
  }
}
```

### Test 2: Create Subscription

```bash
curl -X POST http://localhost:8002/api/billing/subscriptions/create/ \
-H "Content-Type: application/json" \
-d '{
  "corporate_id": "123e4567-e89b-12d3-a456-426614174000",
  "corporate_name": "Test Company",
  "plan_tier": "professional",
  "billing_cycle": "monthly",
  "additional_users": 0
}'
```

### Test 3: Initiate M-Pesa Payment

```bash
curl -X POST http://localhost:8002/api/billing/payments/initiate/ \
-H "Content-Type: application/json" \
-d '{
  "invoice_id": "your-invoice-id",
  "corporate_id": "123e4567-e89b-12d3-a456-426614174000",
  "payment_method": "mpesa",
  "customer_email": "test@example.com",
  "customer_phone": "254708374149"
}'
```

**Expected Response:**
```json
{
  "success": true,
  "payment_id": "...",
  "provider_reference": "ws_CO_...",
  "message": "STK push sent to your phone"
}
```

---

## 🌐 Access the System

### Admin Panel
- URL: http://localhost:8002/admin/
- Login with superuser credentials
- View: Plans, Subscriptions, Trials, Invoices, Payments

### Frontend Billing Page
- URL: http://localhost:3000/billing
- See all plans
- Subscribe to plans
- Pay invoices with M-Pesa or Card

### API Documentation
- Base URL: http://localhost:8002/api/billing/
- Endpoints:
  - `GET /plans/` - List all plans
  - `POST /trials/create/` - Create free trial
  - `POST /trials/status/` - Check trial status
  - `POST /subscriptions/create/` - Create subscription
  - `POST /subscriptions/status/` - Check subscription
  - `POST /invoices/` - List invoices
  - `POST /payments/initiate/` - Initiate payment
  - `POST /payments/webhook/mpesa/` - M-Pesa callback
  - `POST /access/check/` - Check access rights

---

## 🎯 Common Use Cases

### Use Case 1: New Company Sign-Up with Free Trial

```javascript
// 1. User signs up for Quidpath
const user = signUp(email, password);

// 2. Automatically create 30-day free trial
const trial = await fetch('/api/billing/trials/create/', {
  method: 'POST',
  body: JSON.stringify({
    corporate_id: user.corporate.id,
    corporate_name: user.corporate.name,
    plan_tier: 'starter'
  })
});

// 3. User gets full access for 30 days
// 4. After 28 days, show upgrade prompt
// 5. After 30 days, restrict access
```

### Use Case 2: Subscribe During Trial

```javascript
// User decides to subscribe before trial ends
const subscription = await fetch('/api/billing/subscriptions/create/', {
  method: 'POST',
  body: JSON.stringify({
    corporate_id: user.corporate.id,
    plan_tier: 'professional',
    billing_cycle: 'yearly', // Get 20% discount
    additional_users: 5
  })
});

// Invoice automatically created
const invoice = subscription.data.invoice_id;

// Pay with M-Pesa
const payment = await fetch('/api/billing/payments/initiate/', {
  method: 'POST',
  body: JSON.stringify({
    invoice_id: invoice,
    payment_method: 'mpesa',
    customer_phone: '254712345678',
    customer_email: user.email
  })
});
```

### Use Case 3: Trial Expires, User Subscribes

```javascript
// Trial expires, user tries to access system
const accessCheck = await fetch('/api/billing/access/check/', {
  method: 'POST',
  body: JSON.stringify({
    corporate_id: user.corporate.id
  })
});

if (!accessCheck.has_access) {
  // Show billing page
  // User selects plan and subscribes
  // User pays invoice
  // Access restored immediately
}
```

---

## 🔍 Troubleshooting

### Backend not starting?
```bash
# Check if port 8002 is in use
lsof -i :8002
# Kill process if needed
kill -9 <PID>
```

### Frontend can't connect to backend?
```bash
# Verify backend is running
curl http://localhost:8002/api/billing/plans/

# Check CORS settings in backend
# Ensure frontend URL is in CORS_ALLOWED_ORIGINS
```

### M-Pesa STK not working?
```bash
# Verify credentials
echo $MPESA_CONSUMER_KEY
echo $MPESA_CONSUMER_SECRET

# Test authentication
curl -X GET https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials \
  -u $MPESA_CONSUMER_KEY:$MPESA_CONSUMER_SECRET
```

### Database errors?
```bash
# Reset database (CAUTION: Deletes all data)
rm db.sqlite3
python manage.py migrate
python manage.py shell < seed_plans.py
```

---

## 📊 Monitor System

### View Logs
```bash
# Django logs
python manage.py runserver 8002 --verbosity 2

# Watch for payment events
tail -f /path/to/logs/payments.log
```

### Check Database
```bash
python manage.py shell
>>> from billing.models import *
>>> Plan.objects.all()
>>> Trial.objects.all()
>>> Subscription.objects.all()
>>> Invoice.objects.all()
>>> Payment.objects.all()
```

### API Health Check
```bash
curl http://localhost:8002/api/billing/plans/
# Should return list of plans
```

---

## 🚀 Go Live Checklist

When ready for production:

- [ ] Get production M-Pesa credentials
- [ ] Set `MPESA_TEST_MODE=false`
- [ ] Update callback URL to production domain (HTTPS!)
- [ ] Switch to production Paystack keys
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set `DEBUG=False`
- [ ] Configure proper SECRET_KEY
- [ ] Set up SSL/TLS certificates
- [ ] Configure proper logging
- [ ] Set up error monitoring (Sentry)
- [ ] Enable webhook verification
- [ ] Set up payment reconciliation
- [ ] Configure email notifications
- [ ] Set up backup system
- [ ] Load test the system
- [ ] Prepare customer support

---

## 📞 Support

- **M-Pesa Issues**: apisupport@safaricom.co.ke
- **Paystack Issues**: support@paystack.com
- **System Issues**: Your dev team 😊

---

## 🎉 You're Ready!

Your billing system is now fully functional with:
- ✅ 30-day free trials
- ✅ M-Pesa STK push payments
- ✅ Card payments (Paystack)
- ✅ Subscription management
- ✅ Invoice generation
- ✅ Access control

**Test payment with:** 254708374149 (M-Pesa sandbox number)

**Next steps:**
1. Customize plans in Django admin
2. Create promotion codes
3. Test complete flow end-to-end
4. Deploy to staging
5. Go live! 🚀
