# Authoring feature

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
screen.tsx, editor.tsx, assets.tsx.

## Contracts and invariants
Quill 2 content stays original language. Image embeds store stable authorized API URLs, never presigned URLs. Teacher edits are module-scoped; private asset acceptance is asynchronous.

## Verification
pnpm typecheck; pnpm test; pnpm test:e2e.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
