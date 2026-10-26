#!/usr/bin/env bash
# Read-only checks. Works with macOS Bash 3.2 and without Node or Python.
set -u
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$repo_dir/scripts/docker-cli.sh"
mode=docker
if (( $# > 1 )); then printf "Use one option: --docker or --development.\n" >&2; exit 2; fi
case "${1:-}" in
  ''|--docker) ;;
  --development) mode=development ;;
  -h|--help) printf 'Usage: bash scripts/preflight.sh [--docker|--development]\nDocker mode checks run prerequisites; development also requires Node, pnpm and uv.\n'; exit 0 ;;
  *) printf 'Unknown option. Use --docker or --development.\n' >&2; exit 2 ;;
esac
failures=0
ok() { printf '[OK] %s\n' "$*"; }
info() { printf '[INFO] %s\n' "$*"; }
fail() { printf '[FAIL] %s\n' "$*"; failures=$((failures + 1)); }
host_problem() { if [[ "$mode" == development ]]; then fail "$*"; else info "$* (optional for Docker-only use)"; fi; }
at_least() {
  local actual="${1#v}" expected="$2" am an ap em en ep
  IFS=. read -r am an ap <<< "${actual%%-*}"
  IFS=. read -r em en ep <<< "$expected"
  [[ "$am" =~ ^[0-9]+$ && "${an:-0}" =~ ^[0-9]+$ && "${ap:-0}" =~ ^[0-9]+$ ]] || return 1
  (( am > em || (am == em && an > en) || (am == em && an == en && ap >= ep) ))
}

printf 'Databrix preflight (%s)\n\n' "$mode"
if command -v git >/dev/null 2>&1 && git --version >/dev/null 2>&1; then ok "$(git --version)"; else fail 'Git unavailable. Install: https://git-scm.com/downloads'; fi
if databrix_find_docker; then
  if [[ -n "$DATABRIX_DOCKER_DISCOVERED" ]]; then info "Docker found outside PATH: $DATABRIX_DOCKER_DISCOVERED (used for this script only)"; fi
  ok "$(docker --version)"
  compose_version="$(docker compose version --short 2>/dev/null || true)"
  if at_least "$compose_version" 2.24.4; then ok "Docker Compose $compose_version"; else fail 'Docker Compose 2.24.4+ required. Install/update Docker Desktop: https://docs.docker.com/get-started/get-docker/'; fi
  server_version="$(docker version --format '{{.Server.Version}}' 2>/dev/null || true)"
  if [[ -z "$server_version" ]]; then fail 'Docker is installed but its engine is unavailable. Start Docker Desktop (macOS: open -a Docker), or start Docker Engine on Linux.'
  elif at_least "$server_version" 24.0.0; then ok "Docker engine $server_version is reachable"
  else fail 'Docker engine 24+ required; update Docker Desktop/Engine.'; fi
else
  fail 'Docker is missing. Install Docker Desktop/Engine with Compose: https://docs.docker.com/get-started/get-docker/'
fi

printf '\nHost development tools\n'
if command -v node >/dev/null 2>&1; then
  node_version="$(node --version 2>/dev/null || true)"
  if at_least "$node_version" 22.18.0; then ok "Node $node_version"; else host_problem 'Node 22.18+ required for host development. Install Node 22 or newer supported LTS: https://nodejs.org/en/download'; fi
else host_problem 'Node is missing. Install: https://nodejs.org/en/download'; fi
expected_pnpm="$(sed -n 's/.*"packageManager":[[:space:]]*"pnpm@\([^"]*\)".*/\1/p' "$repo_dir/package.json")"
if command -v pnpm >/dev/null 2>&1; then
  pnpm_version="$(pnpm --version 2>/dev/null || true)"
  if [[ "$pnpm_version" == "$expected_pnpm" ]]; then ok "pnpm $pnpm_version (repository version)"; else host_problem "pnpm $expected_pnpm required; found $pnpm_version. Run: npm install --global pnpm@$expected_pnpm"; fi
else host_problem "pnpm is missing. After installing Node run: npm install --global pnpm@$expected_pnpm"; fi
if command -v uv >/dev/null 2>&1; then
  uv_output="$(uv --version 2>/dev/null || true)"; uv_version="${uv_output#uv }"; uv_version="${uv_version%% *}"
  if at_least "$uv_version" 0.9.5; then ok "uv $uv_version"; else host_problem 'uv 0.9.5+ required. Install/update: https://docs.astral.sh/uv/getting-started/installation/'; fi
else host_problem 'uv is missing. Install: https://docs.astral.sh/uv/getting-started/installation/'; fi
if command -v python3 >/dev/null 2>&1; then info "System $(python3 --version 2>&1); backend Python is selected separately by uv"; else info 'System Python is not required; Docker or uv supplies backend Python'; fi
if [[ -x "$repo_dir/apps/backend/.venv/bin/python" ]]; then
  backend_python="$("$repo_dir/apps/backend/.venv/bin/python" --version 2>&1)"
  backend_version="${backend_python#Python }"
  if at_least "$backend_version" 3.11.0 && ! at_least "$backend_version" 3.14.0; then ok "Backend $backend_python"; else host_problem 'Backend requires Python 3.11–3.13. Recreate its environment using uv sync --project apps/backend --python 3.11 --frozen'; fi
else info 'Backend environment not created yet. For host development: uv sync --project apps/backend --python 3.11 --frozen'; fi

printf '\nLocal configuration\n'
if [[ -f "$repo_dir/.env" ]]; then
  ok '.env exists (values are not printed)'
  if command -v docker >/dev/null 2>&1 && [[ -n "${compose_version:-}" ]]; then
    if docker compose --project-directory "$repo_dir" -f "$repo_dir/compose.yaml" config --quiet >/dev/null 2>&1; then ok 'Compose configuration is valid'; else fail 'Compose configuration is invalid. Diagnose privately with: docker compose config --quiet'; fi
  fi
else info '.env is missing; bash scripts/local.sh setup will create it from .env.example'; fi
if command -v lsof >/dev/null 2>&1; then
  for port in 8080 9000 9001; do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then info "Default port $port is occupied; Databrix may already be running. Check: bash scripts/local.sh status"; else ok "Default port $port is available"; fi
  done
else info 'Port availability check skipped (lsof not installed); Docker will report binding conflicts'; fi
printf '\n'
if (( failures > 0 )); then printf 'Preflight failed: %s required check(s). Fix the FAIL items and rerun.\n' "$failures" >&2; exit 1; fi
printf 'Preflight passed. Nothing was installed or changed.\n'
if [[ "$mode" == docker ]]; then printf 'First run: bash scripts/local.sh setup\n'; else printf 'Next: follow docs/runbooks/development.md\n'; fi
