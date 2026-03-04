"""
Secure request parsing and standardized response for billing API.
Use get_clean_data for input; ResponseProvider for all JSON responses.
"""

import json
import logging
from typing import Any, Optional, Tuple

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def get_clean_data(
    request,
    allowed_methods=None,
    require_json_body=True,
    max_body_length=1024 * 1024,
):
    """
    Parse and validate request: method check and optional JSON body.
    Returns (data, response_or_none). If response_or_none is not None, return it from the view.
    data is dict from JSON body (or None if GET/no body); for GET, data can be request.GET params as dict.
    """
    if allowed_methods is None:
        allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
    if request.method not in allowed_methods:
        return None, ResponseProvider.method_not_allowed(allowed_methods)

    data = None
    if require_json_body and request.method in ("POST", "PUT", "PATCH") and request.body:
        if len(request.body) > max_body_length:
            return None, ResponseProvider.error("Request body too large", status=413)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning("Invalid JSON body: %s", e)
            return None, ResponseProvider.error("Invalid JSON body", status=400)
        if not isinstance(data, dict):
            return None, ResponseProvider.error("JSON body must be an object", status=400)
    elif request.method == "GET":
        data = dict(request.GET.items())

    return data, None


def ensure_method(request, *methods):
    """
    If request.method is not in methods, return a 405 JsonResponse; else return None.
    Use instead of @require_http_methods so all responses go through ResponseProvider.
    """
    if request.method not in methods:
        return ResponseProvider.method_not_allowed(list(methods))
    return None


class ResponseProvider:
    """Single place for API JSON responses."""

    @staticmethod
    def success(data=None, message=None, status=200):
        payload = {"success": True}
        if data is not None:
            payload["data"] = data
        if message is not None:
            payload["message"] = message
        return JsonResponse(payload, status=status)

    @staticmethod
    def error(message, status=400, data=None):
        payload = {"success": False, "message": message}
        if data is not None:
            payload["data"] = data
        return JsonResponse(payload, status=status)

    @staticmethod
    def method_not_allowed(allowed_methods):
        return JsonResponse(
            {"success": False, "message": "Method not allowed", "allowed": allowed_methods},
            status=405,
        )

    @staticmethod
    def raw(body: dict, status=200):
        """For webhooks that must return a specific shape (e.g. M-Pesa ResultCode)."""
        return JsonResponse(body, status=status)
