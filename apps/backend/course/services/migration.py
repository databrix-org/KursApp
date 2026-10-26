"""Read-only inventory and resumable copies. Never delete or rename source bytes."""

import hashlib
from collections import Counter
from pathlib import Path
from django.conf import settings
from course.models import (
    Lesson,
    Exercise,
    ExerciseMaterial,
    SubmissionFile,
    Ticket,
    Asset,
)
from course.integrations.storage.client import client, bucket


def checksum(stream):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def references():
    for model, field, category in [
        (Lesson, "video_file", "course"),
        (Exercise, "file", "course"),
        (Exercise, "reference_solution", "assessment"),
        (ExerciseMaterial, "file", "course"),
        (SubmissionFile, "file", "notebooks"),
        (Ticket, "image", "support"),
    ]:
        for obj in (
            model.objects.exclude(**{field: ""})
            .exclude(**{field + "__isnull": True})
            .iterator()
        ):
            lesson = (
                obj
                if isinstance(obj, Lesson)
                else obj.lesson
                if isinstance(obj, Exercise)
                else obj.exercise.lesson
                if isinstance(obj, ExerciseMaterial)
                else obj.submission.exercise.lesson
                if isinstance(obj, SubmissionFile)
                else None
            )
            course = lesson.module.course if lesson else obj.course
            owner = course.instructor if course else obj.user
            if isinstance(obj, SubmissionFile):
                owner = obj.submission.student
            yield {
                "source": f"{model._meta.label_lower}:{obj.pk}:{field}",
                "path": str(getattr(obj, field).name),
                "category": category,
                "course_id": course.pk if course else None,
                "lesson_id": lesson.pk if lesson and category != "notebooks" else None,
                "submission_id": obj.submission_id
                if isinstance(obj, SubmissionFile)
                else None,
                "ticket_id": obj.pk if isinstance(obj, Ticket) else None,
                "owner_id": owner.pk if owner else None,
            }


def inventory():
    root = Path(settings.LEGACY_DATA_ROOT).resolve()
    items = list(references())
    counts = Counter(x["path"] for x in items)
    referenced = set()
    for row in items:
        path = (root / row["path"]).resolve()
        referenced.add(path)
        row["shared_path"] = counts[row["path"]] > 1
        row["safe"] = path.is_relative_to(root) and path.is_file()
        if row["safe"]:
            row["size"] = path.stat().st_size
            with path.open("rb") as f:
                row["sha256"] = checksum(f)
        row["requires_review"] = (
            row["shared_path"] or not row["safe"] or not row["owner_id"]
        )
    orphans = [
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and p.resolve() not in referenced
    ]
    return {
        "format": 1,
        "files": items,
        "unreferenced_files": orphans,
        "uncertain_teams": list(
            SubmissionFile.objects.filter(submission__group__isnull=True)
            .values_list("submission_id", flat=True)
            .distinct()
        ),
    }


def copy_record(row, allow_shared=False):
    import mimetypes

    if (
        not row.get("safe")
        or not row.get("owner_id")
        or row.get("shared_path")
        and not allow_shared
    ):
        raise ValueError(
            "Missing/unsafe source, owner, or unresolved shared historical path"
        )
    root = Path(settings.LEGACY_DATA_ROOT).resolve()
    path = (root / row["path"]).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Path escapes legacy root")
    with path.open("rb") as f:
        if checksum(f) != row["sha256"]:
            raise ValueError("Source checksum changed; inventory again")
        f.seek(0)
        asset, _ = Asset.objects.get_or_create(
            legacy_source=row["source"],
            defaults={
                k: row[k]
                for k in [
                    "category",
                    "course_id",
                    "lesson_id",
                    "submission_id",
                    "ticket_id",
                    "owner_id",
                    "size",
                ]
            }
            | {
                "name": path.name,
                "content_type": mimetypes.guess_type(path.name)[0]
                or "application/octet-stream",
            },
        )
        key = (
            asset.object_key
            or f"accepted/{row['course_id'] or 'platform'}/migration/{asset.id}/{path.name}"
        )
        s3 = client(asset.category)
        b = bucket(asset.category)
        try:
            s3.put_object(
                Bucket=b,
                Key=key,
                Body=f,
                ContentType=asset.content_type,
                Metadata={"sha256": row["sha256"]},
                IfNoneMatch="*",
            )
        except s3.exceptions.ClientError as exc:
            if exc.response["Error"]["Code"] not in ("PreconditionFailed", "412"):
                raise
        body = s3.get_object(Bucket=b, Key=key)["Body"]
        try:
            actual = checksum(body)
        finally:
            body.close()
        if actual != row["sha256"]:
            raise ValueError("Destination checksum differs")
        asset.object_key = key
        asset.sha256 = actual
        asset.status = "accepted"
        asset.save()
        return str(asset.pk)
