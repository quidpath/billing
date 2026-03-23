"""
Management command to create unified subscription plans for both individual and organization.
Run: python manage.py create_unified_plans
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from billing_service.billing.models import Plan


INDIVIDUAL_PLANS = [
    {
        "plan_type": "individual",
        "tier": "starter",
        "name": "Starter",
        "description": "Perfect for freelancers and solo entrepreneurs getting started.",
        "price_monthly": Decimal("999.00"),
        "limits": {
            "invoices": 50,
            "transactions": 100,
            "storage_gb": 5,
            "api_calls_per_day": 0,
            "support": "Email",
        },
        "included_users": 1,
        "max_users": 1,
        "features": {
            "invoicing": True,
            "expense_tracking": True,
            "basic_reports": True,
            "advanced_reports": False,
            "bank_reconciliation": False,
            "multi_currency": False,
            "api_access": False,
            "priority_support": False,
            "custom_logo": False,
            "dedicated_account_manager": False,
            "sla_guarantee": False,
        },
    },
    {
        "plan_type": "individual",
        "tier": "professional",
        "name": "Professional",
        "description": "For growing businesses that need more power and flexibility.",
        "price_monthly": Decimal("2499.00"),
        "limits": {
            "invoices": 500,
            "transactions": 1000,
            "storage_gb": 20,
            "api_calls_per_day": 0,
            "support": "Email & Chat",
        },
        "included_users": 1,
        "max_users": 3,
        "features": {
            "invoicing": True,
            "expense_tracking": True,
            "basic_reports": True,
            "advanced_reports": True,
            "bank_reconciliation": True,
            "multi_currency": True,
            "api_access": False,
            "priority_support": False,
            "custom_logo": False,
            "dedicated_account_manager": False,
            "sla_guarantee": False,
        },
    },
    {
        "plan_type": "individual",
        "tier": "business",
        "name": "Business",
        "description": "Full-featured accounting for established businesses.",
        "price_monthly": Decimal("4999.00"),
        "limits": {
            "invoices": 5000,
            "transactions": 10000,
            "storage_gb": 50,
            "api_calls_per_day": 5000,
            "support": "Priority",
        },
        "included_users": 1,
        "max_users": 10,
        "features": {
            "invoicing": True,
            "expense_tracking": True,
            "basic_reports": True,
            "advanced_reports": True,
            "bank_reconciliation": True,
            "multi_currency": True,
            "api_access": True,
            "priority_support": True,
            "custom_logo": True,
            "dedicated_account_manager": False,
            "sla_guarantee": False,
        },
    },
    {
        "plan_type": "individual",
        "tier": "enterprise",
        "name": "Enterprise",
        "description": "Unlimited access for large-scale operations.",
        "price_monthly": Decimal("9999.00"),
        "limits": {
            "invoices": -1,
            "transactions": -1,
            "storage_gb": -1,
            "api_calls_per_day": -1,
            "support": "24/7 Dedicated",
        },
        "included_users": 1,
        "max_users": -1,
        "features": {
            "invoicing": True,
            "expense_tracking": True,
            "basic_reports": True,
            "advanced_reports": True,
            "bank_reconciliation": True,
            "multi_currency": True,
            "api_access": True,
            "priority_support": True,
            "custom_logo": True,
            "dedicated_account_manager": True,
            "sla_guarantee": True,
        },
    },
    # ── Test plans (1 KES) ────────────────────────────────────────────────────
    {
        "plan_type": "individual",
        "tier": "test_limited",
        "name": "Test - Limited",
        "description": "1 KES test plan with restricted access. For API testing only.",
        "price_monthly": Decimal("1.00"),
        "limits": {
            "invoices": 5,
            "transactions": 10,
            "storage_gb": 1,
            "api_calls_per_day": 0,
            "support": "None",
        },
        "included_users": 1,
        "max_users": 1,
        "features": {
            "invoicing": True,
            "expense_tracking": False,
            "basic_reports": True,
            "advanced_reports": False,
            "bank_reconciliation": False,
            "multi_currency": False,
            "api_access": False,
            "priority_support": False,
            "custom_logo": False,
            "dedicated_account_manager": False,
            "sla_guarantee": False,
        },
    },
    {
        "plan_type": "individual",
        "tier": "test_full",
        "name": "Test - Full Access",
        "description": "1 KES test plan with full access to all features. For API testing only.",
        "price_monthly": Decimal("1.00"),
        "limits": {
            "invoices": -1,
            "transactions": -1,
            "storage_gb": -1,
            "api_calls_per_day": -1,
            "support": "24/7 Dedicated",
        },
        "included_users": 1,
        "max_users": -1,
        "features": {
            "invoicing": True,
            "expense_tracking": True,
            "basic_reports": True,
            "advanced_reports": True,
            "bank_reconciliation": True,
            "multi_currency": True,
            "api_access": True,
            "priority_support": True,
            "custom_logo": True,
            "dedicated_account_manager": True,
            "sla_guarantee": True,
        },
    },
]

ORGANIZATION_PLANS = [
    {
        "plan_type": "organization",
        "tier": "basic",
        "name": "Basic",
        "description": "Essential tools for small organisations just getting started.",
        "price_monthly": Decimal("4999.00"),
        "limits": {
            "storage_gb": 10,
            "api_calls_per_day": 0,
            "support": "Email",
        },
        "included_users": 5,
        "max_users": 5,
        "features": {
            "accounting": True,
            "invoicing": True,
            "inventory": False,
            "pos": False,
            "crm": False,
            "hrm": False,
            "projects": False,
            "reports": "basic",
            "api_access": False,
            "priority_support": False,
            "custom_logo": False,
            "dedicated_account_manager": False,
            "sla_guarantee": False,
            "on_premise_option": False,
        },
    },
    {
        "plan_type": "organization",
        "tier": "standard",
        "name": "Standard",
        "description": "For growing organisations that need more modules.",
        "price_monthly": Decimal("9999.00"),
        "limits": {
            "storage_gb": 50,
            "api_calls_per_day": 0,
            "support": "Email & Chat",
        },
        "included_users": 20,
        "max_users": 20,
        "features": {
            "accounting": True,
            "invoicing": True,
            "inventory": True,
            "pos": True,
            "crm": False,
            "hrm": False,
            "projects": False,
            "reports": "advanced",
            "api_access": False,
            "priority_support": False,
            "custom_logo": False,
            "dedicated_account_manager": False,
            "sla_guarantee": False,
            "on_premise_option": False,
        },
    },
    {
        "plan_type": "organization",
        "tier": "premium",
        "name": "Premium",
        "description": "Full ERP suite for established organisations.",
        "price_monthly": Decimal("19999.00"),
        "limits": {
            "storage_gb": 200,
            "api_calls_per_day": 20000,
            "support": "Priority",
        },
        "included_users": 100,
        "max_users": 100,
        "features": {
            "accounting": True,
            "invoicing": True,
            "inventory": True,
            "pos": True,
            "crm": True,
            "hrm": True,
            "projects": True,
            "reports": "advanced",
            "api_access": True,
            "priority_support": True,
            "custom_logo": True,
            "dedicated_account_manager": False,
            "sla_guarantee": False,
            "on_premise_option": False,
        },
    },
    {
        "plan_type": "organization",
        "tier": "enterprise",
        "name": "Enterprise",
        "description": "Unlimited users and full feature access with dedicated support.",
        "price_monthly": Decimal("49999.00"),
        "limits": {
            "storage_gb": -1,
            "api_calls_per_day": -1,
            "support": "24/7 Dedicated",
        },
        "included_users": -1,
        "max_users": -1,
        "features": {
            "accounting": True,
            "invoicing": True,
            "inventory": True,
            "pos": True,
            "crm": True,
            "hrm": True,
            "projects": True,
            "reports": "advanced",
            "api_access": True,
            "priority_support": True,
            "custom_logo": True,
            "dedicated_account_manager": True,
            "sla_guarantee": True,
            "on_premise_option": True,
        },
    },
    # ── Test plans (1 KES) ────────────────────────────────────────────────────
    {
        "plan_type": "organization",
        "tier": "test_limited",
        "name": "Test - Limited",
        "description": "1 KES test plan with restricted access. For API testing only.",
        "price_monthly": Decimal("1.00"),
        "limits": {
            "storage_gb": 1,
            "api_calls_per_day": 0,
            "support": "None",
        },
        "included_users": 2,
        "max_users": 2,
        "features": {
            "accounting": True,
            "invoicing": True,
            "inventory": False,
            "pos": False,
            "crm": False,
            "hrm": False,
            "projects": False,
            "reports": "basic",
            "api_access": False,
            "priority_support": False,
            "custom_logo": False,
            "dedicated_account_manager": False,
            "sla_guarantee": False,
            "on_premise_option": False,
        },
    },
    {
        "plan_type": "organization",
        "tier": "test_full",
        "name": "Test - Full Access",
        "description": "1 KES test plan with full access to all features. For API testing only.",
        "price_monthly": Decimal("1.00"),
        "limits": {
            "storage_gb": -1,
            "api_calls_per_day": -1,
            "support": "24/7 Dedicated",
        },
        "included_users": -1,
        "max_users": -1,
        "features": {
            "accounting": True,
            "invoicing": True,
            "inventory": True,
            "pos": True,
            "crm": True,
            "hrm": True,
            "projects": True,
            "reports": "advanced",
            "api_access": True,
            "priority_support": True,
            "custom_logo": True,
            "dedicated_account_manager": True,
            "sla_guarantee": True,
            "on_premise_option": True,
        },
    },
]


class Command(BaseCommand):
    help = "Create unified subscription plans for individual and organisation users"

    def handle(self, *args, **options):
        self.stdout.write("Creating unified subscription plans...")

        all_plans = INDIVIDUAL_PLANS + ORGANIZATION_PLANS
        created = updated = 0

        for plan_data in all_plans:
            features = plan_data.pop("features", {})
            limits = plan_data.get("limits", {})
            # Merge features into limits so they're stored together and queryable
            limits["features"] = features
            plan_data["limits"] = limits

            obj, was_created = Plan.objects.update_or_create(
                plan_type=plan_data["plan_type"],
                tier=plan_data["tier"],
                defaults={k: v for k, v in plan_data.items() if k not in ("plan_type", "tier")},
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {obj.name} ({obj.plan_type})"))
            else:
                updated += 1
                self.stdout.write(f"  Updated: {obj.name} ({obj.plan_type})")

        self.stdout.write(
            self.style.SUCCESS(f"\nDone — created: {created}, updated: {updated}")
        )
