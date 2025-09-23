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
import traceback
from django.contrib.auth import get_user_model

# Set up logging
logger = logging.getLogger(__name__)

#Logout settings.
LOGOUT_URL = getattr(settings, 'LOGOUT_URL', '/logout/')
LOGOUT_REDIRECT_URL = getattr(settings, 'LOGOUT_REDIRECT_URL', '/')
LOGIN_URL = getattr(settings, 'LOGIN_URL', '/login/')


class ShibbolethDebugView(TemplateView):
    template_name = 'course/auth_debug.html'

    def get(self, request, *args, **kwargs):
        User = get_user_model()
        
        # Collect debug information
        debug_info = {
            'User Authentication': {
                'is_authenticated': request.user.is_authenticated,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'username': request.user.username if request.user.is_authenticated else None,
                'email': request.user.email if request.user.is_authenticated else None,
                'superuser': request.user.is_superuser if request.user.is_authenticated else None,
                'staff': request.user.is_staff if request.user.is_authenticated else None,
                'user_permissions': list(request.user.get_all_permissions()) if request.user.is_authenticated else None,
            },
            'Session Info': {
                'session_key': request.session.session_key,
                'session_data': dict(request.session.items()),
                'session_cookie_age': settings.SESSION_COOKIE_AGE,
                'session_expire_at_browser_close': settings.SESSION_EXPIRE_AT_BROWSER_CLOSE,
            },
            'Shibboleth Headers': {
                key: value for key, value in request.META.items() 
                if key.startswith(('HTTP_SHIB', 'REMOTE_USER', 'Shib-', 'MAIL'))
            },
            'Shibboleth Middleware Info': {
                'header_used': getattr(settings, 'SHIBBOLETH_ATTRIBUTE_MAP', {}).get('REMOTE_USER', {}).get('HTTP_HEADER', 'HTTP_MAIL'),
                'exempt_paths': getattr(settings, 'SHIBBOLETH_EXEMPT_PATHS', []),
                'create_unknown_user': getattr(settings, 'SHIBBOLETH_CREATE_UNKNOWN_USER', True),
                'login_handler': getattr(settings, 'SHIBBOLETH_LOGIN_URL', '/Shibboleth.sso/Login'),
                'logout_handler': getattr(settings, 'SHIBBOLETH_LOGOUT_URL', '/Shibboleth.sso/Logout'),
            },
            'Request Processing Details': {
                'email_in_headers': request.META.get('HTTP_MAIL'),
                'user_found_by_email': User.objects.filter(email=request.META.get('HTTP_MAIL', '')).exists(),
                'user_id_if_found': User.objects.filter(email=request.META.get('HTTP_MAIL', '')).first().id if User.objects.filter(email=request.META.get('HTTP_MAIL', '')).exists() else None,
                'request_path': request.path,
                'is_exempt_from_shibboleth': any(request.path.startswith(path) for path in getattr(settings, 'SHIBBOLETH_EXEMPT_PATHS', [])),
                'request_method': request.method,
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
                'get_parameters': dict(request.GET.items()),
                'post_parameters': dict(request.POST.items()) if request.method == 'POST' else {},
                'cookies': dict(request.COOKIES.items()),
            },
            'Shibboleth Settings': {
                'LOGIN_URL': getattr(settings, 'LOGIN_URL', None),
                'LOGOUT_URL': getattr(settings, 'LOGOUT_URL', None),
                'SHIBBOLETH_ATTRIBUTE_MAP': getattr(settings, 'SHIBBOLETH_ATTRIBUTE_MAP', None),
                'AUTHENTICATION_BACKENDS': getattr(settings, 'AUTHENTICATION_BACKENDS', None),
                'MIDDLEWARE': [m for m in getattr(settings, 'MIDDLEWARE', []) if 'shibboleth' in m.lower()],
            },
            'App Configuration': {
                'DEBUG': getattr(settings, 'DEBUG', None),
                'ALLOWED_HOSTS': getattr(settings, 'ALLOWED_HOSTS', None),
                'BASE_DIR': str(getattr(settings, 'BASE_DIR', None)),
            }
        }

        # Try to analyze authentication process flow
        auth_flow = []
        try:
            # Check if email exists in the headers
            if request.META.get('mail') or request.META.get('HTTP_MAIL') or request.META.get('Mail'):
                if request.META.get('HTTP_MAIL'):
                    auth_flow.append(f"Email found in headers: 'HTTP_MAIL'")
                elif request.META.get('mail'):
                    auth_flow.append(f"Email found in headers: 'mail'")
                elif request.META.get('Mail'):
                    auth_flow.append(f"Email found in headers: 'Mail'")
                
                # Check if user exists with this email
                user_query = User.objects.filter(email=request.META.get('HTTP_MAIL'))
                if user_query.exists():
                    user = user_query.first()
                    auth_flow.append(f"User found in database with email: {user.email}, username: {user.username}, id: {user.id}")
                    
                    # Check if the found user matches the currently authenticated user
                    if request.user.is_authenticated and request.user.id == user.id:
                        auth_flow.append("Authentication successful: The authenticated user matches the user found by email")
                    else:
                        auth_flow.append("Authentication issue: user not authenticated")
                else:
                    auth_flow.append(f"No user found with email: {request.META.get('HTTP_MAIL')}")
                    
                    if getattr(settings, 'SHIBBOLETH_CREATE_UNKNOWN_USER', True):
                        auth_flow.append("User creation would be attempted based on SHIBBOLETH_CREATE_UNKNOWN_USER=True")
                    else:
                        auth_flow.append("User creation would be skipped based on SHIBBOLETH_CREATE_UNKNOWN_USER=False")
            else:
                auth_flow.append("No email found in HTTP_MAIL header")
        except Exception as e:
            auth_flow.append(f"Error analyzing authentication flow: {str(e)}")
            auth_flow.append(traceback.format_exc())
            
        debug_info['Authentication Flow Analysis'] = auth_flow

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
            # Enhanced logging about the incoming request
            logger.info("==== ShibbolethLoginView GET Request ====")
            logger.info(f"Path: {request.path}")
            logger.info(f"GET params: {request.GET}")
            logger.info(f"Headers: {dict(request.headers)}")
            logger.info(f"User authenticated: {request.user.is_authenticated}")
            
            # Log detailed Shibboleth headers
            shibboleth_headers = {
                key: value for key, value in request.META.items() 
                if key.startswith(('HTTP_SHIB', 'REMOTE_USER', 'Shib-', 'MAIL'))
            }
            logger.info(f"Shibboleth headers: {shibboleth_headers}")
            
            # Log middleware and settings info
            User = get_user_model()
            logger.info(f"Using header: {getattr(settings, 'SHIBBOLETH_ATTRIBUTE_MAP', {}).get('REMOTE_USER', {}).get('HTTP_HEADER', 'HTTP_MAIL')}")
            
            # Check if user exists with the email in headers
            email = request.META.get('HTTP_MAIL', '')
            if email:
                logger.info(f"Found email in headers: {email}")
                user_exists = User.objects.filter(email=email).exists()
                logger.info(f"User exists with this email: {user_exists}")
                if user_exists:
                    user = User.objects.get(email=email)
                    logger.info(f"Found user: id={user.id}, username={user.username}, is_active={user.is_active}")
            else:
                logger.info("No email found in HTTP_MAIL header")
            
            # Check if path is exempt from Shibboleth
            exempt_paths = getattr(settings, 'SHIBBOLETH_EXEMPT_PATHS', [])
            is_exempt = any(request.path.startswith(path) for path in exempt_paths)
            logger.info(f"Path is exempt from Shibboleth: {is_exempt}")
            logger.info(f"Exempt paths: {exempt_paths}")

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


