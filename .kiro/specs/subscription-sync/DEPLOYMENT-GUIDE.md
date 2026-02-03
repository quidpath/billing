# Subscription Synchronization - Deployment Guide

## Overview

This guide covers deploying the subscription synchronization system that keeps subscription status in sync between the Billing Service and Main Backend.

## Architecture

```
┌─────────────────┐         Webhooks          ┌──────────────────┐
│ Billing Service │ ─────────────────────────> │  Main Backend    │
│                 │                            │                  │
│ - Subscriptions │  subscription.created      │ - Corporate      │
│ - Plans         │  subscription.activated    │   Subscriptions  │
│ - Payments      │  subscription.cancelled    │ - Access Control │
└─────────────────┘  subscription.expired      └──────────────────┘
                     payment.succeeded
                     payment.failed
```

## Environment Variables

### Main Backend (.env)

```bash
# Webhook Secret (must match Billing Service)
BILLING_WEBHOOK_SECRET=your-secure-webhook-secret-here

# Billing Service URL
BILLING_SERVICE_URL=http://billing-service:8002/api/billing
```

### Billing Service (.env)

```bash
# Main Backend URL
ERP_BACKEND_URL=http://django-backend:8000

# Webhook Secret (must match Main Backend)
BILLING_WEBHOOK_SECRET=your-secure-webhook-secret-here
```

## Database Migrations

### Main Backend

Run the migration to create the CorporateSubscription table:

```bash
cd quidpath-backend
python manage.py migrate OrgAuth
```

This creates the `corporate_subscriptions` table with the following structure:
- corporate_id (UUID, indexed)
- plan_id (UUID)
- plan_name (varchar)
- plan_slug (varchar)
- status (varchar: trial, active, expired, cancelled, suspended)
- start_date (datetime)
- end_date (datetime)
- trial_end_date (datetime, nullable)
- features (JSON)
- billing_subscription_id (UUID, unique)
- auto_renew (boolean)
- grace_period_days (integer)

## Webhook Events

The Billing Service sends the following webhook events to the Main Backend:

### 1. subscription.created
Sent when a new subscription is created.

### 2. subscription.activated
Sent when a subscription is activated (after trial or payment).

### 3. subscription.cancelled
Sent when a subscription is cancelled by the corporate.

### 4. subscription.expired
Sent when a subscription expires (end_date reached).

### 5. subscription.upgraded
Sent when a subscription is upgraded to a higher plan.

### 6. subscription.downgraded
Sent when a subscription is downgraded to a lower plan.

### 7. payment.succeeded
Sent when a payment is successfully processed.

### 8. payment.failed
Sent when a payment fails.

## Webhook Security

Webhooks are secured using HMAC-SHA256 signatures:

1. Billing Service generates signature using `BILLING_WEBHOOK_SECRET`
2. Signature is sent in `X-Webhook-Signature` header
3. Main Backend validates signature before processing webhook

## API Endpoints

### Main Backend

#### Webhook Endpoint (Internal)
```
POST /api/org-auth/webhooks/subscription
Headers:
  X-Webhook-Signature: <hmac-sha256-signature>
Body:
  {
    "event": "subscription.created",
    "data": { ... }
  }
```

#### Subscription API (For Corporates)

**Get My Subscription**
```
GET /api/org-auth/subscription/my-subscription
Headers:
  Authorization: Bearer <jwt-token>
Response:
  {
    "id": "uuid",
    "plan_name": "Premium",
    "status": "active",
    "start_date": "2026-01-01T00:00:00Z",
    "end_date": "2026-02-01T00:00:00Z",
    "features": {...},
    "days_until_expiry": 28
  }
```

**Check Feature Access**
```
GET /api/org-auth/subscription/check-feature?feature=advanced_reporting
Headers:
  Authorization: Bearer <jwt-token>
Response:
  {
    "has_access": true,
    "feature": "advanced_reporting"
  }
```

**Get Subscription Features**
```
GET /api/org-auth/subscription/features
Headers:
  Authorization: Bearer <jwt-token>
Response:
  {
    "enabled_features": ["basic_reporting", "advanced_reporting", "api_access"]
  }
```

**Sync Subscription from Billing**
```
POST /api/org-auth/subscription/sync
Headers:
  Authorization: Bearer <jwt-token>
Response:
  {
    "message": "Subscription synced successfully",
    "subscription": {...}
  }
```

## Access Control

### Middleware

The subscription middleware automatically checks subscription status for all requests:

```python
# In quidpath_backend/settings/base.py
MIDDLEWARE = [
    ...
    'OrgAuth.middleware.subscription_middleware.SubscriptionMiddleware',
]
```

### Decorators

Use decorators to protect views:

```python
from OrgAuth.middleware.subscription_middleware import (
    require_subscription,
    require_feature,
    require_plan_level
)

@require_subscription()
def my_view(request):
    # Only accessible with active subscription
    pass

@require_feature('advanced_reporting')
def advanced_report(request):
    # Only accessible if subscription includes this feature
    pass

@require_plan_level('premium')
def premium_feature(request):
    # Only accessible with premium or higher plan
    pass
```

## Testing

### 1. Test Webhook Delivery

Create a subscription in Billing Service and verify webhook is received:

```bash
# Check Main Backend logs
docker logs django-backend | grep "Webhook received"
```

### 2. Test Subscription Sync

```bash
# From Main Backend
curl -X POST http://localhost:8000/api/org-auth/subscription/sync \
  -H "Authorization: Bearer <jwt-token>"
```

### 3. Test Access Control

```bash
# Try accessing protected endpoint
curl http://localhost:8000/api/protected-endpoint \
  -H "Authorization: Bearer <jwt-token>"
```

## Monitoring

### Webhook Logs

Check Billing Service logs for webhook delivery:

```bash
docker logs billing-service | grep "Webhook"
```

### Subscription Status

Check Main Backend logs for subscription updates:

```bash
docker logs django-backend | grep "Subscription"
```

## Troubleshooting

### Webhook Not Received

1. Check `BILLING_WEBHOOK_SECRET` matches in both services
2. Check `ERP_BACKEND_URL` is correct in Billing Service
3. Check network connectivity between services
4. Check Main Backend logs for errors

### Subscription Not Syncing

1. Verify webhook signature is valid
2. Check subscription exists in Billing Service
3. Check corporate_id matches between services
4. Run manual sync: `POST /api/org-auth/subscription/sync`

### Access Denied Errors

1. Check subscription status is "active" or "trial"
2. Check subscription has not expired
3. Check feature is included in plan
4. Check grace period settings

## Production Checklist

- [ ] Set strong `BILLING_WEBHOOK_SECRET` in both services
- [ ] Run migrations on Main Backend
- [ ] Configure `ERP_BACKEND_URL` in Billing Service
- [ ] Configure `BILLING_SERVICE_URL` in Main Backend
- [ ] Test webhook delivery end-to-end
- [ ] Test access control decorators
- [ ] Set up monitoring for webhook failures
- [ ] Configure grace period for expired subscriptions
- [ ] Test subscription sync API endpoint
- [ ] Document subscription features for each plan

## Next Steps

1. Create subscription plans in Billing Service
2. Configure features for each plan
3. Test subscription creation flow
4. Implement frontend subscription display
5. Add subscription upgrade/downgrade UI
6. Set up payment processing integration
