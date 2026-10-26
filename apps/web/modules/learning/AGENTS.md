# Learning feature

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
lesson.tsx, content.tsx, assets.tsx.

## Contracts and invariants
Sanitize authored HTML; lesson completion is idempotent. Resolve private media URLs on demand. Never execute notebook code.

## Verification
pnpm typecheck; pnpm test; pnpm test:e2e.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
