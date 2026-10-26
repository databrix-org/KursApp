# Generated API contract

Read the [root guide](../../AGENTS.md) first.

## Ownership and entry points
openapi.yaml, schema.d.ts, index.ts.

## Contracts and invariants
Regenerate schema/types from Django. Never hand-edit generated schema.d.ts. Browser helpers keep same-origin cookies/CSRF and never persist signed URLs.

## Verification
pnpm api:generate; pnpm --filter @repo/api-client typecheck.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
