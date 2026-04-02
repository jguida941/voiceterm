#!/usr/bin/env bash
#
# Remote Bridge Loop — launch Claude Code with remote-control for
# dual-agent coordination with Codex through bridge.md.
#
# Usage:
#   ./dev/scripts/remote-bridge-loop.sh [--session-name NAME] [--no-caffeinate] [--dry-run]
#
# Canonical devctl equivalent: none yet (this is the launcher).
# Requires: Claude Code >= 2.1.51, authenticated via /login.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SESSION_NAME="VoiceTerm Bridge Loop"
USE_CAFFEINATE=true
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --session-name) SESSION_NAME="$2"; shift 2 ;;
        --no-caffeinate) USE_CAFFEINATE=false; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --help|-h)
            echo "Usage: ./dev/scripts/remote-bridge-loop.sh [--session-name NAME] [--no-caffeinate] [--dry-run]"
            echo ""
            echo "Launches Claude Code with remote-control for bridge-based"
            echo "dual-agent coordination with Codex."
            echo ""
            echo "Options:"
            echo "  --session-name NAME   Session label shown in claude.ai/code (default: VoiceTerm Bridge Loop)"
            echo "  --no-caffeinate       Skip caffeinate (Mac will sleep normally)"
            echo "  --dry-run             Print the command without executing"
            echo ""
            echo "After launch, scan the QR code or open the URL on your phone."
            echo "Then steer the session from anywhere."
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

cd "$REPO_ROOT"

# Preflight checks
if ! command -v claude &>/dev/null; then
    echo "Error: claude CLI not found. Install Claude Code first."
    exit 1
fi

CLAUDE_VERSION="$(claude --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')"
if [[ -z "$CLAUDE_VERSION" ]]; then
    echo "Warning: could not detect Claude Code version."
fi

if [[ ! -f ".claude/commands/bridge-loop.md" ]]; then
    echo "Error: slash command not found at .claude/commands/bridge-loop.md"
    exit 1
fi

if [[ ! -f "bridge.md" ]]; then
    echo "Warning: bridge.md not found — Codex may not have set up the bridge yet."
fi

# Keep Mac awake (display sleep ok, system stays up)
if [[ "$USE_CAFFEINATE" == true ]]; then
    if command -v caffeinate &>/dev/null; then
        caffeinate -s &
        CAFFEINATE_PID=$!
        echo "caffeinate started (PID $CAFFEINATE_PID) — Mac will stay awake."
        trap "kill $CAFFEINATE_PID 2>/dev/null || true" EXIT
    fi
fi

echo ""
echo "=== Remote Bridge Loop ==="
echo "Session:  $SESSION_NAME"
echo "Repo:     $REPO_ROOT"
echo ""
echo "After launch:"
echo "  1. Scan the QR code or open the URL on your phone"
echo "  2. Type /project:bridge-loop to start the coordination loop"
echo "  3. Or just tell Claude what to do — it knows the architecture"
echo "==========================="
echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] Would execute:"
    echo "  claude --remote-control \"$SESSION_NAME\""
    exit 0
fi

exec claude --remote-control "$SESSION_NAME"
