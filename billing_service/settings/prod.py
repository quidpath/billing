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
        'NAME': os.getenv('POSTGRES_DB', 'quidpath_billing_db'),
        'USER': os.getenv('POSTGRES_USER', 'quidpath_billing_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': 'postgres_billing_prod',
        'PORT': '5432',
    },
    'auth_db': {
        # Shared authentication database from main backend
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('AUTH_POSTGRES_DB', 'quidpath_db'),
        'USER': os.getenv('AUTH_POSTGRES_USER', 'quidpath_user'),
        'PASSWORD': os.getenv('AUTH_POSTGRES_PASSWORD', 'eDgDiAcayFqcPpXjThL6Ak668'),
        'HOST': os.getenv('AUTH_POSTGRES_HOST', 'postgres_prod'),
        'PORT': '5432',
    }
}

DATABASE_ROUTERS = ['billing_service.routers.AuthRouter']
AUTH_USER_MODEL = 'auth.User'  # Use the default user model from main backend

# ====================================
# 🔒 SECURITY SETTINGS
# ====================================
DEBUG = False

# ... rest of your existing settings ...