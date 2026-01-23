# Billing System Testing Guide

This guide will help you test the complete billing system with M-Pesa STK push integration and 30-day free trials.

## Prerequisites

1. **Backend Service Running** (Port 8002)
2. **Frontend Running** (Port 3000)
3. **M-Pesa Sandbox Credentials** (from Daraja Portal)
4. **ngrok** (for local webhook testing)

## Setup Steps

### 1. Configure Environment Variables

#### Backend (.env)
```bash
# M-Pesa Sandbox
MPESA_TEST_MODE=true
MPESA_CONSUMER_KEY=your_sandbox_consumer_key
MPESA_CONSUMER_SECRET=your_sandbox_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_CALLBACK_URL=https://your-ngrok-url.ngrok.io/api/billing/payments/webhook/mpesa/

# Paystack Sandbox (for card payments)
PAYSTACK_TEST_MODE=true
PAYSTACK_PUBLIC_KEY=pk_test_your_key
PAYSTACK_SECRET_KEY=sk_test_your_key
PAYSTACK_CALLBACK_URL=http://localhost:8002/api/billing/payments/webhook/
```

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/
NEXT_PUBLIC_BILLING_SERVICE_URL=http://localhost:8002/api/billing
NEXT_PUBLIC_ENABLE_BILLING=true
NEXT_PUBLIC_ENABLE_FREE_TRIAL=true
NEXT_PUBLIC_FREE_TRIAL_DAYS=30
```

### 2. Start ngrok (for webhook testing)

```bash
ngrok http 8002
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and update `MPESA_CALLBACK_URL` in your `.env` file.

### 3. Start Services

```bash
# Backend billing service
cd billing
python manage.py runserver 8002

# Frontend
cd quidpath-erp-frontend
npm run dev
```

## Test Scenarios

### Scenario 1: New User - 30-Day Free Trial

**Objective:** Test automatic trial activation for new company

**Steps:**
1. **Create New Company Account**
   - Sign up with a new company email
   - Complete registration
   - Note the `corporate_id` from browser console

2. **Activate Free Trial**
   ```bash
   curl -X POST http://localhost:8002/api/billing/trials/create/ \
   -H "Content-Type: application/json" \
   -d '{
     "corporate_id": "your-corporate-id",
     "corporate_name": "Test Company",
     "plan_tier": "starter"
   }'
   ```

3. **Verify Trial Status**
   - Navigate to `/billing` in frontend
   - Should see: "30-Day Free Trial Active"
   - Should show days remaining

4. **Access System**
   - Try accessing various features
   - Should have full access during trial
   - Trial countdown should be visible

**Expected Results:**
- ✅ Trial created successfully
- ✅ 30 days remaining displayed
- ✅ Full system access granted
- ✅ Trial expiry reminder appears when <7 days left

---

### Scenario 2: Subscribe to a Plan

**Objective:** Create subscription and generate invoice

**Steps:**
1. **Navigate to Billing Page**
   - Go to `/billing`
   - Click "Plans & Pricing" tab

2. **Select a Plan**
   - Choose "Professional" plan
   - Click "Select Plan"

3. **Configure Subscription**
   - Select billing cycle (Monthly/Quarterly/Yearly)
   - Add additional users if needed
   - Enter promotion code (if any)
   - Click "Validate Code" if promotion added

4. **Create Subscription**
   - Review order summary
   - Click "Start Free Trial" or "Subscribe Now"
   - System creates subscription
   - Invoice automatically generated

5. **Verify Invoice Created**
   - Switch to "Invoices" tab
   - Should see new invoice with "PENDING" status
   - Amount should match subscription price

**Expected Results:**
- ✅ Subscription created successfully
- ✅ Invoice generated with correct amount
- ✅ Invoice status is "pending"
- ✅ Due date is set correctly

---

### Scenario 3: Pay Invoice with M-Pesa STK Push

**Objective:** Complete payment using M-Pesa sandbox

**Steps:**
1. **Find Unpaid Invoice**
   - Go to `/billing` → "Invoices" tab
   - Click "Pay Now" on pending invoice

2. **Select M-Pesa Payment**
   - In payment dialog, select "M-Pesa" tab
   - Enter test phone number: `254708374149`
   - Click "Pay with M-Pesa"

3. **STK Push Initiated**
   - Should see: "STK push sent to your phone!"
   - Progress indicator shows "Waiting for confirmation..."

4. **Sandbox Auto-Completion**
   - In sandbox, payment auto-completes after ~5 seconds
   - No actual phone interaction needed

