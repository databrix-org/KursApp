# Private storage and submission lifecycle

Configure `S3_ENDPOINT_URL`, `S3_PUBLIC_ENDPOINT_URL`, `S3_REGION`, bucket names, and scoped credentials at runtime.
The public endpoint must be reachable by browsers and support the same bucket/key namespace.
Production requires HTTPS. No assumption is made that DHBW provides object storage.
The adapter uses Signature V4, path-style addressing, presigned PUT/GET, streaming GET, and conditional PUT.

| Bucket setting | Writer | Content | Reader authorization |
| --- | --- | --- | --- |
| S3_BUCKET_COURSE | Course editor stages; worker accepts | MP4, images, teaching materials | Enrolled/course staff |
| S3_BUCKET_NOTEBOOKS | Student stages; worker accepts | Notebook snapshots and associated files | Historical roster/assigned teacher |
| S3_BUCKET_ASSESSMENT | Teacher stages; worker accepts | Reference notebooks | Course staff only |
| S3_BUCKET_SUPPORT | Ticket owner stages; worker accepts | PNG/JPEG images | Ticket owner/scoped staff |

Per-category `S3_COURSE_ACCESS_KEY_ID` / `S3_COURSE_SECRET_ACCESS_KEY` (and NOTEBOOKS/ASSESSMENT/SUPPORT variants)
override common credentials. Grant only required bucket/prefix operations; public access must be disabled.
The application requires PutObject/GetObject/HeadObject, not DeleteObject.
Enable versioning and independent retention/backups; deny unconditional accepted-prefix overwrites where supported.
Do not attach automatic expiry to accepted artifacts referenced by assessment records.
A retired course/reference asset remains stored; it is removed from current teaching lists.

## Upload protocol

1. Initiate with file names/sizes and an idempotency UUID; Django checks course/team/deadline.
2. PUT each file to its unique signed staging URL (10-minute lifetime, exact content type).
3. Finalize once all uploads finish. Django records finalized_at and a durable job.
4. Worker streams/checks size and SHA-256, validates notebooks/images, and writes the checked bytes to accepted keys.
5. Accepted keys use If-None-Match `*`; they are never issued as browser upload destinations.
6. Worker changes the submission to accepted and timestamps the receipt after every artifact succeeds.
7. Instructor access and grading require accepted status. Pending/invalid work cannot receive an official grade.

Missing objects/storage outages leave recoverable jobs and visible pending/validating state.
Invalid content/size rejects the submission. Students start a fresh submission to change the manifest.
Repeated finalize does not create another accepted record; staging overwrites cannot alter the accepted snapshot.
DHBW edits after export never modify accepted objects.
Allowed extensions and limits are centralized in `course/services/submissions.py` (2 GiB/file, 64 MiB/notebook, 20 files/submission).
Notebook previews never execute code; MP4 delivery uses signed object GET and supports provider byte ranges.

## Endpoint acceptance

Use the local S3 emulator in backend tests; use Compose MinIO for the durable local rehearsal.
Before production, run the storage acceptance script against the selected service's isolated test buckets.
Verify private ACLs/policy, CORS, signed PUT/GET, conditional overwrite rejection, ranges, versioning, and recovery.
Configure CORS only for the platform origin: PUT/GET/HEAD, Content-Type/Range headers, exposed ETag/Content-Range.
Local `bootstrap_storage` creates test buckets/versioning and configures supported bucket CORS.
MinIO uses the explicit service-level origins in Compose. Bootstrap refuses production execution.
Signed URLs are bearer credentials: do not put them in analytics, durable records, or shared logs.

## Legacy file migration

Mount a protected copy of the actual deployment's files as `LEGACY_DATA_ROOT`, read-only.
Commands below run inside the backend environment; use unique private report filenames.

```bash
python manage.py inventory_legacy --output /tmp/inventory.json
python manage.py migrate_artifacts --manifest /tmp/inventory.json --report /tmp/dry-run.json
python manage.py migrate_artifacts --manifest /tmp/inventory.json --apply --report /tmp/copy-report.json
python manage.py reconcile_artifacts --output /tmp/reconciliation.json
```

Inventory includes referenced checksums, missing/unsafe paths, unreferenced files, and uncertain team associations.
Copies are resumable by unique source-record provenance; remote bytes are rehashed before references are accepted.
The old FileFields and originals remain for audit/rollback. Do not delete originals until full reconciliation.
Shared historical paths are blocked because old submissions may already have overwritten each other.
Only after investigation may an operator use `--accept-reviewed-shared-paths`; document unrecoverable history explicitly.
Unreferenced live workspace files are inventoried, never silently promoted to accepted submissions.

## Legacy inline images

The original Quill editor could embed base64 images or link local `/data/` pictures.
Inventory and convert these before activating a migrated course. New editor image uploads use the private course bucket.

```bash
python manage.py migrate_inline_images --output /tmp/inline-inventory.json
python manage.py migrate_inline_images --apply --backup-dir /persistent-backups/inline --output /tmp/inline-copy.json
```

The backup directory must be operator-controlled persistent storage, separate from application images.
Original HTML is retained with restrictive permissions before accepted image objects replace only image source URLs.
The manifest records original/new HTML checksums and asset IDs. Unsupported/missing images stay unchanged for review.
No remote URLs are fetched. Editing a lesson with unconverted inline images is blocked to prevent silent loss.
PNG/JPEG images use an authorized same-origin endpoint that redirects to short-lived private object URLs.
