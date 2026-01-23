# Quidpath Billing Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React/Next.js)                     │
│                         Port 3000                                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Quidpath Main Backend                             │
│                    Django REST Framework                             │
│                    Port 8000/8001                                    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Request Flow                                      │ │
│  │                                                                │ │
│  │  1. User Request                                               │ │
│  │        ↓                                                       │ │
│  │  2. JWT Authentication                                         │ │
│  │        ↓                                                       │ │
│  │  3. SubscriptionMiddleware ←──────────┐                       │ │
│  │        │                               │                       │ │
│  │        ├─ Extract corporate_id         │                       │ │
│  │        │                               │                       │ │
│  │        ├─ Check if exempt path         │                       │ │
│  │        │  (login, register, etc.)      │                       │ │
│  │        │                               │                       │ │
│  │        └─ If not exempt ───────────────┤                       │ │
│  │                                        │                       │ │
│  │  4. Call Billing Service               │                       │ │
│  │     (check_access)                     │                       │ │
│  │        ↓                               │                       │ │
│  │  5. has_access = true?                 │                       │ │
│  │        │                               │                       │ │
│  │        ├─ YES → Continue to View       │                       │ │
│  │        │                               │                       │ │
│  │        └─ NO → 403 Forbidden ──────────┘                       │ │
│  │           (Trial expired/No subscription)                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Apps & Services                                   │ │
│  │                                                                │ │
│  │  • Authentication  - User management, JWT                      │ │
│  │  • OrgAuth        - Corporate/Company management               │ │
│  │  • Banking        - Banking operations                         │ │
│  │  • Accounting     - Accounting features                        │ │
│  │  • Payments       - Payment processing                         │ │
│  │  • Core           - Shared utilities, middleware               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │          Billing Integration Endpoints                         │ │
│  │          /api/billing/                                         │ │
│  │                                                                │ │
│  │  • GET  /status/              - Get subscription status        │ │
│  │  • GET  /invoices/            - List my invoices               │ │
│  │  • GET  /plans/               - List available plans           │ │
│  │  • POST /subscribe/           - Subscribe to plan              │ │
│  │  • POST /payment/initiate/    - Pay invoice                    │ │
│  │  • POST /promotion/validate/  - Validate promo code            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP Requests
                             │ (Internal network)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Billing Microservice                              │
│                    Django REST Framework                             │
│                    Port 8002                                         │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Core Endpoints                                    │ │
│  │                                                                │ │
│  │  POST /api/billing/access/check/                               │ │
│  │       ↓                                                        │ │
│  │       Check Trial Status                                       │ │
│  │       ↓                                                        │ │
│  │       Active? → Return has_access: true                        │ │
│  │       ↓                                                        │ │
│  │       Check Subscription Status                                │ │
│  │       ↓                                                        │ │
│  │       Active? → Return has_access: true                        │ │
│  │       ↓                                                        │ │
│  │       Return has_access: false                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Data Models                                       │ │
│  │                                                                │ │
│  │  • Plan          - Subscription plans (Starter/Pro/Enterprise) │ │
│  │  • Trial         - 30-day free trials                          │ │
│  │  • Subscription  - Active subscriptions                        │ │
│  │  • Invoice       - Generated invoices                          │ │
│  │  • Payment       - Payment records                             │ │
│  │  • Promotion     - Discount codes                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Services                                          │ │
│  │                                                                │ │
│  │  • TrialService         - Trial management                     │ │
│  │  • SubscriptionService  - Subscription lifecycle               │ │
│  │  • InvoiceService       - Invoice generation                   │ │
│  │  • PaymentService       - Payment processing                   │ │
│  │  • PromotionService     - Discount management                  │ │
│  │  • NotificationService  - Email notifications                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
         ┌──────────────────┐  ┌──────────────────┐
         │   PostgreSQL     │  │   Pesaway API    │
         │   Port 5433      │  │  (Payment Gateway)│
         │                  │  │                  │
         │  • Plans         │  │  • M-Pesa        │
         │  • Trials        │  │  • Card Payments │
         │  • Subscriptions │  │  • Webhooks      │
         │  • Invoices      │  └──────────────────┘
         │  • Payments      │
         └──────────────────┘
