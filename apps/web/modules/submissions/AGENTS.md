# Submissions feature

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
upload.tsx, screens.tsx.

## Contracts and invariants
Keep an idempotency UUID/receipt across retry. New manifests require a new submission. Only accepted exact artifacts can be graded.

## Verification
pnpm typecheck; pnpm test; pnpm test:e2e.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
