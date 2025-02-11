from django.conf import settings
from shibboleth.middleware import ShibbolethRemoteUserMiddleware
import logging
from django.urls import resolve
from django.shortcuts import redirect
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model
from django.db import IntegrityError

logger = logging.getLogger(__name__)
User = get_user_model()

class CustomShibbolethMiddleware(ShibbolethRemoteUserMiddleware):
    header = 'HTTP_MAIL'
    
    def process_request(self, request):
        #logger.debug(f"Processing request for path: {request.path}")
        #logger.debug(f"Current user authenticated: {request.user.is_authenticated}")
        #logger.debug(f"Request headers: {dict(request.headers)}")
        #logger.debug(f"Request META: {request.META}")

        # Check if the path should be exempt from Shibboleth
        if any(request.path.startswith(path) for path in getattr(settings, 'SHIBBOLETH_EXEMPT_PATHS', [])):
            logger.debug(f"Path {request.path} is exempt from Shibboleth")
            return

        try:
            # Try to get email from headers
            email = request.META.get(self.header)
            if email:
                # Try to get existing user first
                try:
                    user = User.objects.get(email=email)
                    logger.debug(f"Found existing user with email {email}")
                    request.user = user
                    return None
                except User.DoesNotExist:
                    logger.debug(f"No user found with email {email}, will create new user")
                    
            # Call parent's process_request if no existing user found
            result = super().process_request(request)
            
            #logger.debug(f"After processing: User authenticated: {request.user.is_authenticated}")
            #if hasattr(request, 'session'):
            #    logger.debug(f"Session data: {dict(request.session)}")
                
            return result

        except IntegrityError as e:
            logger.exception("IntegrityError in CustomShibbolethMiddleware")
            # If user exists, try to authenticate them
            try:
                user = User.objects.get(email=email)
                request.user = user
                return None
            except User.DoesNotExist:
                logger.error(f"Could not find or create user with email {email}")
                return redirect(settings.LOGIN_URL)
        except Exception as e:
            logger.exception("Error in CustomShibbolethMiddleware")
            return redirect(settings.LOGIN_URL)

    def clean_username(self, username, request):
        """Clean the username before using it"""
        logger.debug(f"Cleaning username: {username}")
        if username:
            # Use email as username to ensure uniqueness
            email = request.META.get(self.header, '')
            return email.lower() if email else username.lower()
        return None

