# Regression evidence

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
base.py, test_authorization.py, test_storage.py, test_migration.py.

## Contracts and invariants
Use isolated test databases/moto. Populated migration tests restore the latest migration state. Never connect tests to production URLs.

## Verification
uv run --project apps/backend python apps/backend/manage.py test course.tests.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
