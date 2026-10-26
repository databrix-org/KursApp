"""Explicit request/response contracts for action endpoints."""

from rest_framework import serializers as s
from rest_framework import serializers


class User(s.Serializer):
    id = s.IntegerField()
    email = s.EmailField()
    first_name = s.CharField()
    last_name = s.CharField()
    is_admin = s.BooleanField()
    is_instructor = s.BooleanField()
    is_active = s.BooleanField(required=False)


class Session(s.Serializer):
    user = User(allow_null=True)
    sso_enabled = s.BooleanField()


class Login(s.Serializer):
    email = s.EmailField()
    password = s.CharField(write_only=True)


class Message(s.Serializer):
    status = s.CharField(required=False)
    detail = s.CharField(required=False)


class InvitationRequest(s.Serializer):
    email = s.EmailField()
    course = s.IntegerField(required=False, allow_null=True)
    role = s.ChoiceField(choices=["student", "instructor"])


class InvitationAccept(s.Serializer):
    token = s.UUIDField()
    first_name = s.CharField(required=False, allow_blank=True)
    last_name = s.CharField(required=False, allow_blank=True)
    password = s.CharField(write_only=True, required=False)


class Key(s.Serializer):
    key = s.CharField()


class Reset(s.Serializer):
    email = s.EmailField()


class ResetConfirm(Key):
    password = s.CharField(write_only=True)


class Profile(s.Serializer):
    first_name = s.CharField()
    last_name = s.CharField()


class Role(s.Serializer):
    role = s.ChoiceField(choices=["student", "instructor", "admin"])


class UploadFile(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    size = serializers.IntegerField(min_value=1, max_value=2147483648)


class UploadGrant(serializers.Serializer):
    asset_id = serializers.UUIDField()
    url = serializers.URLField()
    content_type = serializers.CharField()


class SubmissionInitiation(serializers.Serializer):
    exercise_id = serializers.IntegerField()
    idempotency_key = serializers.UUIDField()
    files = UploadFile(many=True, min_length=1, max_length=20)


class GradeRequest(serializers.Serializer):
    score = serializers.FloatField(min_value=0)
    feedback = serializers.CharField(required=False, allow_blank=True)


class Completion(serializers.Serializer):
    completed = serializers.BooleanField()


class EnrollmentRequest(serializers.Serializer):
    key = serializers.CharField(required=False, allow_blank=True)


class NotebookDestination(serializers.Serializer):
    status = serializers.ChoiceField(choices=["pending", "unconfigured", "ready"])
    url = serializers.URLField(allow_null=True)


class NotebookAccessRequest(serializers.Serializer):
    user_id = serializers.IntegerField()
    confirmed = serializers.BooleanField()


class MemberRequest(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)


class AnnouncementRequest(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField(max_length=100000)


class AssetInitiation(UploadFile):
    category = serializers.ChoiceField(choices=["course", "assessment", "support"])
    course = serializers.IntegerField(required=False, allow_null=True)
    lesson = serializers.IntegerField(required=False, allow_null=True)
    ticket = serializers.IntegerField(required=False, allow_null=True)


class Download(serializers.Serializer):
    url = serializers.URLField()


class StaffRequest(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(
        choices=["owner", "instructor"], default="instructor"
    )


class AdminAnnouncement(AnnouncementRequest):
    recipients = serializers.ChoiceField(
        choices=["all", "students", "instructors", "selected"]
    )
    selected_users = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )


class CourseStudent(serializers.Serializer):
    student_id = serializers.IntegerField()
    student__first_name = serializers.CharField()
    student__last_name = serializers.CharField()
    student__email = serializers.EmailField()
    notebook_access__confirmed = serializers.BooleanField(allow_null=True)


class GroupStatistics(serializers.Serializer):
    group_id = serializers.IntegerField(allow_null=True)
    submissions = serializers.IntegerField()
    accepted = serializers.IntegerField()
    average = serializers.FloatField(allow_null=True)
    maximum = serializers.FloatField(allow_null=True)
    members = serializers.ListField(child=serializers.CharField())


class InvitationRecord(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    course_id = serializers.IntegerField(allow_null=True)
    role = serializers.CharField()
    expires_at = serializers.DateTimeField()
    consumed_at = serializers.DateTimeField(allow_null=True)


class InvitationCreated(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()


class InvitationAccepted(serializers.Serializer):
    status = serializers.CharField()
    verification_required = serializers.BooleanField()


class Capabilities(serializers.Serializer):
    teach = serializers.BooleanField()
    manage = serializers.BooleanField()


class GroupMember(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
