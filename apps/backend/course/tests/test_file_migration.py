import tempfile
from pathlib import Path
from django.test import override_settings
from moto import mock_aws
from course.models import Asset
from course.services.migration import inventory, copy_record
from course.integrations.storage.client import client, bucket
from .base import PlatformCase


@override_settings(
    S3_ENDPOINT_URL=None, S3_PUBLIC_ENDPOINT_URL=None, S3_REGION="us-east-1"
)
class FileMigrationTests(PlatformCase):
    def test_copy_reconciles_without_deleting_originals_and_is_resumable(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(LEGACY_DATA_ROOT=Path(directory)),
            mock_aws(),
        ):
            path = Path(directory) / "starter.csv"
            path.write_bytes(b"a,b\n1,2\n")
            (Path(directory) / "orphan.txt").write_text("working file")
            self.exercise.file = "starter.csv"
            self.exercise.save()
            client("course").create_bucket(Bucket=bucket("course"))
            manifest = inventory()
            self.assertIn("orphan.txt", manifest["unreferenced_files"])
            row = manifest["files"][0]
            pk = copy_record(row)
            self.assertEqual(copy_record(row), pk)
            self.assertTrue(path.exists())
            self.assertEqual(Asset.objects.get(pk=pk).sha256, row["sha256"])
            path.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                copy_record(row)

    def test_shared_historical_paths_are_blocked_without_review(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(LEGACY_DATA_ROOT=Path(directory)),
        ):
            (Path(directory) / "shared.ipynb").write_bytes(b"{}")
            self.exercise.file = "shared.ipynb"
            self.exercise.reference_solution = "shared.ipynb"
            self.exercise.save()
            manifest = inventory()
            self.assertTrue(all(row["requires_review"] for row in manifest["files"]))
            with self.assertRaises(ValueError):
                copy_record(manifest["files"][0])
