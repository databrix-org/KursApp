# Private object storage

Read the [root guide](../../../../../AGENTS.md) first.

## Ownership and entry points
client.py.

## Contracts and invariants
Only staging keys receive signed browser PUTs. Worker-only accepted writes require conditional create. Four bucket roles, no public access. Real endpoint tests are separate from moto.

## Verification
backend course.tests.test_storage; scripts/storage_acceptance.py.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
