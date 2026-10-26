# Verification and operations

Read the [root guide](../AGENTS.md) first.

## Ownership and entry points
preflight.sh, local.sh, docker-cli.sh, check_docs.py, storage_acceptance.py, container_rehearsal.py.

## Contracts and invariants
Preflight must remain read-only and work without Node/Python. Local helpers must preserve .env/volumes and reject remote Docker/non-local data services. Never default destructive rehearsals to production. Use isolated test resources and retain databases/volumes. Do not print credentials or signed URLs.
Both helpers share macOS Docker CLI discovery; prefer PATH, then known installation locations, without editing shell profiles.

## Verification
pnpm docs:check; pnpm test:setup; bash -n scripts/preflight.sh scripts/local.sh scripts/docker-cli.sh; relevant local rehearsal.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
