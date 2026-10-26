# Shared shadcn design system

Read the [root guide](../../AGENTS.md) first.

## Ownership and entry points
components/ui, components/media.tsx, styles/globals.css, components.json.

## Contracts and invariants
Keep primitives/provider-neutral media here and feature business logic in web modules. Preserve upstream licenses and workspace imports; no src.

## Verification
pnpm --filter @repo/design-system typecheck.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Progress must forward its value to the Radix root for screen-reader announcements.
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
