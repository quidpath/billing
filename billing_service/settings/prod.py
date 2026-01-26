# settings/prod.py
from .base import *
import os
import logging
from corsheaders.defaults import default_headers

logger = logging.getLogger(__name__)
print("Using Production Settings")

# ====================================
# 🗄️ DATABASE CONFIGURATION
# ====================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'billing_prod'),
        'USER': os.getenv('POSTGRES_USER', 'billing_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': 'postgres_billing_prod',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'disable',  # Disable SSL for local Docker network
        },
    },
    'auth_db': {
        # Shared authentication database from main backend
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('AUTH_POSTGRES_DB', 'quidpath_db'),
        'USER': os.getenv('AUTH_POSTGRES_USER', 'quidpath_user'),
        'PASSWORD': os.getenv('AUTH_POSTGRES_PASSWORD'),
        'HOST': os.getenv('AUTH_POSTGRES_HOST', 'postgres_prod'),
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'disable',  # Disable SSL for local Docker network
        },
    }
}

DATABASE_ROUTERS = ['billing_service.routers.AuthRouter']

# ====================================
# 🔒 SECURITY SETTINGS
# ====================================
DEBUG = False

# Load allowed hosts from environment (comma-separated)
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "api.quidpath.com,quidpath.com,www.quidpath.com"
).split(",")

# ====================================
# 🧩 CSRF & CORS CONFIGURATION
# ====================================
# CSRF trusted origins must include scheme (Django 4+). Allow override via env.
_env_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _env_csrf:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _env_csrf.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        "https://quidpath.com",
        "https://www.quidpath.com",
        # wildcard subdomains (admin/api) — Django supports wildcard with scheme
        "https://*.quidpath.com",
    ]

# --- CORS CONFIGURATION ---
CORS_ALLOW_ALL_ORIGINS = False  # GOOD: Override base.py

# These are the *only* origins that can make browser requests
CORS_ALLOWED_ORIGINS = [
    "https://quidpath.com",
    "https://www.quidpath.com",
    # You might want to add your Amplify preview/dev URLs here too
]

# This is vital for sending credentials (like JWT tokens)
CORS_ALLOW_CREDENTIALS = True

# Explicitly allow the methods your frontend uses
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# Headers your frontend is allowed to send
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "content-type",
]

# ====================================
# ⚙️ STATIC & MEDIA FILES
# ====================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ====================================
# 🧱 SECURITY MIDDLEWARE HEADERS
# ====================================
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ====================================
# 📜 LOGGING CONFIGURATION
# ====================================
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