"""Explicit, backed-up conversion of legacy embedded/local images. No external URL fetches."""

import base64, hashlib, html, io, os, re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from course.models import Asset, Lesson
from course.services.submissions import new_asset, validate_asset
from course.integrations.storage.client import client, bucket


class Images(HTMLParser):
    def __init__(self, value):
        super().__init__()
        self.sources = []
        self.feed(value or "")

    def handle_starttag(self, tag, attrs):
        src = dict(attrs).get("src", "")
        if tag == "img" and (src.startswith("data:") or src.startswith("/data/")):
            self.sources.append(src)


def legacy_sources(value):
    return list(dict.fromkeys(Images(value).sources))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def image_bytes(src):
    if src.startswith("data:"):
        match = re.fullmatch(r"data:image/(png|jpeg);base64,([A-Za-z0-9+/=\s]+)", src)
        if not match or len(src) > 48 * 1024 * 1024:
            raise ValidationError("Unsupported embedded image; review original HTML")
        try:
            data = base64.b64decode(re.sub(r"\s", "", match[2]), validate=True)
        except ValueError:
            raise ValidationError("Invalid embedded image encoding")
        name = "embedded." + ("jpg" if match[1] == "jpeg" else "png")
    else:
        root = Path(settings.LEGACY_DATA_ROOT).resolve()
        path = (root / unquote(urlparse(src).path.removeprefix("/data/"))).resolve()
        if (
            not path.is_relative_to(root)
            or not path.is_file()
            or path.stat().st_size > 32 * 1024 * 1024
        ):
            raise ValidationError("Missing, unsafe or oversized local image")
        name = path.name
        data = path.read_bytes()
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            raise ValidationError(
                "Only raster PNG/JPEG images are migrated automatically"
            )
    from PIL import Image

    try:
        image = Image.open(io.BytesIO(data))
        if image.format not in ("PNG", "JPEG"):
            raise ValueError("Unsupported format")
        image.verify()
    except Exception as exc:
        raise ValidationError("Invalid raster image") from exc
    return name, data


def migrate_lesson(lesson, backup_dir):
    original = lesson.lesson_content or ""
    before = digest(original.encode())
    sources = legacy_sources(original)
    if not sources:
        return {"lesson": lesson.pk, "status": "unchanged"}
    # Preserve the exact source before any data/object mutation.
    backup = Path(backup_dir)
    backup.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = backup / f"lesson-{lesson.pk}-{before}.html"
    try:
        with os.fdopen(
            os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w"
        ) as f:
            f.write(original)
    except FileExistsError:
        if digest(target.read_bytes()) != before:
            raise ValidationError("Backup conflict")
    replacements = {}
    ids = []
    for src in sources:
        name, data = image_bytes(src)
        key = f"inline:{lesson.pk}:{digest(src.encode())}"
        asset = Asset.objects.filter(legacy_source=key).first()
        if not asset:
            asset, _ = new_asset(
                lesson.module.instructor,
                name,
                len(data),
                "course",
                course=lesson.module.course,
                lesson=lesson,
            )
            asset.legacy_source = key
            asset.save(update_fields=["legacy_source"])
        if asset.status != "accepted":
            client("course").put_object(
                Bucket=bucket("course"),
                Key=asset.staging_key,
                Body=data,
                ContentType=asset.content_type,
            )
            validate_asset(asset)
        if asset.sha256 != digest(data):
            raise ValidationError("Image source changed after migration initiation")
        replacements[src] = f"/api/v1/assets/{asset.pk}/inline/"
        ids.append(str(asset.pk))
    pattern = re.compile(r"(<img\b[^>]*?\bsrc\s*=\s*)([\"\'])(.*?)\2", re.I | re.S)
    updated = pattern.sub(
        lambda m: m[1] + m[2] + replacements.get(html.unescape(m[3]), m[3]) + m[2],
        original,
    )
    if legacy_sources(updated):
        raise ValidationError(
            "Unsupported HTML attribute form; original retained for review"
        )
    with transaction.atomic():
        current = Lesson.objects.select_for_update().get(pk=lesson.pk)
        if digest((current.lesson_content or "").encode()) != before:
            raise ValidationError("Lesson changed concurrently; inventory again")
        current.lesson_content = updated
        current.save(update_fields=["lesson_content"])
    return {
        "lesson": lesson.pk,
        "status": "verified",
        "before_sha256": before,
        "after_sha256": digest(updated.encode()),
        "backup": target.name,
        "assets": ids,
    }
