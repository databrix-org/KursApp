# Databrix

Databrix teaches data science through reading, private videos, team exercises, and notebook assessment.
Students learn and submit work; instructors author courses and grade snapshots; administrators manage accounts.

## First local run — start here

**Use Docker to run the complete application. You do not need Node, pnpm, Python, or uv installed for this path.**
Use a Bash terminal on macOS/Linux, or WSL/Git Bash on Windows. Run all commands from this repository's root folder.

### 1. Install and start the required tools

| Tool | Needed for | Installation |
| --- | --- | --- |
| Git | Getting/updating this repository | [Install Git](https://git-scm.com/downloads) |
| Docker Desktop, or Docker Engine 24+ with Compose 2.24.4+ | Running the complete local stack | [Install Docker](https://docs.docker.com/get-started/get-docker/) |

Start Docker Desktop and wait until its engine is running. On macOS you can start it with `open -a Docker`.
If you have not downloaded the repository yet, clone it first, then open a terminal in the checkout.

### 2. Check your computer

```bash
bash scripts/preflight.sh
```

This checks Git, Docker/Compose versions, the running Docker engine, local configuration, and default ports.
It also reports Node, pnpm, uv, and Python. Missing host development tools are informational in Docker mode.
Fix any `[FAIL]` items and rerun the check. The preflight does not install tools, start services, or change files.
On macOS, both helpers also find Docker in its standard Desktop/user CLI locations when it is absent from `PATH`.
This applies only inside the scripts; your terminal configuration stays unchanged.
Ports 8080, 9000, and 9001 must be available, or already belong to this Databrix stack.

### 3. Initialize and start everything

```bash
bash scripts/local.sh setup
```

The script checks prerequisites, creates `.env` from [.env.example](.env.example) only if absent, builds the images,
starts PostgreSQL/Redis/local storage, applies migrations, creates private buckets, adds demo accounts/media, and starts the app.
It preserves an existing `.env` and waits for application health checks. The first build can take several minutes.
This helper requires the default local database/storage and development settings; it refuses remote Docker hosts and non-local configurations.

### 4. Open the application

Open [Databrix](http://localhost:8080/en/login), or [the German interface](http://localhost:8080/de/login).
Sign in as `student@example.invalid`, `instructor@example.invalid`, or `admin@example.invalid`.
The initial password is the `DEMO_PASSWORD` value in your `.env`. Existing account passwords are not reset by rerunning setup.
The [local storage console](http://localhost:9001) uses the local S3 credentials in `.env`.
Local email is printed by the worker's console email backend; production requires an email service.
Notebook launch stays pending until an operator configures the DHBW destination and confirms student access.

## Commands after the first run

| Command | When to use it |
| --- | --- |
| `bash scripts/local.sh start` | Start again after stopping the stack or restarting your computer |
| `bash scripts/local.sh stop` | Stop services; keep database records and stored files |
| `bash scripts/local.sh status` | Check which services are running and healthy |
| `bash scripts/local.sh logs` | Inspect recent logs; add `web backend` to limit services |
| `bash scripts/local.sh rebuild` | Rebuild after code changes and apply migrations; keeps data and does not reseed |
| `bash scripts/preflight.sh --development` | Check the additional tools needed for host development |

The helpers never remove durable volumes. `docker compose down` also retains them; `down -v` deletes them.
If setup encounters existing non-demo accounts, use `rebuild` for upgrades; demo seeding intentionally refuses that database.
[Detailed/manual setup and troubleshooting](docs/runbooks/development.md) explains each individual Docker command.

## Editing code and running checks

The optional host tools are [Node 22.18+](https://nodejs.org/en/download), [pnpm 10.33.0](https://pnpm.io/installation),
and [uv 0.9.5+](https://docs.astral.sh/uv/getting-started/installation/) for Python development.
After installing Node, install the repository's pnpm version with `npm install --global pnpm@10.33.0`.
uv can supply Python 3.11; a separate system Python installation is unnecessary.

```bash
bash scripts/preflight.sh --development
pnpm install --frozen-lockfile
uv sync --project apps/backend --python 3.11 --frozen
pnpm verify
uv run --project apps/backend python apps/backend/manage.py test course
```

The [development guide](docs/runbooks/development.md) shows frontend hot reload and browser tests.
`pnpm dev` starts only the frontend; it does not initialize the database, worker, or storage.
For convenience, pnpm also exposes `preflight`, `preflight:dev`, and `local:setup/start/rebuild/stop/status/logs` aliases.

## Two independent environments

**This repository runs the course platform:** Next.js provides the interface; Django owns authentication, permissions,
and PostgreSQL records for courses, enrollment, progress, submissions, official grades, feedback, and grading history.
Private object storage holds videos, materials, accepted notebooks, reference solutions, and support images.

**DHBW runs the notebook environment separately.** Its Hub database manages Jupyter operations; persistent workspace folders hold live work.
Databrix neither accesses that database nor mounts those folders. Students export saved work and upload it here.
Accepted submissions are independent snapshots; later lab edits do not change them. Application images contain no durable student data.

## Repository map

```text
apps/web/                    Next.js App Router and feature modules; no src directory
apps/backend/                Django, domain services, API and preserved migrations
packages/design-system/      Shared shadcn components, tokens and media
packages/api-client/         OpenAPI schema, generated TypeScript contracts and client
packages/i18n/                German/English interface dictionaries
packages/typescript-config/  Shared TypeScript configuration
deploy/                      Application Dockerfiles and reverse proxy
docs/                        Architecture, runbooks, parity matrix and handoff
legacy/                      Preserved original files and reference implementation
scripts/                     Preflight, local setup, documentation and recovery checks
```

## Read next

- [Architecture and ownership](docs/architecture/overview.md)
- [Development and manual setup](docs/runbooks/development.md) · [Production Docker deployment](docs/runbooks/deployment.md)
- [Database migration](docs/runbooks/database.md) · [Private storage and submissions](docs/runbooks/storage.md)
- [Authentication and notebook access](docs/runbooks/authentication.md)
- [Backup/recovery](docs/runbooks/recovery.md) · [Rollout/rollback](docs/runbooks/rollout.md) · [Troubleshooting](docs/runbooks/troubleshooting.md)
- [Feature parity](docs/reference/feature-parity.md) · [Implementation and verification handoff](docs/handoff/current-state.md)

For an AI agent, start with [AGENTS.md](AGENTS.md), then the nearest scoped guide and handoff.
Each application, package, and feature module has a canonical AGENTS.md and a CLAUDE.md symlink.
Run `pnpm docs:check` after documentation edits; every owned Markdown file must stay below 150 lines.