5. **Payment Confirmation**
   - After ~10 seconds, payment status updates
   - Success message: "Payment successful!"
   - Invoice status changes to "PAID"

6. **Verify Subscription Activated**
   - Page refreshes automatically
   - Subscription status shows "ACTIVE"
   - Next billing date is set

**Expected Results:**
- ✅ STK push initiated successfully
- ✅ Payment completes automatically (sandbox)
- ✅ Invoice marked as "PAID"
- ✅ Subscription activated
- ✅ User gets confirmation notification

**Test Phone Numbers (Sandbox):**
- `254708374149` - Success
- `254708374150` - Success
- `254708374151` - Success

---

### Scenario 4: Pay with Card (Paystack)

**Objective:** Complete payment using card payment

**Steps:**
1. **Initiate Card Payment**
   - Go to pending invoice
   - Click "Pay Now"
   - Select "Card" tab

2. **Enter Email**
   - Enter email: `test@example.com`
   - Click "Pay with Card"

3. **Redirected to Paystack**
   - New window opens with Paystack checkout
   - Enter test card details:
     - Card: `4084084084084081`
     - CVV: `408`
     - Expiry: `12/25`
     - PIN: `0000`

4. **Complete Payment**
   - Click "Pay"
   - Paystack processes payment
   - Redirects back to app

5. **Verify Payment**
   - Invoice status updates to "PAID"
   - Subscription activated

**Expected Results:**
- ✅ Redirected to Paystack checkout
- ✅ Test card payment succeeds
- ✅ Webhook received
- ✅ Invoice marked as paid
- ✅ Subscription activated

**Paystack Test Cards:**
```
Success: 4084084084084081 (CVV: 408, PIN: 0000)
Decline: 5060666666666666666 (CVV: 606, PIN: 0000)
```

---

### Scenario 5: Trial Expiration

**Objective:** Test what happens when trial expires

**Steps:**
1. **Manually Expire Trial** (for testing)
   ```bash
   # Update trial end_date to yesterday
   python manage.py shell
   >>> from billing.models import Trial
   >>> from datetime import datetime, timedelta
   >>> trial = Trial.objects.first()
   >>> trial.end_date = datetime.now().date() - timedelta(days=1)
   >>> trial.save()
   ```

2. **Access System**
   - Try to access Quidpath features
   - Should be blocked or see warning

3. **Check Access Endpoint**
   ```bash
   curl -X POST http://localhost:8002/api/billing/access/check/ \
   -H "Content-Type: application/json" \
   -d '{"corporate_id": "your-corporate-id"}'
   ```

4. **Verify Response**
   - Should return: `has_access: false`
   - Reason: `trial_expired`

5. **Subscribe to Continue**
   - User must subscribe to regain access
   - Follow Scenario 2 and 3 to subscribe and pay

**Expected Results:**
- ✅ Trial marked as expired
- ✅ Access denied message shown
- ✅ User prompted to subscribe
- ✅ After subscription + payment, access restored

---

### Scenario 6: Promotion Code

**Objective:** Apply discount with promotion code

**Steps:**
1. **Create Promotion** (via Django admin)
   - Go to: http://localhost:8002/admin/
   - Navigate to Billing → Promotions
   - Create new promotion:
     - Code: `LAUNCH50`
     - Type: `percentage`
     - Value: `50` (50% off)
     - Valid from: today
     - Valid until: 30 days from now
     - Applicable plans: All

2. **Apply During Subscription**
   - Go to billing page
   - Select a plan
   - Enter code: `LAUNCH50`
   - Click "Validate Code"
   - Should show: "Discount applied: KES X,XXX"

3. **Verify Discount**
   - Order summary shows original price
   - Discount line shows -50%
   - Total reflects discounted amount

4. **Complete Subscription**
   - Proceed with subscription
   - Invoice amount should be discounted

**Expected Results:**
- ✅ Promotion code validates successfully
- ✅ Discount calculated correctly
- ✅ Invoice reflects discounted amount
- ✅ Discount recorded in subscription

---

## Webhook Testing

### Test M-Pesa Webhook Manually

```bash
curl -X POST http://localhost:8002/api/billing/payments/webhook/mpesa/ \
-H "Content-Type: application/json" \
-d '{
  "Body": {
    "stkCallback": {
      "MerchantRequestID": "test-merchant-123",
      "CheckoutRequestID": "ws_CO_12345678",
      "ResultCode": 0,
      "ResultDesc": "The service request is processed successfully.",
      "CallbackMetadata": {
        "Item": [
          {"Name": "Amount", "Value": 1000},
          {"Name": "MpesaReceiptNumber", "Value": "ABC123XYZ"},
          {"Name": "PhoneNumber", "Value": 254708374149}
        ]
      }
    }
  }
}'
```

