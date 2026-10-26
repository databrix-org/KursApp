import hashlib
import mimetypes
import tempfile
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from course.models import Asset, Submission, Group, Job
from course.policies.access import require, learns
from course.integrations.storage.client import client, bucket, upload_url

ALLOWED = {
    ".ipynb",
    ".py",
    ".csv",
    ".json",
    ".txt",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".mp4",
    ".webm",
    ".vtt",
    ".zip",
    ".npy",
    ".dat",
}


def check_deadline_date(end_date, at=None):
    if end_date and timezone.localtime(at or timezone.now()).date() > end_date:
        raise ValidationError("Submission deadline has passed")


def check_deadline(course, at=None):
    check_deadline_date(course.end_date, at)


def new_asset(user, name, size, category, **relations):
    name = Path(name.replace("\\", "/")).name
    suffix = Path(name).suffix.lower()
    if (
        not name
        or len(name) > 255
        or suffix not in ALLOWED
        or size <= 0
        or size > settings.MAX_UPLOAD_SIZE
    ):
        raise ValidationError("Invalid filename, extension or file size")
    if suffix == ".ipynb" and size > 64 * 1024**2:
        raise ValidationError(
            "Notebook exceeds 64 MiB; remove unnecessary embedded outputs"
        )
    if category == "assessment" and suffix != ".ipynb":
        raise ValidationError("Reference solutions must be notebooks")
    if category == "support" and suffix not in {".png", ".jpg", ".jpeg"}:
        raise ValidationError("Ticket attachments must be PNG or JPEG images")
    asset = Asset(
        owner=user,
        name=name,
        size=size,
        category=category,
        content_type=mimetypes.guess_type(name)[0] or "application/octet-stream",
        **relations,
    )
    asset.staging_key = f"staging/{user.pk}/{asset.id}/{name}"
    asset.save()
    return asset, upload_url(asset)


@transaction.atomic
def initiate(user, exercise, files, key):
    course = exercise.lesson.module.course
    require(learns(user, course))
    check_deadline(course)
    group = (
        Group.objects.select_for_update().filter(course=course, members=user).first()
    )
    require(group is not None, "Join a course team first")
    if not isinstance(files, list) or not files or len(files) > 20:
        raise ValidationError("Choose between 1 and 20 files")
    if any(
        not isinstance(f, dict)
        or not isinstance(f.get("name"), str)
        or not isinstance(f.get("size"), int)
        for f in files
    ):
        raise ValidationError("Each file requires a name and integer size")
    existing = Submission.objects.filter(idempotency_key=key).first()
    if existing:
        manifest = list(
            existing.assets.order_by("created_at", "id").values("name", "size")
        )
        if sorted((x["name"], x["size"]) for x in manifest) != sorted(
            (Path(x["name"].replace("\\", "/")).name, x["size"]) for x in files
        ):
            raise ValidationError(
                "Idempotency key belongs to a different file manifest; start a new submission"
            )
        require(existing.student_id == user.pk and existing.exercise_id == exercise.pk)
        if existing.status != "pending":
            return existing, []
        return existing, [
            {
                "asset_id": str(a.id),
                "url": upload_url(a),
                "content_type": a.content_type,
            }
            for a in existing.assets.order_by("created_at", "id")
        ]
    if exercise.exercise_type == "jupyter" and not any(
        Path(f["name"]).suffix.lower() == ".ipynb" for f in files
    ):
        raise ValidationError("At least one Jupyter notebook is required")
    sub = Submission.objects.create(
        exercise=exercise,
        student=user,
        group=group,
        roster=list(group.members.values_list("id", flat=True)),
        status="pending",
        idempotency_key=key,
        exercise_version=exercise.version,
        maximum_points=exercise.maximum_points,
        pass_points=exercise.pass_points,
        material_manifest=[
            dict(a, id=str(a["id"]))
            for a in Asset.objects.filter(
                lesson=exercise.lesson, category="course", status="accepted"
            ).values("id", "sha256", "name")
        ],
    )
    urls = []
    for f in files:
        asset, url = new_asset(
            user, f["name"], int(f["size"]), "notebooks", course=course, submission=sub
        )
        urls.append(
            {"asset_id": str(asset.id), "url": url, "content_type": asset.content_type}
        )
    return sub, urls


