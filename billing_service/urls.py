"""
Main URL configuration for billing service
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/billing/", include("billing_service.billing.urls")),
    path("api/admin/billing/", include("billing_service.billing.urls_admin")),
]
