#!/usr/bin/env bash
#
# Remote Bridge Loop — launch Claude Code remote control for
# bridge-backed coordination with the repo-owned review channel.
#
# Usage:
#   ./dev/scripts/remote-bridge-loop.sh [--session-name NAME] [--session-url URL] [--session-id ID] [--bootstrap-review-channel] [--no-caffeinate] [--dry-run]
#
# This is project-local glue, not a second control plane. It syncs the local
# slash command from the tracked prompt source, checks Claude auth, prints the
# current typed review-channel health, and can optionally relaunch the
# sanctioned Codex+Claude review loop before opening remote control.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROMPT_SOURCE="$REPO_ROOT/dev/scripts/remote_bridge_prompt.md"
COMMAND_DIR="$REPO_ROOT/.claude/commands"
COMMAND_TARGET="$COMMAND_DIR/bridge-loop.md"
SESSION_NAME="VoiceTerm Bridge Loop"
CLAUDE_SESSION_URL=""
CLAUDE_REMOTE_SESSION_ID=""
USE_CAFFEINATE=true
BOOTSTRAP_REVIEW_CHANNEL=false
DRY_RUN=false
CAFFEINATE_PID=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --session-name) SESSION_NAME="$2"; shift 2 ;;
        --session-url) CLAUDE_SESSION_URL="$2"; shift 2 ;;
        --session-id) CLAUDE_REMOTE_SESSION_ID="$2"; shift 2 ;;
        --bootstrap-review-channel) BOOTSTRAP_REVIEW_CHANNEL=true; shift ;;
        --no-caffeinate) USE_CAFFEINATE=false; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --help|-h)
            echo "Usage: ./dev/scripts/remote-bridge-loop.sh [--session-name NAME] [--session-url URL] [--session-id ID] [--bootstrap-review-channel] [--no-caffeinate] [--dry-run]"
            echo ""
            echo "Launches Claude Code remote control for bridge-based"
            echo "coordination with the repo-owned review channel."
            echo ""
            echo "Options:"
            echo "  --session-name NAME        Session label shown in claude.ai/code"
            echo "                             (default: VoiceTerm Bridge Loop)"
            echo "  --session-url URL          Attach a known claude.ai/code remote URL"
            echo "                             into typed review-channel runtime state"
            echo "  --session-id ID            Attach a known remote session id when the"
            echo "                             full URL is not available"
            echo "  --bootstrap-review-channel Relaunch the sanctioned Codex+Claude"
            echo "                             review loop first if it is inactive"
            echo "  --no-caffeinate            Skip caffeinate (Mac will sleep normally)"
            echo "  --dry-run                  Print the commands without executing"
            echo ""
            echo "The launcher syncs .claude/commands/bridge-loop.md from"
            echo "dev/scripts/remote_bridge_prompt.md on real runs."
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

cleanup() {
    if [[ -n "$CAFFEINATE_PID" ]]; then
        kill "$CAFFEINATE_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT

register_remote_attachment() {
    local attachment_status="$1"
    local -a attach_cmd=(
        python3 dev/scripts/devctl.py review-channel
        --action attach-remote-control
        --terminal none
        --format json
        --remote-provider claude
        --remote-role implementer
        --session-name "$SESSION_NAME"
        --attachment-status "$attachment_status"
    )

    if [[ -n "$CLAUDE_SESSION_URL" ]]; then
        attach_cmd+=(--session-url "$CLAUDE_SESSION_URL")
    fi
    if [[ -n "$CLAUDE_REMOTE_SESSION_ID" ]]; then
        attach_cmd+=(--remote-session-id "$CLAUDE_REMOTE_SESSION_ID")
    fi

    if ! "${attach_cmd[@]}" >/dev/null 2>&1; then
        echo "Warning: could not register typed remote-control attachment ($attachment_status)." >&2
    fi
}

is_review_channel_bootstrap_command() {
    local command="$1"

    [[ -n "$command" ]] || return 1

    case "$command" in
        *"dev/scripts/devctl.py review-channel --action launch"*|\
        *"dev/scripts/devctl.py review-channel --action rollover"*|\
        *"dev/scripts/devctl.py review-channel --action ensure"*|\
        *"dev/scripts/devctl.py review-channel --action reviewer-heartbeat"*|\
        *"dev/scripts/devctl.py review-channel --action recover"*|\
        *"dev/scripts/devctl.py review-channel --action render-bridge"*)
            return 0
            ;;
    esac

    return 1
}

