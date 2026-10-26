import hmac
from django.core.exceptions import ValidationError
from django.db import transaction
from course.models import Enrollment, Group, TeamMembership
from course.policies.access import require


@transaction.atomic
def enroll(user, course, key=""):
    require(course.is_published)
    if course.enrollment_key and not hmac.compare_digest(course.enrollment_key, key):
        raise ValidationError("Invalid enrollment key")
    return Enrollment.objects.get_or_create(student=user, course=course)[0]


@transaction.atomic
def join(user, group):
    group = Group.objects.select_for_update().select_related("course").get(pk=group.pk)
    enrollment = (
        Enrollment.objects.select_for_update()
        .filter(student=user, course=group.course)
        .first()
    )
    require(enrollment is not None, "Enroll in the course first")
    if TeamMembership.objects.filter(enrollment=enrollment).exists():
        raise ValidationError("Already in a team")
    if group.members.count() >= group.course.max_members:
        raise ValidationError("Team is full")
    TeamMembership.objects.create(enrollment=enrollment, group=group)
    group.members.add(user)
    return group


@transaction.atomic
def leave(user, group):
    Group.objects.select_for_update().get(pk=group.pk)
    TeamMembership.objects.filter(enrollment__student=user, group=group).delete()
    group.members.remove(user)
