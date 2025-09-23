# utils/files.py
import os, shutil, logging
from django.conf import settings
from .background import run_in_background
from course.models import Exercise, Group     # import your own models

logger = logging.getLogger(__name__)

def _copy_exercise_dir(group_id: int, lesson_title: str):
    """(Runs inside background thread) copy one exercise dir, deleting all old files in the destination group directory first."""
    group_dir = os.path.join(settings.USER_FILES_ROOT, f"group_{group_id}")
    src       = os.path.join(settings.EXERCISE_FILES_ROOT, lesson_title)
    dst       = os.path.join(group_dir,        lesson_title)

    os.makedirs(group_dir, exist_ok=True)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    logger.info("✓ Copied %s → %s", src, dst)


def start_group_copies(exercise_id: int):
    """
    Fan-out one background job per group.
    Called AFTER the DB transaction commits.
    """
    exercise = Exercise.objects.select_related("lesson__module__course").get(pk=exercise_id)
    lesson_title = exercise.lesson.title
    group_ids = exercise.lesson.module.course.groups.values_list("id", flat=True)

    for gid in group_ids:
        run_in_background(_copy_exercise_dir, gid, lesson_title)
