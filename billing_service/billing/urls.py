"""
URL configuration for billing service
"""

from django.urls import path

from . import views
from . import views_payment_simple
from . import mpesa_webhook
from . import views_paystack_webhook
from . import views_individual_payment
from . import views_admin_fix

app_name = "billing"

urlpatterns = [
    # Access Control - CRITICAL
    path("access/check/", views.check_access, name="check_access"),
    
    # Paystack Webhook - MUST BE FIRST (no auth required)
    path("webhooks/paystack/", views_paystack_webhook.paystack_webhook, name="paystack_webhook"),
    
    # Individual Payment (new Paystack-based)
    path("payments/individual/initiate/", views_individual_payment.initiate_individual_payment, name="initiate_individual_payment"),
    path("payments/individual/verify/", views_individual_payment.verify_individual_payment, name="verify_individual_payment"),
    # Plans
    path("plans/", views.list_plans, name="list_plans"),
    # Payment Verification (KES 1 verification before trial)
    path(
        "verification/initiate/",
        views.initiate_verification,
        name="initiate_verification",
    ),
    path("verification/status/", views.verification_status, name="verification_status"),
    path(
        "verification/complete/",
        views.complete_verification,
        name="complete_verification",
    ),
    # Trials
    path("trials/create/", views.create_trial, name="create_trial"),
    path("trials/status/", views.get_trial_status, name="get_trial_status"),
    # Subscriptions
    path(
        "subscriptions/create/", views.create_subscription, name="create_subscription"
    ),
    path(
        "subscriptions/status/",
        views.get_subscription_status,
        name="get_subscription_status",
    ),
    # Promotions
    path("promotions/validate/", views.validate_promotion, name="validate_promotion"),
    # Invoices
    path("invoices/", views.list_invoices, name="list_invoices"),
    # Payments - NEW SIMPLIFIED ENDPOINT
    path("payments/initiate/", views_payment_simple.initiate_payment_simple, name="initiate_payment"),
    path("payments/status/", views.check_payment_status, name="check_payment_status"),
    path("payments/history/", views.payment_history, name="payment_history"),
    path("payments/webhook/", views.payment_webhook, name="payment_webhook"),
    
    # M-Pesa Webhook
    path("webhooks/mpesa/", mpesa_webhook.mpesa_callback, name="mpesa_callback"),
    
    # Admin endpoints
    path("admin/corporate-summary/", views.admin_get_corporate_summary, name="admin_corporate_summary"),
    path("admin/fix-invoice/", views_admin_fix.fix_invoice_status, name="fix_invoice_status"),
    path("admin/bulk-fix-invoices/", views_admin_fix.bulk_fix_invoices, name="bulk_fix_invoices"),
]
