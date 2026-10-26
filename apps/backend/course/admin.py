"""Superuser-only operational inspection. Business mutations use policy-checked services/API."""

from django.contrib import admin
from .models import (
    CustomUserModel,
    Course,
    Enrollment,
    Module,
    Lesson,
    Exercise,
    ExerciseMaterial,
    Group,
    Submission,
    SubmissionFile,
    LessonProgress,
    Asset,
    GradeRevision,
    CourseStaff,
    NotebookAccess,
    Job,
    Ticket,
)

admin.site.site_header = "Databrix operations"
admin.site.has_permission = lambda request: (
    request.user.is_active and request.user.is_superuser
)


class InspectionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields if f.name not in self.exclude]

    exclude = ()


@admin.register(CustomUserModel)
class UserInspection(InspectionAdmin):
    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_instructor",
        "is_superuser",
    )
    search_fields = ("email", "first_name", "last_name")
    exclude = ("password",)


@admin.register(Submission)
class SubmissionInspection(InspectionAdmin):
    list_display = (
        "id",
        "student",
        "exercise",
        "status",
        "accepted_at",
        "score",
        "passed",
    )
    list_filter = ("status", "passed")


@admin.register(Asset)
class AssetInspection(InspectionAdmin):
    list_display = ("id", "category", "name", "status", "size", "sha256")
    list_filter = ("category", "status")


@admin.register(Job)
class JobInspection(InspectionAdmin):
    list_display = ("id", "kind", "status", "attempts", "error", "updated_at")
    list_filter = ("kind", "status")
    exclude = (
        "payload",
    )  # Email payloads can contain sensitive invitation/reset URLs.


for model in (
    Course,
    Enrollment,
    Module,
    Lesson,
    Exercise,
    ExerciseMaterial,
    Group,
    SubmissionFile,
    LessonProgress,
    GradeRevision,
    CourseStaff,
    NotebookAccess,
    Ticket,
):
    admin.site.register(model, InspectionAdmin)
