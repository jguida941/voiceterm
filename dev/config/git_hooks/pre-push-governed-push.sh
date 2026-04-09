#!/usr/bin/env bash
# devctl-install-git-hooks: managed hook for review-snapshot refresh
#
# Blocks raw `git push` and forces publication through the governed
# `python3 dev/scripts/devctl.py push --execute` path. The only allowed bypass
# is the internal env set by `devctl push` for its own nested `git push`.
#
# Install: `python3 dev/scripts/devctl.py install-git-hooks`
# Uninstall: `python3 dev/scripts/devctl.py install-git-hooks --uninstall`
# Check status: `python3 dev/scripts/devctl.py install-git-hooks --check`

set -eu

if [ "${DEVCTL_ALLOW_GOVERNED_GIT_PUSH:-}" = "1" ]; then
    exit 0
fi

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$REPO_ROOT" ]; then
    echo "[pre-push hook] Unable to resolve repo root; raw git push is blocked." >&2
    exit 1
fi
cd "$REPO_ROOT"

if ! python3 dev/scripts/devctl.py --help >/dev/null 2>&1; then
    echo "[pre-push hook] devctl is unavailable in this clone; raw git push is blocked." >&2
    exit 1
fi

echo "[pre-push hook] Raw git push is blocked in this repo." >&2
echo "[pre-push hook] Run: python3 dev/scripts/devctl.py push --execute" >&2
exit 1
