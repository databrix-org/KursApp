# Docker production deployment

See the root README for the complete local quickstart.
Production runs on the course-platform cloud; deploy JupyterHub/workspaces independently on DHBW infrastructure.

| Service | Image/state | Responsibility |
| --- | --- | --- |
| web | Next standalone, stateless | German/English interface and SSR |
| backend | Django/Gunicorn, stateless | API, auth, policies, assessment records |
| worker | Same backend image | Validate/accept files, deliver email |
| dispatcher | Same backend image | Recover durable jobs after broker/worker failures |
| redis | Persistent append-only volume | Broker delivery |
| postgres | Durable volume or external service | Databrix records |
| proxy | Unprivileged nginx | Same-origin routing; trusted ingress integration |
| storage (local profile) | Persistent MinIO volume | Local rehearsal only |

## Production configuration

1. Build `deploy/web.Dockerfile` and `deploy/backend.Dockerfile`; push immutable version/digest tags to your registry.
2. Supply runtime `.env`/orchestrator secrets. Never bake credentials or student data into an image.
3. Set `DATABRIX_ENV=production`, a unique 50+ character `DJANGO_SECRET_KEY`, exact ALLOWED_HOSTS/PUBLIC_ORIGIN,
   HTTPS CSRF_TRUSTED_ORIGINS, PostgreSQL DATABASE_URL, and private HTTPS S3 settings.
4. Configure SMTP and a verified sender; demo console email is not a production delivery service.
5. Configure notebook HTTPS host allowlist and course/team destinations independently of the learning platform.
6. Place nginx behind a TLS ingress that strips client-supplied forwarded/identity headers and restricts direct backend access.
7. Configure certificates at that ingress and persist/renew them there. Backend secure cookies and HTTPS redirects are enabled.
8. Run Django `check --deploy`, database migrations, and object endpoint acceptance before enabling traffic.
9. Start backend/worker/dispatcher/web/proxy; verify health, a login, private media, and an accepted submission.
10. Run the staged restore/preservation rehearsal and review the [release gates](rollout.md).

Default Compose exposes nginx on loopback only. Public ingress/TLS is a deployment-specific configuration.
Do not enable the `local` object-storage profile in production.
The base Compose includes PostgreSQL/Redis for a single-host deployment. With external services use
`docker compose -f compose.yaml -f compose.external.yaml up -d` (Compose 2.24.4+).
The override requires external DATABASE_URL/CELERY_BROKER_URL, removes local dependencies, and excludes their services.
Store Redis data on durable disks and isolate broker/database ports from public networks.

## Images and process lifecycle

Dependencies are frozen by pnpm-lock.yaml and uv.lock; Docker builds use frozen installs.
Both application images have separate build/runtime stages and run as UID/GID 10001.
The runtime filesystem is read-only with temporary `/tmp`; compose init forwards termination signals.
Gunicorn/Celery/Next receive SIGTERM with graceful stop periods; migrations never run in every replica's entrypoint.
Static Django admin/legacy files are collected during image build and served by WhiteNoise.
Next standalone includes workspace packages, public assets, and `.next/static`.
Object storage, backups, local databases, `.env`, and legacy content are excluded by `.dockerignore`.

## One-off operations

```bash
docker compose run --rm backend python manage.py check --deploy
docker compose run --rm backend python manage.py migrate --noinput
docker compose exec backend python manage.py createsuperuser
```

Create a production administrator through this command, then invite local users from the admin interface.
Do not run setup_dev_data against production; it refuses non-development settings.
When using Docker secrets files, export/read them through the orchestrator's secret-to-environment facility.
Do not commit a populated `.env` or registry credentials.

The worker spools checked bytes to an owned disk volume, avoiding RAM-backed storage for large uploads.
Temporary bytes are discarded after each operation; PostgreSQL and private accepted objects remain authoritative.
