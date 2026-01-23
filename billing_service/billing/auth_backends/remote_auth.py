"""
Remote Authentication Backend for Billing Service.

This backend allows users to authenticate using credentials from the main
quidpath-backend service. When a user tries to log in:
1. First tries local authentication
2. If local auth fails, verifies credentials with main backend
3. If main backend confirms, creates/updates local user and allows login

This enables single sign-on where main backend superusers can access
the billing service admin without needing separate credentials.
"""
import requests
import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.conf import settings

logger = logging.getLogger(__name__)


class RemoteAuthBackend(ModelBackend):
    """
    Authenticate against the main quidpath-backend service.
    
    If authentication fails locally, this backend will attempt to verify
    credentials with the main backend via API call. If successful, it will
    create or update the local user account.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user against main backend service.
        
        Args:
            request: The HTTP request object
            username: Username to authenticate
            password: Password to authenticate
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if not username or not password:
            return None
        
        # First, try local authentication (ModelBackend's default behavior)
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is not None:
            logger.info(f"User '{username}' authenticated locally")
            return user
        
        # Local authentication failed, try remote authentication
        logger.info(f"Local authentication failed for '{username}', trying remote authentication")
        return self._authenticate_remote(username, password)
    
    def _authenticate_remote(self, username, password):
        """
        Verify credentials with the main backend service.
        
        Args:
            username: Username to verify
            password: Password to verify
            
        Returns:
            User object if remote authentication successful, None otherwise
        """
        # Get the main backend URL from settings
        main_backend_url = getattr(settings, 'MAIN_BACKEND_URL', 'http://django-backend-dev:8000')
        verify_url = f"{main_backend_url}/api/internal/auth/verify/"
        
        try:
            # Make API call to main backend to verify credentials
            response = requests.post(
                verify_url,
                json={'username': username, 'password': password},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    user_data = data.get('user', {})
                    logger.info(f"Remote authentication successful for '{username}'")
                    
                    # Create or update local user
                    user = self._get_or_create_user(username, user_data, password)
                    return user
                else:
                    logger.warning(f"Remote authentication failed for '{username}': {data.get('error')}")
                    return None
            else:
                logger.error(f"Remote auth API returned status {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to main backend for authentication: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during remote authentication: {e}")
            return None
    
    def _get_or_create_user(self, username, user_data, password):
        """
        Get or create a local user based on remote user data.
        
        Args:
            username: Username from remote system
            user_data: User data from remote system
            password: User's password (for local storage)
            
        Returns:
            User object
        """
        try:
            # Try to get existing user
            user = User.objects.get(username=username)
            logger.info(f"Updating existing user '{username}'")
            
            # Update user data from remote
            user.email = user_data.get('email', user.email)
            user.is_staff = user_data.get('is_staff', False)
            user.is_superuser = user_data.get('is_superuser', False)
            user.is_active = user_data.get('is_active', True)
            
            # Update password hash (so local auth works next time)
            user.set_password(password)
            user.save()
            
            return user
            
        except User.DoesNotExist:
            # Create new user
            logger.info(f"Creating new user '{username}' from remote data")
            user = User.objects.create_user(
                username=username,
                email=user_data.get('email', ''),
                password=password,
            )
            user.is_staff = user_data.get('is_staff', False)
            user.is_superuser = user_data.get('is_superuser', False)
            user.is_active = user_data.get('is_active', True)
            user.save()
            
            return user
        except Exception as e:
            logger.error(f"Error creating/updating user '{username}': {e}")
            return None

