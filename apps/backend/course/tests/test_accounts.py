from datetime import timedelta
from unittest.mock import patch
from django.test import override_settings
from django.utils import timezone
from django.core import signing
from allauth.account.models import EmailAddress
from course.models import Invitation, Identity, CustomUserModel, Enrollment
from .base import PlatformCase


class AccountTests(PlatformCase):
    def test_invitation_only_signup_preserves_existing_identity(self):
        inv = Invitation.objects.create(
            email=self.student.email,
            course=self.course,
            expires_at=timezone.now() + timedelta(days=1),
        )
        r = self.api.post(
            "/api/v1/invitations/accept/", {"token": str(inv.token)}, format="json"
        )
        self.assertEqual(r.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("Long-test-pass-449!"))
        self.assertEqual(
            CustomUserModel.objects.filter(email=self.student.email).count(), 1
        )
        self.assertEqual(
            self.api.post(
                "/api/v1/invitations/accept/", {"token": str(inv.token)}, format="json"
            ).status_code,
            400,
        )

        upgrade = Invitation.objects.create(
            email=self.student.email,
            role="instructor",
            expires_at=timezone.now() + timedelta(days=1),
        )
        self.assertEqual(
            self.api.post(
                "/api/v1/invitations/accept/",
                {"token": str(upgrade.token)},
                format="json",
            ).status_code,
            200,
        )
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_instructor)
        self.assertTrue(self.student.check_password("Long-test-pass-449!"))

    def test_new_invitation_requires_verification_and_creates_durable_email(self):
        self.api.force_authenticate(None)
        inv = Invitation.objects.create(
            email="new@example.invalid",
            course=self.course,
            expires_at=timezone.now() + timedelta(days=1),
        )
        r = self.api.post(
            "/api/v1/invitations/accept/",
            {
                "token": str(inv.token),
                "first_name": "New",
                "last_name": "Student",
                "password": "Fresh-Password-583!",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        u = CustomUserModel.objects.get(email=inv.email)
        self.assertFalse(EmailAddress.objects.get(user=u).verified)
        self.assertTrue(
            Enrollment.objects.filter(student=u, course=self.course).exists()
        )
        token = signing.dumps({"user": u.pk, "email": u.email}, salt="databrix-email")
        self.assertEqual(
            self.api.post(
                "/api/v1/session/verify/", {"key": token}, format="json"
            ).status_code,
            200,
        )
        self.assertTrue(EmailAddress.objects.get(user=u).verified)

    def test_expired_invitation_and_untrusted_email_link_rejected(self):
        inv = Invitation.objects.create(
            email="expired@example.invalid",
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.assertEqual(
            self.api.post(
                "/api/v1/invitations/accept/", {"token": str(inv.token)}, format="json"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.api.post(
                "/api/v1/session/verify/", {"key": "tampered"}, format="json"
            ).status_code,
            400,
        )

    @override_settings(
        SSO_ENABLED=True, SSO_LOGIN_URL="https://idp.example.invalid/login"
    )
    @patch.dict("os.environ", {"SSO_GATEWAY_SECRET": "test-gateway-secret"})
    def test_callback_requires_nonce_gateway_and_preserves_mapped_account(self):
        Identity.objects.create(
            user=self.student, issuer="institution", subject="stable-subject"
        )
        self.client.get("/auth/institutional/login/")
        nonce = self.client.session["sso_nonce"]
        r = self.client.get(
            "/auth/institutional/callback/",
            {"state": nonce},
            HTTP_X_DATABRIX_SSO_SECRET="test-gateway-secret",
            HTTP_X_DATABRIX_SSO_ISSUER="institution",
            HTTP_X_DATABRIX_SSO_SUBJECT="stable-subject",
            HTTP_X_DATABRIX_SSO_EMAIL=self.student.email,
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.student.pk)
        r = self.client.get(
            "/auth/institutional/callback/",
            {"state": nonce},
            HTTP_X_DATABRIX_SSO_SECRET="test-gateway-secret",
        )
        self.assertEqual(r.status_code, 403)

    def test_course_teacher_cannot_invite_or_send_global_email(self):
        self.api.force_authenticate(self.teacher)
        self.assertEqual(
            self.api.post(
                "/api/v1/invitations/",
                {"email": "new@example.invalid", "role": "student"},
                format="json",
            ).status_code,
            403,
        )
        self.assertEqual(
            self.api.post(
                "/api/v1/admin/announcements/",
                {"subject": "Hi", "body": "Hello", "recipients": "all"},
                format="json",
            ).status_code,
            403,
        )

    def test_broker_failure_leaves_recoverable_job(self):
        from course.services.submissions import queue_job

        with patch(
            "course.tasks.run_job.delay", side_effect=ConnectionError("offline")
        ):
            with self.captureOnCommitCallbacks(execute=True):
                job = queue_job(
                    "email",
                    {
                        "subject": "Hi",
                        "body": "Hello",
                        "recipients": [self.student.email],
                    },
                )
        job.refresh_from_db()
        self.assertEqual(job.status, "pending")
