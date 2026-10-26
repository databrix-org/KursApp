# Business transactions

Read the [root guide](../../../../AGENTS.md) first.

## Ownership and entry points
enrollment.py, submissions.py, grading.py, migration.py, inline_images.py.

## Contracts and invariants
Lock membership/submission/grade mutations. Persist jobs before broker dispatch. Never execute notebooks, mutate accepted bytes, or delete migration originals.

## Verification
backend course.tests.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
