# Interface translation

Read the [root guide](../../AGENTS.md) first.

## Ownership and entry points
index.ts.

## Contracts and invariants
Both dictionaries must expose identical keys. Keep authored course HTML in its original language. Routes use explicit de/en locale.

## Verification
pnpm --filter @repo/i18n typecheck; pnpm test.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
