# Container delivery

Read the [root guide](../AGENTS.md) first.

## Ownership and entry points
backend.Dockerfile, web.Dockerfile, nginx.conf, ../compose.yaml.

## Contracts and invariants
No secrets/legacy files in contexts. Non-root runtime and one-off migrations. Public ingress strips identity headers; trusted SSO integration requires a restricted path.

## Verification
docker compose config; docker compose build; scripts/container_rehearsal.py.
Run commands from the repository root; "backend course.tests" means the root-guide Django test command.

## Pitfalls
Do not interpret local verification as production/provider acceptance.
Update the feature matrix and handoff for workflow changes; keep this guide below 150 lines.
