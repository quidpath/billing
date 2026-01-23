# Quidpath Billing Integration Guide

## Overview

The billing microservice provides complete subscription management for Quidpath, similar to how Netflix, Odoo, or Acumatica manage customer billing. Companies **cannot use Quidpath without an active subscription or trial**.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Quidpath Main Backend                     │
│                    (Port 8000/8001)                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  SubscriptionMiddleware                                │ │
│  │  - Checks every request                                │ │
│  │  - Verifies active subscription/trial                  │ │
│  │  - Blocks access if expired                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Billing Integration Endpoints                         │ │
│  │  /api/billing/status/                                  │ │
│  │  /api/billing/invoices/                                │ │
│  │  /api/billing/subscribe/                               │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────│───────────────────────────────────┘
                           │
                           │ HTTP Requests
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Billing Microservice (Port 8002)               │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Access Control Endpoint                               │ │
│  │  /api/billing/access/check/                            │ │
│  │  - Returns has_access: true/false                      │ │
│  │  - Checks trials and subscriptions                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Billing Management                                    │ │
│  │  - Plans, Trials, Subscriptions                        │ │
│  │  - Invoices, Payments                                  │ │
│  │  - Notifications                                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. **Company Registration** (OrgAuth)
When a new company registers:
- Company is created in `Corporate` model
- Trial can be automatically created via billing service
- Company gets 30 days free trial

### 2. **Access Control** (Every Request)
The `SubscriptionMiddleware` runs on every request:

```python
# Exempt paths (no billing check):
- /admin/
- /api/auth/login/
- /api/auth/register/
- /api/corporate/register/
- /api/billing/

# All other paths are checked
```

**Flow:**
1. Extract `corporate_id` from authenticated user
2. Call billing service: `POST /api/billing/access/check/`
3. Get response with `has_access: true/false`
4. If `false`, return `403 Forbidden` with message
5. If `true`, allow request to proceed

### 3. **Access Check Response**

#### Active Trial:
```json
{
  "success": true,
  "has_access": true,
  "access_type": "trial",
  "corporate_id": "uuid",
  "trial": {
    "status": "active",
    "days_remaining": 15,
    "end_date": "2026-01-20T00:00:00Z"
  }
}
```

#### Active Subscription:
```json
{
  "success": true,
  "has_access": true,
  "access_type": "subscription",
  "corporate_id": "uuid",
  "subscription": {
    "id": "uuid",
    "plan_name": "Professional Plan",
    "plan_tier": "professional",
    "status": "active",
    "end_date": "2026-02-05T00:00:00Z"
  },
  "unpaid_invoices_count": 1,
  "unpaid_invoices": [
    {
      "id": "uuid",
      "invoice_number": "INV-2026-00123",
      "amount": 9999.00,
      "due_date": "2026-01-12T00:00:00Z"
    }
  ]
}
```

#### No Access (Expired Trial):
```json
{
  "success": true,
  "has_access": false,
  "access_type": null,
  "corporate_id": "uuid",
  "reason": "trial_expired",
  "message": "Trial period has expired. Please subscribe to continue using Quidpath.",
  "trial": {
    "status": "expired",
    "end_date": "2026-01-05T00:00:00Z"
  }
}
```

#### No Access (No Subscription):
```json
{
  "success": true,
  "has_access": false,
  "access_type": null,
  "corporate_id": "uuid",
  "reason": "no_active_subscription",
  "message": "No active subscription or trial found. Please subscribe to use Quidpath."
}
```

## API Endpoints

### Billing Service Endpoints (Port 8002)

#### 1. Check Access (CRITICAL)
```
POST /api/billing/access/check/
Content-Type: application/json

{
  "corporate_id": "uuid"
}
```

#### 2. List Plans
```
GET /api/billing/plans/
```

#### 3. Create Trial
```
POST /api/billing/trials/create/
{
  "corporate_id": "uuid",
  "corporate_name": "Acme Corp",
  "plan_tier": "starter"
}
```

#### 4. Get Subscription Status
```
POST /api/billing/subscriptions/status/
{
  "corporate_id": "uuid"
}
```

#### 5. Create Subscription
```
POST /api/billing/subscriptions/create/
{
  "corporate_id": "uuid",
  "corporate_name": "Acme Corp",
  "plan_tier": "professional",
  "billing_cycle": "monthly",
  "additional_users": 5,
  "promotion_code": "LAUNCH50"
}
```

