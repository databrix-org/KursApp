# Local setup and development

Use the [root README](../../README.md) for the recommended first run. Run commands from the checkout root.
`bash scripts/preflight.sh` needs no Node/Python installation and checks the Docker path.
`bash scripts/preflight.sh --development` additionally requires Node 22.18+, pnpm 10.33.0, and uv 0.9.5+.
Missing tools are reported with installation links; neither mode installs software or changes your configuration.

## Complete local application

```bash
bash scripts/local.sh setup    # First run, including migrations and demo data
bash scripts/local.sh status   # Service status and health
bash scripts/local.sh stop     # Stop; retain all durable data
bash scripts/local.sh start    # Subsequent starts; no demo reseeding
bash scripts/local.sh rebuild  # After code changes; rebuild and migrate without reseeding
```

The helpers use the checked-in Compose file, preserve an existing `.env`, and reject remote Docker endpoints.
Setup/rebuild validate the resolved Django configuration before touching database/storage records.
They require development settings, database `databrix` on service `postgres`, internal storage `http://storage:9000`,
and a localhost public origin. For external infrastructure, follow the [deployment guide](deployment.md).
If an existing local database contains non-demo accounts, use `rebuild`; setup's demo seeding refuses to alter it.

## Equivalent manual first-run commands

These are the individual steps performed by `setup`. Use the default local example for a fresh demo environment.
Create `.env` only if you do not already have one; keep existing secrets/configuration unchanged.

```bash
bash scripts/preflight.sh
# Only on a fresh checkout without .env:
cp .env.example .env
docker compose --profile local build backend web
docker compose --profile local up -d --wait postgres redis storage
docker compose run --rm backend python manage.py migrate --noinput
docker compose run --rm backend python manage.py bootstrap_storage
docker compose run --rm backend python manage.py setup_dev_data
docker compose run --rm backend python manage.py setup_dev_media
docker compose --profile local up -d --wait
```

Open [the application](http://localhost:8080/en/login). The root README explains demo accounts and passwords.
First builds download images/dependencies; later starts reuse them. `stop` and `down` retain volumes; `down -v` deletes data.
If Docker cannot connect, start Docker Desktop first (macOS: `open -a Docker`).
If a port is occupied, check `bash scripts/local.sh status` before stopping anything; the existing listener may be Databrix.
For failures, run `bash scripts/local.sh logs web backend worker` and consult [troubleshooting](troubleshooting.md).

## Frontend hot reload while editing

Install Node and the repository's pnpm version using the links in the README. Then:

```bash
pnpm install --frozen-lockfile
bash scripts/local.sh start
BACKEND_URL=http://localhost:8080 pnpm dev
```

Open [the frontend development server](http://localhost:3000/en/login).
Next.js proxies API requests to the Docker stack on port 8080. Django, worker, database, and storage stay together in that stack.
Changing backend code requires `bash scripts/local.sh rebuild`; the production images do not mount live source folders.
`pnpm dev` alone starts only Next.js and cannot provide the complete application.

## Backend tools and checks

Install uv using the README's official installation link; it supplies the requested compatible Python runtime.
The documentation and setup-test scripts also use that runtime, so system Python is unnecessary.

```bash
uv sync --project apps/backend --python 3.11 --frozen
bash scripts/preflight.sh --development
pnpm verify
uv run --project apps/backend python apps/backend/manage.py test course
uv run --project apps/backend python apps/backend/manage.py makemigrations --check --dry-run
pnpm api:generate
```

Backend tests use isolated test databases and mocked S3. Host commands default to a local SQLite development database.
Host processes do not automatically read Compose's `.env`; configure explicit environment variables when targeting another database.
The complete learning/submission workflow uses the shared Docker services described above.

Browser tests require the initialized local stack and demo accounts:

```bash
pnpm --filter @repo/web exec playwright install chromium
pnpm test:e2e
```

These tests create demo submissions/tickets and edit demo content; never target production.
They handle existing demo completion state, so no reset script is required.
See the [handoff](../handoff/current-state.md) for locally verified results and remaining provider gates.

## Adding functionality

Read the scoped AGENTS.md before editing. Add Django policies/services before exposing mutations.
Keep shared UI primitives in `packages/design-system` and feature composition in `apps/web/modules`.
Add interface translations in both languages; authored course content stays in its original language.
After serializer changes, run `pnpm api:generate` and commit the generated contracts together.
Update feature parity, handoff, and guide coverage. Owned apps/packages must not introduce a `src` directory.
