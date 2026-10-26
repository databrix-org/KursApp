import base64, io, tempfile
from pathlib import Path
from django.test import override_settings
from django.core.exceptions import ValidationError
from moto import mock_aws
from PIL import Image
from course.models import Asset
from course.services.inline_images import migrate_lesson
from course.integrations.storage.client import client, bucket
from .base import PlatformCase


@override_settings(
    S3_ENDPOINT_URL=None, S3_PUBLIC_ENDPOINT_URL=None, S3_REGION="us-east-1"
)
class InlineImageTests(PlatformCase):
    def test_embedded_image_conversion_preserves_source_and_private_access(self):
        image = io.BytesIO()
        Image.new("RGB", (2, 2), "blue").save(image, format="PNG")
        original = (
            '<h2>Original</h2><p><img alt="Diagram" src="data:image/png;base64,'
            + base64.b64encode(image.getvalue()).decode()
            + '"></p>'
        )
        self.lesson.lesson_content = original
        self.lesson.save()
        with tempfile.TemporaryDirectory() as directory, mock_aws():
            client("course").create_bucket(Bucket=bucket("course"))
            report = migrate_lesson(self.lesson, directory)
            self.lesson.refresh_from_db()
            self.assertEqual(Path(directory, report["backup"]).read_text(), original)
            asset = Asset.objects.get(pk=report["assets"][0])
            self.assertEqual(asset.status, "accepted")
            self.assertIn(
                f"/api/v1/assets/{asset.pk}/inline/", self.lesson.lesson_content
            )
            self.assertNotIn("data:image", self.lesson.lesson_content)
            self.assertEqual(
                self.api.get(f"/api/v1/assets/{asset.pk}/inline/").status_code, 302
            )
            self.api.force_authenticate(self.other)
            self.assertEqual(
                self.api.get(f"/api/v1/assets/{asset.pk}/inline/").status_code, 403
            )

    def test_unsupported_image_is_not_silently_removed(self):
        original = '<p><img src="data:image/svg+xml;base64,PHN2Zz4="/></p>'
        self.lesson.lesson_content = original
        self.lesson.save()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValidationError):
                migrate_lesson(self.lesson, directory)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.lesson_content, original)

    def test_authoring_requires_conversion_before_editing_legacy_image_html(self):
        self.lesson.lesson_content = (
            '<p><img src="data:image/png;base64,aGVsbG8="/></p>'
        )
        self.lesson.save()
        self.api.force_authenticate(self.teacher)
        response = self.api.patch(
            f"/api/v1/lessons/{self.lesson.pk}/",
            {"lesson_content": "<p>Edited</p>"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.lesson.refresh_from_db()
        self.assertIn("data:image", self.lesson.lesson_content)
