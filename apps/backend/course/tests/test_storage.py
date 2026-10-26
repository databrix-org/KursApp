import uuid, hashlib
from datetime import timedelta
from unittest.mock import patch
from django.test import override_settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from moto import mock_aws
import nbformat
from course.models import Asset, Submission, Job, Enrollment, Group
from course.services import submissions
from course.services.enrollment import join
from course.integrations.storage.client import client, bucket
from course.tasks import run_job
from .base import PlatformCase


@override_settings(
    S3_ENDPOINT_URL=None, S3_PUBLIC_ENDPOINT_URL=None, S3_REGION="us-east-1"
)
class StorageTests(PlatformCase):
    def setUp(self):
        super().setUp()
        self.mock = mock_aws()
        self.mock.start()
        self.addCleanup(self.mock.stop)
        for category in ["course", "notebooks", "assessment", "support"]:
            client(category).create_bucket(Bucket=bucket(category))
        self.bytes = nbformat.writes(
            nbformat.v4.new_notebook(
                cells=[
                    nbformat.v4.new_code_cell(
                        "print(1)",
                        outputs=[
                            nbformat.v4.new_output("stream", name="stdout", text="1\n")
                        ],
                    )
                ]
            )
        ).encode()

    def start(self, key=None, data=None):
        content = self.bytes if data is None else data
        sub, urls = submissions.initiate(
            self.student,
            self.exercise,
            [{"name": "work.ipynb", "size": len(content)}],
            key or uuid.uuid4(),
        )
        a = sub.assets.get()
        client("notebooks").put_object(
            Bucket=bucket("notebooks"), Key=a.staging_key, Body=content
        )
        return sub, a

    def accept(self, sub):
        submissions.finalize(self.student, sub)
        run_job.run(
            str(Job.objects.get(kind="submission", payload__submission_id=sub.pk).pk)
        )
        sub.refresh_from_db()

    def test_immutable_snapshot_and_idempotent_finalize(self):
        sub, a = self.start()
        self.accept(sub)
        self.assertEqual(sub.status, "accepted")
        submissions.finalize(self.student, sub)
        self.assertEqual(Job.objects.filter(kind="submission").count(), 1)
        a.refresh_from_db()
        self.assertNotEqual(a.staging_key, a.object_key)
        client("notebooks").put_object(
            Bucket=bucket("notebooks"), Key=a.staging_key, Body=b"changed workspace"
        )
        self.assertEqual(
            client("notebooks")
            .get_object(Bucket=bucket("notebooks"), Key=a.object_key)["Body"]
            .read(),
            self.bytes,
        )
        self.assertEqual(a.sha256, hashlib.sha256(self.bytes).hexdigest())

    def test_repeat_initiation_and_same_second_submissions(self):
        key = uuid.uuid4()
        sub, a = self.start(key)
        again, urls = submissions.initiate(
            self.student,
            self.exercise,
            [{"name": "work.ipynb", "size": len(self.bytes)}],
            key,
        )
        another, b = self.start()
        self.assertEqual(sub.pk, again.pk)
        self.assertNotEqual(a.staging_key, b.staging_key)

    def test_empty_invalid_manifest_and_notebook_rejected(self):
        for files in [
            [],
            [{}],
            [{"name": "x.txt", "size": 1}],
            [{"name": "x.ipynb", "size": 0}],
        ]:
            with self.assertRaises(ValidationError):
                submissions.initiate(self.student, self.exercise, files, uuid.uuid4())
        sub, a = self.start(data=b"not a notebook")
        self.accept(sub)
        self.assertEqual(sub.status, "rejected")
        self.assertFalse(Asset.objects.filter(pk=a.pk, status="accepted").exists())

    def test_partial_upload_rejected(self):
        sub, a = self.start()
        client("notebooks").put_object(
            Bucket=bucket("notebooks"), Key=a.staging_key, Body=b"partial"
        )
        self.accept(sub)
        self.assertEqual(sub.status, "rejected")

    def test_deadline_enforced_at_finalize_not_worker_processing(self):
        sub, a = self.start()
        self.course.end_date = timezone.localdate() - timedelta(days=1)
        self.course.save()
        with self.assertRaises(ValidationError):
            submissions.finalize(self.student, sub)
        self.course.end_date = timezone.localdate()
        self.course.save()
        submissions.finalize(self.student, sub)
        with patch(
            "course.tasks.check_deadline_date", wraps=submissions.check_deadline_date
        ) as check:
            run_job.run(str(Job.objects.get(kind="submission").pk))
            self.assertEqual(
                check.call_args.args[1], Submission.objects.get(pk=sub.pk).finalized_at
            )

    def test_other_team_cannot_download_and_reference_is_private(self):
        Enrollment.objects.create(student=self.other, course=self.course)
        join(self.other, Group.objects.create(course=self.course))
        sub, a = self.start()
        self.accept(sub)
        self.api.force_authenticate(self.other)
        self.assertEqual(
            self.api.get(f"/api/v1/assets/{a.pk}/download/").status_code, 403
        )
        ref = Asset.objects.create(
            owner=self.teacher,
            course=self.course,
            category="assessment",
            status="accepted",
            object_key="private",
            name="ref.ipynb",
        )
        self.api.force_authenticate(self.student)
        self.assertEqual(
            self.api.get(f"/api/v1/assets/{ref.pk}/download/").status_code, 403
        )

    def test_historical_team_snapshot_survives_membership_changes(self):
        Enrollment.objects.create(student=self.other, course=self.course)
        join(self.other, self.group)
        sub, a = self.start()
        self.accept(sub)
        self.group.members.remove(self.other)
        self.api.force_authenticate(self.other)
        self.assertEqual(
            self.api.get(f"/api/v1/submissions/{sub.pk}/").status_code, 200
        )
        self.assertEqual(sub.roster, [self.student.pk, self.other.pk])

    def test_storage_outage_preserves_state_and_grades(self):
        old = Submission.objects.create(
            exercise=self.exercise, student=self.student, score=9, feedback="Retain"
        )
        sub, a = self.start()
        submissions.finalize(self.student, sub)
        with patch(
            "course.tasks.validate_asset", side_effect=OSError("storage offline")
        ):
            with self.assertRaises(Exception):
                run_job.run(str(Job.objects.get(kind="submission").pk))
        sub.refresh_from_db()
        old.refresh_from_db()
        self.assertEqual(sub.status, "validating")
        self.assertEqual(old.score, 9)
        self.assertEqual(old.feedback, "Retain")
        self.assertEqual(Job.objects.get(kind="submission").status, "failed")

    def test_accepted_write_is_conditional_and_retry_safe(self):
        sub, a = self.start()
        submissions.validate_asset(a)
        key = a.object_key
        # A retry only accepts identical verified bytes.
        submissions.validate_asset(a)
        self.assertEqual(a.object_key, key)
        modified = self.bytes.replace(b"print(1)", b"print(2)")
        self.assertEqual(len(modified), len(self.bytes))
        client("notebooks").put_object(
            Bucket=bucket("notebooks"), Key=a.staging_key, Body=modified
        )
        with self.assertRaises(ValidationError):
            submissions.validate_asset(a)

    def test_material_manifest_and_grading_scale_are_snapshots(self):
        material = Asset.objects.create(
            course=self.course,
            lesson=self.lesson,
            owner=self.teacher,
            name="starter.ipynb",
            category="course",
            status="accepted",
            sha256="a" * 64,
        )
        sub, a = self.start()
        self.assertEqual(sub.material_manifest[0]["id"], str(material.pk))
        self.assertEqual(sub.maximum_points, 10)
        self.exercise.pass_points = 10
        self.exercise.maximum_points = 20
        self.exercise.save()
        self.accept(sub)
        from course.services.grading import grade

        grade(self.teacher, sub, 9)
        self.assertEqual(sub.grade_history.get().score, 9)
        sub.refresh_from_db()
        self.assertTrue(sub.passed)
