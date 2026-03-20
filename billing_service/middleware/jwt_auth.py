"""
JWT Authentication Middleware for Billing Service
Validates JWT tokens and enriches request with user data.
Allows server-to-server calls with X-Service-Key for backend-only endpoints.
"""

import logging
import os

import jwt   
from django.conf import settings
from django.http import JsonResponse

from billing_service.services.user_cache_service import UserCacheService

logger = logging.getLogger(__name__)

# Paths the main backend calls without a user JWT (server-to-server)
SERVICE_TO_SERVICE_PATHS = [
    "/api/billing/subscriptions/create/",
    "/api/billing/trials/create/",
    "/api/billing/trials/status/",
    "/api/billing/access/check/",
    "/api/admin/billing/",  # admin corporate summary etc.
]


class JWTAuthenticationMiddleware:
    """Middleware to validate JWT tokens and attach user data to request"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_service = UserCacheService()

    def __call__(self, request):
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.path):
            return self.get_response(request)

        # Server-to-server: allow X-Service-Key if path is backend-only and secret matches
        service_secret = os.environ.get("BILLING_SERVICE_SECRET") or getattr(
            settings, "BILLING_SERVICE_SECRET", ""
        )
        if service_secret and self._is_service_to_service_path(request.path):
            key = request.META.get("HTTP_X_SERVICE_KEY", "").strip()
            if key and key == service_secret:
                request.service_call = True
                request.user_id = None
                request.corporate_id = None
                request.user_data = {}
                request.corporate_data = None
                return self.get_response(request)

        # Extract token from Authorization header
        auth_header = request.META.get("HTTP_AUTHORIZATION", "").strip()
        if not auth_header.startswith("Bearer "):
            has_any = bool(request.META.get("HTTP_AUTHORIZATION"))
            logger.warning(
                "Auth rejected for %s: header %s",
                request.path,
                "present but not Bearer" if has_any else "missing",
            )
            return JsonResponse(
                {"error": "Missing or invalid authorization header"}, status=401
            )

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return JsonResponse(
                {"error": "Missing or invalid authorization header"}, status=401
            )

        try:
            # Decode and validate token
            secret_key = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)

            payload = jwt.decode(
                token, secret_key, algorithms=["HS256"], issuer="quidpath-backend"
            )

            # Mark as user call (not service-to-service)
            request.service_call = False
            # Attach basic user data from token to request
            request.user_id = payload["user_id"]
            request.corporate_id = payload.get("corporate_id")
            request.user_data = {
                "id": payload["user_id"],
                "username": payload["username"],
                "email": payload["email"],
                "role": payload.get("role"),
                "is_staff": payload.get("is_staff", False),
            }

            # Enrich with cached/API data
            try:
                enriched_user_data = self.cache_service.get_user_data(
                    payload["user_id"]
                )
                if enriched_user_data:
                    request.user_data.update(enriched_user_data)

                if request.corporate_id:
                    request.corporate_data = self.cache_service.get_corporate_data(
                        request.corporate_id
                    )
                else:
                    request.corporate_data = None
            except Exception as e:
                logger.warning(f"Failed to enrich user data: {e}")
                # Continue with basic token data
                request.corporate_data = None

        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=401)
        except jwt.InvalidTokenError as e:
            return JsonResponse(
                {
                    "error": "Invalid token",
                    "detail": str(e),
                    "hint": "Ensure JWT_SECRET_KEY on this service matches the main backend (quidpath-backend).",
                },
                status=401,
            )
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return JsonResponse(
                {"error": f"Authentication failed: {str(e)}"}, status=500
            )

        return self.get_response(request)

    def _is_public_endpoint(self, path):
        """Check if endpoint is public (no authentication required)"""
        public_paths = [
            "/health/",
            "/api/docs/",
            "/admin/",
            "/static/",
            "/media/",
            "/api/billing/plans/",  # Allow public access to plans
            "/api/billing/webhooks/",  # Allow webhooks
        ]
        return any(path.startswith(p) for p in public_paths)

    def _is_service_to_service_path(self, path):
        """Check if path is allowed for X-Service-Key (backend-only)"""
        return any(path.startswith(p) for p in SERVICE_TO_SERVICE_PATHS)
