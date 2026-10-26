import math
from django.core.exceptions import ValidationError
from django.db import transaction
from course.models import Submission, GradeRevision
from course.policies.access import require, edits_module, assessment_open


@transaction.atomic
def grade(user, submission, score, feedback=""):
    submission = (
        Submission.objects.select_for_update()
        .select_related("exercise__lesson__module__course")
        .get(pk=submission.pk)
    )
    require(edits_module(user, submission.exercise.lesson.module))
    require(
        assessment_open(user, submission.exercise.lesson.module.course),
        "Assessment opens after the course end date",
    )
    if submission.status != "accepted":
        raise ValidationError("Only accepted submissions can be graded")
    try:
        value = float(score)
    except (TypeError, ValueError):
        raise ValidationError("Invalid score")
    if (
        not math.isfinite(value)
        or value < 0
        or value
        > (
            submission.maximum_points
            if submission.maximum_points is not None
            else submission.exercise.maximum_points
        )
    ):
        raise ValidationError("Score must be finite and within the exercise range")
    if submission.score is not None and not submission.grade_history.exists():
        GradeRevision.objects.create(
            submission=submission,
            grader=None,
            score=submission.score,
            feedback=submission.feedback or "",
            is_legacy_snapshot=True,
        )
    submission.score = value
    submission.feedback = feedback
    submission.save()
    GradeRevision.objects.create(
        submission=submission, grader=user, score=value, feedback=feedback
    )
    return submission
