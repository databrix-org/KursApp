# Grading feature

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
notebook.tsx.

## Contracts and invariants
Preview accepted snapshots safely and compare source cells. Render notebook text as text; never execute outputs/scripts.

## Verification
pnpm typecheck; pnpm test; pnpm test:e2e.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
