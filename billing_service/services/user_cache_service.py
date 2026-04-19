"""
User Cache Service for Billing Service
Handles caching and fetching of user/corporate data from main backend
"""

import json
import logging
from typing import Dict, Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class UserCacheService:
    """Service for caching and fetching user/corporate data"""

    def __init__(self):
        self.user_ttl = getattr(settings, "USER_CACHE_TTL", 3600)  # 1 hour
        self.corporate_ttl = getattr(settings, "CORPORATE_CACHE_TTL", 86400)  # 24 hours
        self.backend_url = getattr(settings, "ERP_BACKEND_URL", "http://localhost:8000")
        self.service_key = getattr(settings, "BILLING_SERVICE_SECRET", "")

    def get_user_data(self, user_id: str) -> Dict:
        """Get user data from cache or API"""
        cache_key = f"user:{user_id}"

        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for user {user_id}")
            return cached_data

        # Fetch from API
        logger.debug(f"Cache miss for user {user_id}, fetching from API")
        user_data = self._fetch_user_from_api(user_id)
        if user_data:
            # Cache the result
            cache.set(cache_key, user_data, self.user_ttl)

        return user_data or {}

    def get_corporate_data(self, corporate_id: str) -> Dict:
        """Get corporate data from cache or API"""
        cache_key = f"corporate:{corporate_id}"

        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for corporate {corporate_id}")
            return cached_data

        # Fetch from API
        logger.debug(f"Cache miss for corporate {corporate_id}, fetching from API")
        corporate_data = self._fetch_corporate_from_api(corporate_id)
        if corporate_data:
            # Cache the result
            cache.set(cache_key, corporate_data, self.corporate_ttl)

        return corporate_data or {}

    def batch_get_users(self, user_ids: list) -> Dict[str, Dict]:
        """Get multiple users in a single API call"""
        if not user_ids:
            return {}

        # Check cache for each user
        result = {}
        uncached_ids = []

        for user_id in user_ids:
            cache_key = f"user:{user_id}"
            cached_data = cache.get(cache_key)
            if cached_data:
                result[user_id] = cached_data
            else:
                uncached_ids.append(user_id)

        # Fetch uncached users from API
        if uncached_ids:
            users_data = self._batch_fetch_users_from_api(uncached_ids)
            for user_id, user_data in users_data.items():
                cache.set(f"user:{user_id}", user_data, self.user_ttl)
                result[user_id] = user_data

        return result

    def invalidate_user_cache(self, user_id: str):
        """Invalidate user cache (called via webhook)"""
        cache_key = f"user:{user_id}"
        cache.delete(cache_key)
        logger.info(f"Invalidated cache for user {user_id}")

    def invalidate_corporate_cache(self, corporate_id: str):
        """Invalidate corporate cache (called via webhook)"""
        cache_key = f"corporate:{corporate_id}"
        cache.delete(cache_key)
        logger.info(f"Invalidated cache for corporate {corporate_id}")

    def _fetch_user_from_api(self, user_id: str) -> Optional[Dict]:
        """Fetch user data from main backend API"""
        try:
            url = f"{self.backend_url}/api/auth/users/{user_id}/"
            headers = {"X-Service-Key": self.service_key}

            if not self.service_key:
                logger.error("BILLING_SERVICE_SECRET not configured")
                return None

            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Failed to fetch user %s: HTTP %s - %s", user_id, response.status_code, response.text)
                return None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch user data for {user_id}: {e}")
            return None

    def _fetch_corporate_from_api(self, corporate_id: str) -> Optional[Dict]:
        """Fetch corporate data from main backend API"""
        try:
            url = f"{self.backend_url}/api/auth/corporates/{corporate_id}/"
            headers = {"X-Service-Key": self.service_key}

            if not self.service_key:
                logger.error("BILLING_SERVICE_SECRET not configured")
                return None

            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Failed to fetch corporate %s: HTTP %s - %s", corporate_id, response.status_code, response.text)
                return None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch corporate data for {corporate_id}: {e}")
            return None

    def _batch_fetch_users_from_api(self, user_ids: list) -> Dict[str, Dict]:
        """Fetch multiple users from main backend API"""
        try:
            # For now, fetch individually since batch endpoint may not exist
            result = {}
            for user_id in user_ids:
                user_data = self._fetch_user_from_api(user_id)
                if user_data:
                    result[str(user_id)] = user_data
            return result
        except Exception as e:
            logger.error(f"Failed to batch fetch users: {e}")
            return {}
