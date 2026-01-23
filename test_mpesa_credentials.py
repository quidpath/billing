"""
Test M-Pesa credentials to verify they are valid
Run this script to check if your M-Pesa credentials work
"""
import os
import sys
import django
import requests

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'billing_service.settings')
django.setup()

print("=" * 80)
print("M-PESA CREDENTIALS TEST")
print("=" * 80)

# Get credentials from environment
consumer_key = os.environ.get('MPESA_CONSUMER_KEY', '')
consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET', '')
shortcode = os.environ.get('MPESA_SHORTCODE', '174379')
passkey = os.environ.get('MPESA_PASSKEY', '')
test_mode = os.environ.get('MPESA_TEST_MODE', 'true').lower() == 'true'

print("\n1. CHECKING CONFIGURATION")
print("-" * 80)
print(f"Consumer Key: {'✅ Set' if consumer_key else '❌ Missing'} ({'*' * min(len(consumer_key), 10) if consumer_key else 'N/A'}...)")
print(f"Consumer Secret: {'✅ Set' if consumer_secret else '❌ Missing'} ({'*' * min(len(consumer_secret), 10) if consumer_secret else 'N/A'}...)")
print(f"Business Short Code: {shortcode}")
print(f"Passkey: {'✅ Set' if passkey else '❌ Missing'} ({'*' * min(len(passkey), 10) if passkey else 'N/A'}...)")
print(f"Test Mode: {'✅ Enabled' if test_mode else '❌ Disabled'}")

if not all([consumer_key, consumer_secret, passkey]):
    print("\n❌ ERROR: Missing required credentials!")
    print("\nPlease set these environment variables:")
    print("  - MPESA_CONSUMER_KEY")
    print("  - MPESA_CONSUMER_SECRET")
    print("  - MPESA_PASSKEY")
    sys.exit(1)

# Determine base URL
base_url = 'https://sandbox.safaricom.co.ke' if test_mode else 'https://api.safaricom.co.ke'

print("\n2. TESTING ACCESS TOKEN GENERATION")
print("-" * 80)
print(f"Base URL: {base_url}")

auth_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"

try:
    print(f"\nRequesting access token from: {auth_url}")
    response = requests.get(
        auth_url,
        auth=(consumer_key, consumer_secret),
        timeout=30
    )
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access_token')
        
        if access_token:
            print(f"✅ SUCCESS! Access token obtained")
            print(f"   Token (first 20 chars): {access_token[:20]}...")
            print(f"   Expires in: {data.get('expires_in', 'N/A')} seconds")
        else:
            print(f"❌ ERROR: No access token in response")
            print(f"   Response: {data}")
    elif response.status_code == 400:
        print(f"❌ ERROR: Bad Request (400)")
        print(f"   This usually means invalid Consumer Key or Consumer Secret")
        try:
            error_data = response.json()
            print(f"   Error details: {error_data}")
        except:
            print(f"   Response text: {response.text[:200]}")
        print("\n💡 TIP: Verify your credentials at https://developer.safaricom.co.ke/")
    elif response.status_code == 401:
        print(f"❌ ERROR: Unauthorized (401)")
        print(f"   This means your Consumer Key or Consumer Secret is incorrect")
        print("\n💡 TIP: Check your credentials in the M-Pesa Developer Portal")
    else:
        print(f"❌ ERROR: Unexpected status code {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.ConnectionError:
    print(f"❌ ERROR: Could not connect to M-Pesa API")
    print(f"   Check your internet connection")
except requests.exceptions.Timeout:
    print(f"❌ ERROR: Request timed out")
    print(f"   M-Pesa API may be slow or unavailable")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
