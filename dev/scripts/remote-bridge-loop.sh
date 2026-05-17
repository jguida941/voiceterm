#!/usr/bin/env bash
#
# Compatibility wrapper for the repo-owned remote-control lifecycle.
#
# Usage:
#   ./dev/scripts/remote-bridge-loop.sh [remote-control start flags]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

exec python3 dev/scripts/devctl.py remote-control start \
  --launcher-source remote-bridge-loop \
  --entrypoint legacy_remote_bridge_loop \
  "$@"
