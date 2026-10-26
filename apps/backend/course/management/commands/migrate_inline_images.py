import json, os
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from course.models import Lesson
from course.services.inline_images import legacy_sources, image_bytes, migrate_lesson


class Command(BaseCommand):
    help = "Inventory/convert legacy embedded/local lesson images with protected original HTML backups"

    def add_arguments(self, p):
        p.add_argument("--output", required=True)
        p.add_argument("--apply", action="store_true")
        p.add_argument("--backup-dir")

    def handle(self, *args, **o):
        if o["apply"] and not o["backup_dir"]:
            raise CommandError("--apply requires a persistent --backup-dir")
        report = []
        for lesson in Lesson.objects.select_related(
            "module__course", "module__instructor"
        ).iterator():
            sources = legacy_sources(lesson.lesson_content)
            if not sources:
                continue
            row = {"lesson": lesson.pk, "images": len(sources), "status": "planned"}
            try:
                for src in sources:
                    image_bytes(src)
                if o["apply"]:
                    row = migrate_lesson(lesson, o["backup_dir"])
            except Exception as exc:
                row.update(status="blocked", reason=type(exc).__name__)
            report.append(row)
        with os.fdopen(
            os.open(Path(o["output"]), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w"
        ) as f:
            json.dump(report, f, indent=2)
        if any(r["status"] == "blocked" for r in report):
            raise CommandError(
                "Some images require review; their original HTML was retained"
            )
        self.stdout.write(
            f"{len(report)} lessons inventoried; no external image URLs fetched"
        )
