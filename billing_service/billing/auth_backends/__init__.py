"""
Authentication backends for the billing service.
"""

from .remote_auth import RemoteAuthBackend

__all__ = ["RemoteAuthBackend"]
