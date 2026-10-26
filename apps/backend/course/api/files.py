from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from course.models import Lesson, Exercise, ExerciseMaterial, SubmissionFile, Ticket
from course.policies.access import require, learns, is_staff, sees_submission


@login_required
def legacy_file(request, path):
    """Only DB-referenced legacy files; never raw workspace directory access."""
    path = path.replace("\\", "/")
    if ".." in Path(path).parts:
        raise Http404
    found = False
    for model, field in [
        (Lesson, "video_file"),
        (Exercise, "file"),
        (Exercise, "reference_solution"),
        (ExerciseMaterial, "file"),
        (SubmissionFile, "file"),
        (Ticket, "image"),
    ]:
        obj = model.objects.filter(**{field: path}).first()
        if not obj:
            continue
        if isinstance(obj, Lesson):
            allowed = learns(request.user, obj.module.course)
        elif isinstance(obj, Exercise):
            allowed = (
                is_staff(request.user, obj.lesson.module.course)
                if field == "reference_solution"
                else learns(request.user, obj.lesson.module.course)
            )
        elif isinstance(obj, ExerciseMaterial):
            allowed = learns(request.user, obj.exercise.lesson.module.course)
        elif isinstance(obj, SubmissionFile):
            allowed = sees_submission(request.user, obj.submission)
        else:
            allowed = request.user.is_superuser or obj.user_id == request.user.pk
        require(allowed)
        found = True
        break
    if not found:
        raise Http404
    root = Path(settings.LEGACY_DATA_ROOT).resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise Http404
    response = FileResponse(target.open("rb"), as_attachment=True, filename=target.name)
    response["X-Content-Type-Options"] = "nosniff"
    return response
