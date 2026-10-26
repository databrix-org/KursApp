import hmac
import os
import secrets
from datetime import timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from drf_spectacular.utils import extend_schema
from . import contracts
from allauth.account.models import EmailAddress
from course.models import Invitation, CourseStaff, Enrollment, Identity
from course.policies.access import require
from course.services.submissions import queue_job


def profile(user):
    return {
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_admin": user.is_superuser,
        "is_instructor": user.is_instructor,
    }


@ensure_csrf_cookie
@extend_schema(request=None, responses=contracts.Session)
@api_view(["GET"])
@permission_classes([AllowAny])
def session(request):
    return Response(
        {
            "user": profile(request.user) if request.user.is_authenticated else None,
            "sso_enabled": settings.SSO_ENABLED,
        }
    )


@csrf_protect
@extend_schema(methods=["POST"], request=contracts.Login, responses=contracts.User)
@extend_schema(methods=["PATCH"], request=contracts.Profile, responses=contracts.User)
@extend_schema(methods=["DELETE"], request=None, responses=contracts.Message)
@api_view(["POST", "DELETE", "PATCH"])
@permission_classes([AllowAny])
def session_change(request):
    SessionAuthentication().enforce_csrf(request)
    if request.method == "POST":
        user = (
            get_user_model()
            .objects.filter(email__iexact=request.data.get("email", ""))
            .first()
        )
        valid = authenticate(
            request,
            username=user.username if user else "unknown_" + secrets.token_hex(16),
            password=request.data.get("password", ""),
        )
        if (
            not valid
            or not valid.is_active
            or not EmailAddress.objects.filter(
                user=valid, verified=True, email__iexact=valid.email
            ).exists()
        ):
            return Response(
                {"detail": "Invalid credentials or email not verified"}, status=400
            )
        login(request, valid, backend="django.contrib.auth.backends.ModelBackend")
        return Response(profile(valid))
    require(request.user.is_authenticated)
    if request.method == "DELETE":
        logout(request)
        return Response({"status": "signed_out"})
    for key in ("first_name", "last_name"):
        if key in request.data:
            setattr(request.user, key, str(request.data[key])[:100])
    request.user.save(update_fields=["first_name", "last_name"])
    return Response(profile(request.user))


@extend_schema(
    methods=["POST"],
    request=contracts.InvitationRequest,
    responses={201: contracts.InvitationCreated},
)
@extend_schema(methods=["GET"], responses=contracts.InvitationRecord(many=True))
@api_view(["GET", "POST"])
def invitations(request):
    require(request.user.is_superuser)
    if request.method == "GET":
        return Response(
            list(
                Invitation.objects.values(
                    "id", "email", "course_id", "role", "expires_at", "consumed_at"
                )
            )
        )
    from django.core.validators import validate_email

    email = str(request.data.get("email", "")).strip().lower()
    validate_email(email)
    role = request.data.get("role", "student")
    if role not in ("student", "instructor"):
        raise ValidationError("Invalid invitation role")
    inv = Invitation.objects.create(
        email=email,
        course_id=request.data.get("course") or None,
        role=role,
        expires_at=timezone.now() + timedelta(days=7),
    )
    url = f"{settings.PUBLIC_ORIGIN}/de/account/invitation?token={inv.token}"
    queue_job(
        "email",
        {
            "subject": "Databrix invitation / Einladung",
            "body": f"Accept your invitation / Einladung annehmen: {url}",
            "recipients": [email],
        },
    )
    return Response({"id": inv.pk, "status": "queued"}, status=201)


