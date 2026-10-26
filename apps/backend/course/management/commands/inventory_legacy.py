import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from course.services.migration import inventory


class Command(BaseCommand):
    help = "Read-only inventory of DB-referenced and unreferenced durable files"

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        path = Path(options["output"])
        path.parent.mkdir(parents=True, exist_ok=True)
        with os.fdopen(
            os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w"
        ) as f:
            json.dump(inventory(), f, indent=2)
        path.chmod(0o600)
        self.stdout.write(
            "Inventory written; inspect missing files, shared paths, and uncertain teams before copying"
        )
