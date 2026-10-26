# Databrix implementation handoff

## Implemented

- No-src pnpm/Turborepo workspace; Next.js 16 interface and shared official shadcn primitives.
- Compass-inspired curriculum/sidebar/breadcrumb/TOC layout; original Compass reference is unchanged.
- Django remains persistence/auth/policy owner; preserved app label and all historical migrations.
- Multi-course staff/enrollment, trusted SSO callback, invitation-only local accounts and verified login.
- Course/lesson/module authoring, Quill 2 formats/private inline images, progress, teams, support, admin and announcements.
- Staged private uploads, immutable checked acceptance, idempotent finalization, durable worker jobs.
- Submission roster/material/scale/deadline snapshots, exact-artifact previews/comparison, grade revision history.
- Explicit legacy grade baselines retain original scores/feedback without inventing a grader or grading time.
- Four private bucket responsibilities, private videos, migration inventory/copy/checksum reconciliation.
- Backed-up conversion of embedded/local lesson images; blocked unsafe saves prevent silent image loss.
- Production application images, local durable PostgreSQL/Redis/MinIO, same-origin unprivileged proxy.
- Scoped agent guides and automated Markdown/link/coverage/symlink/no-src checks.

## Verified locally

Verified on 2026-10-26 in the local checkout/isolated Docker environment:

| Check | Result |
| --- | --- |
| Backend regression suite | 39 passed on SQLite; 39 passed on PostgreSQL 17 |
| Frontend checks | TypeScript, lint, 3 unit tests passed |
| Browser journeys | 7 passed: learning, localization, submissions, authoring/images, grades, admin, mobile, MP4 |
| Accessibility | Axe checks passed on login, administration and accepted-receipt pages; progress value exposed |
| Production application images | Both multi-stage images built and served successfully as non-root processes |
| Storage acceptance | Signed PUT/GET, private access, CORS, ranges, conditional writes, checksums, version recovery passed on local MinIO |
| Persistence/recovery | Recreated PostgreSQL/Redis/MinIO/apps; fresh PostgreSQL restore and full referenced-object reconciliation passed |
| Record reconciliation | Fingerprints include all course models and stable durable-job identity/payload data |
| Legacy upgrade | IDs, password hashes, enrollment/progress, file references, team evidence and grade baselines preserved in populated fixture |
| Route rollout/rollback | Per-course switch and legacy reading rollback passed |
| Original source preservation | 155 archive/migration files compared byte-for-byte with the original revision |
| Documentation | 40 owned Markdown files pass line/link/guide/symlink/no-src checks |

Browser tests create demo records; this evidence does not establish real deployment reconciliation or provider readiness.

## Blocked before production rollout

- Restore and reconcile the actual deployment database and media, including ignored/untracked files.
- Complete selected real object endpoint acceptance, private policies, retention/version recovery and restore timing.
- Configure/verify institutional gateway, identity mappings, SMTP and DHBW external-account provisioning.
- Obtain instructor sign-off on imported course content and every relevant feature-parity row.
- Activate pilot courses and record an observed, schema-compatible rollback rehearsal.
- Automatic Hub provisioning and cross-cloud transfer remain outside this release.

## Known operational boundaries

- SSO public headers are stripped; a trusted restricted gateway path must be configured before enabling SSO.
- Local demo credentials/storage are development-only and must never be reused in production.
- Legacy destructive upload routes stay blocked; rollback supports legacy reading with new safe submission/grading.
- Historical shared file paths may already have lost old versions; migration flags rather than invents them.
- Git media is not evidence of the actual production media inventory.
- Course deletion with academic/assets references is intentionally blocked; unpublish instead.
- No production or provider state was changed by this local implementation.

## Local onboarding

The root README now starts with `bash scripts/preflight.sh` and `bash scripts/local.sh setup`.
Docker-only use needs Git and Docker; Node/pnpm/uv are for host development.
`local.sh start/stop/status/logs/rebuild` cover subsequent use; setup preserves an existing `.env`.
Both real preflight modes and Bash syntax pass; nine isolated CLI-fixture tests cover missing tools,
macOS CLI discovery outside PATH, stopped engines, configuration preservation, command ordering,
and refusal of remote/non-local initialization.
Real preflight/status also pass with a minimal macOS PATH that excludes Docker; Desktop CLI discovery succeeds.
These helper tests do not claim a fresh real-container initialization; CI now exercises that path.

## Continue here

Read [root guide](../../AGENTS.md), [architecture](../architecture/overview.md), [parity](../reference/feature-parity.md),
and [rollout](../runbooks/rollout.md), then the scoped AGENTS.md for the affected module.
Use the retained migrations and generated API contract; do not re-create the database or substitute browser-only permissions.

## Final verification record

Reproduce with the root README, `pnpm verify`, Django `test course`, `pnpm test:e2e`,
`scripts/storage_acceptance.py`, and `scripts/container_rehearsal.py --confirm-local-demo`.
The storage acceptance command requires an explicit isolated test bucket; never run rehearsals against production.
Implementation is proposed on `vintotan/databrix-platform` for review against `main`.
Remaining rollout work is tracked in [GitHub issue #2](https://github.com/databrix-org/KursApp/issues/2)
and its seven scoped child issues; merging the implementation does not complete provider/production acceptance.
