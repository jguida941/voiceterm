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
#   DEVCTL_REVIEW_SNAPSHOT_RECEIPT_COMMIT=1 skip the gate/refresh on the
#                                           snapshot-only receipt commit
#   DEVCTL_NO_ARTIFACT_WRITES=1             skip the snapshot refresh only
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

if ! command -v python3 >/dev/null 2>&1; then
    echo "[pre-commit hook] python3 is required to evaluate commit_permission; raw git commit is blocked." >&2
    exit 1
fi

if ! PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="$REPO_ROOT/dev/scripts${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m devctl.runtime.commit_permission_hook "$REPO_ROOT"; then
    exit 1
fi

if [ "${DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH:-}" = "1" ]; then
    exit 0
fi
if [ "${DEVCTL_NO_ARTIFACT_WRITES:-}" = "1" ]; then
    exit 0
fi

# Bail out quietly if devctl isn't importable in this clone (partial
# checkout, missing virtualenv, etc.).
if ! python3 dev/scripts/devctl.py --help >/dev/null 2>&1; then
    exit 0
fi

# Run the refresh through the typed command so the output path comes
# from ProjectGovernance.artifact_roots.review_snapshot_path (adopter
# repos override it via devctl_repo_policy.json).
if ! python3 dev/scripts/devctl.py review-snapshot --write --format terminal >/dev/null 2>&1; then
    echo "[pre-commit hook] devctl review-snapshot --write failed; continuing commit." >&2
    exit 0
fi

# Resolve the configured target path and stage it if it exists. Not
# hardcoding "dev/audits/REVIEW_SNAPSHOT.md" here: the install command
# installs this hook verbatim into every adopter repo, so the lookup
# has to route through ProjectGovernance.
TARGET=$(python3 - <<'PYEOF' 2>/dev/null || echo ""
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
