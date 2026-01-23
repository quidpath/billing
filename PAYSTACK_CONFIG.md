# Paystack Configuration Guide

This billing service has been updated to use **Paystack** instead of Pesaway for payment processing.

## Environment Variables

Add the following environment variables to your `.env` file:

### Required Paystack Variables

```bash
# Paystack Test Mode Configuration
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key_here
PAYSTACK_SECRET_KEY=sk_test_your_secret_key_here
PAYSTACK_TEST_MODE=true
PAYSTACK_CALLBACK_URL=http://localhost:8000/api/billing/webhooks/paystack/
```

### For Production

```bash
# Paystack Live Mode Configuration
PAYSTACK_PUBLIC_KEY=pk_live_your_public_key_here
PAYSTACK_SECRET_KEY=sk_live_your_secret_key_here
PAYSTACK_TEST_MODE=false
PAYSTACK_CALLBACK_URL=https://yourdomain.com/api/billing/webhooks/paystack/
```

## Getting Paystack API Keys

1. Sign up for a Paystack account at https://paystack.com
2. Log in to your Paystack dashboard
3. Navigate to **Settings > API Keys & Webhooks**
4. Copy your **Public Key** and **Secret Key**
5. For testing, use the test keys (starting with `pk_test_` and `sk_test_`)
6. For production, use the live keys (starting with `pk_live_` and `sk_live_`)

## Supported Currencies

Paystack supports the following currencies:
- **NGN** (Nigerian Naira)
- **GHS** (Ghanaian Cedi)
- **ZAR** (South African Rand)
- **USD** (US Dollar)
- **KES** (Kenyan Shilling)

## Supported Payment Methods

The Paystack adapter supports:
- **Card payments** (Visa, Mastercard, Verve)
- **Bank transfers**
- **USSD**
- **Mobile money** (for supported countries)
- **QR payments**

## Payment Flow

1. **Initialize Payment**: Call the payment service to create a payment
2. **Redirect Customer**: Customer is redirected to Paystack checkout page
3. **Customer Pays**: Customer completes payment on Paystack
4. **Webhook Notification**: Paystack sends webhook to your callback URL
5. **Payment Verified**: System verifies and updates payment status

## Webhook Configuration

1. In Paystack dashboard, go to **Settings > API Keys & Webhooks**
2. Add your webhook URL: `https://yourdomain.com/api/billing/webhooks/paystack/`
3. The webhook is automatically verified using your secret key

## Testing

Use Paystack test cards for testing:

### Successful Payment
- **Card Number**: 4084084084084081
- **CVV**: 408
- **Expiry**: Any future date
- **PIN**: 0000

### Declined Payment
- **Card Number**: 5060666666666666666
- **CVV**: 606
- **Expiry**: Any future date
- **PIN**: 0000

## Code Changes Made

1. Created `PaystackAdapter` class in `billing/adapters/paystack.py`
2. Updated `PaymentService` to use `PaystackAdapter` instead of `PesawayAdapter`
3. Updated environment variable names from `PESAWAY_*` to `PAYSTACK_*`
4. Payment provider changed from `'pesaway'` to `'paystack'` in database

## Migration Notes

- All new payments will use Paystack
- Existing Pesaway payments remain unchanged
- Update your environment variables before restarting the service



