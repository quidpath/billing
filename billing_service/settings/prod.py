# settings/prod.py
import logging
import os

from corsheaders.defaults import default_headers

from .base import *

logger = logging.getLogger(__name__)
print("Using Production Settings")

# DATABASE CONFIGURATION
# Use DATABASE_URL when set (e.g. from deploy secrets); otherwise require POSTGRES_* from env (no hardcoded defaults).
if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ.get("DATABASE_URL"),
            conn_max_age=600,
        )
    }
    DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}
else:
    _user = os.getenv("POSTGRES_USER")
    _db = os.getenv("POSTGRES_DB")
    if not _user or not _db:
        raise ValueError(
            "Production requires DATABASE_URL or both POSTGRES_USER and POSTGRES_DB from environment (e.g. deploy secrets). "
            "Do not rely on hardcoded defaults."
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _db,
            "USER": _user,
            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "HOST": os.getenv("DB_HOST", "db"),
            "PORT": "5432",
            "OPTIONS": {"sslmode": "disable"},
        },
    }

# SECURITY SETTINGS
DEBUG = False

# Load allowed hosts from environment (comma-separated).
# Always include billing-backend so main backend can call this service by container name.
_default_hosts = "billing.quidpath.com,api.quidpath.com,quidpath.com,www.quidpath.com,localhost,127.0.0.1,0.0.0.0"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", _default_hosts).split(",") if h.strip()]
if "billing-backend" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("billing-backend")

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
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
