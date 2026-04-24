#!/usr/bin/env bash
# devctl-install-git-hooks: managed hook for review-snapshot refresh
#
# Creates a trailing ReviewSnapshot receipt commit after ordinary commits.
# The receipt commit is snapshot-only and binds the generated external-review
# surface to the code commit that was just sealed.
#
# Install: `python3 dev/scripts/devctl.py install-git-hooks`
# Uninstall: `python3 dev/scripts/devctl.py install-git-hooks --uninstall`
# Check status: `python3 dev/scripts/devctl.py install-git-hooks --check`
#
# Environment overrides:
#   DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH=1     skip the refresh entirely
#   DEVCTL_REVIEW_SNAPSHOT_RECEIPT_COMMIT=1 skip recursive receipt commits
#   DEVCTL_NO_ARTIFACT_WRITES=1             skip (read-only mount, CI sandbox)
#
# Failure policy: every error is a warning, never a blocker. A failed receipt
# hook must not make `git commit` appear to fail after the commit already
# succeeded; the freshness guard remains the authoritative backstop.

set -eu

if [ "${DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH:-}" = "1" ]; then
    exit 0
fi
if [ "${DEVCTL_REVIEW_SNAPSHOT_RECEIPT_COMMIT:-}" = "1" ]; then
    exit 0
fi
if [ "${DEVCTL_NO_ARTIFACT_WRITES:-}" = "1" ]; then
    exit 0
fi

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

if [ -z "$DEVCTL_PYTHON" ]; then
    exit 0
fi

if ! "$DEVCTL_PYTHON" dev/scripts/devctl.py --help >/dev/null 2>&1; then
    exit 0
fi

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

if [ -z "$TARGET" ]; then
    exit 0
fi

# A snapshot-only HEAD is already a receipt. Without this guard, a manually
# created receipt commit could trigger an infinite receipt-on-receipt chain.
CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null || true)
if [ "$CHANGED" = "$TARGET" ]; then
    exit 0
fi

if ! "$DEVCTL_PYTHON" dev/scripts/devctl.py review-snapshot --write --receipt-commit --format terminal >/dev/null 2>&1; then
    echo "[post-commit hook] devctl review-snapshot --receipt-commit failed; continuing commit." >&2
fi

exit 0
