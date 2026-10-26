# DHBW launch boundary

Read the [root guide](../../../../../AGENTS.md) first.

## Ownership and entry points
launch.py.

## Contracts and invariants
Require enrolled/staff access, operator confirmation, HTTPS and host allowlist. Do not provision Hub users or mount cross-cloud folders.

## Verification
backend authorization tests; provider/operator acceptance.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
