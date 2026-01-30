"""
Custom User Model - Proxy to main backend's Authentication.CustomUser
This allows the billing service to reference users from the shared auth database
without creating its own user table.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Proxy model that points to the Authentication_customuser table
    in the shared auth database (quidpath_db).
    
    This model does NOT create its own table. It uses the existing
    Authentication_customuser table from the main backend.
    """
    
    class Meta:
        # Use the existing table from main backend
        db_table = 'Authentication_customuser'
        # This is a managed model (Django won't try to create/modify the table)
        managed = False
        # Use the auth_db database (shared authentication database)
        app_label = 'billing'
