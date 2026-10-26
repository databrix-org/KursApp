from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework.views import exception_handler as default_handler
from rest_framework.response import Response
from django.db.models.deletion import ProtectedError
from django.db import IntegrityError


def exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        return Response({"detail": exc.messages}, status=400)
    if isinstance(exc, PermissionDenied):
        return Response({"detail": str(exc)}, status=403)
    if isinstance(exc, ProtectedError):
        return Response(
            {
                "detail": "Academic history or stored assets still reference this record. Unpublish the course or retain the record."
            },
            status=409,
        )
    if isinstance(exc, IntegrityError):
        return Response({"detail": "Conflicting record; refresh and retry"}, status=409)
    return default_handler(exc, context)
