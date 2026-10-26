import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from allauth.account.models import EmailAddress
from course.models import (
    CustomUserModel,
    Course,
    CourseStaff,
    Module,
    Lesson,
    Exercise,
    Enrollment,
    Group,
)
from course.services.enrollment import join


class Command(BaseCommand):
    help = "Idempotent LOCAL demo data. Password is read from DEMO_PASSWORD."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            raise CommandError("Demo data is development-only")
        password = os.environ.get("DEMO_PASSWORD")
        if not password or len(password) < 12:
            raise CommandError("Set DEMO_PASSWORD (12+ characters)")
        demo_emails = [
            name + "@example.invalid" for name in ("admin", "instructor", "student")
        ]
        if CustomUserModel.objects.exclude(email__in=demo_emails).exists():
            raise CommandError(
                "Use an empty or demo-only database; existing accounts must be preserved"
            )
        people = {}
        for name in ("admin", "instructor", "student"):
            u, created = CustomUserModel.objects.get_or_create(
                username=name,
                defaults={
                    "email": name + "@example.invalid",
                    "first_name": "Demo",
                    "last_name": name,
                    "is_instructor": name != "student",
                    "is_superuser": name == "admin",
                    "is_staff": name == "admin",
                },
            )
            if created:
                u.set_password(password)
                u.save()
            EmailAddress.objects.get_or_create(
                user=u, email=u.email, defaults={"verified": True, "primary": True}
            )
            people[name] = u
        for title in ("Data Science Foundations", "Applied Notebook Projects"):
            c, _ = Course.objects.get_or_create(
                title=title,
                defaults={
                    "instructor": people["instructor"],
                    "is_published": True,
                    "max_members": 4,
                    "frontend_enabled": True,
                    "description": "Learn, apply, and collaborate. Lernen, anwenden und zusammenarbeiten.",
                },
            )
            CourseStaff.objects.get_or_create(
                course=c, user=people["instructor"], defaults={"role": "owner"}
            )
            m, _ = Module.objects.get_or_create(
                course=c,
                title="Getting started",
                defaults={"instructor": people["instructor"], "order": 1},
            )
            for order, (name, kind, body) in enumerate(
                [
                    (
                        "Introduction",
                        "reading",
                        "<h2>Welcome to Databrix</h2><p>Explore the course, then open your notebook environment.</p>",
                    ),
                    (
                        "Video lesson",
                        "video",
                        "<h2>Watch and learn</h2><p>Your instructor can upload a private MP4 video.</p>",
                    ),
                    (
                        "Notebook exercise",
                        "exercise",
                        "<h2>Your assignment</h2><p>Download the starter notebook, work in DHBW, export it, and submit your saved work here.</p>",
                    ),
                ],
                1,
            ):
                l, _ = Lesson.objects.get_or_create(
                    module=m,
                    title=name,
                    defaults={
                        "order": order,
                        "lesson_type": kind,
                        "lesson_content": body,
                    },
                )
                if kind == "exercise":
                    Exercise.objects.get_or_create(
                        lesson=l,
                        defaults={
                            "exercise_type": "jupyter",
                            "maximum_points": 10,
                            "pass_points": 5,
                        },
                    )
            Enrollment.objects.get_or_create(course=c, student=people["student"])
            g = Group.objects.filter(course=c).first() or Group.objects.create(course=c)
            if not g.members.filter(pk=people["student"].pk).exists():
                join(people["student"], g)
        self.stdout.write(
            "Demo accounts ready: admin, instructor, student at example.invalid. Existing passwords are unchanged."
        )
