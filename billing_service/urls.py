"""
Main URL configuration for billing service
"""

from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", lambda request: JsonResponse({"status": "ok"})),
    path("api/billing/", include("billing_service.billing.urls")),
    path("api/admin/billing/", include("billing_service.billing.urls_admin")),
]