@csrf_protect
@extend_schema(
    request=contracts.InvitationAccept, responses=contracts.InvitationAccepted
)
@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def accept_invitation(request):
    SessionAuthentication().enforce_csrf(request)
    inv = get_object_or_404(
        Invitation.objects.select_for_update(), token=request.data.get("token")
    )
    if inv.consumed_at or inv.expires_at < timezone.now():
        raise ValidationError("Invitation expired or already used")
    User = get_user_model()
    existing = User.objects.filter(email__iexact=inv.email).first()
    if existing:
        require(
            request.user.is_authenticated and request.user.pk == existing.pk,
            "Sign in to the existing account before accepting",
        )
        user = existing
    else:
        first = str(request.data.get("first_name", "")).strip()
        last = str(request.data.get("last_name", "")).strip()
        if not first or not last:
            raise ValidationError("First and last name are required")
        password = request.data.get("password", "")
        validate_password(password)
        user = User.objects.create_user(
            email=inv.email,
            username="local_" + secrets.token_hex(12),
            first_name=first,
            last_name=last,
            password=password,
            is_instructor=inv.role == "instructor",
        )
        EmailAddress.objects.create(
            user=user, email=inv.email, primary=True, verified=False
        )
        token = signing.dumps(
            {"user": user.pk, "email": user.email}, salt="databrix-email"
        )
        url = f"{settings.PUBLIC_ORIGIN}/de/account/verify-email?key={token}"
        queue_job(
            "email",
            {
                "subject": "Verify Databrix email / E-Mail bestätigen",
                "body": url,
                "recipients": [user.email],
            },
        )
    if inv.role == "instructor":
        user.is_instructor = True
        user.save(update_fields=["is_instructor"])
    if inv.course_id:
        if inv.role == "instructor":
            CourseStaff.objects.get_or_create(
                course=inv.course, user=user, defaults={"role": "instructor"}
            )
        else:
            Enrollment.objects.get_or_create(course=inv.course, student=user)
    inv.consumed_at = timezone.now()
    inv.save(update_fields=["consumed_at"])
    return Response({"status": "accepted", "verification_required": not existing})


@csrf_protect
@extend_schema(request=contracts.Key, responses=contracts.Message)
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email(request):
    SessionAuthentication().enforce_csrf(request)
    try:
        data = signing.loads(
            request.data.get("key", ""), salt="databrix-email", max_age=172800
        )
    except signing.BadSignature:
        raise ValidationError("Invalid or expired verification link")
    address = get_object_or_404(EmailAddress, user_id=data["user"], email=data["email"])
    address.verified = True
    address.save(update_fields=["verified"])
    return Response({"status": "verified"})


@csrf_protect
@extend_schema(request=contracts.Reset, responses=contracts.Message)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset(request):
    SessionAuthentication().enforce_csrf(request)
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes

    user = (
        get_user_model()
        .objects.filter(email__iexact=request.data.get("email", ""), is_active=True)
        .first()
    )
    if user and user.has_usable_password():
        key = (
            urlsafe_base64_encode(force_bytes(user.pk))
            + "-"
            + default_token_generator.make_token(user)
        )
        queue_job(
            "email",
            {
                "subject": "Databrix password reset / Passwort zurücksetzen",
                "body": f"{settings.PUBLIC_ORIGIN}/de/account/reset-password?key={key}",
                "recipients": [user.email],
            },
        )
    return Response({"status": "If an account exists, instructions will be sent"})


@csrf_protect
@extend_schema(request=contracts.ResetConfirm, responses=contracts.Message)
@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    SessionAuthentication().enforce_csrf(request)
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_decode

    try:
        uid, ts, signature = str(request.data.get("key", "")).split("-", 2)
        user = get_user_model().objects.get(pk=int(urlsafe_base64_decode(uid)))
    except Exception:
        raise ValidationError("Invalid reset link")
    if not default_token_generator.check_token(user, ts + "-" + signature):
        raise ValidationError("Expired reset link")
    validate_password(request.data.get("password", ""), user)
    user.set_password(request.data["password"])
    user.save(update_fields=["password"])
    return Response({"status": "password_updated"})


def _users(request, pk=None):
    require(request.user.is_superuser)
    User = get_user_model()
    if request.method == "GET":
        return Response(
            [
                profile(u) | {"is_active": u.is_active}
                for u in User.objects.order_by("id")
            ]
        )
    u = get_object_or_404(User, pk=pk)
    require(u.pk != request.user.pk, "Use another administrator for self changes")
    if request.method == "DELETE":
        u.is_active = False
        u.save(update_fields=["is_active"])
        return Response({"status": "deactivated; academic history retained"})
    role = request.data.get("role")
    if role not in ("student", "instructor", "admin"):
        raise ValidationError("Invalid role")
    u.is_superuser = u.is_staff = role == "admin"
    u.is_instructor = role in ("instructor", "admin")
    u.is_student = role == "student"
    u.save()
    return Response(profile(u))


