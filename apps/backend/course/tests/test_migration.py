from django.test import TransactionTestCase
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.contrib.auth.hashers import make_password, check_password


class HistoricalMigrationTests(TransactionTestCase):
    def test_populated_upgrade_preserves_ids_hashes_scores_files(self):
        executor = MigrationExecutor(connection)
        executor.migrate([("course", "0026_alter_course_difficulty_level_and_more")])
        apps = executor.loader.project_state(
            [("course", "0026_alter_course_difficulty_level_and_more")]
        ).apps
        U = apps.get_model("course", "CustomUserModel")
        C = apps.get_model("course", "Course")
        M = apps.get_model("course", "Module")
        L = apps.get_model("course", "Lesson")
        E = apps.get_model("course", "Exercise")
        S = apps.get_model("course", "Submission")
        teacher = U.objects.create(
            username="oldteach",
            email="oldteach@example.invalid",
            first_name="Old",
            last_name="Teacher",
            is_instructor=True,
            password=make_password("historical-secret"),
        )
        student = U.objects.create(
            username="oldstudent",
            email="oldstudent@example.invalid",
            first_name="Old",
            last_name="Student",
        )
        c = C.objects.create(title="Historical", instructor=teacher)
        m = M.objects.create(course=c, instructor=teacher, title="Original", order=0)
        l = L.objects.create(module=m, title="Lesson", order=0)
        e = E.objects.create(
            lesson=l,
            file="exercise_files/original.ipynb",
            reference_solution="reference_solutions/original.ipynb",
        )
        OldEnrollment = apps.get_model("course", "Enrollment")
        OldGroup = apps.get_model("course", "Group")
        OldProgress = apps.get_model("course", "LessonProgress")
        OldFile = apps.get_model("course", "SubmissionFile")
        enrollment = OldEnrollment.objects.create(
            student=student, course=c, progress=50
        )
        group = OldGroup.objects.create(course=c, group_number=1)
        group.members.add(student)
        progress = OldProgress.objects.create(
            student=student, lesson=l, is_completed=True
        )
        ids = [
            S.objects.create(
                exercise=e, student=student, score=8, feedback="Original feedback"
            ).pk
            for _ in range(3)
        ]
        filename = f"exercise_submissions/group_{group.pk}/Original/work.ipynb"
        stored = OldFile.objects.create(
            submission_id=ids[0], file=filename, description="Original file"
        )
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
            from course.models import (
                CustomUserModel,
                Submission,
                CourseStaff,
                GradeRevision,
            )

            self.assertTrue(
                check_password(
                    "historical-secret",
                    CustomUserModel.objects.get(pk=teacher.pk).password,
                )
            )
            self.assertEqual(
                Submission.objects.filter(
                    pk__in=ids, score=8, feedback="Original feedback"
                ).count(),
                3,
            )
            self.assertEqual(
                len(
                    set(
                        Submission.objects.filter(pk__in=ids).values_list(
                            "idempotency_key", flat=True
                        )
                    )
                ),
                3,
            )
            self.assertTrue(
                CourseStaff.objects.filter(course_id=c.pk, user_id=teacher.pk).exists()
            )
            from course.models import (
                Enrollment,
                LessonProgress,
                SubmissionFile,
                Exercise,
                TeamMembership,
            )

            self.assertEqual(Enrollment.objects.get(pk=enrollment.pk).progress, 50)
            self.assertTrue(LessonProgress.objects.get(pk=progress.pk).is_completed)
            self.assertEqual(
                SubmissionFile.objects.get(pk=stored.pk).file.name, filename
            )
            self.assertEqual(
                Exercise.objects.get(pk=e.pk).reference_solution.name,
                "reference_solutions/original.ipynb",
            )
            self.assertEqual(Submission.objects.get(pk=ids[0]).group_id, group.pk)
            self.assertEqual(
                TeamMembership.objects.get(enrollment_id=enrollment.pk).group_id,
                group.pk,
            )
            self.assertIsNone(Submission.objects.get(pk=ids[1]).group_id)
            self.assertEqual(
                GradeRevision.objects.filter(
                    submission_id__in=ids,
                    score=8,
                    feedback="Original feedback",
                    grader__isnull=True,
                    is_legacy_snapshot=True,
                ).count(),
                3,
            )
        finally:
            ex = MigrationExecutor(connection)
            ex.migrate(ex.loader.graph.leaf_nodes())