is_repo_owned_shell_command() {
    local command="$1"

    [[ -n "$command" ]] || return 1
    [[ "$command" == *"dev/scripts/devctl.py"* ]] || return 1
    [[ "$command" == *" "* ]] || return 1

    return 0
}

cd "$REPO_ROOT"

if ! command -v claude >/dev/null 2>&1; then
    echo "Error: claude CLI not found. Install Claude Code first."
    exit 1
fi

CLAUDE_VERSION="$(claude --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || true)"
if [[ -z "$CLAUDE_VERSION" ]]; then
    echo "Warning: could not detect Claude Code version; --remote-control support is unverified."
else
    # --remote-control landed in 2.1.51; compare major.minor.patch
    IFS='.' read -r V_MAJ V_MIN V_PAT <<<"$CLAUDE_VERSION"
    if (( V_MAJ < 2 || (V_MAJ == 2 && V_MIN < 1) || (V_MAJ == 2 && V_MIN == 1 && V_PAT < 51) )); then
        echo "Error: Claude Code $CLAUDE_VERSION is too old; --remote-control requires >= 2.1.51."
        exit 1
    fi
fi

if [[ "$DRY_RUN" != true ]]; then
    AUTH_STATUS="$(claude auth status 2>/dev/null || true)"
    if [[ "$AUTH_STATUS" != *'"loggedIn": true'* ]]; then
        echo "Error: Claude Code is not logged in."
        echo "Run: claude auth login"
        if [[ -n "$AUTH_STATUS" ]]; then
            echo "$AUTH_STATUS"
        fi
        exit 1
    fi
fi

if [[ ! -f "$PROMPT_SOURCE" ]]; then
    echo "Error: tracked prompt source not found at $PROMPT_SOURCE"
    exit 1
fi

if [[ ! -f "bridge.md" ]]; then
    echo "Warning: bridge.md not found — Codex may not have set up the bridge yet."
fi

if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] Would sync $COMMAND_TARGET from $PROMPT_SOURCE."
else
    mkdir -p "$COMMAND_DIR"
    if [[ ! -f "$COMMAND_TARGET" ]] || ! cmp -s "$PROMPT_SOURCE" "$COMMAND_TARGET"; then
        cp "$PROMPT_SOURCE" "$COMMAND_TARGET"
        echo "Synced $COMMAND_TARGET from $PROMPT_SOURCE."
    fi
fi

REVIEW_STATUS_JSON=""
REVIEWER_MODE="unknown"
EFFECTIVE_MODE="unknown"
CODEX_ACTIVE="unknown"
CLAUDE_ACTIVE="unknown"
ATTENTION_STATUS="unknown"
RECOMMENDED_ACTION=""
RECOMMENDED_COMMAND=""
RECOMMENDED_COMMAND_SOURCE=""
DOCTOR_DECISION_ACTION=""
DOCTOR_DECISION_COMMAND=""
HOOK_STATUS="unknown"
HOOK_FIX_COMMAND="python3 dev/scripts/devctl.py install-git-hooks"

if REVIEW_STATUS_JSON="$(python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json 2>/dev/null)"; then
    REVIEW_FIELDS="$(
        python3 -c 'import json, sys
