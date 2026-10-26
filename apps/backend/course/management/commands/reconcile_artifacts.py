import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from course.models import Asset
from course.services.migration import checksum
from course.integrations.storage.client import client, bucket


class Command(BaseCommand):
    help = "Verify every referenced accepted/retired object against its stored SHA-256"

    def add_arguments(self, p):
        p.add_argument("--output", required=True)

    def handle(self, *args, **o):
        report = []
        for a in Asset.objects.filter(status__in=["accepted", "retired"]).iterator():
            try:
                body = client(a.category).get_object(
                    Bucket=bucket(a.category), Key=a.object_key
                )["Body"]
                try:
                    valid = checksum(body) == a.sha256
                finally:
                    body.close()
                report.append({"asset": str(a.pk), "verified": valid})
            except Exception:
                report.append({"asset": str(a.pk), "verified": False})
        p = Path(o["output"])
        with os.fdopen(
            os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w"
        ) as f:
            json.dump(report, f, indent=2)
        p.chmod(0o600)
        if any(not r["verified"] for r in report):
            raise CommandError(
                "Artifact recovery/reconciliation required; no records modified"
            )
        self.stdout.write(f"{len(report)} artifacts verified")
