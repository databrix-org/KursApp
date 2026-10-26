from django.core.exceptions import PermissionDenied
from django.utils import timezone
from course.models import CourseStaff, Enrollment


def require(condition, message="Permission denied"):
    if not condition:
        raise PermissionDenied(message)


def is_staff(user, course):
    return user.is_authenticated and (
        user.is_superuser
        or course.instructor_id == user.pk
        or CourseStaff.objects.filter(course=course, user=user).exists()
    )


def manages(user, course):
    return user.is_authenticated and (
        user.is_superuser
        or course.instructor_id == user.pk
        or CourseStaff.objects.filter(course=course, user=user, role="owner").exists()
    )


def edits_module(user, module):
    return manages(user, module.course) or (
        is_staff(user, module.course) and module.instructor_id == user.pk
    )


def learns(user, course):
    return is_staff(user, course) or (
        course.is_published
        and user.is_authenticated
        and Enrollment.objects.filter(course=course, student=user).exists()
    )


def assessment_open(user, course):
    return (
        user.is_superuser
        or not course.end_date
        or timezone.localdate() > course.end_date
    )


def can_grade(user, submission):
    return (
        edits_module(user, submission.exercise.lesson.module)
        and assessment_open(user, submission.exercise.lesson.module.course)
        and submission.status == "accepted"
    )


def sees_submission(user, submission):
    return (
        (
            edits_module(user, submission.exercise.lesson.module)
            and assessment_open(user, submission.exercise.lesson.module.course)
        )
        or submission.student_id == user.pk
        or (
            learns(user, submission.exercise.lesson.module.course)
            and user.pk in submission.roster
        )
    )


def manages_ticket(user, ticket):
    return user.is_superuser or bool(ticket.course_id and is_staff(user, ticket.course))


def sees_ticket(user, ticket):
    return user.is_authenticated and (
        ticket.user_id == user.pk or manages_ticket(user, ticket)
    )


def sees_asset(user, asset):
    if asset.category == "assessment":
        return asset.course_id and is_staff(user, asset.course)
    if asset.submission_id:
        return sees_submission(user, asset.submission)
    if asset.ticket_id:
        return sees_ticket(user, asset.ticket)
    return asset.course_id and learns(user, asset.course)
