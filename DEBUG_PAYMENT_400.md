# 🔍 Debugging 400 Bad Request Error

## Issue

Getting `400 Bad Request` when trying to pay with M-Pesa using phone `254708374149`.

## What to Check

### 1. Check Backend Logs

The logs should now show detailed information about what's failing:

```bash
docker-compose -f docker-compose.dev.yml logs -f web | grep -i "payment\|error\|warning"
```

**Look for**:
- `Payment initiation request: ...` - Shows what data was received
- `Payment initiation failed: ...` - Shows why it failed

### 2. Common Causes

#### A. Missing Phone Number
**Error**: "Phone number is required for M-Pesa payments"

**Fix**: Make sure phone number is being sent from frontend

#### B. Invalid Corporate ID
**Error**: "Corporate ID is required for payment security"

**Fix**: Check if user is logged in and has corporate association

#### C. Invoice Not Found
**Error**: "Invoice not found"

**Fix**: Verify invoice exists and invoice_id is correct

#### D. Invoice Already Paid
**Error**: "Invoice already paid"

**Fix**: Check invoice status

### 3. Check Frontend Console

Open browser console (F12) and look for:
- `Payment initiation response: {...}` - Shows backend response
- `Payment initiation error: ...` - Shows error message

### 4. Test the Endpoint Directly

You can test the endpoint with curl:

```bash
curl -X POST http://localhost:8002/api/billing/payments/initiate/ \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": "your-invoice-id",
    "corporate_id": "your-corporate-id",
    "payment_method": "mpesa",
    "customer_email": "test@example.com",
    "customer_phone": "254708374149"
  }'
```

### 5. Check What Data is Being Sent

The backend now logs the exact request data. Check logs for:
```
Payment initiation request: invoice_id=..., payment_method=mpesa, customer_phone=254708374149, corporate_id=...
```

---

## Quick Fix Steps

1. **Check backend logs** for the exact error message
2. **Check browser console** for frontend errors
3. **Verify**:
   - User is logged in
   - Invoice exists
   - Phone number is provided
   - Corporate ID is valid

---

## Next Steps

After checking logs, you'll see the exact validation that's failing. The improved logging will show:
- What data was received
- Which validation failed
- Why it failed

This will help identify the exact issue! 🔍
