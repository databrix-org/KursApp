from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from course.api.accounts import sso_start, sso_callback
from course.api.files import legacy_file


def health(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
        return JsonResponse({"status": "ready"})
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)


urlpatterns = [
    path("healthz", health),
    path("healthz/", health),
    path("readyz", ready),
    path("readyz/", ready),
    path("admin/", admin.site.urls),
    path("api/v1/", include("course.api.urls")),
    path("auth/institutional/login/", sso_start),
    path("auth/institutional/callback/", sso_callback),
    path("course/", include("course.urls")),
    path("data/<path:path>", legacy_file),
]
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
