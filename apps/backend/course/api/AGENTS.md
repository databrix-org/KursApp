# REST boundary

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
urls.py, views.py, serializers.py, accounts.py, contracts.py.

## Contracts and invariants
Check shared policies on every read/mutation. Public unsafe auth endpoints still require CSRF. Regenerate OpenAPI/client after contract edits.

## Verification
pnpm api:generate; backend course.tests.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
