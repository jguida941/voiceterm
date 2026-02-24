#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE=0
STATUS_ONLY=0

usage() {
  cat <<'EOF'
Usage: sync_external_integrations.sh [--remote] [--status-only]

Options:
  --remote       Update integrations to latest remote-tracked commits.
  --status-only  Print current submodule status only.
  -h, --help     Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      REMOTE=1
      ;;
    --status-only)
      STATUS_ONLY=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option '$1'" >&2
      usage
      exit 2
      ;;
  esac
  shift
done

MODULES=(
  "integrations/code-link-ide"
  "integrations/ci-cd-hub"
)

cd "$ROOT_DIR"

if [[ "$STATUS_ONLY" -eq 1 ]]; then
  git submodule status -- "${MODULES[@]}"
  exit 0
fi

git submodule sync -- "${MODULES[@]}"
if [[ "$REMOTE" -eq 1 ]]; then
  git submodule update --init --remote -- "${MODULES[@]}"
else
  git submodule update --init -- "${MODULES[@]}"
fi

echo "== External integration pins =="
for module in "${MODULES[@]}"; do
  sha="$(git -C "$module" rev-parse HEAD)"
  branch="$(git -C "$module" rev-parse --abbrev-ref HEAD || true)"
  url="$(git config --file .gitmodules --get "submodule.${module}.url" || true)"
  echo "- $module"
  echo "  sha: $sha"
  echo "  branch: ${branch:-detached}"
  echo "  url: ${url:-unknown}"
done

echo "== Submodule status =="
git submodule status -- "${MODULES[@]}"