data = json.load(sys.stdin)
bridge = data.get("bridge_liveness", {})
attention = data.get("attention", {})
doctor = data.get("doctor", {})
fields = [
    bridge.get("reviewer_mode", "unknown"),
    bridge.get("effective_reviewer_mode", bridge.get("reviewer_mode", "unknown")),
    str(bool(bridge.get("codex_conductor_active", False))).lower(),
    str(bool(bridge.get("claude_conductor_active", False))).lower(),
    attention.get("status", "unknown"),
    attention.get("recommended_action", "") or "",
    str(data.get("recommended_command") or ""),
    str(data.get("recommended_command_source") or ""),
    str(doctor.get("decision_action_id") or ""),
    str(doctor.get("decision_command") or ""),
]
print("\t".join(fields))' <<<"$REVIEW_STATUS_JSON"
    )"
    IFS=$'\t' read -r REVIEWER_MODE EFFECTIVE_MODE CODEX_ACTIVE CLAUDE_ACTIVE ATTENTION_STATUS RECOMMENDED_ACTION RECOMMENDED_COMMAND RECOMMENDED_COMMAND_SOURCE DOCTOR_DECISION_ACTION DOCTOR_DECISION_COMMAND <<<"$REVIEW_FIELDS"
else
    echo "Warning: could not read review-channel status. Remote control can still start, but loop health is unknown."
fi

if HOOK_STATUS_JSON="$(python3 dev/scripts/devctl.py install-git-hooks --check --format json 2>/dev/null)"; then
    HOOK_STATUS="$(
        python3 -c 'import json, sys
data = json.load(sys.stdin)
print(str(data.get("hook_status") or "unknown"))' <<<"$HOOK_STATUS_JSON"
    )"
fi

echo ""
echo "=== Remote Bridge Loop ==="
echo "Session:          $SESSION_NAME"
echo "Repo:             $REPO_ROOT"
echo "Slash command:    /project:bridge-loop"
echo "Reviewer mode:    $REVIEWER_MODE"
echo "Effective mode:   $EFFECTIVE_MODE"
echo "Codex active:     $CODEX_ACTIVE"
echo "Claude active:    $CLAUDE_ACTIVE"
echo "Attention status: $ATTENTION_STATUS"
if [[ -n "$RECOMMENDED_ACTION" ]]; then
    echo "Status hint:      $RECOMMENDED_ACTION"
fi
if is_repo_owned_shell_command "$RECOMMENDED_COMMAND"; then
    echo "Next action:      $RECOMMENDED_COMMAND"
    if [[ -n "$RECOMMENDED_COMMAND_SOURCE" ]]; then
        echo "Action source:    $RECOMMENDED_COMMAND_SOURCE"
    fi
elif [[ -n "$RECOMMENDED_COMMAND" ]]; then
    echo "Next decision:    $RECOMMENDED_COMMAND"
fi
if is_repo_owned_shell_command "$DOCTOR_DECISION_COMMAND"; then
    echo "Loop recovery:    $DOCTOR_DECISION_COMMAND"
    if [[ -n "$DOCTOR_DECISION_ACTION" ]]; then
        echo "Recovery action:  $DOCTOR_DECISION_ACTION"
    fi
elif [[ -n "$DOCTOR_DECISION_ACTION" ]]; then
    echo "Recovery action:  $DOCTOR_DECISION_ACTION"
fi
echo "Git hooks:        $HOOK_STATUS"
if [[ "$HOOK_STATUS" != "managed" ]]; then
    echo "Hook fix:         $HOOK_FIX_COMMAND"
fi
if [[ -n "$CLAUDE_SESSION_URL" || -n "$CLAUDE_REMOTE_SESSION_ID" ]]; then
    echo "Remote attach:    typed session registration requested"
fi
echo ""

LAUNCH_REVIEW_CMD=(
    python3 dev/scripts/devctl.py review-channel
    --action launch
    --terminal terminal-app
    --format json
    --execution-mode markdown-bridge
    --refresh-bridge-heartbeat-if-stale
)

BOOTSTRAP_COMMAND_STR="${LAUNCH_REVIEW_CMD[*]}"
BOOTSTRAP_COMMAND_SOURCE="fallback_launch"