class ShibbolethRequestDebugView(TemplateView):
    """
    Debug view specifically for the process_request method of the middleware.
    Simulates the middleware's processing and provides detailed information.
    """
    template_name = 'course/auth_process_debug.html'
    
    def get(self, request, *args, **kwargs):
        from course.shib_middleware import CustomShibbolethMiddleware
        
        # Get User model
        User = get_user_model()
        
        # Prepare debug info dictionary
        debug_info = {
            'Request Basics': {
                'path': request.path,
                'method': request.method,
                'is_secure': request.is_secure(),
                'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
            },
            'Pre-Processing State': {
                'user_authenticated': request.user.is_authenticated,
                'username': request.user.username if request.user.is_authenticated else None,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'session_key': request.session.session_key,
            },
            'Headers and META': {
                'headers': dict(request.headers),
                'shibboleth_headers': {
                    key: value for key, value in request.META.items() 
                    if key.startswith(('HTTP_SHIB', 'REMOTE_USER', 'Shib-', 'MAIL'))
                },
            },
            'Middleware Configuration': {
                'header_used': 'HTTP_MAIL',  # CustomShibbolethMiddleware.header
                'shibboleth_exempt_paths': getattr(settings, 'SHIBBOLETH_EXEMPT_PATHS', []),
                'create_unknown_user': getattr(settings, 'SHIBBOLETH_CREATE_UNKNOWN_USER', True),
            },
        }
        
        # Simulate middleware's process_request method
        process_steps = []
        
        # Step 1: Check if path is exempt
        is_exempt = any(request.path.startswith(path) for path in getattr(settings, 'SHIBBOLETH_EXEMPT_PATHS', []))
        process_steps.append({
            'step': 'Check if path is exempt from Shibboleth',
            'result': f"Path {request.path} is {'exempt' if is_exempt else 'not exempt'} from Shibboleth",
            'action': 'Return None' if is_exempt else 'Continue processing'
        })
        
        if not is_exempt:
            # Step 2: Try to get email from headers
            email = request.META.get('HTTP_MAIL')
            process_steps.append({
                'step': 'Get email from HTTP_MAIL header',
                'result': f"Email {'found' if email else 'not found'} in headers: {email}",
                'action': 'Continue with email' if email else 'Skip user lookup'
            })
            
            if email:
                # Step 3: Try to get existing user
                user_exists = User.objects.filter(email=email).exists()
                process_steps.append({
                    'step': 'Look up user by email',
                    'result': f"User {'found' if user_exists else 'not found'} with email {email}",
                    'action': 'Use existing user' if user_exists else 'Create new user if allowed'
                })
                
                if user_exists:
                    user = User.objects.get(email=email)
                    process_steps.append({
                        'step': 'Get user details',
                        'result': f"User ID: {user.id}, Username: {user.username}, Active: {user.is_active}",
                        'action': 'Set request.user and login'
                    })
                else:
                    # Step 4: User does not exist, check if should create
                    create_unknown = getattr(settings, 'SHIBBOLETH_CREATE_UNKNOWN_USER', True)
                    process_steps.append({
                        'step': 'Check if should create unknown user',
                        'result': f"Create unknown user setting is {create_unknown}",
                        'action': 'Create new user' if create_unknown else 'Skip user creation'
                    })
        
        # Add the process steps to the debug info
        debug_info['Process Request Simulation'] = process_steps
        
        # Log the debug information
        logger.info("Process Request Debug Information:\n%s", pformat(debug_info))
        
        return render(request, self.template_name, {'debug_info': debug_info})