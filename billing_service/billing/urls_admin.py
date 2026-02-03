"""
Admin URL configuration for billing service
These endpoints are used by the main Quidpath backend admin panel
"""

from django.urls import path

from . import views

app_name = "billing_admin"

urlpatterns = [
    # Admin endpoints for Django admin panel integration
    path(
        "corporate/<str:corporate_id>/summary/",
        views.admin_corporate_summary,
        name="corporate_summary",
    ),
]
