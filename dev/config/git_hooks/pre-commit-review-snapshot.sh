#!/usr/bin/env bash
# devctl-install-git-hooks: managed hook for review-snapshot refresh
#
# Blocks raw `git commit` when the typed commit_permission contract says
# implementation is not currently allowed. Projection refreshes deliberately
# do not run in pre-commit: this hook executes while git is preparing the
# index/tree for the user commit, so write/stage operations here can contend
# with the commit index and hide long-running projection work behind a quiet
# `git commit`. The post-commit hook owns the trailing ReviewSnapshot receipt
# after HEAD is stable.
#
# Install: `python3 dev/scripts/devctl.py install-git-hooks`
# Uninstall: `python3 dev/scripts/devctl.py install-git-hooks --uninstall`
# Check status: `python3 dev/scripts/devctl.py install-git-hooks --check`
#
# Environment overrides:
#   DEVCTL_REVIEW_SNAPSHOT_RECEIPT_COMMIT=1 skip the gate/refresh on the
#                                           snapshot-only receipt commit
#   DEVCTL_MANAGED_PROJECTION_RECEIPT_COMMIT=1
#                                           allow a repo-owned generated-surface
#                                           receipt only when completed-handoff
#                                           authority and staged-path checks pass
#
# Failure policy:
# - commit_permission failures are blocking. raw git commits must not bypass
#   the existing typed implementation-authority boundary.
# - ReviewSnapshot refresh failures are handled by the post-commit receipt
#   hook and the CI freshness guard, not by this pre-commit hook.

set -eu

# Resolve repo root reliably regardless of CWD at hook invocation time.
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$REPO_ROOT" ]; then
    exit 0
fi
cd "$REPO_ROOT"

DEVCTL_PYTHON="@DEVCTL_PYTHON@"
if [ ! -x "$DEVCTL_PYTHON" ]; then
    if command -v python3.11 >/dev/null 2>&1; then
        DEVCTL_PYTHON="$(command -v python3.11)"
    elif command -v python3 >/dev/null 2>&1; then
        DEVCTL_PYTHON="$(command -v python3)"
    else
        DEVCTL_PYTHON=""
    fi
fi

# Skip during rebase / merge / cherry-pick / bisect — running the refresh
# during those operations can confuse the commit tree that git is about
# to build. The guards will catch any stale state at CI push time.
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null || echo ".git")
for marker in \
    "$GIT_DIR/MERGE_HEAD" \
    "$GIT_DIR/CHERRY_PICK_HEAD" \
    "$GIT_DIR/REBASE_HEAD" \
    "$GIT_DIR/rebase-merge" \
    "$GIT_DIR/rebase-apply" \
    "$GIT_DIR/BISECT_LOG"; do
    if [ -e "$marker" ]; then
        exit 0
    fi
done

# Snapshot-only receipt commits are already governed by the post-commit path
# and must not re-enter the raw git commit gate.
if [ "${DEVCTL_REVIEW_SNAPSHOT_RECEIPT_COMMIT:-}" = "1" ]; then
    exit 0
fi

# Governed `devctl commit` marks the underlying `git commit` invocation with a
# transient config flag so the raw-commit gate can distinguish the repo-owned
# pipeline from an ungoverned shell/editor commit.
if [ "${DEVCTL_GOVERNED_COMMIT:-}" != "1" ] && [ "$(git config --bool --get devctl.governed-commit 2>/dev/null || true)" != "true" ]; then
    if [ -z "$DEVCTL_PYTHON" ]; then
        echo "[pre-commit hook] A compatible Python interpreter is required to evaluate commit_permission; raw git commit is blocked." >&2
        exit 1
    fi

    if ! PYTHONDONTWRITEBYTECODE=1 \
        PYTHONPATH="$REPO_ROOT/dev/scripts${PYTHONPATH:+:$PYTHONPATH}" \
        "$DEVCTL_PYTHON" -m devctl.runtime.commit_permission_hook "$REPO_ROOT"; then
        exit 1
    fi
fi

exit 0
