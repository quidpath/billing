# Subscription Synchronization - Quick Reference

## Environment Setup

### Main Backend (.env)
```bash
BILLING_WEBHOOK_SECRET=your-secure-webhook-secret
BILLING_SERVICE_URL=http://billing-service:8002/api/billing
```

### Billing Service (.env)
```bash
ERP_BACKEND_URL=http://django-backend:8000
BILLING_WEBHOOK_SECRET=your-secure-webhook-secret
```

## Webhook Events

| Event | Trigger | Action |
|-------|---------|--------|
| `subscription.created` | New subscription created | Creates CorporateSubscription in Main Backend |
| `subscription.activated` | Subscription activated | Updates status to "active" |
| `subscription.cancelled` | Subscription cancelled | Updates status to "cancelled" |
| `subscription.expired` | Subscription expired | Updates status to "expired" |
| `subscription.upgraded` | Plan upgraded | Updates plan and features |
| `subscription.downgraded` | Plan downgraded | Updates plan and features |
| `payment.succeeded` | Payment successful | Logs payment success |
| `payment.failed` | Payment failed | Logs payment failure |

## API Endpoints

### Get My Subscription
```bash
GET /api/org-auth/subscription/my-subscription
Authorization: Bearer <jwt-token>
```

### Check Feature Access
```bash
GET /api/org-auth/subscription/check-feature?feature=advanced_reporting
Authorization: Bearer <jwt-token>
```

### Get Enabled Features
```bash
GET /api/org-auth/subscription/features
Authorization: Bearer <jwt-token>
```

### Manual Sync
```bash
POST /api/org-auth/subscription/sync
Authorization: Bearer <jwt-token>
```

## Access Control Decorators

### Require Active Subscription
```python
from OrgAuth.middleware.subscription_middleware import require_subscription

@require_subscription()
def my_view(request):
    # Only accessible with active subscription
    pass
```

### Require Specific Feature
```python
from OrgAuth.middleware.subscription_middleware import require_feature

@require_feature('advanced_reporting')
def advanced_report(request):
    # Only accessible if subscription includes this feature
    pass
```

### Require Plan Level
```python
from OrgAuth.middleware.subscription_middleware import require_plan_level

@require_plan_level('premium')
def premium_feature(request):
    # Only accessible with premium or higher plan
    pass
```

## Subscription Status

| Status | Description | Access Allowed |
|--------|-------------|----------------|
| `trial` | Trial period | Yes (until trial_end_date) |
| `active` | Active subscription | Yes (until end_date) |
| `expired` | Subscription expired | Yes (during grace period) |
| `cancelled` | Subscription cancelled | No |
| `suspended` | Subscription suspended | No |

## Testing Commands

### Test Webhook Delivery
```bash
# Check Main Backend logs
docker logs django-backend | grep "Webhook received"

# Check Billing Service logs
docker logs billing-backend | grep "Webhook sent"
```

### Test Subscription Sync
```bash
curl -X POST http://localhost:8000/api/org-auth/subscription/sync \
  -H "Authorization: Bearer <jwt-token>"
```

### Test Feature Access
```bash
curl http://localhost:8000/api/org-auth/subscription/check-feature?feature=advanced_reporting \
  -H "Authorization: Bearer <jwt-token>"
```

## Common Issues

### Webhook Not Received
- Check `BILLING_WEBHOOK_SECRET` matches in both services
- Verify `ERP_BACKEND_URL` is correct
- Check network connectivity
- Check Main Backend logs for signature validation errors

### Subscription Not Syncing
- Verify webhook signature is valid
- Check subscription exists in Billing Service
- Check corporate_id matches
- Try manual sync endpoint

### Access Denied
- Check subscription status is active/trial
- Verify subscription has not expired
- Check feature is included in plan
- Check grace period settings

## Database Schema

### CorporateSubscription Table
```sql
CREATE TABLE corporate_subscriptions (
    id UUID PRIMARY KEY,
    corporate_id UUID NOT NULL,
    plan_id UUID NOT NULL,
    plan_name VARCHAR(100),
    plan_slug VARCHAR(100),
    status VARCHAR(20),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    trial_end_date TIMESTAMP,
    features JSONB,
    billing_subscription_id UUID UNIQUE,
    auto_renew BOOLEAN,
    grace_period_days INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_corporate_status ON corporate_subscriptions(corporate_id, status);
CREATE INDEX idx_billing_sub ON corporate_subscriptions(billing_subscription_id);
CREATE INDEX idx_end_date ON corporate_subscriptions(end_date);
```

## Deployment Checklist

- [ ] Set `BILLING_WEBHOOK_SECRET` in both services
- [ ] Set `ERP_BACKEND_URL` in Billing Service
- [ ] Set `BILLING_SERVICE_URL` in Main Backend
- [ ] Run migration: `python manage.py migrate OrgAuth`
- [ ] Restart both services
- [ ] Test webhook delivery
- [ ] Test subscription sync
- [ ] Test access control
- [ ] Monitor logs for errors

## Monitoring

### Key Metrics
- Webhook delivery success rate
- Subscription sync latency
- Failed webhook attempts
- Expired subscriptions count
- Grace period usage

### Log Patterns
```bash
# Successful webhook
"Webhook sent successfully: subscription.created"

# Failed webhook
"Webhook failed: subscription.created - Status 500"

# Subscription synced
"Subscription synced successfully for corporate"

# Access denied
"Subscription required but not found"
```

## Support

For issues or questions:
1. Check logs in both services
2. Verify environment variables
3. Test webhook delivery manually
4. Check database records
5. Review DEPLOYMENT-GUIDE.md for detailed troubleshooting
