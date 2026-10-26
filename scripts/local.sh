#!/usr/bin/env bash
# Local demo operations only. Never sources .env as executable shell code.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
command_name="${1:-help}"
if (( $# > 0 )); then shift; fi
usage() {
  cat <<'HELP'
Usage: bash scripts/local.sh COMMAND
  setup    First run: check tools, create .env if absent, build, migrate, seed demo, start
  start    Start an already initialized local stack
  rebuild  Rebuild images, apply migrations and restart; does not reseed demo data
  stop     Stop local services while retaining containers, database and files
  status   Show services and health
  logs     Show recent logs (optional service names, e.g. logs web backend)
HELP
}
case "$command_name" in setup|start|rebuild|stop|status|logs) ;; help|-h|--help) usage; exit 0 ;; *) usage >&2; exit 2 ;; esac
if [[ "$command_name" != logs ]] && (( $# > 0 )); then usage >&2; exit 2; fi
source "$repo_dir/scripts/docker-cli.sh"
if ! databrix_find_docker; then printf 'Docker CLI unavailable in PATH or standard macOS locations. Run: bash scripts/preflight.sh\n' >&2; exit 1; fi
if [[ -n "$DATABRIX_DOCKER_DISCOVERED" ]]; then printf 'Using Docker outside PATH: %s (this script only)\n' "$DATABRIX_DOCKER_DISCOVERED"; fi
# Do not let a local convenience script operate on a remote Docker host.
if [[ -n "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" ]]; then endpoint="$DOCKER_HOST"; else endpoint="$(docker context inspect --format '{{(index .Endpoints "docker").Host}}' 2>/dev/null)"; fi
case "$endpoint" in unix://*|npipe://*|tcp://localhost:*|tcp://127.0.0.1:*|tcp://\[::1\]:*) ;; *) printf 'Refusing a remote Docker endpoint. Select your local Docker Desktop/Engine context first.\n' >&2; exit 1 ;; esac
compose() { docker compose --project-directory "$repo_dir" --env-file "$repo_dir/.env" -f "$repo_dir/compose.yaml" --profile local "$@"; }
require_env() { if [[ ! -f .env ]]; then printf 'No .env found. First run: bash scripts/local.sh setup\n' >&2; exit 1; fi; }
local_guard() {
  compose run --rm --no-deps -T backend python -c 'from django.conf import settings as s; from urllib.parse import urlparse; d=s.DATABASES["default"]; valid=s.DEBUG and d.get("HOST")=="postgres" and d.get("NAME")=="databrix" and s.S3_ENDPOINT_URL=="http://storage:9000" and urlparse(s.PUBLIC_ORIGIN).hostname in ("localhost","127.0.0.1"); raise SystemExit(0 if valid else "Refusing non-local configuration. This helper requires development mode and the default local database/storage. Use the production runbook for other deployments.")'
}
start_stack() { compose up -d --wait --wait-timeout 180; printf '\nDatabrix: http://localhost:8080/en/login\nDemo accounts and initial password: see README.md and DEMO_PASSWORD in your .env.\n'; }
case "$command_name" in
  setup)
    bash scripts/preflight.sh --docker
    if [[ ! -e .env && ! -L .env ]]; then (umask 077; set -o noclobber; cat .env.example > .env); printf 'Created .env from the local example.\n'; else printf 'Keeping your existing .env unchanged.\n'; fi
    compose config --quiet
    printf 'Building application images; the first build downloads dependencies and can take several minutes.\n'
    compose build backend web
    local_guard
    compose up -d --wait --wait-timeout 180 postgres redis storage
    compose run --rm -T backend python manage.py migrate --noinput
    compose run --rm -T backend python manage.py bootstrap_storage
    compose run --rm -T backend python manage.py setup_dev_data
    compose run --rm -T backend python manage.py setup_dev_media
    start_stack
    ;;
  start)
    bash scripts/preflight.sh --docker; require_env
    if ! docker image inspect databrix/backend:local databrix/web:local >/dev/null 2>&1; then printf 'Local images missing. Run: bash scripts/local.sh setup\n' >&2; exit 1; fi
    local_guard; start_stack
    ;;
  rebuild)
    bash scripts/preflight.sh --docker; require_env
    compose build backend web; local_guard
    compose up -d --wait --wait-timeout 180 postgres redis storage
    compose run --rm -T backend python manage.py migrate --noinput
    start_stack
    ;;
  stop) require_env; compose stop ;;
  status) require_env; compose ps ;;
  logs) require_env; compose logs --tail=100 "$@" ;;
esac
