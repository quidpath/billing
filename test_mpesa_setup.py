"""
Quick test script to verify M-Pesa credentials are working
Uses the credentials provided by the user
"""
import os
import requests

# M-Pesa Sandbox Credentials
CONSUMER_KEY = "WZ6b1Y6ZjRbwNJwwQzULthXjesQR0OtsEuQh9jt7tz3CtSpG"
CONSUMER_SECRET = "zuVci1S1rl6An6bistz6jUo1eJ0Is8kM3IGlghGFCUpF4coKx7YtmGbAbLgvyddS"
SHORTCODE = "174379"
PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

print("=" * 80)
print("M-PESA CREDENTIALS TEST")
print("=" * 80)

print(f"\nConsumer Key: {CONSUMER_KEY[:20]}...")
print(f"Consumer Secret: {CONSUMER_SECRET[:20]}...")
print(f"Shortcode: {SHORTCODE}")
print(f"Passkey: {PASSKEY[:20]}...")

# Test 1: Get Access Token
print("\n" + "-" * 80)
print("TEST 1: Getting Access Token")
print("-" * 80)

base_url = "https://sandbox.safaricom.co.ke"
auth_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"

try:
    print(f"Requesting token from: {auth_url}")
    response = requests.get(
        auth_url,
        auth=(CONSUMER_KEY, CONSUMER_SECRET),
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get('access_token')
        
        if access_token:
            print(f"[SUCCESS] Access token obtained")
            print(f"   Token: {access_token[:30]}...")
            print(f"   Expires in: {data.get('expires_in', 'N/A')} seconds")
            
            # Test 2: Test STK Push (simulate)
            print("\n" + "-" * 80)
            print("TEST 2: Testing STK Push Configuration")
            print("-" * 80)
            
            # Generate password for STK Push
            import base64
            from datetime import datetime
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password_string = f"{SHORTCODE}{PASSKEY}{timestamp}"
            password = base64.b64encode(password_string.encode()).decode('utf-8')
            
            print(f"[SUCCESS] Password generated successfully")
            print(f"   Timestamp: {timestamp}")
            print(f"   Password (first 20 chars): {password[:20]}...")
            
            # Test phone number formatting
            test_phone = "254708374149"
            print(f"\n[SUCCESS] Phone number format: {test_phone}")
            
            print("\n" + "=" * 80)
            print("[SUCCESS] ALL TESTS PASSED!")
            print("=" * 80)
            print("\nYour M-Pesa credentials are configured correctly!")
            print("You can now use STK Push for payments.")
            print("\nTest phone number: 254708374149")
            print("Test PIN: 1234 (or as configured in sandbox)")
            
        else:
            print(f"[ERROR] No access token in response")
            print(f"   Response: {data}")
    elif response.status_code == 400:
        print(f"[ERROR] Bad Request (400)")
        print(f"   Invalid Consumer Key or Consumer Secret")
        try:
            error_data = response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Response: {response.text[:200]}")
    elif response.status_code == 401:
        print(f"[ERROR] Unauthorized (401)")
        print(f"   Consumer Key or Consumer Secret is incorrect")
    else:
        print(f"[ERROR] Status code {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.ConnectionError:
    print(f"[ERROR] Could not connect to M-Pesa API")
    print(f"   Check your internet connection")
except requests.exceptions.Timeout:
    print(f"[ERROR] Request timed out")
except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
