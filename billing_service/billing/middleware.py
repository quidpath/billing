"""
Middleware for billing service authentication and company tracing
"""

import json

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class BillingAuthMiddleware(MiddlewareMixin):
    """
    Middleware to verify corporate_id in requests and ensure security
    """

    def process_request(self, request):
        # Skip authentication for webhooks and public endpoints
        if request.path.startswith("/api/billing/payments/webhook/"):
            return None

        # For POST requests, extract corporate_id from body
        if request.method == "POST" and request.body:
            try:
                data = json.loads(request.body)
                corporate_id = data.get("corporate_id")

                # Store corporate_id in request for use in views
                request.billing_corporate_id = corporate_id

                # Verify corporate_id is provided for billing operations
                if not corporate_id and "/api/billing/" in request.path:
                    # Allow GET requests to plans without corporate_id
                    if request.path.endswith("/plans/") or request.path.endswith(
                        "/modules/"
                    ):
                        return None

                    # For other endpoints, require corporate_id
                    if (
                        "/trials/" in request.path
                        or "/subscriptions/" in request.path
                        or "/invoices/" in request.path
                    ):
                        return JsonResponse(
                            {
                                "success": False,
                                "message": "Corporate ID is required for security",
                                "error": "MISSING_CORPORATE_ID",
                            },
                            status=400,
                        )
            except json.JSONDecodeError:
                pass

        return None


class CompanyTracingMiddleware(MiddlewareMixin):
    """
    Middleware to ensure all billing operations are traced to companies
    """

    def process_response(self, request, response):
        # Add corporate_id to response headers for tracing (if available)
        if hasattr(request, "billing_corporate_id") and request.billing_corporate_id:
            response["X-Corporate-ID"] = str(request.billing_corporate_id)

        return response
