# Troubleshooting

| Symptom | Inspect | Safe next step |
| --- | --- | --- |
| Login rejected | CSRF cookie/origin, verified EmailAddress, active user | Verify email or correct origin; do not bypass CSRF |
| Institutional login unavailable | SSO_ENABLED, gateway, secret/nonce | Complete restricted gateway integration |
| Existing SSO user gets 409 | Identity mapping | Operator-reviewed link_identity; preserve user ID |
| Lab access pending | Enrollment NotebookAccess and provider account | Operator confirms access after DHBW setup |
| Lab URL rejected | HTTPS URL and NOTEBOOK_ALLOWED_HOSTS | Correct the exact configured host |
| Browser upload fails | CORS, public endpoint, content type, URL expiry | Request a new staging URL; retain original export |
| Submission validating | Worker, broker, Job row, storage health | Restore dependencies and redispatch durable jobs |
| Submission rejected | Receipt rejection reason | Fix file/size/deadline issue; start a new submission |
| Duplicate finalize | Same receipt/submission ID | Refresh; operation is idempotent |
| Video stops | Signed URL expiry or missing range support | Retry playback URL; test provider range delivery |
| Delete returns 409 | Academic/artifact references | Unpublish/retire content while retaining history |
| Migration blocks shared path | Historical overlapping file references | Investigate originals/backups; document uncertainty |
| Restore reports missing object | Backup/version reference and checksum | Recover object; never erase a grade to hide the error |
| Course 403 | Publication, enrollment, module teacher | Fix course-specific membership, not global privileges |
| Docker web unhealthy | Backend logs and standalone server | Check runtime BACKEND_URL and build assets |
| Terminal says Docker is missing but Desktop is installed | CLI path versus running engine | Rerun the updated preflight; macOS helpers discover standard Desktop/user CLI locations |

Useful local diagnostics:

If manual `docker` commands are unavailable on macOS but Docker Desktop is installed, run
`export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"` in that terminal first.
The Bash helpers perform this discovery themselves; they do not edit shell startup files.

```bash
docker compose ps
docker compose logs --tail=100 backend worker dispatcher web proxy
docker compose exec backend python manage.py check
docker compose exec backend python manage.py showmigrations
```

Email logs in local development contain sensitive invitation/reset links. Do not publish them.
Production logs must exclude request secrets, presigned object URLs, notebook contents, and SSO identity headers.
A green health endpoint proves liveness; it does not prove provider access, successful migrations, or completed jobs.

For an exhausted, individually reviewed failed job, use
`python manage.py dispatch_jobs --job-id JOB_UUID --retry-exhausted` after resolving the provider failure.
