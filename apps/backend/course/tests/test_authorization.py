from django.core.exceptions import PermissionDenied, ValidationError
from allauth.account.models import EmailAddress
from course.models import (
    Course,
    Enrollment,
    Group,
    Submission,
    Ticket,
)
from course.services.enrollment import enroll, join
from course.services.grading import grade
from .base import PlatformCase


class AuthorizationTests(PlatformCase):
    def test_multiple_courses_and_enrollments_preserve_identity(self):
        c = Course.objects.create(
            title="Two", instructor=self.teacher, is_published=True
        )
        enroll(self.student, c)
        self.assertEqual(self.student.enrollments.count(), 2)
        self.assertTrue(self.student.check_password("Long-test-pass-449!"))

    def test_key_required_for_form_and_api(self):
        self.api.force_authenticate(self.other)
        self.assertEqual(
            self.api.post(
                f"/api/v1/courses/{self.course.pk}/enroll/",
                {"key": "wrong"},
                format="json",
            ).status_code,
            400,
        )
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.post(
                f"/course/enroll/{self.course.pk}/", {"enrollment_key": "wrong"}
            ).status_code,
            400,
        )
        self.assertFalse(Enrollment.objects.filter(student=self.other).exists())

    def test_unenrolled_team_join_and_student_authoring_forbidden(self):
        self.api.force_authenticate(self.other)
        self.assertEqual(
            self.api.post(
                f"/api/v1/groups/{self.group.pk}/join/", {}, format="json"
            ).status_code,
            404,
        )
        self.api.force_authenticate(self.student)
        r = self.api.patch(
            f"/api/v1/lessons/{self.lesson.pk}/", {"title": "Hijacked"}, format="json"
        )
        self.assertEqual(r.status_code, 403)
        self.client.force_login(self.student)
        self.assertEqual(
            self.client.post(
                f"/course/manage/save_lesson/{self.lesson.pk}/",
                {},
                content_type="application/json",
            ).status_code,
            403,
        )

    def test_unrelated_instructor_cannot_grade_or_read_assets(self):
        sub = Submission.objects.create(
            exercise=self.exercise,
            student=self.student,
            group=self.group,
            roster=[self.student.pk],
        )
        self.api.force_authenticate(self.stranger)
        self.assertEqual(
            self.api.post(
                f"/api/v1/submissions/{sub.pk}/grade/", {"score": 9}, format="json"
            ).status_code,
            404,
        )
        with self.assertRaises(PermissionDenied):
            grade(self.stranger, sub, 9)

    def test_team_capacity_and_uniqueness(self):
        Enrollment.objects.create(student=self.other, course=self.course)
        join(self.other, self.group)
        with self.assertRaises(ValidationError):
            join(self.student, Group.objects.create(course=self.course))
        Enrollment.objects.create(student=self.stranger, course=self.course)
        with self.assertRaises(ValidationError):
            join(self.stranger, self.group)

    def test_grading_is_finite_bounded_and_append_only(self):
        sub = Submission.objects.create(
            exercise=self.exercise,
            student=self.student,
            group=self.group,
            maximum_points=10,
            pass_points=5,
        )
        for score in [-1, 11, "nan", "inf", None]:
            with self.assertRaises(ValidationError):
                grade(self.teacher, sub, score)
        grade(self.teacher, sub, 7, "First")
        grade(self.teacher, sub, 8, "Second")
        self.assertEqual(
            list(sub.grade_history.values_list("score", flat=True)), [7, 8]
        )
        sub.refresh_from_db()
        self.assertTrue(sub.passed)

    def test_html_sanitized_on_write_and_read(self):
        self.api.force_authenticate(self.teacher)
        r = self.api.patch(
            f"/api/v1/lessons/{self.lesson.pk}/",
            {
                "lesson_content": "<h2>Title</h2><img src=x onerror=alert(1)><script>alert(2)</script>"
            },
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("onerror", r.data["lesson_content"])
        self.assertNotIn("<script", r.data["lesson_content"])

    def test_private_legacy_workspace_and_reference_denied(self):
        self.client.force_login(self.student)
        self.assertEqual(
            self.client.get("/data/user_directories/group_1/private.ipynb").status_code,
            404,
        )
        self.exercise.reference_solution = "solutions/reference.ipynb"
        self.exercise.save()
        self.assertEqual(
            self.client.get("/data/solutions/reference.ipynb").status_code, 403
        )

    def test_support_is_course_scoped(self):
        ticket = Ticket.objects.create(
            user=self.student, course=self.course, subject="Help", description="Details"
        )
        self.api.force_authenticate(self.teacher)
        self.assertEqual(self.api.get(f"/api/v1/tickets/{ticket.pk}/").status_code, 200)
        self.api.force_authenticate(self.stranger)
        self.assertEqual(self.api.get(f"/api/v1/tickets/{ticket.pk}/").status_code, 404)
        self.api.force_authenticate(self.student)
        self.assertEqual(
            self.api.patch(
                f"/api/v1/tickets/{ticket.pk}/", {"status": "closed"}, format="json"
            ).status_code,
            403,
        )

    def test_sso_headers_outside_callback_do_not_authenticate(self):
        from rest_framework.test import APIClient

        r = APIClient().get(
            "/api/v1/session/",
            HTTP_REMOTE_USER="teacher",
            HTTP_X_DATABRIX_SSO_EMAIL=self.teacher.email,
        )
        self.assertIsNone(r.data["user"])

    def test_login_requires_csrf_and_verified_email(self):
        from rest_framework.test import APIClient

        client = APIClient(enforce_csrf_checks=True)
        body = {"email": self.student.email, "password": "Long-test-pass-449!"}
        self.assertEqual(
            client.post("/api/v1/session/change/", body, format="json").status_code, 403
        )
        client.get("/api/v1/session/")
        token = client.cookies["csrftoken"].value
        self.assertEqual(
            client.post(
                "/api/v1/session/change/", body, format="json", HTTP_X_CSRFTOKEN=token
            ).status_code,
            400,
        )
        EmailAddress.objects.create(
            user=self.student, email=self.student.email, verified=True, primary=True
        )
        self.assertEqual(
            client.post(
                "/api/v1/session/change/", body, format="json", HTTP_X_CSRFTOKEN=token
            ).status_code,
            200,
        )

    def test_user_deactivation_retains_history(self):
        self.teacher.is_superuser = True
        self.teacher.save()
        sub = Submission.objects.create(exercise=self.exercise, student=self.student)
        self.api.force_authenticate(self.teacher)
        self.assertEqual(
            self.api.delete(f"/api/v1/users/{self.student.pk}/").status_code, 200
        )
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)
        self.assertTrue(Submission.objects.filter(pk=sub.pk).exists())

    def test_assessment_embargo_and_maximum_statistics_are_preserved(self):
        from django.utils import timezone
        from course.policies.access import sees_submission

        self.course.end_date = timezone.localdate()
        self.course.save()
        sub = Submission.objects.create(
            exercise=self.exercise, student=self.student, group=self.group, score=8
        )
        self.assertFalse(sees_submission(self.teacher, sub))
        with self.assertRaises(PermissionDenied):
            grade(self.teacher, sub, 9)
        self.api.force_authenticate(self.teacher)
        self.assertEqual(
            self.api.get(f"/api/v1/courses/{self.course.pk}/statistics/").status_code,
            403,
        )
        self.teacher.is_superuser = True
        self.teacher.save()
        grade(self.teacher, sub, 9)
        data = self.api.get(f"/api/v1/courses/{self.course.pk}/statistics/").data
        self.assertEqual(data[0]["maximum"], 9)
        self.assertEqual(data[0]["submissions"], 1)

    def test_operational_admin_cannot_bypass_grading_history(self):
        self.teacher.is_staff = True
        self.teacher.save()
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        self.teacher.is_superuser = True
        self.teacher.save()
        sub = Submission.objects.create(
            exercise=self.exercise, student=self.student, score=7
        )
        self.assertEqual(
            self.client.post(
                f"/admin/course/submission/{sub.pk}/change/", {"score": 9}
            ).status_code,
            403,
        )
        sub.refresh_from_db()
        self.assertEqual(sub.score, 7)

    def test_editing_legacy_grade_keeps_original_feedback_and_score(self):
        sub = Submission.objects.create(
            exercise=self.exercise,
            student=self.student,
            score=6,
            feedback="Historical feedback",
        )
        grade(self.teacher, sub, 9, "Revised feedback")
        history = list(sub.grade_history.order_by("id"))
        self.assertEqual(len(history), 2)
        self.assertEqual(
            (
                history[0].score,
                history[0].feedback,
                history[0].grader_id,
                history[0].is_legacy_snapshot,
            ),
            (6, "Historical feedback", None, True),
        )
        self.assertEqual(
            (history[1].score, history[1].feedback), (9, "Revised feedback")
        )

    def test_course_route_switch_and_reading_rollback(self):
        self.lesson.lesson_type = "reading"
        self.lesson.lesson_content = "<p>Retained reading content</p>"
        self.lesson.save()
        self.client.force_login(self.student)
        url = f"/course/lesson/{self.lesson.pk}/"
        self.course.frontend_enabled = True
        self.course.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, f"/de/courses/{self.course.pk}/lessons/{self.lesson.pk}"
        )
        self.course.frontend_enabled = False
        self.course.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Retained reading content")

    def test_new_administrator_can_author_a_course_without_legacy_instructor_flag(self):
        self.teacher.is_superuser = True
        self.teacher.is_instructor = False
        self.teacher.save()
        self.api.force_authenticate(self.teacher)
        response = self.api.post(
            "/api/v1/courses/", {"title": "Administrator course"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        module = self.api.post(
            "/api/v1/modules/",
            {
                "title": "First module",
                "course": response.data["id"],
                "instructor": self.teacher.pk,
                "order": 1,
            },
            format="json",
        )
        self.assertEqual(module.status_code, 201)
