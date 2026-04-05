#!/usr/bin/env bash
# Governance pre-commit hook — blocks commit when guard bundle fails.
#
# Install:
#   cp dev/config/templates/portable_governance_pre_commit_hook.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# Or use the governed path:
#   python3 dev/scripts/devctl.py commit --message "..."
#
# Skip (emergency only):
#   git commit --no-verify ...

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"

# Use --profile quick for speed; the full CI profile runs in push preflight
# and CI pipelines. --format json suppresses interactive decoration.
# Guard exit code is captured explicitly so the remediation message prints.
exit_code=0
python3 "$REPO_ROOT/dev/scripts/devctl.py" check --profile quick --format json 2>/dev/null || exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "[pre-commit] Guard bundle failed. Fix violations before committing."
    echo "[pre-commit] Run: python3 dev/scripts/devctl.py check --profile quick"
    echo "[pre-commit] Or use: python3 dev/scripts/devctl.py commit --message '...'"
    exit 1
fi
