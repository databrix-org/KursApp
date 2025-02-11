from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from urllib.parse import quote  
import logging
from pprint import pformat

# Set up logging
logger = logging.getLogger(__name__)

#Logout settings.
LOGOUT_URL = getattr(settings, 'LOGOUT_URL', '/logout/')
LOGOUT_REDIRECT_URL = getattr(settings, 'LOGOUT_REDIRECT_URL', '/')
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/login/')


class ShibbolethDebugView(TemplateView):
    template_name = 'course/auth_debug.html'

    def get(self, request, *args, **kwargs):
        # Collect debug information
        debug_info = {
            'User Authentication': {
                'is_authenticated': request.user.is_authenticated,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'username': request.user.username if request.user.is_authenticated else None,
                'email': request.user.email if request.user.is_authenticated else None,
            },
            'Session Info': {
                'session_key': request.session.session_key,
                'session_data': dict(request.session.items()),
            },
            'Shibboleth Headers': {
                key: value for key, value in request.META.items() 
                if key.startswith(('HTTP_SHIB', 'REMOTE_USER', 'Shib-', 'MAIL'))
            },
            'All Request Headers': {
                key: value for key, value in request.META.items() 
                if key.startswith('HTTP_')
            },
            'Request Details': {
                'path': request.path,
                'method': request.method,
                'is_secure': request.is_secure(),
                'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
            },
            'Shibboleth Settings': {
                'LOGIN_URL': getattr(settings, 'LOGIN_URL', None),
                'LOGOUT_URL': getattr(settings, 'LOGOUT_URL', None),
                'SHIBBOLETH_ATTRIBUTE_MAP': getattr(settings, 'SHIBBOLETH_ATTRIBUTE_MAP', None),
            }
        }

        # Log the debug information
        logger.info("Authentication Debug Information:\n%s", pformat(debug_info))

        return render(request, self.template_name, {'debug_info': debug_info})


class ShibbolethLoginView(TemplateView):
    """
    Handle Shibboleth login with better debugging
    """
    redirect_field_name = "target"

    def get(self, request, *args, **kwargs):
        try:
            logger.info("=== ShibbolethLoginView GET Request ===")
            logger.info(f"Path: {request.path}")
            logger.info(f"GET params: {request.GET}")
            logger.info(f"Headers: {dict(request.headers)}")
            logger.info(f"User authenticated: {request.user.is_authenticated}")

            # Use the direct Shibboleth.sso handler
            shibboleth_login_url = '/Shibboleth.sso/Login'
            
            # Add the target parameter to redirect to /course/home after login
            target = request.build_absolute_uri('/course/home')
            full_url = f'{shibboleth_login_url}?target={quote(target)}'
            logger.info(f"Redirecting to: {full_url}")
            
            return redirect(full_url)

        except Exception as e:
            logger.exception("Error in ShibbolethLoginView")
            return HttpResponse("Authentication error. Please contact support.", status=500)


class ShibbolethLogoutView(TemplateView):
    """
    Handle logout with debug logging.
    """
    redirect_field_name = "next"

    def handle_logout(self, request, *args, **kwargs):
        logger.info("Starting logout process...")
        
        # Log pre-logout state
        logger.info("Pre-logout user state: authenticated=%s, user=%s", 
                   request.user.is_authenticated,
                   getattr(request.user, 'username', 'AnonymousUser'))

        # Perform logout
        auth.logout(request)
        
        # Log post-logout state
        logger.info("Post-logout user state: authenticated=%s", 
                   request.user.is_authenticated)

        # Get target URL
        target = (
            request.GET.get(self.redirect_field_name) or 
            getattr(settings, 'LOGOUT_REDIRECT_URL', None) or 
            '/'
        )
        
        # Ensure absolute URI
        if not target.startswith('http'):
            target = request.build_absolute_uri(target)
        
        logger.info("Logout target URL: %s", target)

        # Get logout URL
        logout_url = LOGOUT_URL
        if '%s' in logout_url:
            logout_url = logout_url % quote(target)

        return redirect(logout_url)

    def get(self, request, *args, **kwargs):
        return self.handle_logout(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.handle_logout(request, *args, **kwargs)