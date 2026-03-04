"""
Management command to create test subscription plans (1 KES per month for testing)
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from billing_service.billing.models import Plan


class Command(BaseCommand):
    help = "Create test subscription plans (1 KES per month) for testing the payment system"

    def handle(self, *args, **options):
        self.stdout.write("Creating test subscription plans...")
        
        test_plans = [
            {
                "plan_type": "individual",
                "tier": "test_starter",
                "name": "Test Starter",
                "description": "Test plan for payment system testing - 1 KES per month",
                "price_monthly": Decimal("1.00"),
                "limits": {
                    "invoices": 5,
                    "transactions": 10,
                    "storage_gb": 1,
                    "support": "Email",
                    "note": "This is a test plan for development/testing only",
                },
                "included_users": 1,
                "max_users": 1,
            },
            {
                "plan_type": "individual",
                "tier": "test_professional",
                "name": "Test Professional",
                "description": "Test plan for payment system testing - 1 KES per month",
                "price_monthly": Decimal("1.00"),
                "limits": {
                    "invoices": 10,
                    "transactions": 20,
                    "storage_gb": 2,
                    "support": "Email & Chat",
                    "note": "This is a test plan for development/testing only",
                },
                "included_users": 2,
                "max_users": 2,
            },
            {
                "plan_type": "organization",
                "tier": "test_org_starter",
                "name": "Test Organization Starter",
                "description": "Test plan for organization payment testing - 1 KES per month",
                "price_monthly": Decimal("1.00"),
                "limits": {
                    "invoices": 10,
                    "transactions": 50,
                    "storage_gb": 5,
                    "support": "Email",
                    "note": "This is a test plan for development/testing only",
                },
                "included_users": 3,
                "max_users": 5,
            },
        ]
        
        for plan_data in test_plans:
            plan, created = Plan.objects.update_or_create(
                plan_type=plan_data["plan_type"],
                tier=plan_data["tier"],
                defaults={
                    "name": plan_data["name"],
                    "description": plan_data["description"],
                    "price_monthly": plan_data["price_monthly"],
                    "limits": plan_data["limits"],
                    "included_users": plan_data["included_users"],
                    "max_users": plan_data["max_users"],
                    "is_active": True,
                    "is_featured": False,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created test plan: {plan.name} ({plan.plan_type}) - KES {plan.price_monthly}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Updated test plan: {plan.name} ({plan.plan_type}) - KES {plan.price_monthly}")
                )
        
        self.stdout.write(self.style.SUCCESS("\nTest plans created successfully!"))
        self.stdout.write(self.style.WARNING("\nIMPORTANT: These are test plans with 1 KES pricing."))
        self.stdout.write(self.style.WARNING("Remember to deactivate or delete them before going to production!"))
