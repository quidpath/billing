# settings/dev.py
from .base import *
import os

if os.environ.get("DJANGO_ENV") == "dev":
    DEBUG = True
    ALLOWED_HOSTS = ["*"]

# CSRF settings for development
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8002',
    'http://127.0.0.1:8002',
    'http://0.0.0.0:8002',
]

# CSRF cookie settings for development (more permissive for local testing)
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'

# Session settings for development
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# Debug settings
if DEBUG:
    # Allow all referers in development
    CSRF_COOKIE_DOMAIN = None

print("Using Development Settings")
print("DATABASE_URL:", os.environ.get("DATABASE_URL"))



