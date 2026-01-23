#!/usr/bin/env python3
"""
Test script to simulate browser login to billing admin.
This helps debug CSRF issues.
"""
import requests
from urllib.parse import urljoin

BASE_URL = "http://localhost:8002"
LOGIN_URL = urljoin(BASE_URL, "/admin/login/")

def test_login(username, password):
    """Test the login flow with CSRF token handling."""
    
    # Create a session to persist cookies
    session = requests.Session()
    
    print(f"[*] Testing login for user: {username}")
    print(f"[*] Base URL: {BASE_URL}")
    print()
    
    # Step 1: GET the login page to get CSRF token
    print("Step 1: Getting login page...")
    try:
        response = session.get(LOGIN_URL)
        print(f"   Status: {response.status_code}")
        print(f"   Cookies: {session.cookies.get_dict()}")
        
        # Extract CSRF token from cookies
        csrf_token = session.cookies.get('csrftoken')
        if csrf_token:
            print(f"   [OK] CSRF Token: {csrf_token[:20]}...")
        else:
            print(f"   [ERROR] No CSRF token in cookies!")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Error getting login page: {e}")
        return False
    
    print()
    
    # Step 2: POST login credentials with CSRF token
    print("Step 2: Submitting login form...")
    try:
        login_data = {
            'username': username,
            'password': password,
            'csrfmiddlewaretoken': csrf_token,
            'next': '/admin/',
        }
        
        headers = {
            'Referer': LOGIN_URL,
            'X-CSRFToken': csrf_token,
        }
        
        response = session.post(
            LOGIN_URL,
            data=login_data,
            headers=headers,
            allow_redirects=False
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            redirect_url = response.headers.get('Location', '')
            print(f"   [OK] Redirect to: {redirect_url}")
            
            if '/admin/' in redirect_url and '/login/' not in redirect_url:
                print(f"\n[SUCCESS] Login worked!")
                print(f"   Session cookies: {session.cookies.get_dict()}")
                return True
            else:
                print(f"\n[ERROR] Login failed - redirected to login page")
                return False
                
        elif response.status_code == 200:
            # Check if there's an error message
            if 'errorlist' in response.text or 'CSRF' in response.text:
                print(f"\n[ERROR] Login failed - CSRF error or invalid credentials")
                # Print part of response for debugging
                if 'CSRF' in response.text:
                    print("   CSRF error detected in response")
            else:
                print(f"\n[ERROR] Login failed - form returned with errors")
            return False
        else:
            print(f"\n[ERROR] Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error during login: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # Get credentials from command line or use defaults
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "Blackforest1"
    
    success = test_login(username, password)
    sys.exit(0 if success else 1)

