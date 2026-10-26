# External adapters

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
storage/client.py, notebooks/launch.py.

## Contracts and invariants
Providers do not own course records. Keep URLs/credentials runtime configured. Never print signed URLs, headers, or notebook content.

## Verification
backend storage/authorization tests.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
