#!/usr/bin/env bash
# devctl-install-git-hooks: managed hook for review-snapshot refresh
#
# Blocks raw `git commit` when the typed commit_permission contract says
# implementation is not currently allowed, then auto-refreshes the
# configured ReviewSnapshot file so the committed tree carries a current
# projection even when the commit goes through raw `git commit` (CLI,
# IDE, editor plugin, AI tool) rather than through the governed
# `devctl vcs.commit` action.
#
# Install: `python3 dev/scripts/devctl.py install-git-hooks`
# Uninstall: `python3 dev/scripts/devctl.py install-git-hooks --uninstall`
# Check status: `python3 dev/scripts/devctl.py install-git-hooks --check`
#
# Environment overrides:
#   DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH=1     skip the snapshot refresh only
#   DEVCTL_NO_REVIEW_CHANNEL_STATUS_REFRESH=1
#                                           skip the bridge/status refresh only
#   DEVCTL_REVIEW_SNAPSHOT_RECEIPT_COMMIT=1 skip the gate/refresh on the
#                                           snapshot-only receipt commit
#   DEVCTL_MANAGED_PROJECTION_RECEIPT_COMMIT=1
#                                           allow a repo-owned generated-surface
#                                           receipt only when completed-handoff
#                                           authority and staged-path checks pass
#   DEVCTL_NO_ARTIFACT_WRITES=1             skip the bridge/status + snapshot
#                                           refreshes
#   DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS  snapshot refresh timeout (default 90)
#
# Failure policy:
# - commit_permission failures are blocking. raw git commits must not bypass
#   the existing typed implementation-authority boundary.
# - ReviewSnapshot refresh failures remain warning-only. A failed refresh
#   here cannot abort an otherwise-allowed commit because the CI freshness
#   guard (check_review_snapshot_freshness.py) remains the authoritative
#   backstop for projection drift.

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

if [ "${DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH:-}" = "1" ]; then
    exit 0
fi
if [ "${DEVCTL_NO_ARTIFACT_WRITES:-}" = "1" ]; then
    exit 0
fi

if [ -z "$DEVCTL_PYTHON" ]; then
    exit 0
fi

# Bail out quietly if devctl isn't importable in this clone (partial
# checkout, missing virtualenv, etc.).
if ! "$DEVCTL_PYTHON" dev/scripts/devctl.py --help >/dev/null 2>&1; then
    exit 0
fi

DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS="${DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS:-90}"
case "$DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS" in
    ''|*[!0-9]*)
        echo "[pre-commit hook] invalid DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS; using 90." >&2
        DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS=90
        ;;
esac

run_review_snapshot_refresh() {
    if [ "$DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS" = "0" ]; then
        "$DEVCTL_PYTHON" dev/scripts/devctl.py review-snapshot --write --format terminal >/dev/null 2>&1
        return $?
    fi

    "$DEVCTL_PYTHON" dev/scripts/devctl.py review-snapshot --write --format terminal >/dev/null 2>&1 &
    child_pid=$!
    elapsed=0

    while kill -0 "$child_pid" 2>/dev/null; do
        if [ "$elapsed" -ge "$DEVCTL_REVIEW_SNAPSHOT_TIMEOUT_SECONDS" ]; then
            kill "$child_pid" 2>/dev/null || true
            sleep 1
            if kill -0 "$child_pid" 2>/dev/null; then
                kill -9 "$child_pid" 2>/dev/null || true
            fi
            wait "$child_pid" 2>/dev/null || true
            return 124
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done

    wait "$child_pid"
}

if [ "${DEVCTL_NO_REVIEW_CHANNEL_STATUS_REFRESH:-}" != "1" ] && [ "${DEVCTL_NO_ARTIFACT_WRITES:-}" != "1" ]; then
    if "$DEVCTL_PYTHON" dev/scripts/devctl.py review-channel --action status --terminal none --format json >/dev/null 2>&1; then
        BRIDGE_TARGET=$("$DEVCTL_PYTHON" - <<'PYEOF' 2>/dev/null || echo ""
import sys
from pathlib import Path
sys.path.insert(0, "dev/scripts")
try:
    from devctl.runtime.governance_scan import scan_repo_governance_safely
    governance = scan_repo_governance_safely(Path("."))
    relative = ""
    if governance is not None:
        bridge_config = getattr(governance, "bridge_config", None)
        if bridge_config is not None:
            relative = str(getattr(bridge_config, "bridge_path", "") or "").strip()
    print(relative)
except Exception:
    print("")
PYEOF
)

        if [ -n "$BRIDGE_TARGET" ] && [ -f "$BRIDGE_TARGET" ]; then
            git add "$BRIDGE_TARGET" 2>/dev/null || true
        fi
    else
        echo "[pre-commit hook] devctl review-channel --action status failed; continuing commit." >&2
    fi
fi

# Run the refresh through the typed command so the output path comes
# from ProjectGovernance.artifact_roots.review_snapshot_path (adopter
# repos override it via devctl_repo_policy.json).
if ! run_review_snapshot_refresh; then
    echo "[pre-commit hook] devctl review-snapshot --write failed; continuing commit." >&2
    exit 0
fi

# Resolve the configured target path and stage it if it exists. Not
# hardcoding "dev/audits/REVIEW_SNAPSHOT.md" here: the install command
# installs this hook verbatim into every adopter repo, so the lookup
# has to route through ProjectGovernance.
TARGET=$("$DEVCTL_PYTHON" - <<'PYEOF' 2>/dev/null || echo ""
import sys
from pathlib import Path
sys.path.insert(0, "dev/scripts")
try:
    from devctl.runtime.governance_scan import scan_repo_governance_safely
    governance = scan_repo_governance_safely(Path("."))
    relative = ""
    if governance is not None:
        artifact_roots = getattr(governance, "artifact_roots", None)
        if artifact_roots is not None:
            relative = str(
                getattr(artifact_roots, "review_snapshot_path", "") or ""
            ).strip()
    print(relative or "dev/audits/REVIEW_SNAPSHOT.md")
except Exception:
    print("dev/audits/REVIEW_SNAPSHOT.md")
PYEOF
)

if [ -n "$TARGET" ] && [ -f "$TARGET" ]; then
    git add "$TARGET" 2>/dev/null || true
fi

exit 0
