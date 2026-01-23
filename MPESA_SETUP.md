# M-Pesa Daraja API Setup Guide

This guide explains how to set up M-Pesa STK Push integration for the billing service.

## Prerequisites

1. A Safaricom M-Pesa Till or Paybill number
2. Access to Safaricom Daraja API Portal: https://developer.safaricom.co.ke/

## Step 1: Create a Daraja Account

1. Visit https://developer.safaricom.co.ke/
2. Click "Sign Up" and create an account
3. Verify your email address
4. Log in to the Daraja Portal

## Step 2: Create an App

1. Go to "My Apps" section
2. Click "Create New App"
3. Select "Lipa Na M-Pesa Online" product
4. Fill in app details:
   - App Name: Quidpath Billing
   - Description: Subscription billing and payments
5. Click "Create App"

## Step 3: Get Your Credentials

### Sandbox Credentials (for Testing)

1. In your app dashboard, click on "Keys" tab
2. Copy the following credentials:
   - **Consumer Key**: Used for OAuth authentication
   - **Consumer Secret**: Used for OAuth authentication

3. For Sandbox, use these default values:
   ```
   Business Short Code: 174379
   Passkey: bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
   Test Phone Number: 254708374149
   ```

### Production Credentials (for Live)

1. Switch to "Production" tab in your app
2. Complete Go-Live process (requires business verification)
3. Get production credentials:
   - Consumer Key (production)
   - Consumer Secret (production)
   - Your actual Paybill/Till number
   - Your passkey (provided by Safaricom)

## Step 4: Configure Environment Variables

Add these to your `.env` file:

```bash
# M-Pesa Sandbox (Testing)
MPESA_TEST_MODE=true
MPESA_CONSUMER_KEY=your_sandbox_consumer_key_here
MPESA_CONSUMER_SECRET=your_sandbox_consumer_secret_here
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_CALLBACK_URL=http://your-domain.com/api/billing/payments/webhook/mpesa/
```

## Step 5: Set Up Callback URL

### For Local Testing (using ngrok)

1. Install ngrok: https://ngrok.com/download
2. Run ngrok to expose your local server:
   ```bash
   ngrok http 8000
   ```
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
4. Set callback URL:
   ```
   MPESA_CALLBACK_URL=https://abc123.ngrok.io/api/billing/payments/webhook/mpesa/
   ```

### For Production

1. Use your actual domain with HTTPS:
   ```
   MPESA_CALLBACK_URL=https://api.yourdomain.com/api/billing/payments/webhook/mpesa/
   ```

## Step 6: Testing STK Push

### Test Phone Numbers (Sandbox Only)

Use any of these test phone numbers:
- 254708374149
- 254708374150
- 254708374151

### Test Flow

1. Initiate a payment from your frontend
2. Enter a test phone number (e.g., 254708374149)
3. A simulated STK push prompt will appear
4. In sandbox, the payment is auto-completed after a few seconds
5. Your callback URL receives the payment confirmation

### Test Cases

**Successful Payment:**
- Phone: 254708374149
- Amount: Any amount
- Expected: Payment completes successfully

**Cancelled Payment:**
- Simulate by not responding to STK prompt
- Expected: Payment times out after ~60 seconds

**Insufficient Balance:**
- In production, this happens if M-Pesa balance is low
- In sandbox, you can't simulate this

## Step 7: Go Live Checklist

Before switching to production:

1. ✅ Complete Safaricom business verification
2. ✅ Get production credentials from Daraja
3. ✅ Update environment variables with production values
4. ✅ Set `MPESA_TEST_MODE=false`
5. ✅ Update callback URL to production domain (HTTPS required)
6. ✅ Test with small real transactions first
7. ✅ Monitor callback logs for any issues
8. ✅ Set up proper error monitoring and alerts

## Troubleshooting

### "Invalid Access Token"
- Check that consumer key and secret are correct
- Ensure you're using sandbox/production credentials consistently

### "Invalid Phone Number"
- Phone must be in format: 254XXXXXXXXX
- Remove any spaces, dashes, or +
- Must be a valid Kenyan number (254)

### "Callback Not Received"
- Check that callback URL is accessible from internet
- Use ngrok for local testing
- Ensure HTTPS for production
- Check firewall/security groups

### "Transaction Failed"
- In production: Check M-Pesa account has sufficient float
- Check transaction limits
- Verify business short code is active

## API Endpoints

### Initiate Payment
```
POST /api/billing/payments/initiate/
Body:
{
  "invoice_id": "uuid",
  "payment_method": "mpesa",
  "customer_email": "user@example.com",
  "customer_phone": "254708374149",
  "corporate_id": "uuid"
}
```

### M-Pesa Callback
```
POST /api/billing/payments/webhook/mpesa/
(Automatically called by Safaricom)
```

## Transaction Limits

### Sandbox
- No actual money is transferred
- Unlimited test transactions
- All amounts work

### Production
- Minimum: KES 10
- Maximum: KES 150,000 per transaction
- Daily limits apply per customer

## Support

- Safaricom Support: https://developer.safaricom.co.ke/support
- Daraja Slack: https://safaricom-developers.slack.com
- Email: apisupport@safaricom.co.ke
- Phone: +254 711 082 495

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use HTTPS** for all production callbacks
3. **Verify callback signatures** (implement IP whitelist)
4. **Log all transactions** for audit trail
5. **Monitor for fraud** patterns
6. **Rate limit** payment requests
7. **Implement retries** for failed callbacks
8. **Use environment variables** for all config

## Currency Support

M-Pesa Daraja API supports:
- **KES** (Kenyan Shilling) - Primary currency
- All amounts are in KES
- No decimal places (amounts are integers)

## Sample Response Codes

| Code | Description | Action |
|------|-------------|--------|
| 0 | Success | Payment completed |
| 1 | Insufficient Balance | Ask user to top up |
| 1032 | Cancelled by user | User cancelled STK push |
| 1037 | Timeout | STK push expired |
| 2001 | Invalid phone | Validate phone format |

## Additional Resources

- Official Documentation: https://developer.safaricom.co.ke/docs
- Sample Code: https://github.com/safaricom/mpesa-php-sdk
- Postman Collection: Available on Daraja portal
- Community Forum: https://safaricom-developers.slack.com