### Test Paystack Webhook Manually

```bash
curl -X POST http://localhost:8002/api/billing/payments/webhook/ \
-H "Content-Type: application/json" \
-H "x-paystack-signature: test_signature" \
-d '{
  "event": "charge.success",
  "data": {
    "reference": "test_ref_123",
    "status": "success",
    "amount": 100000,
    "currency": "KES"
  }
}'
```

---

## Testing Checklist

### Free Trial Testing
- [ ] New company automatically gets 30-day trial
- [ ] Trial days countdown correctly
- [ ] Warning appears when <7 days remaining
- [ ] Trial expires and blocks access after 30 days
- [ ] User can subscribe during trial

### Subscription Testing
- [ ] Can select different plans
- [ ] Billing cycle options work (monthly/quarterly/yearly)
- [ ] Additional users calculated correctly
- [ ] Promotion codes apply correctly
- [ ] Invoice generated on subscription creation

### M-Pesa Payment Testing
- [ ] STK push initiated successfully
- [ ] Payment status polling works
- [ ] Payment confirmation received
- [ ] Invoice marked as paid
- [ ] Subscription activated
- [ ] Webhook processes correctly

### Card Payment Testing
- [ ] Redirect to Paystack works
- [ ] Test card payment succeeds
- [ ] Webhook received and processed
- [ ] Invoice updated correctly
- [ ] User redirected back to app

### Access Control Testing
- [ ] Active trial grants access
- [ ] Active subscription grants access
- [ ] Expired trial blocks access
- [ ] Unpaid subscription blocks access
- [ ] Check access endpoint works correctly

---

## Common Issues & Solutions

### Issue: STK Push Not Received
**Solution:**
- Verify phone number format (254XXXXXXXXX)
- Check M-Pesa credentials are correct
- Ensure using sandbox test numbers
- Check callback URL is accessible (ngrok)

### Issue: Webhook Not Triggered
**Solution:**
- Verify ngrok is running
- Check MPESA_CALLBACK_URL is set correctly
- Ensure backend is accessible from internet
- Check firewall settings

### Issue: Payment Status Not Updating
**Solution:**
- Check polling interval (should poll every 4 seconds)
- Verify webhook endpoint is working
- Check payment_id and provider_reference are saved
- Look at backend logs for errors

### Issue: Trial Not Created
**Solution:**
- Verify corporate_id is valid UUID
- Check plan exists in database
- Ensure trial doesn't already exist
- Check database constraints

### Issue: Promotion Code Invalid
**Solution:**
- Verify promotion exists in database
- Check valid_from and valid_until dates
- Ensure is_active is True
- Check usage_limit not exceeded

---

## Monitoring & Logs

### Backend Logs
```bash
# Watch Django logs
tail -f /path/to/billing/logs/django.log

# Watch payment logs
tail -f /path/to/billing/logs/payments.log
```

### Frontend Logs
```bash
# Browser console
# Look for:
# - Payment initiation requests
# - Polling status updates
# - Error messages
```

### Database Queries
```sql
-- Check trial status
SELECT * FROM billing_trial WHERE corporate_id = 'your-id';

-- Check subscription
SELECT * FROM billing_subscription WHERE corporate_id = 'your-id';

-- Check invoices
SELECT * FROM billing_invoice WHERE corporate_id = 'your-id';

-- Check payments
SELECT * FROM billing_payment WHERE invoice_id = 'invoice-id';
```

---

## Production Checklist

Before going live:

- [ ] Switch to production M-Pesa credentials
- [ ] Set `MPESA_TEST_MODE=false`
- [ ] Update callback URL to production domain
- [ ] Switch to production Paystack keys
- [ ] Set up proper SSL certificates
- [ ] Configure webhook monitoring/alerts
- [ ] Set up error tracking (Sentry)
- [ ] Enable payment reconciliation
- [ ] Set up backup webhooks
- [ ] Test with real small transactions first
- [ ] Set up customer support for payment issues
- [ ] Configure email notifications
- [ ] Set up automated invoice generation
- [ ] Enable payment failure retries
- [ ] Configure subscription renewal reminders

---

## Support Resources

- **M-Pesa**: apisupport@safaricom.co.ke
- **Paystack**: support@paystack.com
- **Quidpath**: support@quidpath.com

## Report Issues

If you encounter issues during testing, please include:
1. Steps to reproduce
2. Expected vs actual behavior
3. Screenshots/logs
4. Environment (sandbox/production)
5. Test phone numbers/emails used
