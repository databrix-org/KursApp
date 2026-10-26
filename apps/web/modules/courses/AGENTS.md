# Courses feature

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
catalog.tsx, overview.tsx.

## Contracts and invariants
Catalog and outlines preserve enrollment/course boundaries. Publication and eligibility remain server decisions.

## Verification
pnpm typecheck; pnpm test; pnpm test:e2e.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
