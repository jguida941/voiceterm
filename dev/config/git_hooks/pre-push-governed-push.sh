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

STARTUP_SUMMARY="$(python3 dev/scripts/devctl.py startup-context --format summary 2>/dev/null || true)"
NEXT_COMMAND="$(printf '%s\n' "$STARTUP_SUMMARY" | awk -F= '/^next=/{sub(/^next=/,""); print; exit}')"
ACTION="$(printf '%s\n' "$STARTUP_SUMMARY" | awk -F= '/^action=/{sub(/^action=/,""); print; exit}')"
REASON="$(printf '%s\n' "$STARTUP_SUMMARY" | awk -F= '/^reason=/{sub(/^reason=/,""); print; exit}')"

echo "[pre-push hook] Raw git push is blocked in this repo." >&2
if [ -n "$ACTION" ] || [ -n "$REASON" ]; then
    echo "[pre-push hook] Typed state: ${ACTION:-unknown} / ${REASON:-unknown}" >&2
fi
if [ -n "$NEXT_COMMAND" ]; then
    echo "[pre-push hook] Next typed step: $NEXT_COMMAND" >&2
fi
echo "[pre-push hook] Governed path: python3 dev/scripts/devctl.py push --execute" >&2
exit 1
