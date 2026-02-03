"""
Seed database with subscription plans
Run with: python manage.py shell < seed_plans.py
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing_service.settings")
django.setup()

from decimal import Decimal

from billing.models import Plan

# Clear existing plans (optional)
# Plan.objects.all().delete()

# Create plans
plans_data = [
    {
        "name": "Starter",
        "tier": "starter",
        "description": "Perfect for small businesses just getting started",
        "price_monthly": Decimal("4999.00"),
        "price_quarterly": Decimal("14247.15"),  # 5% discount
        "price_yearly": Decimal("47990.40"),  # 20% discount
        "currency": "KES",
        "billing_period": "monthly",
        "included_users": 5,
        "additional_user_price": Decimal("500.00"),
        "max_users": 20,
        "is_active": True,
        "is_featured": False,
        "limits": {
            "invoices": 100,
            "customers": 200,
            "products": 500,
            "storage_gb": 10,
            "api_calls_per_day": 1000,
        },
        "features": [
            "Basic accounting features",
            "Invoice management",
            "Customer management",
            "Basic reports",
            "Email support",
        ],
    },
    {
        "name": "Professional",
        "tier": "professional",
        "description": "Ideal for growing businesses with advanced needs",
        "price_monthly": Decimal("9999.00"),
        "price_quarterly": Decimal("28497.15"),  # 5% discount
        "price_yearly": Decimal("95990.40"),  # 20% discount
        "currency": "KES",
        "billing_period": "monthly",
        "included_users": 15,
        "additional_user_price": Decimal("400.00"),
        "max_users": 50,
        "is_active": True,
        "is_featured": True,
        "limits": {
            "invoices": 500,
            "customers": 1000,
            "products": 2000,
            "storage_gb": 50,
            "api_calls_per_day": 5000,
        },
        "features": [
            "All Starter features",
            "Advanced reporting",
            "Multi-currency support",
            "Inventory management",
            "Purchase orders",
            "Priority email support",
            "API access",
        ],
    },
    {
        "name": "Business",
        "tier": "business",
        "description": "Comprehensive solution for established businesses",
        "price_monthly": Decimal("19999.00"),
        "price_quarterly": Decimal("56997.15"),  # 5% discount
        "price_yearly": Decimal("191990.40"),  # 20% discount
        "currency": "KES",
        "billing_period": "monthly",
        "included_users": 30,
        "additional_user_price": Decimal("350.00"),
        "max_users": 100,
        "is_active": True,
        "is_featured": False,
        "limits": {
            "invoices": -1,  # Unlimited
            "customers": -1,
            "products": -1,
            "storage_gb": 200,
            "api_calls_per_day": 20000,
        },
        "features": [
            "All Professional features",
            "Unlimited invoices & customers",
            "Advanced analytics",
            "Custom reports",
            "Multi-location support",
            "Role-based access control",
            "Priority phone support",
            "Dedicated account manager",
        ],
    },
    {
        "name": "Enterprise",
        "tier": "enterprise",
        "description": "Custom solution for large organizations",
        "price_monthly": Decimal("39999.00"),
        "price_quarterly": Decimal("113997.15"),  # 5% discount
        "price_yearly": Decimal("383990.40"),  # 20% discount
        "currency": "KES",
        "billing_period": "monthly",
        "included_users": 100,
        "additional_user_price": Decimal("300.00"),
        "max_users": -1,  # Unlimited
        "is_active": True,
        "is_featured": False,
        "limits": {
            "invoices": -1,
            "customers": -1,
            "products": -1,
            "storage_gb": -1,  # Unlimited
            "api_calls_per_day": -1,
        },
        "features": [
            "All Business features",
            "Unlimited everything",
            "Custom integrations",
            "White-label options",
            "SLA guarantee",
            "24/7 phone & chat support",
            "On-site training",
            "Custom development",
        ],
    },
]

for plan_data in plans_data:
    plan, created = Plan.objects.get_or_create(
        tier=plan_data["tier"], defaults=plan_data
    )
    if created:
        print(f"✅ Created plan: {plan.name}")
    else:
        # Update existing plan
        for key, value in plan_data.items():
            setattr(plan, key, value)
        plan.save()
        print(f"📝 Updated plan: {plan.name}")

print("\n🎉 Plans seeded successfully!")
print("\nCreated plans:")
for plan in Plan.objects.all().order_by("price_monthly"):
    print(
        f"  - {plan.name}: {plan.currency} {plan.price_monthly}/month ({plan.included_users} users)"
    )
