# Course domain

Read the [root guide](../../../AGENTS.md) first.

## Ownership and entry points
models.py, api, policies, services, tasks.py, migrations.

## Contracts and invariants
Do not cascade-delete assessment history. Local/user roles do not replace course/module permissions. Legacy data stays recoverable.

## Verification
uv run --project apps/backend python apps/backend/manage.py test course.tests.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