@transaction.atomic
def finalize(user, sub):
    sub = (
        Submission.objects.select_for_update()
        .select_related("exercise__lesson__module__course")
        .get(pk=sub.pk)
    )
    require(sub.student_id == user.pk)
    if sub.status in ("accepted", "validating", "rejected"):
        return sub
    require(learns(user, sub.exercise.lesson.module.course))
    require(
        sub.group_id and Group.objects.filter(pk=sub.group_id, members=user).exists()
    )
    check_deadline(sub.exercise.lesson.module.course)
    if not sub.assets.exists():
        raise ValidationError("No files uploaded")
    sub.deadline_date = sub.exercise.lesson.module.course.end_date
    sub.status = "validating"
    sub.finalized_at = timezone.now()
    sub.save(update_fields=["status", "finalized_at", "deadline_date"])
    queue_job("submission", {"submission_id": sub.pk})
    return sub


def queue_job(kind, payload):
    job = Job.objects.create(kind=kind, payload=payload)
    from course.tasks import run_job

    def dispatch():
        try:
            run_job.delay(str(job.id))
        except Exception:
            # Durable job remains pending for the dispatcher; never lose acceptance state.
            import logging

            logging.getLogger(__name__).warning(
                "Broker unavailable; durable job awaits dispatcher"
            )

    transaction.on_commit(dispatch)
    return job


def validate_asset(asset):
    """Read exactly the checked bytes; never copy a mutable staging object after hashing it."""
    s3 = client(asset.category)
    b = bucket(asset.category)
    response = s3.get_object(Bucket=b, Key=asset.staging_key)
    if response["ContentLength"] != asset.size:
        raise ValidationError("Uploaded size does not match the manifest")
    digest = hashlib.sha256()
    total = 0
    with tempfile.TemporaryFile() as f:
        body = response["Body"]
        try:
            for chunk in body.iter_chunks(1024 * 1024):
                total += len(chunk)
                if total > asset.size:
                    raise ValidationError("File exceeds declared size")
                f.write(chunk)
                digest.update(chunk)
        finally:
            body.close()
        if total != asset.size:
            raise ValidationError("Upload is incomplete")
        f.seek(0)
        if asset.name.lower().endswith(".ipynb"):
            import nbformat

            try:
                nbformat.validate(nbformat.read(f, as_version=4))
            except Exception as exc:
                raise ValidationError("Invalid notebook document") from exc
        elif asset.name.lower().endswith((".png", ".jpg", ".jpeg")):
            from PIL import Image

            try:
                Image.open(f).verify()
            except Exception as exc:
                raise ValidationError("Invalid image") from exc
        f.seek(0)
        key = f"accepted/{asset.course_id or 'platform'}/{asset.submission_id or asset.ticket_id or 'assets'}/{asset.id}/{asset.name}"
        sha = digest.hexdigest()
        try:
            s3.put_object(
                Bucket=b,
                Key=key,
                Body=f,
                ContentType=asset.content_type,
                Metadata={"sha256": sha},
                IfNoneMatch="*",
            )
        except s3.exceptions.ClientError as exc:
            if exc.response["Error"]["Code"] not in ("PreconditionFailed", "412"):
                raise
            head = s3.head_object(Bucket=b, Key=key)
            if head.get("Metadata", {}).get("sha256") != sha:
                raise ValidationError("Immutable artifact conflict")
    asset.object_key = key
    asset.sha256 = sha
    asset.status = "accepted"
    asset.save(update_fields=["object_key", "sha256", "status"])
    return asset
