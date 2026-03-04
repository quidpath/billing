"""
Management command to seed initial subscription plans
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from billing_service.billing.models import Plan, PlanModule


class Command(BaseCommand):
    help = "Seed initial subscription plans"

    def handle(self, *args, **options):
        self.stdout.write("Creating subscription plans...")

        # Create Plans
        plans_data = [
            {
                "name": "Starter",
                "tier": "starter",
                "description": "Perfect for small businesses getting started",
                "price_monthly": Decimal("3500.00"),
                "price_quarterly": Decimal("9975.00"),  # 3 months with 5% discount
                "price_yearly": Decimal("33600.00"),  # 12 months with 20% discount
                "included_users": 3,
                "additional_user_price": Decimal("800.00"),
                "max_users": None,
                "limits": {
                    "invoices": 50,
                    "storage_gb": 5,
                    "api_calls": 1000,
                },
                "is_featured": False,
            },
            {
                "name": "Professional",
                "tier": "professional",
                "description": "For growing businesses with advanced needs",
                "price_monthly": Decimal("12000.00"),
                "price_quarterly": Decimal("34200.00"),
                "price_yearly": Decimal("115200.00"),
                "included_users": 10,
                "additional_user_price": Decimal("1200.00"),
                "max_users": None,
                "limits": {
                    "invoices": -1,  # unlimited
                    "storage_gb": 25,
                    "api_calls": 10000,
                },
                "is_featured": True,
            },
            {
                "name": "Business",
                "tier": "business",
                "description": "For established businesses with complex operations",
                "price_monthly": Decimal("35000.00"),
                "price_quarterly": Decimal("99750.00"),
                "price_yearly": Decimal("336000.00"),
                "included_users": 25,
                "additional_user_price": Decimal("1500.00"),
                "max_users": None,
                "limits": {
                    "invoices": -1,
                    "storage_gb": 100,
                    "api_calls": 50000,
                },
                "is_featured": False,
            },
            {
                "name": "Enterprise",
                "tier": "enterprise",
                "description": "For large enterprises with unlimited needs",
                "price_monthly": Decimal("100000.00"),
                "price_quarterly": Decimal("285000.00"),
                "price_yearly": Decimal("960000.00"),
                "included_users": -1,  # unlimited
                "additional_user_price": Decimal("2000.00"),
                "max_users": None,
                "limits": {
                    "invoices": -1,
                    "storage_gb": -1,
                    "api_calls": -1,
                },
                "is_featured": False,
            },
        ]

        for plan_data in plans_data:
            plan, created = Plan.objects.get_or_create(
                tier=plan_data["tier"], defaults=plan_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS("Created %s plan" % plan.name))
            else:
                self.stdout.write(
                    self.style.WARNING("%s plan already exists" % plan.name)
                )

        self.stdout.write(self.style.SUCCESS("\nPlans seeded successfully."))
