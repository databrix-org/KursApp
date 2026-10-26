# Staged rollout and rollback

## Release gates

- Run backend authorization/storage/populated-migration tests and frontend type/lint/unit checks.
- Build both production images and run the browser workflow/accessibility/responsive suite.
- Restore the real staging database, migrate files, and reconcile IDs, identities, grades, feedback, and checksums.
- Resolve missing/shared historical files and uncertain teams; document irrecoverable old overwrites explicitly.
- Run storage acceptance against isolated buckets on the selected real endpoint, including private policies and recovery.
- Confirm institutional gateway identity mapping and DHBW operator-managed external-user access.
- Test German/English, supported browsers, keyboard navigation, private video range/renewal, and screen readers.
- Recreate containers, restore PostgreSQL, recover object versions, and prove accepted notebooks stay unchanged.
- Have a course owner verify every applicable row in the [parity matrix](../reference/feature-parity.md).

Local tests cannot establish production permissions, SSO trust, existing deployment reconciliation, or DHBW behavior.
Record evidence and remaining blockers in the [handoff](../handoff/current-state.md).

## Incremental activation

1. Back up the deployment; retain image digests and a read-only legacy media snapshot.
2. Apply additive/backfilled migrations and import/reconcile private assets.
3. Start the new services with LEGACY_UI_ENABLED=true; leave courses' frontend_enabled=false.
4. Test the new routes with staff, without switching existing course entry links.
5. Enable frontend_enabled for one pilot course. Supported old course/lesson entry routes redirect to Next.js.
6. Compare pilot enrollment/progress/submissions and instructor grading against expected records.
7. Expand course-by-course only after parity and storage reconciliation succeed.
8. Retain legacy routes until the pilot observation period and rollback rehearsal are complete.

Direct new URLs remain available for staff testing; the course flag controls legacy entry-route switching.
Legacy destructive notebook submission/reference-file mutations are intentionally blocked even during rollback.
They cannot safely coexist with immutable private submissions; use the versioned new upload/grading workflows.

## Rollback

1. Pause mutations if assessment data or files are at risk; preserve all new accepted objects and grade revisions.
2. Disable the affected course's frontend_enabled flag to restore supported legacy reading entry routes.
3. Keep new submission/grading routes available until a compatible rollback upload path exists.
4. Revert web/backend images together to a schema-compatible release; do not reverse schema migrations blindly.
5. Reconcile writes made since the backup before considering a database restore.
6. Repeat authorization, receipt download, object checksum, and grade-history checks.

A full restore to a pre-migration database is a disaster-recovery operation requiring a write freeze and reconciliation.
Do not claim a lossless whole-platform rollback merely because an old read route can be selected.