```

## Access Control Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   User Makes Request                            │
│              GET /api/accounting/accounts/                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           SubscriptionMiddleware.__call__()                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Is path exempt? │
                    │ (/admin/, etc.)│
                    └────────┬───────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
             YES                           NO
              │                             │
              ▼                             ▼
    ┌─────────────────┐         ┌──────────────────────┐
    │ Allow Request   │         │ Extract corporate_id │
    └─────────────────┘         │ from user object     │
                                └──────────┬───────────┘
                                           │
                                           ▼
                                ┌────────────────────┐
                                │ corporate_id found?│
                                └──────────┬─────────┘
                                           │
                              ┌────────────┴────────────┐
                              │                         │
                             NO                        YES
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌──────────────────────────┐
                    │ Allow Request   │    │ HTTP POST to Billing     │
                    │ (other middleware│    │ /api/billing/access/check│
                    │  will handle)    │    └──────────┬───────────────┘
                    └─────────────────┘               │
                                                      ▼
                                        ┌──────────────────────────┐
                                        │ Billing Service Checks:  │
                                        │                          │
                                        │ 1. Active Trial?         │
                                        │    - Not expired         │
                                        │    - Days remaining > 0  │
                                        │                          │
                                        │ 2. Active Subscription?  │
                                        │    - Status = 'active'   │
                                        │    - Not expired         │
                                        │    - End date > today    │
                                        └──────────┬───────────────┘
                                                   │
                                    ┌──────────────┴──────────────┐
                                    │                             │
                                   YES                           NO
                            has_access: true          has_access: false
                                    │                             │
                                    ▼                             ▼
                    ┌───────────────────────────┐  ┌──────────────────────┐
                    │ Add subscription_info     │  │ Return 403 Forbidden │
                    │ to request object         │  │                      │
                    │                           │  │ {                    │
                    │ Continue to View          │  │   "error":           │
                    │                           │  │   "subscription_     │
                    │ Return Response           │  │    required",        │
                    └───────────────────────────┘  │   "message":         │
                                                   │   "Trial expired"    │
                                                   │ }                    │
                                                   └──────────────────────┘
```

## Subscription Lifecycle State Machine

```
                        ┌──────────────────┐
                        │  Company Created │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Create Trial    │
                        │  (30 days)       │
                        └────────┬─────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Trial Active         │
                    │   has_access = true    │
                    └────────┬───────────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
                  │                     │
          Days pass (7 left)    Days pass (3 left)
                  │                     │
                  ▼                     ▼
        ┌─────────────────┐   ┌─────────────────┐
        │ Email: Trial    │   │ Email: Trial    │
        │ Expiring Soon   │   │ Expires in 3    │
        └─────────────────┘   └─────────────────┘
                  │                     │
                  └──────────┬──────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Trial Expired   │
                    │  has_access = false│
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │ User Subscribes │           │ Access Blocked  │
    └────────┬────────┘           │ (No subscription)│
             │                    └─────────────────┘
             ▼
    ┌─────────────────────┐
    │ Create Subscription │
    │ Generate Invoice    │
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────┐
    │ Invoice Sent        │
    │ Status: pending     │
    └────────┬────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐     ┌─────────────┐
│ User    │     │ Reminder    │
│ Pays    │     │ Emails      │
└────┬────┘     │ (7,3,1 days)│
     │          └─────────────┘
     ▼
┌──────────────────────┐
│ Payment Processing   │
│ (Pesaway)            │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Webhook Received     │
│ Payment Confirmed    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────┐
│ Invoice Status: paid     │
│ Subscription: active     │
│ has_access = true        │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Email: Payment Confirmed │
│ Access Granted           │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│ Recurring Billing        │
│ (Monthly/Yearly)         │
└──────────┬───────────────┘
           │
           │ (Next billing date)
           └─────────────────────┐
                                 ▼
                    ┌────────────────────────┐
                    │ Generate New Invoice   │
                    │ (Automatic renewal)    │
                    └────────────────────────┘
```

## Payment Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   User: "Pay Invoice"                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/billing/payments/initiate/                           │
│  {                                                              │
│    "invoice_id": "uuid",                                        │
│    "payment_method": "mpesa",                                   │
│    "customer_phone": "+254712345678"                            │
│  }                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              PaymentService.initiate_payment()                  │
│                                                                 │
│  1. Create Payment record (status: pending)                     │
│  2. Call PesawayAdapter                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PesawayAdapter                               │
│                                                                 │
│  if payment_method == 'mpesa':                                  │
│     - POST to Pesaway M-Pesa API                                │
│     - Return provider_reference                                 │
│                                                                 │
│  if payment_method == 'card':                                   │
│     - POST to Pesaway Card API                                  │
│     - Return checkout_url                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Update Payment Status                              │
│              status: pending → processing                       │
│              Save provider_reference                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Return to User                                     │
│  {                                                              │
│    "success": true,                                             │
│    "payment_id": "uuid",                                        │
│    "provider_reference": "PSW-12345",                           │
│    "checkout_url": "https://...",                               │
│    "message": "STK push sent to your phone"                     │
│  }                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │
            ┌────────────────┴────────────────┐
            │                                 │
            ▼                                 ▼
┌───────────────────────┐         ┌──────────────────────┐
│  M-Pesa: STK Push     │         │  Card: Redirect to   │
│  to User's Phone      │         │  Checkout Page       │
└───────────┬───────────┘         └──────────┬───────────┘
            │                                 │
            │ User enters PIN                 │ User enters card details
            │                                 │
            └────────────────┬────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Pesaway Processes Payment                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Pesaway → Webhook to Billing Service                           │
