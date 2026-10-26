# Django service

Read the [root guide](../../AGENTS.md) first.

## Ownership and entry points
config/settings.py, config/urls.py, course.

## Contracts and invariants
Preserve course app label and migrations. Runtime secrets only. Production PostgreSQL; no Hub DB access.

## Verification
uv run --project apps/backend python apps/backend/manage.py test course.tests.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
