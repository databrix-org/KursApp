# Databrix contributor guide

Read the nearest nested AGENTS.md before changing an app, package, or module.

## Boundaries
- Django owns PostgreSQL, authentication, policies, grades, and submission metadata.
- Next.js consumes the versioned API. Never connect it directly to PostgreSQL.
- DHBW owns Jupyter servers, Hub database, kernels, and working folders.
- Accepted notebooks are private object-storage artifacts, never workspace mounts.
- Preserve existing model IDs, password hashes, migrations, files, and assessments.

## Structure
- `apps/web`: Next.js, root-level app/modules/lib; no src directories.
- `apps/backend`: Django, retained course app label and migrations.
- `packages/design-system`: canonical shadcn UI, tokens, and media components.
- `packages/api-client`: generated OpenAPI contracts and browser client.
- `legacy`: retained data/reference sources; excluded from application images.
- `docs/handoff/current-state.md`: implemented and verified state.

## Rules
- All Databrix-owned Markdown must be under 150 lines.
- CLAUDE.md is a symlink to the adjacent canonical AGENTS.md.
- Keep UI primitives in the shared design system.
- Never log credentials, full request headers, signed URLs, or notebook contents.
- Use scoped backend policies on every operation, including legacy endpoints.
- Object/database mutations are not atomic: use pending states and idempotent jobs.
- Never execute uploaded notebooks on the learning platform.
- No production changes or provider verification may be claimed from local tests.

## Checks
- `pnpm typecheck`, `pnpm lint`, `pnpm test`, `pnpm docs:check`.
- `uv run --project apps/backend python apps/backend/manage.py test course`.
- `docker compose config` and production image/container smoke checks.
- Update feature matrix, runbooks, and handoff when behavior changes.
