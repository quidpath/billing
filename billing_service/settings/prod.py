# settings/prod.py
import logging
import os

from corsheaders.defaults import default_headers

from .base import *

logger = logging.getLogger(__name__)
print("Using Production Settings")

# DATABASE CONFIGURATION
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "billing_prod"),
        "USER": os.getenv("POSTGRES_USER", "billing_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": "postgres_billing_prod",
        "PORT": "5432",
        "OPTIONS": {
            "sslmode": "disable",
        },
    },
}

# SECURITY SETTINGS
DEBUG = False

# Load allowed hosts from environment (comma-separated)
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS", "api.quidpath.com,quidpath.com,www.quidpath.com"
).split(",")

# CSRF & CORS CONFIGURATION
_env_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _env_csrf:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _env_csrf.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        "https://quidpath.com",
        "https://www.quidpath.com",
        "https://*.quidpath.com",
    ]

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "https://quidpath.com",
    "https://www.quidpath.com",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "content-type",
]

# STATIC & MEDIA FILES
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# SECURITY MIDDLEWARE HEADERS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# LOGGING CONFIGURATION
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.streamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
