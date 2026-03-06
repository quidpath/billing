# Billing Service

Independent billing microservice for QuidPath ERP.

## Quick Start

```bash
# Start the service
docker compose up -d

# Check logs
docker logs billing-backend

# Create superuser
docker exec billing-backend python manage.py createsuperuser

# Access admin
http://localhost:8002/admin/
```

## Environment Variables

See `.env` file and `.env.production.template` for configuration.

## Database

Uses its own PostgreSQL database (billing_prod).

## Deployment (Stage & Production)

Pushes to **Development** deploy to **stage** (docker-compose.stage.yml). Pushes to **master** deploy to **production** (docker-compose.yml). The repo does **not** ship a `.env` file; the deployment creates secrets (e.g. from GitHub Actions `env_secrets`) and runs compose with them. On the server, create a `.env` from the payload and run e.g. `docker compose --env-file .env up -d` so variables are injected at deploy time. The image never contains `.env` (see `.dockerignore`).

### GitHub Secrets for Billing (incl. M-Pesa)

Add these in the billing repo: **Settings → Secrets and variables → Actions**. Required for M-Pesa billing:

| Secret | Description | Used for |
|--------|-------------|----------|
| `MPESA_CONSUMER_KEY` | Daraja API consumer key | STK Push, callbacks |
| `MPESA_CONSUMER_SECRET` | Daraja API consumer secret | OAuth & STK Push |
| `MPESA_SHORTCODE` | Business short code (Paybill/Till) | Views, payment_service, verification_service |
| `MPESA_BUSINESS_SHORT_CODE` | Same as short code (or Paybill) | mpesa_service, settings |
| `MPESA_TILL_NUMBER` | Till number (CustomerBuyGoodsOnline) | mpesa_service (PartyB) |
| `MPESA_PASSKEY` | Daraja passkey | STK Push password generation |
| `MPESA_CALLBACK_URL` | **Production** M-Pesa callback URL | Where Safaricom POSTs STK result |
| `MPESA_CALLBACK_URL_STAGE` | **Stage** M-Pesa callback URL (optional) | Used when branch = Development |
| `MPESA_TEST_MODE` | `true` or `false` | Sandbox vs live |
| `MPESA_ENVIRONMENT` | `sandbox` or `production` | API base URL (sandbox.safaricom.co.ke vs api.safaricom.co.ke) |

**M-Pesa callback URL (webhook) to register:**

- **Production:** `https://<billing-host>/api/billing/webhooks/mpesa/`  
  Example: `https://billing.quidpath.com/api/billing/webhooks/mpesa/`
- **Stage:** Same path on your stage billing host, e.g. `https://billing-stage.quidpath.com/api/billing/webhooks/mpesa/`

Safaricom will send **POST** requests to this URL with the STK callback payload. The billing app accepts them at `webhooks/mpesa/` (no auth; validate using `CheckoutRequestID` and payment record).

**Tip:** You can set `MPESA_SHORTCODE` and `MPESA_BUSINESS_SHORT_CODE` to the same value if you use one Paybill. Set `MPESA_TILL_NUMBER` for Till-based STK (CustomerBuyGoodsOnline).

### Stage: Main backend ↔ Billing

For stage to work without "Unauthorized" or "Connection refused":

1. **BILLING_SERVICE_URL** – On the main backend (quidpath-backend), set this to the billing service URL. In Docker stage this is `http://billing-backend-stage:8000/api/billing` (container name from billing’s `docker-compose.stage.yml`, port 8000 inside the container; both stacks use network `stage_quidpath_network`).
2. **BILLING_SERVICE_SECRET** – You **create** this yourself; it is not issued by any service. Generate a random value once (e.g. `openssl rand -hex 32`), then set the **same** value on **both** the main backend and billing (server `.env` or GitHub Actions secrets). The main backend sends it as `X-Service-Key` for server-to-server calls (e.g. create subscription, admin corporate summary). Billing accepts it only on those paths.
3. **JWT_SECRET_KEY** – Set the **same** value on **both** the main backend and billing. User tokens are issued by the main backend; billing verifies them with this key. If they differ, frontend calls to `/api/billing/subscriptions/status/` and `/api/billing/payments/initiate/` return 401.
