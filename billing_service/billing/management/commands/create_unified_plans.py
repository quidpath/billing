"""
Management command to create unified subscription plans for both individual and organization
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from billing_service.billing.models import Plan


class Command(BaseCommand):
    help = "Create unified subscription plans for individual and organization users"

    def handle(self, *args, **options):
        self.stdout.write("Creating unified subscription plans...")
        
        individual_plans = [
            {
                "plan_type": "individual",
                "tier": "starter",
                "name": "Starter",
                "description": "Perfect for freelancers and solo entrepreneurs",
                "price_monthly": Decimal("1500.00"),
                "limits": {
                    "invoices": 50,
                    "transactions": 100,
                    "storage_gb": 5,
                    "support": "Email",
                },
                "included_users": 1,
                "max_users": 1,
            },
            {
                "plan_type": "individual",
                "tier": "professional",
                "name": "Professional",
                "description": "For growing businesses and small teams",
                "price_monthly": Decimal("3500.00"),
                "limits": {
                    "invoices": 200,
                    "transactions": 500,
                    "storage_gb": 20,
                    "support": "Email & Chat",
                },
                "included_users": 3,
                "max_users": 3,
            },
            {
                "plan_type": "individual",
                "tier": "business",
                "name": "Business",
                "description": "For established businesses with multiple users",
                "price_monthly": Decimal("7500.00"),
                "limits": {
                    "invoices": 1000,
                    "transactions": 2000,
                    "storage_gb": 50,
                    "support": "Priority Support",
                },
                "included_users": 10,
                "max_users": 10,
            },
            {
                "plan_type": "individual",
                "tier": "enterprise",
                "name": "Enterprise",
                "description": "For large organizations with unlimited needs",
                "price_monthly": Decimal("15000.00"),
                "limits": {
                    "invoices": "Unlimited",
                    "transactions": "Unlimited",
                    "storage_gb": "Unlimited",
                    "support": "24/7 Dedicated Support",
                },
                "included_users": 999999,
                "max_users": 999999,
            },
        ]
        
        for plan_data in individual_plans:
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
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created plan: {plan.name} ({plan.plan_type})")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Updated plan: {plan.name} ({plan.plan_type})")
                )
        
        self.stdout.write(self.style.SUCCESS("Unified plans created successfully!"))