#### 6. List Invoices
```
POST /api/billing/invoices/
{
  "corporate_id": "uuid"
}
```

#### 7. Initiate Payment
```
POST /api/billing/payments/initiate/
{
  "corporate_id": "uuid",
  "invoice_id": "uuid",
  "payment_method": "mpesa",
  "customer_email": "admin@company.com",
  "customer_phone": "+254700000000"
}
```

### Main Backend Endpoints (Port 8000)

These are proxied through the main backend for authenticated users:

#### 1. Get My Subscription Status
```
GET /api/billing/status/
Authorization: Bearer <jwt_token>
```

#### 2. List My Invoices
```
GET /api/billing/invoices/
Authorization: Bearer <jwt_token>
```

#### 3. List Available Plans
```
GET /api/billing/plans/
Authorization: Bearer <jwt_token>
```

#### 4. Subscribe to Plan
```
POST /api/billing/subscribe/
Authorization: Bearer <jwt_token>
{
  "plan_tier": "professional",
  "billing_cycle": "yearly",
  "additional_users": 10,
  "promotion_code": "ANNUAL20"
}
```

#### 5. Pay Invoice
```
POST /api/billing/payment/initiate/
Authorization: Bearer <jwt_token>
{
  "invoice_id": "uuid",
  "payment_method": "mpesa",
  "customer_phone": "+254700000000"
}
```

## Payment Flow

### 1. **Invoice Creation**
When a subscription is created or renewed:
1. System creates invoice with line items
2. Email notification sent (if configured)
3. Invoice status: `pending`

### 2. **Payment Initiation**
User initiates payment:
1. POST to `/api/billing/payments/initiate/`
2. System creates Payment record
3. Calls Pesaway API (M-Pesa/Card)
4. Returns checkout URL or STK push initiated
5. Payment status: `processing`

### 3. **Payment Webhook**
Pesaway sends webhook when payment completes:
1. POST to `/api/billing/payments/webhook/`
2. System verifies signature
3. Updates payment status
4. Updates invoice status to `paid`
5. Activates/extends subscription
6. Sends confirmation email

### 4. **Subscription Activation**
After successful payment:
- Invoice: `pending` → `paid`
- Payment: `processing` → `completed`
- Subscription: `pending` → `active`
- Access: User can now use Quidpath

## Notification System

### Email Notifications

1. **Invoice Created**
   - Sent when new invoice is generated
   - Includes invoice details and due date
   - Call-to-action: "View Invoice"

2. **Payment Confirmed**
   - Sent when payment is successful
   - Includes receipt details
   - Confirms continued access

3. **Invoice Reminder**
   - Sent 7, 3, and 1 days before due date
   - Warns about service interruption
   - Call-to-action: "Pay Now"

4. **Trial Expiring**
   - Sent 7 and 3 days before trial ends
   - Encourages subscription
   - Call-to-action: "Subscribe Now"

### Configuration

Set in environment variables:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=billing@quidpath.com
```

## Security Features

### 1. **Corporate ID Validation**
Every billing endpoint (except public ones) requires `corporate_id`:
- Validates UUID format
- Ensures data isolation between companies
- Prevents unauthorized access

### 2. **Request Verification**
```python
# All endpoints verify corporate_id matches the resource
if str(subscription.corporate_id) != str(corporate_id):
    return 403 Forbidden
```

### 3. **Fail-Open Design**
If billing service is down:
- Middleware allows requests through
- Logs error for monitoring
- Prevents complete system failure

### 4. **Webhook Security**
- Signature verification for payment webhooks
- Prevents fake payment notifications
- Uses HMAC-SHA256

## Testing the Integration

### 1. Start Both Services

**Billing Service:**
```bash
cd e:\billing
docker compose -f docker-compose.dev.yml up
```

**Main Backend:**
```bash
cd e:\quidpath-backend
python manage.py runserver 8000
```

### 2. Create Test Company
```bash
# Register a company through the registration endpoint
POST http://localhost:8000/api/corporate/register/
```

### 3. Create Trial
```bash
POST http://localhost:8002/api/billing/trials/create/
{
  "corporate_id": "<company_uuid>",
  "corporate_name": "Test Company",
  "plan_tier": "starter"
}
```

### 4. Test Access Check
```bash
POST http://localhost:8002/api/billing/access/check/
{
  "corporate_id": "<company_uuid>"
}

