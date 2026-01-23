"""
Quick test script for the admin billing endpoint
Run this to verify the admin endpoint is working correctly
"""
import requests
import json
import sys

def test_admin_endpoint(corporate_id):
    """Test the admin billing summary endpoint"""
    url = f"http://localhost:8002/api/admin/billing/corporate/{corporate_id}/summary/"
    
    print(f"\n{'='*80}")
    print(f"Testing Admin Billing Endpoint")
    print(f"{'='*80}")
    print(f"\nURL: {url}")
    print(f"Corporate ID: {corporate_id}\n")
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"\n{'='*80}")
        print("Response:")
        print(f"{'='*80}\n")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            
            # Check for currency field
            if data.get('success'):
                subscription = data.get('data', {}).get('subscription')
                if subscription:
                    if 'currency' in subscription:
                        print(f"\n✅ SUCCESS: Currency field found - {subscription['currency']}")
                    else:
                        print(f"\n❌ ERROR: Currency field missing from subscription data")
                else:
                    print(f"\n⚠️  NOTE: No active subscription (this is OK if corporate has only trial)")
                
                trial = data.get('data', {}).get('trial')
                if trial:
                    print(f"✅ Trial found: {trial['status']} - {trial['days_remaining']} days remaining")
                
                totals = data.get('data', {}).get('totals', {})
                print(f"\n💰 Financial Summary:")
                print(f"   - Total Invoiced: KES {totals.get('invoiced', 0):,.2f}")
                print(f"   - Total Paid: KES {totals.get('paid', 0):,.2f}")
                print(f"   - Outstanding: KES {totals.get('outstanding', 0):,.2f}")
                
            else:
                print(f"\n❌ ERROR: {data.get('message', 'Unknown error')}")
        else:
            print(response.text)
            print(f"\n❌ ERROR: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Could not connect to billing service")
        print(f"\nMake sure the billing service is running:")
        print(f"  cd E:\\billing")
        print(f"  python manage.py runserver 8002")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python test_admin_endpoint.py <corporate_id>")
        print("\nExample:")
        print("  python test_admin_endpoint.py 15024ee3-e4bb-48cc-91ea-9cacad85ecb4")
        sys.exit(1)
    
    corporate_id = sys.argv[1]
    test_admin_endpoint(corporate_id)
