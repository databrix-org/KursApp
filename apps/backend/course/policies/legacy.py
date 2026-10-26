from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from course.models import Course, Module, Lesson, Exercise, Group, Submission, Ticket
from .access import (
    require,
    manages,
    edits_module,
    learns,
    is_staff,
    sees_ticket,
    manages_ticket,
)


class LegacyAuthorizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, args, kwargs):
        if not request.path.startswith("/course/"):
            return
        if not settings.LEGACY_UI_ENABLED:
            return HttpResponseRedirect("/de/courses")
        if not request.user.is_authenticated:
            return
        name = getattr(request.resolver_match, "url_name", "")
        if (
            request.method not in ("GET", "HEAD", "OPTIONS")
            and request.content_type == "multipart/form-data"
            and name in {"save_lesson","create_lesson","create_jupyter_exercise","create_jupyter_exercise_ajax","edit_jupyter_exercise","upload_reference_solution","create_ticket"}
        ):
            return JsonResponse(
                {"detail": "Use private staged uploads in the new interface"},
                status=409,
            )
        try:
            course = None
            module = None
            if "lesson_id" in kwargs:
                lesson = (
                    Lesson.objects.select_related("module__course")
                    .filter(pk=kwargs["lesson_id"])
                    .first()
                )
                if lesson:
                    module = lesson.module
                    course = module.course
            elif "module_id" in kwargs:
                module = (
                    Module.objects.select_related("course")
                    .filter(pk=kwargs["module_id"])
                    .first()
                )
                if module:
                    course = module.course
            elif "exercise_id" in kwargs:
                exercise = (
                    Exercise.objects.select_related("lesson__module__course")
                    .filter(pk=kwargs["exercise_id"])
                    .first()
                )
                if exercise:
                    module = exercise.lesson.module
                    course = module.course
            elif "submission_id" in kwargs:
                sub = (
                    Submission.objects.select_related(
                        "exercise__lesson__module__course"
                    )
                    .filter(pk=kwargs["submission_id"])
                    .first()
                )
                if sub:
                    module = sub.exercise.lesson.module
                    course = module.course
            if not course and "course_id" in kwargs:
                course = Course.objects.filter(pk=kwargs["course_id"]).first()
            if not course and "group_id" in kwargs:
                group = (
                    Group.objects.select_related("course")
                    .filter(pk=kwargs["group_id"])
                    .first()
                )
                if group:
                    course = group.course
            if "ticket_id" in kwargs:
                ticket = Ticket.objects.filter(pk=kwargs["ticket_id"]).first()
                require(ticket and sees_ticket(request.user, ticket))
                if name == "update_ticket":
                    require(manages_ticket(request.user, ticket))
                if name == "delete_ticket":
                    require(request.user.is_superuser)
            if course and course.frontend_enabled and request.method == "GET":
                if name == "lesson_detail":
                    return HttpResponseRedirect(
                        f"/de/courses/{course.pk}/lessons/{lesson.pk}"
                    )
                if name in {"course_overview", "manage_course", "manage_groups"}:
                    return HttpResponseRedirect(
                        f"/de/courses/{course.pk}"
                        + (
                            "/manage"
                            if name == "manage_course"
                            else "/teams"
                            if name == "manage_groups"
                            else ""
                        )
                    )
            if name in {
                "ticket_list",
                "ticket_detail",
                "create_ticket",
                "update_ticket",
                "delete_ticket",
            }:
                return (
                    HttpResponseRedirect("/de/support")
                    if request.method == "GET"
                    else JsonResponse(
                        {"detail": "Use the versioned support API"}, status=409
                    )
                )
            if name in {"grade_submission", "exercise_submissions"}:
                return HttpResponseRedirect(
                    f"/de/submissions/{sub.pk}"
                    if name == "grade_submission" and sub
                    else "/de/submissions"
                )
            if name in {
                "upload_reference_solution",
                "delete_jupyter_file",
                "delete_material",
            }:
                return JsonResponse(
                    {"detail": "Use versioned private assets in the new interface"},
                    status=409,
                )
            if name.startswith("admin_"):
                require(request.user.is_superuser)
            if name in {
                "save_lesson",
                "create_lesson",
                "delete_lesson",
                "get_lesson",
                "delete_jupyter_file",
                "delete_material",
                "create_jupyter_exercise",
                "create_jupyter_exercise_ajax",
                "edit_jupyter_exercise",
                "reorder_lessons",
                "grade_submission",
                "upload_reference_solution",
            }:
                require(module and edits_module(request.user, module))
            if name in {
                "manage_course",
                "manage_groups",
                "manage_create_group",
                "delete_group",
                "add_group_member",
                "remove_group_member",
                "create_module",
                "add_domain",
                "add_jupyter_image",
            }:
                require(course and manages(request.user, course))
            if name == "get_group_members":
                require(course and is_staff(request.user, course))
            if name in {"lesson_detail", "complete_lesson", "course_overview"}:
                require(course and learns(request.user, course))
            if request.method not in ('GET','HEAD','OPTIONS') and name in {'save_lesson','create_lesson','delete_lesson','create_module','update_module','delete_module','update_module_order','reorder_lessons'}:
                return JsonResponse({'detail':'Use versioned authoring in the new course interface'},status=409)
            # Legacy submissions used destructive cross-cloud filesystem assumptions.
            if name in {
                "submit_exercise",
                "create_jupyter_exercise",
                "create_jupyter_exercise_ajax",
                "edit_jupyter_exercise",
            }:
                return JsonResponse(
                    {
                        "detail": "Use the new course interface for private artifact uploads"
                    },
                    status=409,
                )
            if name in {
                "submissions_dashboard",
                "submission_statistics",
                "admin_dashboard",
                "dev_login",
            }:
                return HttpResponseRedirect(
                    "/de/admin" if request.user.is_superuser else "/de/courses"
                )
        except PermissionDenied:
            return JsonResponse({"detail": "Permission denied"}, status=403)
