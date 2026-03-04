# Single set of live M-Pesa & Pesaway for Stage and Prod

Stage and prod use the **same live** M-Pesa and Pesaway credentials. Only the **callback / webhook URLs** differ (stage → stage-billing host, prod → billing host). No `_STAGE` payment secrets are needed.

---

## Is it viable?

**Yes.** Using one set of live values for both environments is viable when:

- You want stage to hit the same live M-Pesa/Pesaway account and shortcode (e.g. 9895960).
- You accept that payments triggered from stage are real (same merchant/shortcode); you control risk by who has access to stage.
- You keep **different callback URLs** so Safaricom/Pesaway send webhooks to the correct host (stage vs prod). The workflow sets these by environment; you don’t need separate payment keys.

**What must differ by environment**

- `MPESA_CALLBACK_URL` — stage: `https://stage-billing.quidpath.com/api/billing/webhooks/mpesa/`, prod: `https://billing.quidpath.com/api/billing/webhooks/mpesa/`
- `PESAWAY_WEBHOOK_URL` — stage: `https://stage-billing.quidpath.com/api/billing/webhooks/pesaway/`, prod: `https://billing.quidpath.com/api/billing/webhooks/pesaway/`

The deploy workflow sets these automatically; you only configure **one set** of payment secrets below.

---

## 1. GitHub Actions secrets (one set, no _STAGE for payments)

In the **billing** repo: **Settings → Secrets and variables → Actions**. Add these (replace placeholder values with your live ones):

**Pesaway (live)**

```
PESAWAY_API_KEY          = <your_live_pesaway_api_key>
PESAWAY_SECRET_KEY       = <your_live_pesaway_secret_key>
PESAWAY_MERCHANT_ID      = <your_live_pesaway_merchant_id>
PESAWAY_WEBHOOK_SECRET   = <your_live_webhook_secret>
PESAWAY_TEST_MODE        = false
PESAWAY_WEBHOOK_URL      = https://billing.quidpath.com/api/billing/webhooks/pesaway/
```

**M-Pesa (live)**

```
MPESA_CONSUMER_KEY             = WZ6b1Y6ZjRbwNJwwQzULthXjesQR0OtsEuQh9jt7tz3CtSpG
MPESA_CONSUMER_SECRET          = zuVci1S1rl6An6bistz6jUo1eJ0Is8kM3IGlghGFCUpF4coKx7YtmGbAbLgvyddS
MPESA_SHORTCODE                 = 9895960
MPESA_BUSINESS_SHORT_CODE      = 9895960
MPESA_TILL_NUMBER               = 9100097
MPESA_PASSKEY                  = bfb279f9aa9bdbcf158e97dd71a467cd
MPESA_CALLBACK_URL             = https://billing.quidpath.com/api/billing/webhooks/mpesa/
MPESA_TEST_MODE                = false
MPESA_ENVIRONMENT              = production
```

You do **not** need any `MPESA_*_STAGE` or `PESAWAY_*_STAGE` secrets for payments. The workflow uses the same values for stage and prod and overrides only the two URLs for stage.

---

## 2. Copy-paste for .env (production / local prod)

Use this block for **production** (e.g. `.env` on the server or local prod). Same live values; prod callback/webhook URLs:

```env
# PESAWAY (live) – same for stage and prod
PESAWAY_API_KEY=your_production_pesaway_api_key
PESAWAY_SECRET_KEY=your_production_pesaway_secret_key
PESAWAY_MERCHANT_ID=your_production_pesaway_merchant_id
PESAWAY_TEST_MODE=false
PESAWAY_WEBHOOK_URL=https://billing.quidpath.com/api/billing/webhooks/pesaway/
PESAWAY_WEBHOOK_SECRET=your_production_webhook_secret

# M-PESA (live) – same for stage and prod
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY=WZ6b1Y6ZjRbwNJwwQzULthXjesQR0OtsEuQh9jt7tz3CtSpG
MPESA_CONSUMER_SECRET=zuVci1S1rl6An6bistz6jUo1eJ0Is8kM3IGlghGFCUpF4coKx7YtmGbAbLgvyddS
MPESA_SHORTCODE=9895960
MPESA_BUSINESS_SHORT_CODE=9895960
MPESA_TILL_NUMBER=9100097
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd
MPESA_CALLBACK_URL=https://billing.quidpath.com/api/billing/webhooks/mpesa/
MPESA_TEST_MODE=false
```

---

## 3. Copy-paste for .env.stage (staging)

Same live M-Pesa and Pesaway values as prod. **Only** these two lines differ (stage host):

```env
# PESAWAY (live) – same keys as prod; only URL is stage
PESAWAY_API_KEY=your_production_pesaway_api_key
PESAWAY_SECRET_KEY=your_production_pesaway_secret_key
PESAWAY_MERCHANT_ID=your_production_pesaway_merchant_id
PESAWAY_TEST_MODE=false
PESAWAY_WEBHOOK_URL=https://stage-billing.quidpath.com/api/billing/webhooks/pesaway/
PESAWAY_WEBHOOK_SECRET=your_production_webhook_secret

# M-PESA (live) – same keys as prod; only URL is stage
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY=WZ6b1Y6ZjRbwNJwwQzULthXjesQR0OtsEuQh9jt7tz3CtSpG
MPESA_CONSUMER_SECRET=zuVci1S1rl6An6bistz6jUo1eJ0Is8kM3IGlghGFCUpF4coKx7YtmGbAbLgvyddS
MPESA_SHORTCODE=9895960
MPESA_BUSINESS_SHORT_CODE=9895960
MPESA_TILL_NUMBER=9100097
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd
MPESA_CALLBACK_URL=https://stage-billing.quidpath.com/api/billing/webhooks/mpesa/
MPESA_TEST_MODE=false
```

Replace `your_production_*` with your actual live Pesaway values when you have them.
