# Authorization

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
access.py, legacy.py.

## Contracts and invariants
Scope teachers to course/module. Historical roster controls peer submission access; reference solutions are staff-only. Keep legacy paths gated.

## Verification
backend course.tests.test_authorization and test_storage.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
