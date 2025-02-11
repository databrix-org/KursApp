from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
import os
from .models import (
    CustomUserModel, Course, Enrollment,
    Module, Lesson, Submission, StudentProfile,
    InstructorProfile, Exercise, Group, ExerciseMaterial,
    SubmissionFile
)

# Register your models here.
class UserAdminCustom(UserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_instructor",
                    "is_student",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "password1", "password2"),},
        ),
    )
    list_display = ("email", "first_name", "last_name", "is_staff", "is_instructor", "is_student")
    search_fields = ("first_name", "last_name", "email")
    ordering = ("email",)
    readonly_fields = ['date_joined', 'last_login']

class SubmissionFileInline(admin.TabularInline):
    model = SubmissionFile
    extra = 0
    readonly_fields = ('uploaded_at',)
    fields = ('file', 'description', 'uploaded_at')
    can_delete = False
    max_num = 0  # Don't allow adding files through admin

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'exercise_title', 'submitted_at', 'file_count', 'score')
    list_filter = ('submitted_at', 'exercise__lesson__title', 'student')
    search_fields = ('student__first_name', 'student__last_name', 'exercise__lesson__title')
    date_hierarchy = 'submitted_at'
    readonly_fields = ('submitted_at', 'file_count')
    inlines = [SubmissionFileInline]
    
    def student_name(self, obj):
        return obj.student.get_full_name()
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__first_name'
    
    def exercise_title(self, obj):
        return obj.exercise.lesson.title
    exercise_title.short_description = 'Exercise'
    exercise_title.admin_order_field = 'exercise__lesson__title'
    
    def file_count(self, obj):
        return obj.files.count()
    file_count.short_description = 'Number of Files'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student',
            'exercise__lesson'
        ).prefetch_related('files')

@admin.register(SubmissionFile)
class SubmissionFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'student_name', 'exercise_title', 'uploaded_at')
    list_filter = ('uploaded_at', 'submission__exercise__lesson__title')
    search_fields = (
        'submission__student__first_name',
        'submission__student__last_name',
        'submission__exercise__lesson__title',
        'file'
    )
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at',)
    
    def file_name(self, obj):
        return os.path.basename(obj.file.name)
    file_name.short_description = 'File Name'
    
    def student_name(self, obj):
        return obj.submission.student.get_full_name()
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'submission__student__first_name'
    
    def exercise_title(self, obj):
        return obj.submission.exercise.lesson.title
    exercise_title.short_description = 'Exercise'
    exercise_title.admin_order_field = 'submission__exercise__lesson__title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'submission__student',
            'submission__exercise__lesson'
        )

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'created_at', 'difficulty_level')
    list_filter = ('difficulty_level', 'created_at', 'instructor')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'

class GroupMemberInline(admin.TabularInline):
    model = Group.members.through
    extra = 1
    verbose_name = "Member"
    verbose_name_plural = "Members"
    autocomplete_fields = ['customusermodel']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'course', 'member_count', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('course__title', 'members__email', 'members__first_name', 'members__last_name')
    date_hierarchy = 'created_at'
    inlines = [GroupMemberInline]
    exclude = ('members',)
    readonly_fields = ('created_at',)

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Number of Members'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course').prefetch_related('members')

@admin.register(ExerciseMaterial)
class ExerciseMaterialAdmin(admin.ModelAdmin):
    list_display = ('description', 'exercise', 'get_lesson_title', 'created_at')
    list_filter = ('created_at', 'exercise__lesson__title')
    search_fields = ('description', 'exercise__lesson__title')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    def get_lesson_title(self, obj):
        return obj.exercise.lesson.title
    get_lesson_title.short_description = 'Lesson'
    get_lesson_title.admin_order_field = 'exercise__lesson__title'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('exercise', 'exercise__lesson')

admin.site.register(Enrollment)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Exercise)
admin.site.register(StudentProfile)
admin.site.register(InstructorProfile)
admin.site.register(CustomUserModel, UserAdminCustom)
