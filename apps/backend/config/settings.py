"""Environment-only deployment settings. No connections or directory creation at import."""

import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent.parent
env = environ.Env()
ENVIRONMENT = env("DATABRIX_ENV", default="development")
DEBUG = ENVIRONMENT == "development"
SECRET_KEY = env(
    "DJANGO_SECRET_KEY", default="local-development-key-not-for-production"
)
if ENVIRONMENT == "production" and (
    SECRET_KEY.startswith("local-") or len(SECRET_KEY) < 50
):
    raise ValueError("Set a unique DJANGO_SECRET_KEY of at least 50 characters")
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "backend", "testserver"]
)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS", default=["http://localhost:8080", "http://localhost:3000"]
)
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'local.sqlite3'}")
}
if (
    ENVIRONMENT == "production"
    and DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql"
):
    raise ValueError("Production requires PostgreSQL")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "shibboleth",
    "course.apps.CourseConfig",
]
SITE_ID = 1
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "course.policies.legacy.LegacyAuthorizationMiddleware",
    "course.api.middleware.PrivateAPIMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "course.views.course_context_processor",
            ]
        },
    }
]
AUTH_USER_MODEL = "course.CustomUserModel"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
    "first_name*",
    "last_name*",
]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_ADAPTER = "course.services.accounts.InvitationAccountAdapter"
HEADLESS_ONLY = True
HEADLESS_CLIENTS = ("browser",)
PUBLIC_ORIGIN = env("PUBLIC_ORIGIN", default="http://localhost:8080").rstrip("/")
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": PUBLIC_ORIGIN + "/de/account/verify-email/{key}",
    "account_reset_password_from_key": PUBLIC_ORIGIN
    + "/de/account/reset-password/{key}",
    "account_signup": PUBLIC_ORIGIN + "/de/account/invitation",
}
LOGIN_URL = "/de/login"
LOGIN_REDIRECT_URL = "/de/courses"
LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
LEGACY_DATA_ROOT = Path(env("LEGACY_DATA_ROOT", default=str(REPO_ROOT / "legacy/data")))
DATA_ROOT = MEDIA_ROOT = LEGACY_DATA_ROOT
DATA_URL = MEDIA_URL = "/data/"
USER_FILES_ROOT = DATA_ROOT / "user_directories"
EXERCISE_FILES_ROOT = DATA_ROOT / "exercise_files"
EXERCISE_SUBMISSIONS_ROOT = DATA_ROOT / "exercise_submissions"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": str(DATA_ROOT), "base_url": "/data/"},
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 4 * 1024 * 1024
MAX_UPLOAD_SIZE = 2 * 1024**3
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = ENVIRONMENT == "production"
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000 if ENVIRONMENT == "production" else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_PRELOAD = ENVIRONMENT == "production"
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="Databrix <noreply@example.invalid>"
)
SUPPORT_EMAIL = env.list("SUPPORT_EMAIL", default=["support@example.invalid"])
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": 3600}
S3_ENDPOINT_URL = env("S3_ENDPOINT_URL", default="http://localhost:5000")
S3_PUBLIC_ENDPOINT_URL = env("S3_PUBLIC_ENDPOINT_URL", default=S3_ENDPOINT_URL)
S3_REGION = env("S3_REGION", default="eu-central-1")
S3_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID", default="local")
S3_SECRET_ACCESS_KEY = env("S3_SECRET_ACCESS_KEY", default="local")
S3_BUCKETS = {
    name: env("S3_BUCKET_" + name.upper(), default="databrix-" + name)
    for name in ("course", "notebooks", "assessment", "support")
}
if ENVIRONMENT == "production" and (
    S3_ACCESS_KEY_ID.startswith("local")
    or S3_SECRET_ACCESS_KEY.startswith("local")
    or not S3_ENDPOINT_URL.startswith("https://")
):
    raise ValueError(
        "Production requires private HTTPS object storage and scoped credentials"
    )
NOTEBOOK_ALLOWED_HOSTS = env.list("NOTEBOOK_ALLOWED_HOSTS", default=[])
SSO_ENABLED = env.bool("SSO_ENABLED", default=False)
SSO_LOGIN_URL = env("SSO_LOGIN_URL", default="/Shibboleth.sso/Login")
LEGACY_UI_ENABLED = env.bool("LEGACY_UI_ENABLED", default=True)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "course.api.errors.exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "30/min", "user": "300/min"},
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Databrix API",
    "VERSION": "1.0.0",
    "COMPONENT_SPLIT_REQUEST": True,
}
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
]
SECURE_SSL_REDIRECT = ENVIRONMENT == "production"
CELERY_BROKER_CONNECTION_TIMEOUT = 3
CELERY_TASK_PUBLISH_RETRY = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

SECURE_REDIRECT_EXEMPT = [r"^healthz/?$", r"^readyz/?$"]

if ENVIRONMENT == "production":
    if not PUBLIC_ORIGIN.startswith(
        "https://"
    ) or not S3_PUBLIC_ENDPOINT_URL.startswith("https://"):
        raise ValueError(
            "Production requires HTTPS platform and public object endpoints"
        )
    if EMAIL_BACKEND.endswith("console.EmailBackend"):
        raise ValueError("Configure production email delivery")
    if SSO_ENABLED and len(os.environ.get("SSO_GATEWAY_SECRET", "")) < 32:
        raise ValueError(
            "Configure a trusted SSO gateway secret of at least 32 characters"
        )
