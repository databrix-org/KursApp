# Shared TypeScript rules

Read the [root guide](../../AGENTS.md) first.

## Ownership and entry points
base.json.

## Contracts and invariants
Preserve strict checking, bundler resolution and no-emit. Databrix app/package paths have no src directory.

## Verification
pnpm typecheck.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
