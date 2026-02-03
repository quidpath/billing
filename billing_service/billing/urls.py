"""
URL configuration for billing service
"""

from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    # Access Control - CRITICAL
    path("access/check/", views.check_access, name="check_access"),
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
    # Payments
    path("payments/initiate/", views.initiate_payment, name="initiate_payment"),
    path("payments/status/", views.check_payment_status, name="check_payment_status"),
    path("payments/history/", views.payment_history, name="payment_history"),
    path("payments/webhook/", views.payment_webhook, name="payment_webhook"),
    path("payments/webhook/mpesa/", views.mpesa_webhook, name="mpesa_webhook"),
]
