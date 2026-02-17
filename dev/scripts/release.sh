#!/usr/bin/env bash
#
# Legacy compatibility adapter.
# Canonical path: python3 dev/scripts/devctl.py release --version <version>
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

VERSION="${1:-}"
if [[ "$VERSION" == "--help" || "$VERSION" == "-h" ]]; then
    echo "Usage: ./dev/scripts/release.sh <version> [--homebrew] [--yes] [--allow-ci] [--dry-run]"
    echo "Canonical: python3 dev/scripts/devctl.py release --version <version>"
    exit 0
fi
if [[ -z "$VERSION" ]]; then
    echo "Usage: ./dev/scripts/release.sh <version> [--homebrew] [--yes] [--allow-ci] [--dry-run]"
    echo "Canonical: python3 dev/scripts/devctl.py release --version <version>"
    exit 1
fi

shift || true
exec python3 "$REPO_ROOT/dev/scripts/devctl.py" release --version "$VERSION" "$@"