@require_GET
def sso_start(request):
    if not settings.SSO_ENABLED:
        return JsonResponse(
            {"detail": "Institutional SSO is not configured"}, status=503
        )
    nonce = secrets.token_urlsafe(32)
    request.session["sso_nonce"] = nonce
    target = (
        settings.PUBLIC_ORIGIN
        + "/auth/institutional/callback/?"
        + urlencode({"state": nonce})
    )
    return HttpResponseRedirect(
        settings.SSO_LOGIN_URL + "?" + urlencode({"target": target})
    )


@require_GET
def sso_callback(request):
    secret = os.environ.get("SSO_GATEWAY_SECRET", "")
    nonce = request.session.pop("sso_nonce", "")
    if (
        not settings.SSO_ENABLED
        or not secret
        or not hmac.compare_digest(
            secret, request.headers.get("X-Databrix-Sso-Secret", "")
        )
        or not nonce
        or not hmac.compare_digest(nonce, request.GET.get("state", ""))
    ):
        return JsonResponse({"detail": "Untrusted SSO callback"}, status=403)
    issuer = request.headers.get("X-Databrix-Sso-Issuer", "")
    subject = request.headers.get("X-Databrix-Sso-Subject", "")
    email = request.headers.get("X-Databrix-Sso-Email", "").lower()
    if not issuer or not subject or not email:
        return JsonResponse(
            {"detail": "Missing verified identity attributes"}, status=400
        )
    identity = Identity.objects.filter(issuer=issuer, subject=subject).first()
    if identity:
        user = identity.user
    elif request.user.is_authenticated:
        user = request.user
        Identity.objects.create(issuer=issuer, subject=subject, user=user)
    elif get_user_model().objects.filter(email__iexact=email).exists():
        return JsonResponse(
            {
                "detail": "Sign in to link the existing account or contact an administrator"
            },
            status=409,
        )
    else:
        if not request.headers.get(
            "X-Databrix-Sso-First-Name"
        ) or not request.headers.get("X-Databrix-Sso-Last-Name"):
            return JsonResponse(
                {
                    "detail": "Verified first and last names are required for a new account"
                },
                status=400,
            )
        from django.core.validators import validate_email

        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse(
                {"detail": "Invalid verified email attribute"}, status=400
            )
        with transaction.atomic():
            user = get_user_model().objects.create_user(
                username="sso_" + secrets.token_hex(12),
                email=email,
                first_name=request.headers.get("X-Databrix-Sso-First-Name", ""),
                last_name=request.headers.get("X-Databrix-Sso-Last-Name", ""),
            )
            Identity.objects.create(issuer=issuer, subject=subject, user=user)
            EmailAddress.objects.create(
                user=user, email=email, verified=True, primary=True
            )
    if not user.is_active:
        return JsonResponse({"detail": "Inactive account"}, status=403)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return HttpResponseRedirect("/de/courses")


@extend_schema(responses=contracts.User(many=True))
@api_view(["GET"])
def users_list(request):
    return _users(request)


@extend_schema(methods=["PATCH"], request=contracts.Role, responses=contracts.User)
@extend_schema(methods=["DELETE"], request=None, responses=contracts.Message)
@api_view(["PATCH", "DELETE"])
def user_detail(request, pk):
    return _users(request, pk)


@extend_schema(request=contracts.AdminAnnouncement, responses=contracts.Message)
@api_view(["POST"])
def admin_announcement(request):
    require(request.user.is_superuser)
    body = contracts.AdminAnnouncement(data=request.data)
    body.is_valid(raise_exception=True)
    data = body.validated_data
    users = get_user_model().objects.filter(is_active=True)
    if data["recipients"] == "students":
        users = users.filter(is_student=True)
    elif data["recipients"] == "instructors":
        users = users.filter(is_instructor=True)
    elif data["recipients"] == "selected":
        users = users.filter(pk__in=data.get("selected_users", []))
    for email in users.values_list("email", flat=True):
        queue_job(
            "email",
            {"subject": data["subject"], "body": data["body"], "recipients": [email]},
        )
    return Response({"status": "queued"}, status=202)
