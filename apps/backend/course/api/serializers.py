from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from . import contracts
from course.models import (
    Course,
    Module,
    Lesson,
    Exercise,
    Group,
    Submission,
    Ticket,
    Asset,
    GradeRevision,
)
from course.policies.access import is_staff, manages
from course.services.content import clean_html


class CourseSerializer(serializers.ModelSerializer):
    enrollment_key = serializers.CharField(
        write_only=True, required=False, allow_blank=True, max_length=100
    )
    capabilities = serializers.SerializerMethodField()
    enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "instructor",
            "start_date",
            "end_date",
            "difficulty_level",
            "max_members",
            "is_published",
            "frontend_enabled",
            "lab_url",
            "capabilities",
            "enrolled",
            "enrollment_key",
        ]
        read_only_fields = ["instructor"]

    @extend_schema_field(contracts.Capabilities)
    def get_capabilities(self, obj) -> dict:
        u = self.context["request"].user
        return {"teach": is_staff(u, obj), "manage": manages(u, obj)}

    def get_enrolled(self, obj) -> bool:
        return obj.enrollments.filter(student=self.context["request"].user).exists()

    def validate_max_members(self, v):
        if v < 1 or v > 100:
            raise serializers.ValidationError("Team limit must be 1–100")
        return v

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError("End date precedes start date")
        return attrs


class ModuleSerializer(serializers.ModelSerializer):
    # Course policies determine teaching authority, including superusers without the legacy instructor flag.
    instructor = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(is_active=True)
    )

    class Meta:
        model = Module
        fields = [
            "id",
            "course",
            "instructor",
            "title",
            "description",
            "order",
            "difficulty_level",
        ]


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ["id", "exercise_type", "maximum_points", "pass_points", "version"]
        read_only_fields = ["id", "version"]

    def validate(self, attrs):
        maximum = attrs.get(
            "maximum_points", getattr(self.instance, "maximum_points", 10)
        )
        threshold = attrs.get("pass_points", getattr(self.instance, "pass_points", 0))
        if threshold > maximum:
            raise serializers.ValidationError("Pass points exceed maximum")
        return attrs


class LessonSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(source="lesson_exercise", read_only=True)
    completed = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "module",
            "title",
            "order",
            "lesson_type",
            "duration",
            "lesson_content",
            "exercise",
            "completed",
        ]

    def validate_lesson_content(self, value):
        from course.services.inline_images import legacy_sources

        if (
            legacy_sources(value)
            or self.instance
            and legacy_sources(self.instance.lesson_content)
        ):
            raise serializers.ValidationError(
                "Migrate existing embedded/local images first; use private image upload for new images"
            )
        return clean_html(value)

    def get_completed(self, obj) -> bool:
        return obj.student_progress.filter(
            student=self.context["request"].user, is_completed=True
        ).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["lesson_content"] = clean_html(data["lesson_content"])
        return data


class GroupSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ["id", "course", "group_number", "members", "lab_url"]
        read_only_fields = ["group_number"]

    @extend_schema_field(contracts.GroupMember(many=True))
    def get_members(self, obj) -> list[dict]:
        return list(obj.members.values("id", "first_name", "last_name"))


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "id",
            "category",
            "course",
            "lesson",
            "ticket",
            "submission",
            "name",
            "size",
            "sha256",
            "content_type",
            "status",
        ]


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeRevision
        fields = [
            "id",
            "grader",
            "score",
            "feedback",
            "created_at",
            "is_legacy_snapshot",
        ]


class SubmissionSerializer(serializers.ModelSerializer):
    assets = AssetSerializer(many=True, read_only=True)
    grade_history = GradeSerializer(many=True, read_only=True)
    can_grade = serializers.SerializerMethodField()
    processing_delayed = serializers.SerializerMethodField()

    def get_processing_delayed(self, obj) -> bool:
        from course.models import Job

        return (
            obj.status == "validating"
            and Job.objects.filter(
                kind="submission", payload__submission_id=obj.pk, status="failed"
            ).exists()
        )

    def get_can_grade(self, obj) -> bool:
        from course.policies.access import can_grade

        return (
            can_grade(self.context["request"].user, obj)
            if "request" in self.context
            else False
        )

    exercise_title = serializers.CharField(
        source="exercise.lesson.title", read_only=True
    )

    class Meta:
        model = Submission
        fields = [
            "id",
            "exercise",
            "exercise_title",
            "student",
            "group",
            "roster",
            "submitted_at",
            "accepted_at",
            "finalized_at",
            "status",
            "rejection_reason",
            "exercise_version",
            "score",
            "passed",
            "feedback",
            "assets",
            "grade_history",
            "material_manifest",
            "deadline_date",
            "maximum_points",
            "pass_points",
            "can_grade",
            "processing_delayed",
        ]


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "id",
            "user",
            "course",
            "subject",
            "description",
            "status",
            "assigned_to",
            "resolution_notes",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]
