# Human and agent documentation

Read the [root guide](../AGENTS.md) first.

## Ownership and entry points
architecture, runbooks, reference, handoff.

## Contracts and invariants
Keep every owned Markdown below 150 lines. Separate implemented/local verified/external blocked status. Update parity and handoff with behavior changes.

## Verification
pnpm docs:check.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
