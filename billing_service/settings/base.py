# settings/base.py
import os
from pathlib import Path

import dj_database_url
from corsheaders.defaults import default_headers
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env or .env.dev depending on DJANGO_ENV
ENV_FILE = BASE_DIR / (".env.dev" if os.environ.get("DJANGO_ENV") == "dev" else ".env")
load_dotenv(ENV_FILE)

# Security & Debug
SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-dev-key")
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(
    ","
)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "billing_service.billing.apps.BillingConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "billing_service.middleware.jwt_auth.JWTAuthenticationMiddleware",  # JWT auth
    "billing_service.billing.middleware.BillingAuthMiddleware",
    "billing_service.billing.middleware.CompanyTracingMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "billing_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "billing_service.wsgi.application"

# Database (PostgreSQL via DATABASE_URL)
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get(
            "DATABASE_URL"
        ),  # e.g. postgres://devuser:devpass@db:5432/devdb
        conn_max_age=600,
    )
}

# Optional: enforce SSL for production
if os.environ.get("REQUIRE_DB_SSL", "false").lower() == "true":
    DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "billing_service.billing.auth_backends.RemoteAuthBackend",  # Remote auth against main backend
    "django.contrib.auth.backends.ModelBackend",  # Local auth (fallback)
]

# Main backend URL for remote authentication
MAIN_BACKEND_URL = os.environ.get("MAIN_BACKEND_URL", "http://django-backend-dev:8000")

# JWT Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)

# Microservice Configuration
ERP_BACKEND_URL = os.environ.get("ERP_BACKEND_URL", "http://django-backend:8000")
SERVICE_API_KEY = os.environ.get("SERVICE_API_KEY", "")

# Webhook Configuration
BILLING_WEBHOOK_SECRET = os.environ.get("BILLING_WEBHOOK_SECRET", "")

# Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "billing-cache",
    }
}

# Cache TTLs
USER_CACHE_TTL = int(os.environ.get("USER_CACHE_TTL", 3600))  # 1 hour
CORPORATE_CACHE_TTL = int(os.environ.get("CORPORATE_CACHE_TTL", 86400))  # 24 hours

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# REST Framework setup
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static & Media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "https://quidpath.com",
    "https://www.quidpath.com",
    "http://localhost:3000",
]
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
]

# Pesaway Configuration
PESAWAY_API_KEY = os.environ.get("PESAWAY_API_KEY", "")
PESAWAY_SECRET_KEY = os.environ.get("PESAWAY_SECRET_KEY", "")
PESAWAY_MERCHANT_ID = os.environ.get("PESAWAY_MERCHANT_ID", "")
PESAWAY_TEST_MODE = os.environ.get("PESAWAY_TEST_MODE", "true").lower() == "true"
PESAWAY_WEBHOOK_URL = os.environ.get("PESAWAY_WEBHOOK_URL", "")
PESAWAY_WEBHOOK_SECRET = os.environ.get("PESAWAY_WEBHOOK_SECRET", "")

# M-Pesa Daraja Configuration
MPESA_CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY", "")
MPESA_CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET", "")
MPESA_BUSINESS_SHORT_CODE = os.environ.get("MPESA_BUSINESS_SHORT_CODE", "9895960")
MPESA_TILL_NUMBER = os.environ.get("MPESA_TILL_NUMBER", "9100097")
MPESA_PASSKEY = os.environ.get("MPESA_PASSKEY", "")
MPESA_CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL", "")
MPESA_ENVIRONMENT = os.environ.get("MPESA_ENVIRONMENT", "production")
