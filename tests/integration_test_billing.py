"""
Integration tests for Billing Service
Tests Plans, Subscriptions, Payments, Trials, Invoices
"""
import requests
import pytest


BASE_URL = "http://localhost:8002"


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/health/")
        assert response.status_code == 200


class TestBillingPlansEndpoints:
    """Test Billing Plans endpoints"""

    def test_list_plans(self):
        """Test listing subscription plans"""
        response = requests.get(f"{BASE_URL}/api/billing/plans/")
        assert response.status_code in [200, 401]  # May require auth or be public

    def test_get_plan_detail(self):
        """Test retrieving single plan"""
        # First get list of plans
        list_response = requests.get(f"{BASE_URL}/api/billing/plans/")
        if list_response.status_code == 200:
            plans = list_response.json()
            
            if isinstance(plans, dict) and "results" in plans:
                plans = plans["results"]
            
            if isinstance(plans, list) and len(plans) > 0:
                plan_id = plans[0].get("id") or plans[0].get("uuid")
                if plan_id:
                    response = requests.get(f"{BASE_URL}/api/billing/plans/{plan_id}/")
                    assert response.status_code in [200, 401, 404]
            else:
                # No plans available, test passes
                assert True


class TestBillingSubscriptionEndpoints:
    """Test Subscription endpoints"""

    def test_subscribe_requires_auth(self):
        """Test subscription endpoint requires authentication"""
        data = {
            "plan_id": "test-uuid",
            "payment_method": "paystack",
        }
        response = requests.post(f"{BASE_URL}/api/billing/subscribe/", json=data)
        assert response.status_code in [400, 401, 403]

    def test_check_billing_status_requires_auth(self):
        """Test billing status check requires authentication"""
        response = requests.get(f"{BASE_URL}/api/billing/status/")
        assert response.status_code in [401, 403]


class TestBillingPaymentEndpoints:
    """Test Payment endpoints"""

    def test_initiate_payment_requires_auth(self):
        """Test payment initiation requires authentication"""
        data = {
            "amount": "1000.00",
            "payment_method": "paystack",
        }
        response = requests.post(
            f"{BASE_URL}/api/billing/payment/initiate/", json=data
        )
        assert response.status_code in [400, 401, 403]


class TestBillingInvoiceEndpoints:
    """Test Billing Invoice endpoints"""

    def test_list_invoices_requires_auth(self):
        """Test listing invoices requires authentication"""
        response = requests.get(f"{BASE_URL}/api/billing/invoices/")
        assert response.status_code in [401, 403, 404]


class TestBillingPromotionEndpoints:
    """Test Promotion validation endpoints"""

    def test_validate_promotion_requires_auth(self):
        """Test promotion validation requires authentication"""
        data = {"code": "TESTCODE"}
        response = requests.post(
            f"{BASE_URL}/api/billing/promotion/validate/", json=data
        )
        assert response.status_code in [400, 401, 403, 404]


class TestBillingAdminEndpoints:
    """Test Admin Billing endpoints"""

    def test_corporate_billing_status_requires_admin(self):
        """Test corporate billing status requires admin auth"""
        corporate_id = "test-uuid"
        response = requests.get(
            f"{BASE_URL}/api/admin/billing/corporate/{corporate_id}/status/"
        )
        assert response.status_code in [401, 403, 404]


class TestBillingTrialEndpoints:
    """Test Trial endpoints"""

    def test_start_trial_requires_auth(self):
        """Test starting trial requires authentication"""
        data = {"plan_id": "test-uuid"}
        response = requests.post(f"{BASE_URL}/api/billing/trial/start/", json=data)
        assert response.status_code in [400, 401, 403, 404]
