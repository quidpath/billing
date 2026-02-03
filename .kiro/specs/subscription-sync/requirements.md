# Subscription Synchronization System

## Overview
Implement a bidirectional synchronization system between the Billing Service and Main Backend to ensure subscription status, payment information, and access control are consistent across both systems.

## Problem Statement
Currently:
- Billing Service manages subscriptions and payments
- Main Backend needs to know subscription status to enforce access control
- Corporates need to see billing information from the main ERP interface
- No synchronization mechanism exists between the two systems

## User Stories

### 1. Corporate Subscription Purchase
**As a** corporate admin  
**I want to** choose and purchase a billing plan  
**So that** my organization's users can access features based on the plan

**Acceptance Criteria:**
- 1.1 Corporate can view available plans in the main ERP
- 1.2 Corporate can select a plan and initiate payment
- 1.3 Payment is processed in Billing Service
- 1.4 Subscription status is immediately synced to Main Backend
- 1.5 Users gain access to features based on the plan

### 2. Subscription Status Enforcement
**As a** main backend  
**I want to** know the current subscription status of each corporate  
**So that** I can enforce access control to features

**Acceptance Criteria:**
- 2.1 Main Backend has a local copy of subscription status
- 2.2 Subscription status includes: plan_id, status, start_date, end_date, features
- 2.3 Access control middleware checks subscription before allowing feature access
- 2.4 Expired subscriptions are automatically detected and access revoked
- 2.5 Trial periods are supported

### 3. Billing Information Visibility
**As a** corporate admin  
**I want to** view my billing history and invoices from the main ERP  
**So that** I can manage my organization's finances

**Acceptance Criteria:**
- 3.1 Corporate can view current subscription details in main ERP
- 3.2 Corporate can view payment history
- 3.3 Corporate can download invoices
- 3.4 Corporate can see upcoming renewal dates
- 3.5 Corporate can upgrade/downgrade plans

### 4. Webhook-Based Synchronization
**As a** billing service  
**I want to** notify the main backend when subscription changes occur  
**So that** access control is updated in real-time

**Acceptance Criteria:**
- 4.1 Billing Service sends webhook on subscription creation
- 4.2 Billing Service sends webhook on payment success/failure
- 4.3 Billing Service sends webhook on subscription cancellation
- 4.4 Billing Service sends webhook on plan upgrade/downgrade
- 4.5 Main Backend processes webhooks and updates local subscription data
- 4.6 Webhook delivery is retried on failure (max 3 attempts)

### 5. Subscription API Endpoints
**As a** main backend  
**I want to** query subscription status from Billing Service  
**So that** I can verify access control decisions

**Acceptance Criteria:**
- 5.1 Main Backend can query subscription by corporate_id
- 5.2 Main Backend can verify feature access for a corporate
- 5.3 API responses include plan details and feature list
- 5.4 API is authenticated with service API key
- 5.5 API responses are cached for performance

### 6. Access Control Middleware
**As a** developer  
**I want to** easily enforce subscription-based access control  
**So that** features are only accessible to subscribed corporates

**Acceptance Criteria:**
- 6.1 Decorator `@require_subscription(plan='premium')` enforces access
- 6.2 Decorator `@require_feature('advanced_analytics')` enforces feature access
- 6.3 Unauthorized access returns 403 with clear error message
- 6.4 Trial period is respected
- 6.5 Grace period after expiry is supported (configurable)

## Technical Requirements

### Data Models

#### Main Backend - CorporateSubscription
```python
class CorporateSubscription(BaseModel):
    corporate_id = UUIDField()  # Reference to Corporate
    plan_id = UUIDField()  # Reference to Plan in Billing Service
    plan_name = CharField()  # Cached plan name
    status = CharField()  # active, expired, cancelled, trial
    start_date = DateTimeField()
    end_date = DateTimeField()
    trial_end_date = DateTimeField(null=True)
    features = JSONField()  # List of enabled features
    billing_subscription_id = UUIDField()  # Reference to Billing Service subscription
    last_synced_at = DateTimeField()
    auto_renew = BooleanField(default=True)
```

#### Billing Service - Subscription (existing, may need updates)
```python
class Subscription(BaseModel):
    corporate_id = UUIDField()
    plan = ForeignKey(Plan)
    status = CharField()  # active, expired, cancelled, trial
    start_date = DateTimeField()
    end_date = DateTimeField()
    trial_end_date = DateTimeField(null=True)
    auto_renew = BooleanField(default=True)
```

### Webhook Events

1. **subscription.created**
   - Sent when a new subscription is created
   - Payload: subscription details, plan details, corporate_id

2. **subscription.activated**
   - Sent when payment is successful and subscription becomes active
   - Payload: subscription_id, corporate_id, start_date, end_date

3. **subscription.cancelled**
   - Sent when subscription is cancelled
   - Payload: subscription_id, corporate_id, cancellation_date

4. **subscription.expired**
   - Sent when subscription expires
   - Payload: subscription_id, corporate_id, expiry_date

5. **subscription.upgraded**
   - Sent when plan is upgraded
   - Payload: subscription_id, old_plan, new_plan, corporate_id

6. **subscription.downgraded**
   - Sent when plan is downgraded
   - Payload: subscription_id, old_plan, new_plan, corporate_id

7. **payment.succeeded**
   - Sent when payment is successful
   - Payload: payment_id, subscription_id, amount, corporate_id

8. **payment.failed**
   - Sent when payment fails
   - Payload: payment_id, subscription_id, reason, corporate_id

### API Endpoints

#### Billing Service → Main Backend
- `POST /api/billing/webhooks/subscription/` - Receive subscription webhooks
- `GET /api/billing/subscription/status/<corporate_id>/` - Get subscription status

#### Main Backend → Billing Service
- `GET /api/billing/subscriptions/<corporate_id>/` - Get subscription details
- `GET /api/billing/subscriptions/<corporate_id>/features/` - Get enabled features
- `POST /api/billing/subscriptions/<corporate_id>/verify-feature/` - Verify feature access

## Non-Functional Requirements

1. **Performance**: Webhook processing < 500ms
2. **Reliability**: 99.9% webhook delivery success rate
3. **Consistency**: Subscription data synced within 5 seconds
4. **Availability**: Access control checks < 50ms (cached)
5. **Security**: All webhooks signed with HMAC-SHA256

## Out of Scope

1. Payment gateway integration (already handled by Billing Service)
2. Billing invoice generation (already handled by Billing Service)
3. Tax calculation (already handled by Billing Service)
4. Refund processing (already handled by Billing Service)

## Success Metrics

1. 100% of subscription changes synced to Main Backend
2. < 5 seconds sync latency
3. 99.9% webhook delivery success rate
4. Zero unauthorized feature access
5. < 50ms access control check latency

## Dependencies

1. JWT authentication system (already implemented)
2. Webhook signature verification library
3. Celery for async webhook processing (optional)
4. Redis for caching subscription status

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Webhook delivery failure | High | Implement retry mechanism with exponential backoff |
| Sync delay | Medium | Use Redis cache, implement polling fallback |
| Inconsistent state | High | Add reconciliation job to sync periodically |
| Performance degradation | Medium | Cache subscription status, use async processing |
| Security breach | Critical | Sign webhooks, validate signatures, use HTTPS |
