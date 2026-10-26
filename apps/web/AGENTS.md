# Next.js interface

Read the [root guide](../../AGENTS.md) first.

## Ownership and entry points
app/[locale], modules, lib/server.ts, lib/hooks.ts.

## Contracts and invariants
Consume Django API; never own database/auth policy. Use shared design-system components. Preserve no-src and both UI locales.

## Verification
pnpm --filter @repo/web typecheck; pnpm --filter @repo/web test; pnpm test:e2e.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