│  POST /api/billing/payments/webhook/                            │
│  {                                                              │
│    "provider_reference": "PSW-12345",                           │
│    "status": "success",                                         │
│    "signature": "hmac-signature"                                │
│  }                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           PaymentService.handle_payment_webhook()               │
│                                                                 │
│  1. Verify webhook signature (HMAC)                             │
│  2. Find Payment by provider_reference                          │
│  3. Update Payment status: processing → completed               │
│  4. Update Invoice status: pending → paid                       │
│  5. Mark Invoice.paid_at = now()                                │
│  6. Update Subscription: activate/extend                        │
│  7. Send confirmation email                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Email: "Payment Confirmed"                         │
│              User can now access Quidpath                       │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema (Simplified)

```
┌─────────────────────────┐
│        Corporate        │
│     (Main Backend)      │
├─────────────────────────┤
│ id (UUID)               │
│ name                    │
│ email                   │
│ ...                     │
└───────────┬─────────────┘
            │
            │ corporate_id (FK reference)
            │
            ▼
┌──────────────────────────────────────────────────────────────────┐
│                 Billing Microservice Tables                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐      ┌──────────────────┐                 │
│  │      Plan       │      │      Trial       │                 │
│  ├─────────────────┤      ├──────────────────┤                 │
│  │ id              │      │ id               │                 │
│  │ name            │◄─────┤ plan (FK)        │                 │
│  │ tier            │      │ corporate_id     │                 │
│  │ price_monthly   │      │ corporate_name   │                 │
│  │ included_users  │      │ start_date       │                 │
│  └─────────────────┘      │ end_date         │                 │
│                           │ status           │                 │
│  ┌─────────────────┐      └──────────────────┘                 │
│  │  Subscription   │                                            │
│  ├─────────────────┤                                            │
│  │ id              │                                            │
│  │ plan (FK)       ├────►┌──────────────────┐                  │
│  │ corporate_id    │     │     Invoice      │                  │
│  │ corporate_name  │     ├──────────────────┤                  │
│  │ status          │     │ id               │                  │
│  │ billing_cycle   │◄────┤ subscription(FK) │                  │
│  │ start_date      │     │ corporate_id     │                  │
│  │ end_date        │     │ invoice_number   │                  │
│  │ total_amount    │     │ status           │                  │
│  └─────────────────┘     │ total_amount     │                  │
│                          │ due_date         │                  │
│                          │ paid_at          │                  │
│                          └────────┬─────────┘                  │
│                                   │                            │
│                                   ▼                            │
│                          ┌──────────────────┐                  │
│                          │     Payment      │                  │
│                          ├──────────────────┤                  │
│                          │ id               │                  │
│                          │ invoice (FK)     │                  │
│                          │ corporate_id     │                  │
│                          │ amount           │                  │
│                          │ payment_method   │                  │
│                          │ provider         │                  │
│                          │ status           │                  │
│                          │ provider_ref     │                  │
│                          │ paid_at          │                  │
│                          └──────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
```

## Component Interactions

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │─────►│ Main Backend │─────►│   Billing    │
│              │◄─────│              │◄─────│ Microservice │
└──────────────┘      └──────────────┘      └──────────────┘
      │                      │                      │
      │                      │                      │
      ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Browser    │      │  PostgreSQL  │      │  PostgreSQL  │
│   Storage    │      │  (Main DB)   │      │ (Billing DB) │
└──────────────┘      └──────────────┘      └──────────────┘
                             │                      │
                             │                      │
                             ▼                      ▼
                      ┌──────────────┐      ┌──────────────┐
                      │    Redis     │      │   Pesaway    │
                      │   (Cache)    │      │   Gateway    │
                      └──────────────┘      └──────────────┘
```

## Security Layers

```
Layer 1: Network Security
┌─────────────────────────────────────┐
│ • HTTPS/SSL                         │
│ • Firewall rules                    │
│ • VPC isolation                     │
└─────────────────────────────────────┘

Layer 2: Authentication
┌─────────────────────────────────────┐
│ • JWT tokens                        │
│ • Session management                │
│ • Password hashing (bcrypt)         │
└─────────────────────────────────────┘

Layer 3: Authorization
┌─────────────────────────────────────┐
│ • SubscriptionMiddleware            │
│ • Role-based access control         │
│ • Corporate ID validation           │
└─────────────────────────────────────┘

Layer 4: Data Security
┌─────────────────────────────────────┐
│ • Corporate data isolation          │
│ • Encrypted database connections    │
│ • Sensitive data encryption         │
└─────────────────────────────────────┘

Layer 5: Payment Security
┌─────────────────────────────────────┐
│ • Webhook signature verification    │
│ • PCI DSS compliance (Pesaway)      │
│ • No card data stored locally       │
└─────────────────────────────────────┘
```

---

This architecture ensures:
- ✅ **High Availability** - Fail-open design
- ✅ **Security** - Multi-layer protection
- ✅ **Scalability** - Microservice architecture
- ✅ **Data Integrity** - Strong validation
- ✅ **User Experience** - Clear error messages
- ✅ **Compliance** - PCI DSS through Pesaway

© 2026 Quidpath. All rights reserved.


