# QuidPath Billing Service

Billing microservice for QuidPath ERP with subscription management, payment processing, and promotions.

## Location
The billing service has been moved to `E:/billing` (separate from the ERP monolith).

## Quick Start

1. Install dependencies:
```bash
cd E:\billing
pip install -r requirements.txt
```

2. Set environment variables (create `.env` file):
```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://user:pass@localhost:5432/billing_db
PESAWAY_API_KEY=your-key
PESAWAY_SECRET_KEY=your-secret
PESAWAY_MERCHANT_ID=your-merchant-id
PESAWAY_TEST_MODE=true
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Start server:
```bash
python manage.py runserver 8002
```

## API Base URL
`http://localhost:8002/api/billing/`

## Features
- Subscription Plans (Starter, Professional, Business, Enterprise)
- 30-Day Free Trial
- Promotions & Discounts
- Payment Processing (Pesaway: M-Pesa, Cards, Bank Transfer)
- Invoice Management

See IMPLEMENTATION_SUMMARY.md for full documentation.








