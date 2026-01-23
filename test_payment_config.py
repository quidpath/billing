"""
Test script to verify payment gateway configurations
Run this to check if M-Pesa and Paystack are properly configured
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'billing_service.settings')
django.setup()

from billing_service.billing.adapters.mpesa_daraja import MpesaDarajaAdapter
from billing_service.billing.adapters.paystack import PaystackAdapter
from decimal import Decimal

print("=" * 80)
print("PAYMENT GATEWAY CONFIGURATION TEST")
print("=" * 80)

# Test M-Pesa Configuration
print("\n1. M-PESA CONFIGURATION")
print("-" * 80)

mpesa_config = {
    'consumer_key': os.environ.get('MPESA_CONSUMER_KEY', ''),
    'consumer_secret': os.environ.get('MPESA_CONSUMER_SECRET', ''),
    'business_short_code': os.environ.get('MPESA_SHORTCODE', '174379'),
    'passkey': os.environ.get('MPESA_PASSKEY', ''),
    'test_mode': os.environ.get('MPESA_TEST_MODE', 'true').lower() == 'true',
    'callback_url': os.environ.get('MPESA_CALLBACK_URL', ''),
}

print(f"Consumer Key: {'✅ Set' if mpesa_config['consumer_key'] else '❌ Missing'}")
print(f"Consumer Secret: {'✅ Set' if mpesa_config['consumer_secret'] else '❌ Missing'}")
print(f"Business Short Code: {mpesa_config['business_short_code']}")
print(f"Passkey: {'✅ Set' if mpesa_config['passkey'] else '❌ Missing'}")
print(f"Test Mode: {'✅ Enabled' if mpesa_config['test_mode'] else 'Disabled'}")
print(f"Callback URL: {mpesa_config['callback_url'] or '❌ Not Set'}")

mpesa_configured = all([
    mpesa_config['consumer_key'],
    mpesa_config['consumer_secret'],
    mpesa_config['passkey'],
])

if mpesa_configured:
    print("\n✅ M-Pesa is CONFIGURED")
    print("\nTesting M-Pesa access token...")
    try:
        adapter = MpesaDarajaAdapter(mpesa_config)
        token = adapter._get_access_token()
        print(f"✅ Access token obtained successfully!")
        print(f"   Token (first 20 chars): {token[:20]}...")
    except Exception as e:
        print(f"❌ Failed to get access token: {str(e)}")
else:
    print("\n❌ M-Pesa is NOT CONFIGURED")
    print("\nTo configure M-Pesa, set these environment variables:")
    print("  - MPESA_CONSUMER_KEY")
    print("  - MPESA_CONSUMER_SECRET")
    print("  - MPESA_PASSKEY")
    print("  - MPESA_CALLBACK_URL (recommended)")

# Test Paystack Configuration
print("\n\n2. PAYSTACK CONFIGURATION")
print("-" * 80)

paystack_config = {
    'public_key': os.environ.get('PAYSTACK_PUBLIC_KEY', ''),
    'secret_key': os.environ.get('PAYSTACK_SECRET_KEY', ''),
    'test_mode': os.environ.get('PAYSTACK_TEST_MODE', 'true').lower() == 'true',
    'callback_url': os.environ.get('PAYSTACK_CALLBACK_URL', ''),
}

print(f"Public Key: {'✅ Set' if paystack_config['public_key'] else '❌ Missing'}")
print(f"Secret Key: {'✅ Set' if paystack_config['secret_key'] else '❌ Missing'}")
print(f"Test Mode: {'✅ Enabled' if paystack_config['test_mode'] else 'Disabled'}")
print(f"Callback URL: {paystack_config['callback_url'] or '❌ Not Set'}")

paystack_configured = all([
    paystack_config['public_key'],
    paystack_config['secret_key'],
])

if paystack_configured:
    print("\n✅ Paystack is CONFIGURED")
    print("\nNote: Paystack requires actual initialization to fully test")
else:
    print("\n❌ Paystack is NOT CONFIGURED")
    print("\nTo configure Paystack, set these environment variables:")
    print("  - PAYSTACK_PUBLIC_KEY")
    print("  - PAYSTACK_SECRET_KEY")
    print("  - PAYSTACK_CALLBACK_URL (recommended)")

# Test phone number formatting
print("\n\n3. PHONE NUMBER FORMATTING TEST")
print("-" * 80)

if mpesa_configured:
    adapter = MpesaDarajaAdapter(mpesa_config)
    test_numbers = [
        '0712345678',
        '712345678',
        '254712345678',
        '+254712345678',
        '254 712 345 678',
    ]
    
    print("Testing phone number formatting:")
    for number in test_numbers:
        formatted = adapter._format_phone_number(number)
        print(f"  {number:20s} → {formatted}")
else:
    print("⚠️  M-Pesa not configured, skipping phone number test")

# Summary
print("\n\n" + "=" * 80)
print("CONFIGURATION SUMMARY")
print("=" * 80)

print(f"\nM-Pesa STK Push: {'✅ Ready' if mpesa_configured else '❌ Not Configured'}")
print(f"Paystack Card Payments: {'✅ Ready' if paystack_configured else '❌ Not Configured'}")

if not (mpesa_configured or paystack_configured):
    print("\n⚠️  WARNING: No payment gateways configured!")
    print("   Users will not be able to make payments.")
    print("\n   See E:\\MPESA_SETUP.md for M-Pesa configuration")
    print("   See Paystack documentation for card payment setup")

print("\n" + "=" * 80 + "\n")
