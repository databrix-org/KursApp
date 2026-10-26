# Feature preservation matrix

This is a reviewable inventory, not a claim that every historical production scenario has been verified.
The API/UI replacements are implemented; local automated evidence and remaining provider/manual gates are recorded separately.

| Existing capability | New owner/entry point | Verification |
| --- | --- | --- |
| Public homepage, explore, legal pages | web locale pages; original German legal copy retained | Browser public journey |
| Institutional account/session | Django accounts callback and Identity | Header isolation unit test; gateway acceptance pending |
| Local invitation, verification, reset | accounts API; auth module | CSRF/login tests; mail service acceptance pending |
| Profile names/roles/deactivation | profile/admin screens; accounts API | Browser admin; academic history test |
| Enrollment keys, multi-course | enrollment service; catalog/course views | Authorization and populated migration tests |
| Course publication, dates, difficulty | Course API; authoring settings | Browser/manual course-owner review |
| Modules, teacher assignment, ordering | Module API; authoring forms | Scoped API tests; owner review |
| Reading content, instructions and private inline images | sanitized HTML; Quill 2 authoring and backed-up inline-image conversion | XSS/unit and browser reading/authoring |
| Private videos | course assets; signed object GET | Range test against local store; real endpoint gate |
| Materials/starter notebooks | private course assets | Upload/download storage tests; legacy import rehearsal |
| Progress completion | idempotent lesson completion API | Browser learning journey |
| Teams and capacity | enrollment/TeamMembership services | Capacity/uniqueness/unauthorized join tests |
| Notebook image/destination | retained JupyterLabImage legacy metadata; course/team launch URL | No Hub deployment; operator/provider gate |
| Traditional exercises | Exercise API; file submission form | Backend manifest validation; instructor review |
| Notebook exercises | manual export + staged upload | Browser accepted receipt journey |
| Multiple submission history | Submission API and receipt views | Same-second/idempotency tests |
| Reference solutions | separate assessment bucket | Student read-denial test |
| Notebook preview/output/compare | safe preview; side-by-side cell source comparison | Unit/browser preview; instructor review |
| Official grades, passed state, feedback | grading service and append-only revisions | Score bounds/history/snapshot tests |
| Course/team statistics (mean, max, counts, members) | scoped statistics API/tab | Teacher scope test and owner review |
| Announcements/email | durable individual email jobs | Queue tests; SMTP acceptance pending |
| Support tickets/images/assignment | course-scoped ticket API/module | Support authorization tests; browser ticket journey |
| Database/file continuity | preserved app/migrations and copy manifest | Populated migration; real staging reconciliation pending |
| First local run and lifecycle | Bash preflight/setup/start/stop/status/logs/rebuild; macOS CLI discovery | Real prerequisite checks; 9 isolated helper tests; fresh CI setup pending |
| Docker durability/recovery | named volumes/external storage; reconciliation tools | Container rehearsal; selected provider restore gate |
| German/English and responsive UI | locale routing/shared shadcn | Dictionary/browser/mobile/a11y checks |

## Intentional boundary changes

- Databrix no longer copies starter files destructively into team workspaces.
- Uploads are explicit student exports, independent of the DHBW live filesystem.
- Accepted files cannot be overwritten through a reused student upload URL.
- Unrelated instructors cannot edit lessons/grade/read artifacts just because of a global role.
- Deactivating accounts preserves academic records; deleting referenced content is blocked.
- Unsafe legacy submission mutations are blocked while supported reading routes remain for staged rollout.
- Exact historical peers cannot be reconstructed when old records lack evidence; retain review items.

## Release review

A course owner must verify its existing videos, attachments, authored HTML/Quill formatting, deadlines,
traditional/notebook exercise settings, teacher assignments, team records, and historical feedback after import.
Compare row IDs/counts and file checksums using a restored copy of the actual deployment, not Git fixtures alone.
Record any capability gap and keep the course on its current entry route until that gap is resolved.

Instructor submission inspection, grading, and statistics retain the legacy post-course-end restriction.
Superusers remain exempt; students can see their own receipts before assessment opens.
