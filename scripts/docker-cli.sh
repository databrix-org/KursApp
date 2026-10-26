#!/usr/bin/env bash
# Shared CLI discovery; changes PATH only inside the calling script process.
databrix_find_docker() {
  DATABRIX_DOCKER_DISCOVERED=''
  if command -v docker >/dev/null 2>&1; then return 0; fi
  [[ "$(uname -s 2>/dev/null)" == Darwin ]] || return 1
  local candidate directory
  local candidates=()
  if [[ -n "${HOME:-}" ]]; then candidates+=("$HOME/.docker/bin/docker"); fi
  candidates+=(
    /Applications/Docker.app/Contents/Resources/bin/docker
    /usr/local/bin/docker
    /opt/homebrew/bin/docker
  )
  for candidate in "${candidates[@]}"; do
    if [[ -x "$candidate" ]]; then
      directory="${candidate%/*}"
      export PATH="$directory:$PATH"
      DATABRIX_DOCKER_DISCOVERED="$candidate"
      return 0
    fi
  done
  return 1
}
