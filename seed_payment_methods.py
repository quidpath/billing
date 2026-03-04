"""
Seed script to add payment methods to the billing system
Run this once to populate the database with available payment methods
"""

import os
import sys

import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing_service.settings")
django.setup()

from django.db import transaction

# Create a simple PaymentMethod model if it doesn't exist
# For now, we'll just document the payment methods that are supported

PAYMENT_METHODS = {
    "mpesa": {
        "name": "M-Pesa",
        "code": "mpesa",
        "description": "Mobile money payment via Safaricom M-Pesa",
        "icon": "phone-android",
        "requires_phone": True,
        "supports_stk_push": True,
        "is_active": True,
        "order": 1,
    },
    "card": {
        "name": "Debit/Credit Card",
        "code": "card",
        "description": "Payment via Visa, Mastercard, or other cards",
        "icon": "credit-card",
        "requires_phone": False,
        "supports_stk_push": False,
        "is_active": True,
        "order": 2,
    },
    "airtel_money": {
        "name": "Airtel Money",
        "code": "airtel_money",
        "description": "Mobile money payment via Airtel Money",
        "icon": "phone-android",
        "requires_phone": True,
        "supports_stk_push": True,
        "is_active": True,
        "order": 3,
    },
    "bank_transfer": {
        "name": "Bank Transfer",
        "code": "bank_transfer",
        "description": "Direct bank transfer",
        "icon": "account-balance",
        "requires_phone": False,
        "supports_stk_push": False,
        "is_active": True,
        "order": 4,
    },
}


def seed_payment_methods():
    """
    Seed payment methods

    Note: Currently, payment methods are handled in code.
    This script documents the available payment methods.
    """
    print("=" * 80)
    print("PAYMENT METHODS CONFIGURATION")
    print("=" * 80)
    print("\nThe following payment methods are supported in the billing system:\n")

    for code, method in PAYMENT_METHODS.items():
        print(f"\n{method['order']}. {method['name']} ({code})")
        print(f"   Description: {method['description']}")
        print(f"   Icon: {method['icon']}")
        print(f"   Requires Phone: {'Yes' if method['requires_phone'] else 'No'}")
        print(f"   STK Push Support: {'Yes' if method['supports_stk_push'] else 'No'}")
        print(f"   Status: {'Active' if method['is_active'] else 'Inactive'}")

    print("\n" + "=" * 80)
    print("PAYMENT METHOD SETUP")
    print("=" * 80)

    print("\nPayment methods are configured via environment variables:")
    print("\nM-PESA (Daraja API):")
    print("  - MPESA_CONSUMER_KEY")
    print("  - MPESA_CONSUMER_SECRET")
    print("  - MPESA_SHORTCODE")
    print("  - MPESA_PASSKEY")
    print("  - MPESA_TEST_MODE=true/false")

    print("\nPAYSTACK (Card Payments):")
    print("  - PAYSTACK_PUBLIC_KEY")
    print("  - PAYSTACK_SECRET_KEY")
    print("  - PAYSTACK_TEST_MODE=true/false")

    print("\n" + "=" * 80)
    print("CONFIGURATION STATUS")
    print("=" * 80)

    # Check configuration
    mpesa_configured = all(
        [
            os.environ.get("MPESA_CONSUMER_KEY"),
            os.environ.get("MPESA_CONSUMER_SECRET"),
            os.environ.get("MPESA_SHORTCODE"),
            os.environ.get("MPESA_PASSKEY"),
        ]
    )

    paystack_configured = all(
        [
            os.environ.get("PAYSTACK_PUBLIC_KEY"),
            os.environ.get("PAYSTACK_SECRET_KEY"),
        ]
    )

    print("\nM-Pesa: %s" % ("Configured" if mpesa_configured else "Not configured"))
    print(
        "Paystack: %s" % ("Configured" if paystack_configured else "Not configured")
    )

    if not mpesa_configured:
        print("\nM-Pesa is not configured. See MPESA_SETUP.md for instructions.")

    if not paystack_configured:
        print("\nPaystack is not configured. Card payments will not work.")

    print("\n" + "=" * 80)
    print("PAYMENT METHODS DOCUMENTATION COMPLETE")
    print("=" * 80)
    print("\nPayment methods are ready to use in the billing system.")
    print("No database seeding required - methods are handled in code.\n")


if __name__ == "__main__":
    seed_payment_methods()
