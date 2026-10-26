import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Avg, Count, Max
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.utils import timezone
from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer
from course.models import (
    Course,
    Module,
    Lesson,
    Exercise,
    Group,
    Enrollment,
    CourseStaff,
    Submission,
    Asset,
    Ticket,
    LessonProgress,
    NotebookAccess,
)
from course.policies.access import (
    require,
    is_staff,
    manages,
    edits_module,
    learns,
    sees_submission,
    sees_asset,
    manages_ticket,
    sees_ticket,
    assessment_open,
)
from course.services import enrollment, submissions, grading
from course.integrations.notebooks.launch import launch
from course.integrations.storage.client import download_url
from . import contracts
from .serializers import (
    CourseSerializer,
    ModuleSerializer,
    LessonSerializer,
    GroupSerializer,
    SubmissionSerializer,
    ExerciseSerializer,
    AssetSerializer,
    TicketSerializer,
)


def staff_courses(user):
    if user.is_superuser:
        return Course.objects.all()
    return Course.objects.filter(
        Q(instructor=user) | Q(staff_memberships__user=user)
    ).distinct()


def learned_courses(user):
    return Course.objects.filter(
        Q(pk__in=staff_courses(user)) | Q(is_published=True, enrollments__student=user)
    ).distinct()


def serializer_data(serializer, obj, request, many=False):
    return serializer(obj, many=many, context={"request": request}).data


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.none()
    serializer_class = CourseSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.serializer_class.Meta.model.objects.none()
        return (
            Course.objects.filter(
                Q(is_published=True) | Q(pk__in=staff_courses(self.request.user))
            )
            .distinct()
            .order_by("id")
        )

    def perform_create(self, serializer):
        require(self.request.user.is_superuser or self.request.user.is_instructor)
        course = serializer.save(instructor=self.request.user)
        CourseStaff.objects.create(course=course, user=self.request.user, role="owner")

    def perform_update(self, serializer):
        require(manages(self.request.user, serializer.instance))
        serializer.save()

    def perform_destroy(self, instance):
        require(manages(self.request.user, instance))
        instance.delete()

    @extend_schema(request=contracts.EnrollmentRequest, responses=contracts.Message)
    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        enrollment.enroll(
            request.user, self.get_object(), str(request.data.get("key", ""))
        )
        return Response({"status": "enrolled"})

    @extend_schema(
        responses=inline_serializer(
            name="Outline",
            fields={
                "modules": ModuleSerializer(many=True),
                "lessons": LessonSerializer(many=True),
            },
        )
    )
    @action(detail=True)
    def outline(self, request, pk=None):
        c = self.get_object()
        require(learns(request.user, c))
        return Response(
            {
                "modules": serializer_data(
                    ModuleSerializer, c.modules.all(), request, True
                ),
                "lessons": serializer_data(
                    LessonSerializer,
                    Lesson.objects.filter(module__course=c),
                    request,
                    True,
                ),
            }
        )

    @extend_schema(responses=contracts.NotebookDestination)
    @action(detail=True)
    def notebook(self, request, pk=None):
        return Response(launch(request.user, self.get_object()))

    @extend_schema(
        request=contracts.NotebookAccessRequest,
        responses=inline_serializer(
            name="NotebookAccessResult",
            fields={"confirmed": serializers.BooleanField()},
        ),
    )
    @action(detail=True, methods=["post"], url_path="notebook-access")
    def notebook_access(self, request, pk=None):
        c = self.get_object()
        require(manages(request.user, c))
        e = get_object_or_404(
            Enrollment, course=c, student_id=request.data.get("user_id")
        )
        body = contracts.NotebookAccessRequest(data=request.data)
        body.is_valid(raise_exception=True)
        a, _ = NotebookAccess.objects.update_or_create(
            enrollment=e,
            defaults={
                "confirmed": body.validated_data["confirmed"],
                "confirmed_by": request.user,
            },
        )
        return Response({"confirmed": a.confirmed})

    @extend_schema(
        request=contracts.StaffRequest,
        responses=inline_serializer(
            name="StaffMember",
            fields={
                "id": serializers.IntegerField(),
                "first_name": serializers.CharField(),
                "last_name": serializers.CharField(),
                "role": serializers.CharField(),
            },
            many=True,
        ),
    )
    @action(detail=True, methods=["get", "post", "delete"])
    def staff(self, request, pk=None):
        c = self.get_object()
        require(is_staff(request.user, c))
        if request.method == "DELETE":
            require(manages(request.user, c))
            user_id = request.data.get("user_id")
            require(
                str(user_id) != str(c.instructor_id),
                "Transfer primary ownership through an operator before removing its binding",
            )
            CourseStaff.objects.filter(course=c, user_id=user_id).delete()
        if request.method == "POST":
            require(manages(request.user, c))
            u = get_object_or_404(
                get_user_model(), pk=request.data.get("user_id"), is_instructor=True
            )
            role = request.data.get("role", "instructor")
            require(role in ("owner", "instructor"))
            CourseStaff.objects.update_or_create(
                course=c, user=u, defaults={"role": role}
            )
        return Response(
            [
                {
                    "id": m.user_id,
                    "first_name": m.user.first_name,
                    "last_name": m.user.last_name,
                    "role": m.role,
                }
                for m in c.staff_memberships.select_related("user")
            ]
        )

    @extend_schema(responses=contracts.CourseStudent(many=True))
    @action(detail=True)
    def students(self, request, pk=None):
        c = self.get_object()
        require(is_staff(request.user, c))
        return Response(
            list(
                c.enrollments.values(
                    "student_id",
                    "student__first_name",
                    "student__last_name",
                    "student__email",
                    "notebook_access__confirmed",
                )
            )
        )

    @extend_schema(responses=contracts.GroupStatistics(many=True))
    @action(detail=True)
    def statistics(self, request, pk=None):
        c = self.get_object()
        require(is_staff(request.user, c))
        require(
            assessment_open(request.user, c),
            "Statistics open after the course end date",
        )
        query = Submission.objects.filter(
            exercise__lesson__module__course=c, status="accepted"
        )
        if not manages(request.user, c):
            query = query.filter(exercise__lesson__module__instructor=request.user)
        stats = {
            r["group_id"]: r
            for r in query.values("group_id").annotate(
                submissions=Count("id", filter=Q(score__isnull=False)),
                accepted=Count("id"),
                average=Avg("score"),
                maximum=Max("score"),
            )
        }
        records = []
        for group in c.groups.prefetch_related("members"):
            row = stats.pop(
                group.pk,
                {
                    "group_id": group.pk,
                    "submissions": 0,
                    "accepted": 0,
                    "average": None,
                    "maximum": None,
                },
            )
            row["members"] = [u.get_full_name() for u in group.members.all()]
            records.append(row)
        records.extend(dict(r, members=[]) for r in stats.values())
        return Response(records)

    @extend_schema(request=contracts.AnnouncementRequest, responses=contracts.Message)
    @action(detail=True, methods=["post"])
    def announcements(self, request, pk=None):
        c = self.get_object()
        require(manages(request.user, c))
        subject = str(request.data.get("subject", "")).strip()
        body = str(request.data.get("body", "")).strip()
        if not subject or not body:
            raise ValidationError("Subject and message are required")
        # Individual jobs prevent disclosing recipients to one another.
        for email in c.enrollments.values_list("student__email", flat=True):
            submissions.queue_job(
                "email", {"subject": subject, "body": body, "recipients": [email]}
            )
        return Response({"status": "queued"}, status=202)


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.none()
    serializer_class = ModuleSerializer

    def get_queryset(self):
        return Module.objects.filter(
            course__in=learned_courses(self.request.user)
        ).order_by("course_id", "order")

    def perform_create(self, serializer):
        c = serializer.validated_data["course"]
        require(manages(self.request.user, c))
        teacher = serializer.validated_data["instructor"]
        require(is_staff(teacher, c), "Assign a course instructor")
        serializer.save()

    def perform_update(self, serializer):
        require(edits_module(self.request.user, serializer.instance))
        require(
            serializer.validated_data.get("course", serializer.instance.course)
            == serializer.instance.course
        )
        teacher = serializer.validated_data.get(
            "instructor", serializer.instance.instructor
        )
        require(is_staff(teacher, serializer.instance.course))
        if teacher != serializer.instance.instructor:
            require(manages(self.request.user, serializer.instance.course))
        serializer.save()

    def perform_destroy(self, instance):
        require(edits_module(self.request.user, instance))
        instance.delete()


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.none()
    serializer_class = LessonSerializer

    def get_queryset(self):
        return Lesson.objects.filter(
            module__course__in=learned_courses(self.request.user)
        ).order_by("module__order", "order")

    def perform_create(self, serializer):
        require(edits_module(self.request.user, serializer.validated_data["module"]))
        serializer.save()

    def perform_update(self, serializer):
        require(edits_module(self.request.user, serializer.instance.module))
        require(
            serializer.validated_data.get("module", serializer.instance.module)
            == serializer.instance.module
        )
        serializer.save()

    def perform_destroy(self, instance):
        require(edits_module(self.request.user, instance.module))
        instance.delete()

    @extend_schema(request=contracts.Completion, responses=contracts.Completion)
    @action(detail=True, methods=["put"])
    def completion(self, request, pk=None):
        lesson = self.get_object()
        require(learns(request.user, lesson.module.course))
        complete = request.data.get("completed")
        if not isinstance(complete, bool):
            raise ValidationError("completed must be boolean")
        progress, _ = LessonProgress.objects.update_or_create(
            student=request.user,
            lesson=lesson,
            defaults={
                "is_completed": complete,
                "completed_at": timezone.now() if complete else None,
            },
        )
        return Response({"completed": progress.is_completed})

    @extend_schema(request=ExerciseSerializer, responses=ExerciseSerializer)
    @action(detail=True, methods=["put"])
    def exercise(self, request, pk=None):
        lesson = self.get_object()
        require(edits_module(request.user, lesson.module))
        obj = Exercise.objects.filter(lesson=lesson).first()
        s = ExerciseSerializer(obj, data=request.data, partial=obj is not None)
        s.is_valid(raise_exception=True)
        with transaction.atomic():
            ex = s.save(lesson=lesson, version=(obj.version + 1 if obj else 1))
            lesson.lesson_type = "exercise"
            lesson.save(update_fields=["lesson_type"])
        return Response(ExerciseSerializer(ex).data)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.none()
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(
            course__in=learned_courses(self.request.user)
        ).order_by("course_id", "group_number")

    def perform_create(self, serializer):
        require(manages(self.request.user, serializer.validated_data["course"]))
        serializer.save()

    def perform_update(self, serializer):
        require(manages(self.request.user, serializer.instance.course))
        require(
            serializer.validated_data.get("course", serializer.instance.course)
            == serializer.instance.course
        )
        serializer.save()

    def perform_destroy(self, instance):
        require(manages(self.request.user, instance.course))
        instance.delete()

    @extend_schema(request=contracts.MemberRequest, responses=contracts.Message)
    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        group = self.get_object()
        target = request.user
        if request.data.get("user_id"):
            require(manages(request.user, group.course))
            target = get_object_or_404(get_user_model(), pk=request.data["user_id"])
        enrollment.join(target, group)
        return Response({"status": "joined"})

    @extend_schema(request=contracts.MemberRequest, responses=contracts.Message)
    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        group = self.get_object()
        target = request.user
        if request.data.get("user_id"):
            require(manages(request.user, group.course))
            target = get_object_or_404(get_user_model(), pk=request.data["user_id"])
        enrollment.leave(target, group)
        return Response({"status": "removed"})


class SubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Submission.objects.none()
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.serializer_class.Meta.model.objects.none()
        q = Submission.objects.select_related(
            "exercise__lesson__module__course", "student", "group"
        ).prefetch_related("assets", "grade_history")
        if self.request.user.is_superuser:
            return q
        u = self.request.user
        roster_ids = [
            pk
            for pk, roster in Submission.objects.values_list("pk", "roster")
            if u.pk in roster
        ]
        return q.filter(
            Q(student=u)
            | Q(exercise__lesson__module__course__in=staff_courses(u))
            | Q(pk__in=roster_ids)
        ).distinct()

    def retrieve(self, request, *args, **kwargs):
        require(sees_submission(request.user, self.get_object()))
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        records = [
            s
            for s in self.filter_queryset(self.get_queryset())
            if sees_submission(request.user, s)
        ]
        return Response(serializer_data(self.serializer_class, records, request, True))

    @extend_schema(
        request=contracts.SubmissionInitiation,
        responses=inline_serializer(
            name="SubmissionUpload",
            fields={
                "submission": SubmissionSerializer(),
                "uploads": contracts.UploadGrant(many=True),
            },
        ),
    )
    @action(detail=False, methods=["post"])
    def initiate(self, request):
        body = contracts.SubmissionInitiation(data=request.data)
        body.is_valid(raise_exception=True)
        try:
            key = uuid.UUID(str(request.data.get("idempotency_key")))
        except (ValueError, TypeError):
            raise ValidationError("A UUID idempotency key is required")
        ex = get_object_or_404(Exercise, pk=request.data.get("exercise_id"))
        sub, urls = submissions.initiate(
            request.user, ex, request.data.get("files", []), key
        )
        return Response(
            {
                "submission": SubmissionSerializer(
                    sub, context={"request": request}
                ).data,
                "uploads": urls,
            },
            status=201,
        )

    @extend_schema(request=None, responses={202: SubmissionSerializer})
    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        return Response(
            SubmissionSerializer(
                submissions.finalize(request.user, self.get_object()),
                context={"request": request},
            ).data,
            status=202,
        )

    @extend_schema(request=contracts.GradeRequest, responses=SubmissionSerializer)
    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None):
        sub = grading.grade(
            request.user,
            self.get_object(),
            request.data.get("score"),
            str(request.data.get("feedback", "")),
        )
        return Response(SubmissionSerializer(sub, context={"request": request}).data)


class AssetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Asset.objects.none()
    serializer_class = AssetSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.serializer_class.Meta.model.objects.none()
        q = Asset.objects.select_related(
            "course", "submission__exercise__lesson__module__course", "ticket"
        )
        for param in ("course", "lesson", "ticket", "submission"):
            if self.request.query_params.get(param):
                q = q.filter(**{param + "_id": self.request.query_params[param]})
        return q

    def list(self, request, *args, **kwargs):
        return Response(
            AssetSerializer(
                [a for a in self.get_queryset() if sees_asset(request.user, a)],
                many=True,
            ).data
        )

    def retrieve(self, request, *args, **kwargs):
        require(sees_asset(request.user, self.get_object()))
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=contracts.AssetInitiation,
        responses=inline_serializer(
            name="AssetUpload",
            fields={
                "asset": AssetSerializer(),
                "url": serializers.URLField(),
                "content_type": serializers.CharField(),
            },
        ),
    )
    @action(detail=False, methods=["post"], url_path="initiate")
    def initiate(self, request):
        body = contracts.AssetInitiation(data=request.data)
        body.is_valid(raise_exception=True)
        category = request.data.get("category")
        relations = {}
        if category in ("course", "assessment"):
            course = get_object_or_404(Course, pk=request.data.get("course"))
            lesson = (
                get_object_or_404(
                    Lesson, pk=request.data["lesson"], module__course=course
                )
                if request.data.get("lesson")
                else None
            )
            require(
                edits_module(request.user, lesson.module)
                if lesson
                else manages(request.user, course)
            )
            relations = {"course": course, "lesson": lesson}
        elif category == "support":
            ticket = get_object_or_404(Ticket, pk=request.data.get("ticket"))
            require(ticket.user_id == request.user.pk or request.user.is_superuser)
            relations = {"ticket": ticket}
        else:
            raise ValidationError("Use submission initiation for notebooks")
        asset, url = submissions.new_asset(
            request.user,
            str(request.data.get("name", "")),
            int(request.data.get("size", 0)),
            category,
            **relations,
        )
        return Response(
            {
                "asset": AssetSerializer(asset).data,
                "url": url,
                "content_type": asset.content_type,
            },
            status=201,
        )

    @extend_schema(request=None, responses={202: AssetSerializer})
    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        a = self.get_object()
        require(a.owner_id == request.user.pk and not a.submission_id)
        if a.category in ("course", "assessment"):
            require(
                edits_module(request.user, a.lesson.module)
                if a.lesson_id
                else manages(request.user, a.course)
            )
        elif a.ticket_id:
            require(a.ticket.user_id == request.user.pk or request.user.is_superuser)
        if a.status == "pending":
            a.status = "validating"
            a.save(update_fields=["status"])
            submissions.queue_job("asset", {"asset_id": str(a.id)})
        return Response(AssetSerializer(a).data, status=202)

    @extend_schema(request=None, responses=contracts.Message)
    @action(detail=True, methods=["post"])
    def retire(self, request, pk=None):
        a = self.get_object()
        require(a.category in ("course", "assessment") and not a.submission_id)
        require(
            edits_module(request.user, a.lesson.module)
            if a.lesson_id
            else manages(request.user, a.course)
        )
        a.status = "retired"
        a.save(update_fields=["status"])
        return Response({"status": "retired; historical artifact retained"})

    @extend_schema(responses={302: None})
    @action(detail=True)
    def inline(self, request, pk=None):
        a = self.get_object()
        require(
            sees_asset(request.user, a)
            and a.status == "accepted"
            and a.content_type in ("image/png", "image/jpeg")
        )
        return HttpResponseRedirect(download_url(a, inline=True))

    @extend_schema(responses=contracts.Download)
    @action(detail=True)
    def download(self, request, pk=None):
        a = self.get_object()
        require(sees_asset(request.user, a) and a.status == "accepted")
        if a.submission_id:
            require(a.submission.status == "accepted")
        return Response(
            {"url": download_url(a, inline=a.content_type.startswith("video/"))}
        )


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.none()
    serializer_class = TicketSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Ticket.objects.all()
        return Ticket.objects.filter(
            Q(user=self.request.user) | Q(course__in=staff_courses(self.request.user))
        ).distinct()

    def perform_create(self, serializer):
        course = serializer.validated_data.get("course")
        if course:
            require(learns(self.request.user, course))
        ticket = serializer.save(
            user=self.request.user, status="open", assigned_to=None, resolution_notes=""
        )
        submissions.queue_job(
            "email",
            {
                "subject": f"Ticket #{ticket.pk}: {ticket.subject}",
                "body": ticket.description,
                "recipients": settings.SUPPORT_EMAIL,
            },
        )

    def perform_update(self, serializer):
        require(sees_ticket(self.request.user, serializer.instance))
        require(
            serializer.validated_data.get("course", serializer.instance.course)
            == serializer.instance.course
        )
        if not manages_ticket(self.request.user, serializer.instance):
            require(
                not any(
                    k in serializer.validated_data
                    for k in ("status", "assigned_to", "resolution_notes")
                )
            )
        assigned = serializer.validated_data.get("assigned_to")
        if assigned:
            require(manages_ticket(assigned, serializer.instance))
        serializer.save()

    def perform_destroy(self, instance):
        require(self.request.user.is_superuser)
        instance.delete()
