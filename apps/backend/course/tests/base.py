from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from course.models import (
    Course,
    CourseStaff,
    Module,
    Lesson,
    Exercise,
    Enrollment,
    Group,
)
from course.services.enrollment import join


class PlatformCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.teacher = User.objects.create_user(
            username="teacher",
            email="teacher@example.invalid",
            first_name="Test",
            last_name="Teacher",
            password="Long-test-pass-449!",
            is_instructor=True,
        )
        self.student = User.objects.create_user(
            username="student",
            email="student@example.invalid",
            first_name="Test",
            last_name="Student",
            password="Long-test-pass-449!",
        )
        self.other = User.objects.create_user(
            username="other",
            email="other@example.invalid",
            first_name="Other",
            last_name="Student",
        )
        self.stranger = User.objects.create_user(
            username="stranger",
            email="stranger@example.invalid",
            first_name="Other",
            last_name="Teacher",
            is_instructor=True,
        )
        self.course = Course.objects.create(
            title="Data",
            instructor=self.teacher,
            is_published=True,
            max_members=2,
            enrollment_key="invite",
        )
        CourseStaff.objects.create(course=self.course, user=self.teacher, role="owner")
        self.module = Module.objects.create(
            course=self.course, instructor=self.teacher, title="Module", order=0
        )
        self.lesson = Lesson.objects.create(
            module=self.module, title="Notebook", order=0, lesson_type="exercise"
        )
        self.exercise = Exercise.objects.create(
            lesson=self.lesson,
            exercise_type="jupyter",
            maximum_points=10,
            pass_points=5,
        )
        Enrollment.objects.create(student=self.student, course=self.course)
        self.group = Group.objects.create(course=self.course)
        join(self.student, self.group)
        self.api = APIClient()
        self.api.force_authenticate(self.student)