if is_review_channel_bootstrap_command "$DOCTOR_DECISION_COMMAND"; then
    BOOTSTRAP_COMMAND_STR="$DOCTOR_DECISION_COMMAND"
    BOOTSTRAP_COMMAND_SOURCE="doctor.decision_command"
elif is_review_channel_bootstrap_command "$RECOMMENDED_COMMAND"; then
    BOOTSTRAP_COMMAND_STR="$RECOMMENDED_COMMAND"
    BOOTSTRAP_COMMAND_SOURCE="recommended_command"
fi

if [[ "$BOOTSTRAP_REVIEW_CHANNEL" == true ]]; then
    if [[ "$EFFECTIVE_MODE" == "active_dual_agent" && "$CODEX_ACTIVE" == "true" && "$CLAUDE_ACTIVE" == "true" ]]; then
        echo "Review channel already live; skipping bootstrap."
    elif [[ "$DRY_RUN" == true ]]; then
        printf '[dry-run] Would execute (%s):' "$BOOTSTRAP_COMMAND_SOURCE"
        if [[ "$BOOTSTRAP_COMMAND_SOURCE" == "fallback_launch" ]]; then
            printf ' %q' "${LAUNCH_REVIEW_CMD[@]}"
        else
            printf ' %s' "$BOOTSTRAP_COMMAND_STR"
        fi
        printf '\n'
    else
        echo "Bootstrapping repo-owned review channel ($BOOTSTRAP_COMMAND_SOURCE)..."
        if [[ "$BOOTSTRAP_COMMAND_SOURCE" == "fallback_launch" ]]; then
            "${LAUNCH_REVIEW_CMD[@]}"
        else
            mapfile -t BOOTSTRAP_CMD < <(
                python3 -c 'import shlex, sys
for token in shlex.split(sys.argv[1]):
    print(token)' "$BOOTSTRAP_COMMAND_STR"
            )
            "${BOOTSTRAP_CMD[@]}"
        fi
    fi
elif [[ "$EFFECTIVE_MODE" != "active_dual_agent" || "$CODEX_ACTIVE" != "true" || "$CLAUDE_ACTIVE" != "true" ]]; then
    echo "Review loop is not fully live."
    echo "Suggested bootstrap ($BOOTSTRAP_COMMAND_SOURCE): $BOOTSTRAP_COMMAND_STR"
    echo "Pass --bootstrap-review-channel now, or tell Claude to use the typed recovery command instead of inventing a relaunch path."
fi

if [[ "$DRY_RUN" != true ]] && [[ "$USE_CAFFEINATE" == true ]] && command -v caffeinate >/dev/null 2>&1; then
    caffeinate -s &
    CAFFEINATE_PID=$!
    echo "caffeinate started (PID $CAFFEINATE_PID) — Mac will stay awake."
fi

echo ""
echo "After launch:"
echo "  1. Scan the QR code or open the URL Claude prints on your phone"
echo "  2. If your terminal does not render the QR, use the printed URL"
echo "  3. Type /project:bridge-loop to load the tracked remote bridge prompt"
echo "  4. Ask for 'status' or 'what is codex doing' to have Claude relay bridge state"
echo "  5. Optional: rerun this wrapper with --session-url <printed-link> from another local shell to attach the live Claude URL into typed review-channel state"
echo "========================="
echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo "[dry-run] Would execute:"
    echo "  claude --remote-control \"$SESSION_NAME\""
    exit 0
fi

if [[ -n "$CLAUDE_SESSION_URL" || -n "$CLAUDE_REMOTE_SESSION_ID" ]]; then
    register_remote_attachment "attached"
else
    register_remote_attachment "unknown"
fi

set +e
claude --remote-control "$SESSION_NAME"
CLAUDE_EXIT=$?
set -e

register_remote_attachment "detached"

exit "$CLAUDE_EXIT"
