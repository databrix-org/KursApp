# Teams feature

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
screen.tsx.

## Contracts and invariants
Django enforces enrollment, capacity and one team per course. Do not infer historical roster from current team state.

## Verification
pnpm typecheck; pnpm test; pnpm test:e2e.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