# Should return: has_access: true, access_type: "trial"
```

### 5. Login and Try Protected Endpoint
```bash
# Login
POST http://localhost:8000/api/auth/login/
{
  "username": "user@company.com",
  "password": "password"
}

# Access protected resource
GET http://localhost:8000/api/accounting/accounts/
Authorization: Bearer <jwt_token>

# Should work if trial is active
# Should return 403 if trial expired
```

### 6. Subscribe to Plan
```bash
POST http://localhost:8000/api/billing/subscribe/
Authorization: Bearer <jwt_token>
{
  "plan_tier": "professional",
  "billing_cycle": "monthly",
  "additional_users": 5
}
```

### 7. View Invoices
```bash
GET http://localhost:8000/api/billing/invoices/
Authorization: Bearer <jwt_token>
```

### 8. Initiate Payment
```bash
POST http://localhost:8000/api/billing/payment/initiate/
Authorization: Bearer <jwt_token>
{
  "invoice_id": "<invoice_uuid>",
  "payment_method": "mpesa",
  "customer_phone": "+254712345678"
}
```

## Monitoring & Logging

### Key Metrics to Monitor

1. **Access Check Latency**
   - Should be < 200ms
   - Caching can be added for performance

2. **Failed Access Checks**
   - Track companies blocked due to expired subscriptions
   - Correlate with payment failures

3. **Payment Success Rate**
   - Monitor webhook delivery
   - Track payment provider issues

4. **Email Delivery**
   - Monitor notification sending
   - Track bounces and failures

### Log Messages

```python
# Subscription middleware
logger.error(f"Billing service error for corporate {corporate_id}")
logger.error(f"Error checking subscription for corporate {corporate_id}")

# Invoice service
logger.info(f"Invoice {invoice_number} created for corporate {corporate_id}")

# Payment service
logger.info(f"Payment confirmed for invoice {invoice_number}")
```

## Production Checklist

- [ ] Configure SMTP for email notifications
- [ ] Set up Pesaway production credentials
- [ ] Configure webhook URL with SSL
- [ ] Set strong SECRET_KEY in both services
- [ ] Enable database SSL connections
- [ ] Set up monitoring and alerting
- [ ] Configure proper ALLOWED_HOSTS
- [ ] Set DEBUG=False
- [ ] Set up log aggregation
- [ ] Configure Redis for caching (optional)
- [ ] Set up automated invoice reminders
- [ ] Test payment webhook with real transactions
- [ ] Configure backup and disaster recovery
- [ ] Set up rate limiting on billing endpoints
- [ ] Document corporate admin procedures

## Troubleshooting

### Issue: Users blocked despite having active subscription

**Check:**
1. Billing service is running: `curl http://localhost:8002/api/billing/plans/`
2. Subscription status: `POST /api/billing/subscriptions/status/`
3. Check logs for middleware errors
4. Verify corporate_id extraction is working

### Issue: Payments not processing

**Check:**
1. Pesaway credentials configured
2. Webhook URL accessible from internet
3. Payment provider test mode settings
4. Check payment logs in database

### Issue: Notifications not sending

**Check:**
1. SMTP credentials configured
2. SMTP_USER has "App Password" (Gmail)
3. Check email service logs
4. Verify email addresses are valid

## Future Enhancements

1. **Caching Layer**
   - Cache access check results (5-15 minutes)
   - Reduce latency and billing service load

2. **Grace Period**
   - Allow 3-day grace period after invoice due
   - Soft-block with warnings before hard-block

3. **Usage-Based Billing**
   - Track API usage, storage, users
   - Bill based on actual consumption

4. **Self-Service Portal**
   - Frontend dashboard for billing
   - Invoice downloads, payment history
   - Plan upgrades/downgrades

5. **Multi-Currency Support**
   - Support USD, EUR, KES
   - Automatic currency conversion

6. **Dunning Management**
   - Automated retry for failed payments
   - Smart reminder sequences
   - Escalation procedures

## Support

For issues or questions:
- Email: support@quidpath.com
- Slack: #billing-support
- Docs: https://docs.quidpath.com/billing

## License

© 2026 Quidpath. All rights reserved.


