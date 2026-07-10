#!/usr/bin/env bash
# Reviewer loop: keeps Codex reviewer alive and polling inbox.
#
# Usage: ./dev/scripts/reviewer_loop.sh [--interval SECONDS]
#
# This script continuously:
#   1. Checks for pending packets addressed to Codex
#   2. If packets exist, launches Codex --full-auto with inbox context
#   3. Waits for Codex to complete its review pass
#   4. Repeats
#
# Codex communicates with Claude only through typed review-channel packets.
# All commits/pushes go through the governed devctl system.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# Ensure codex is in PATH (homebrew, pyenv, local bins)
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$HOME/.pyenv/shims:$PATH"

# Codex requires a TTY — fail early if running without one
if ! [ -t 0 ]; then
    echo "[reviewer-loop] ERROR: stdin is not a terminal. Codex requires a TTY."
    echo "[reviewer-loop] Launch in Terminal.app: ./dev/scripts/reviewer_loop.sh"
    exit 1
fi

INTERVAL="30"
if [[ $# -ge 1 && "$1" == "--interval" ]]; then
    INTERVAL="${2:-30}"
elif [[ $# -ge 1 ]]; then
    INTERVAL="$1"
fi

REVIEWER_PROMPT='You are the Codex REVIEWER for this repo.

STEP 1: Read your inbox:
  python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status pending --terminal none --format md --execution-mode markdown-bridge

STEP 2: For each pending packet from Claude, review the referenced code.
  - Read the files mentioned in the packet body
  - Check for correctness, fail-closed contracts, code shape compliance
  - Run relevant tests if needed

STEP 3: Post your review back via typed packet:
  python3 dev/scripts/devctl.py review-channel --action post --from-agent codex --to-agent claude --kind finding --summary "..." --body "..." --terminal none --format json --execution-mode markdown-bridge

STEP 4: Also review any uncommitted worktree changes:
  git diff --stat
  Then read and review any changed files.

Rules: Communicate ONLY through typed packets. Never raw git push. Read CLAUDE.md for full governance rules.'

echo "[reviewer-loop] Starting continuous reviewer loop (interval=${INTERVAL}s)"
echo "[reviewer-loop] Repo: $REPO_ROOT"

ROUND=0
while true; do
    ROUND=$((ROUND + 1))
    echo ""
    echo "[reviewer-loop] === Round $ROUND ($(date -u '+%Y-%m-%dT%H:%M:%SZ')) ==="

    # Check for pending packets
    PENDING=$(python3 dev/scripts/devctl.py review-channel --action inbox \
        --target codex --status pending \
        --terminal none --format json --execution-mode markdown-bridge 2>/dev/null \
        | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    q = d.get('queue', {})
    print(q.get('pending_codex', 0))
except:
    print(0)
" 2>/dev/null || echo "0")

    echo "[reviewer-loop] Pending packets for Codex: $PENDING"

    # Check worktree: staged + unstaged + untracked
    DIRTY=$(( $(git diff --stat 2>/dev/null | wc -l) + $(git diff --cached --stat 2>/dev/null | wc -l) + $(git ls-files --others --exclude-standard 2>/dev/null | wc -l) ))
    DIRTY=$(echo "$DIRTY" | tr -d ' ')

    if [[ "$PENDING" -gt 0 ]] || [[ "$DIRTY" -gt 0 ]]; then
        echo "[reviewer-loop] Launching Codex reviewer pass (packets=$PENDING, dirty=$DIRTY)..."
        codex --full-auto "$REVIEWER_PROMPT" 2>&1 || true
        echo "[reviewer-loop] Codex pass completed."
    else
        echo "[reviewer-loop] Nothing to review. Sleeping ${INTERVAL}s..."
    fi

    sleep "$INTERVAL"
done
