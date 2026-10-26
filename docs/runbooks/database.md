# Database and historical migration

Django alone connects to `DATABASE_URL`. Next.js and DHBW receive no Databrix database credentials.
Production requires PostgreSQL; Compose provides PostgreSQL 17 with a durable named volume.
Set an external PostgreSQL URL, with verified TLS where required, to use managed infrastructure.
Apply migrations once per release as a separate operation, before starting incompatible application versions.

```bash
docker compose run --rm backend python manage.py showmigrations
docker compose run --rm backend python manage.py migrate --plan
docker compose run --rm backend python manage.py migrate --noinput
```

## Existing deployment rehearsal

1. Capture a PostgreSQL custom-format backup and a protected snapshot of the real media/filesystem roots.
2. Restore into an isolated staging PostgreSQL database; never use production credentials for rehearsal.
3. Set `DATABASE_URL` to that staging database and mount the legacy file snapshot read-only.
4. Apply migrations, retaining the existing `course` app label and original migration records.
5. Compare IDs/counts for users, courses, modules, lessons, enrollment, progress, submissions, scores, and feedback.
6. Check existing password hashes byte-for-byte and test institutional identity mapping with operators.
7. Review uncertain historical teams and shared file paths; do not infer peers from current membership.
8. Inventory/copy files using the [storage migration](storage.md) commands, including inline images; reconcile checksums.
9. Record evidence, unresolved rows, and the approved pilot course list in the release manifest.

## Migration semantics

- The one-course-per-instructor and one-enrollment-per-user constraints become course-specific relationships.
- Course owners/module teachers are backfilled as course staff.
- Existing submission UUID keys are generated per row, avoiding duplicate default UUIDs.
- Legacy accepted submissions keep their original IDs, timestamps, score, feedback, and file references.
- Historical team attribution uses an unambiguous group identifier in recorded file paths only.
- Historical rosters conservatively include the submitter; uncertain associations remain operator review items.
- New submissions capture their exercise version, material asset IDs/checksums, scoring scale, and roster.
- Grading appends GradeRevision rows; previous official values are retained in those revisions.
- 0031 retains preexisting grades/feedback as explicit legacy snapshots with an unknown grader.
  Their `created_at` records snapshot creation, not an invented historical grading time.

## Reversibility

Rollback application routing before attempting a schema rollback.
Do not reverse migrations after multi-course records/new grades exist without a reviewed conversion.
A pre-release database restore discards newer writes unless reconciled; freeze mutations before any restore.
See [recovery](recovery.md) and [rollout](rollout.md).

0030 snapshots the deadline applied at finalization so later course date edits do not invalidate queued work.
Instructor assessment reads/grading/statistics retain the legacy post-course-end restriction; superusers are exempt.

Use a restricted application database role in production and a separately controlled migration role.
