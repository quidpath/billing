"""
JWT Authentication Middleware for Billing Service
Validates JWT tokens and enriches request with user data
"""

import logging

import jwt
from django.conf import settings
from django.http import JsonResponse

from billing_service.services.user_cache_service import UserCacheService

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware:
    """Middleware to validate JWT tokens and attach user data to request"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_service = UserCacheService()

    def __call__(self, request):
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.path):
            return self.get_response(request)

        # Extract token from Authorization header
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Missing or invalid authorization header"}, status=401
            )

        token = auth_header.split(" ")[1]

        try:
            # Decode and validate token
            secret_key = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)

            payload = jwt.decode(
                token, secret_key, algorithms=["HS256"], issuer="quidpath-backend"
            )

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
            return JsonResponse({"error": f"Invalid token: {str(e)}"}, status=401)
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return JsonResponse(
                {"error": f"Authentication failed: {str(e)}"}, status=500
            )

        return self.get_response(request)

    def _is_public_endpoint(self, path):
        """Check if endpoint is public (no authentication required)"""
        public_paths = ["/health/", "/api/docs/", "/admin/", "/static/", "/media/"]
        return any(path.startswith(p) for p in public_paths)
