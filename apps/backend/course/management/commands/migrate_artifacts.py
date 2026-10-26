import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from course.services.migration import copy_record


class Command(BaseCommand):
    help = "Copy and verify inventory files into private storage; keep legacy originals and references"

    def add_arguments(self, parser):
        parser.add_argument("--manifest", required=True)
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--accept-reviewed-shared-paths", action="store_true")
        parser.add_argument("--report", required=True)

    def handle(self, *args, **o):
        manifest = json.loads(Path(o["manifest"]).read_text())
        report = []
        if manifest.get("format") != 1:
            raise CommandError("Unknown manifest version")
        for row in manifest["files"]:
            result = {"source": row["source"], "status": "planned"}
            if o["apply"]:
                try:
                    result.update(
                        status="verified",
                        asset_id=copy_record(row, o["accept_reviewed_shared_paths"]),
                    )
                except Exception as exc:
                    result.update(status="blocked", reason=type(exc).__name__)
            report.append(result)
        path = Path(o["report"])
        with os.fdopen(
            os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w"
        ) as f:
            json.dump(report, f, indent=2)
        path.chmod(0o600)
        if any(x["status"] == "blocked" for x in report):
            raise CommandError(
                "Some records require reconciliation; originals retained"
            )
        self.stdout.write(f"{len(report)} records processed; original files retained")
