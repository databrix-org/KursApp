from urllib.parse import urlparse
from django.conf import settings
from django.core.exceptions import ValidationError
from course.models import Group, NotebookAccess, Enrollment
from course.policies.access import is_staff, learns, require


def launch(user, course):
    require(learns(user, course))
    group = Group.objects.filter(course=course, members=user).first()
    enrollment = Enrollment.objects.filter(course=course, student=user).first()
    confirmed = is_staff(user, course) or (
        enrollment
        and NotebookAccess.objects.filter(
            enrollment=enrollment, confirmed=True
        ).exists()
    )
    url = (group.lab_url if group else "") or course.lab_url
    if not url and course.domain_name:
        suffix = f"group_{group.pk}" if group else user.username
        url = f"https://{course.domain_name}/jupyterhub/hub/user/{suffix}/lab"
    if not confirmed:
        return {"status": "pending", "url": None}
    if not url:
        return {"status": "unconfigured", "url": None}
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.hostname not in settings.NOTEBOOK_ALLOWED_HOSTS
    ):
        raise ValidationError(
            "Notebook destination must use HTTPS and an operator-approved host"
        )
    return {"status": "ready", "url": url}
