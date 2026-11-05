#!/bin/bash
# Record a VoiceTerm session with resize forwarding and HUD debug logging.
# usage: scripts/diagnostics/rec.sh <backend> <name> [extra voiceterm args]
#   e.g. scripts/diagnostics/rec.sh claude jetbrains-claude
# Run it from the project folder you want the backend to work in. Output lands
# in $VOICETERM_CAPTURE_DIR (default ~/voiceterm-captures) as <name>.bytes,
# <name>.bytes.events (resizes with byte offsets) and <name>.log.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
BACKEND=${1:-claude}
NAME=${2:-capture}
if [ $# -ge 2 ]; then shift 2; else shift $#; fi
DIR="${VOICETERM_CAPTURE_DIR:-$HOME/voiceterm-captures}"
mkdir -p "$DIR"
exec env VOICETERM_DEBUG_CLAUDE_HUD=1 VOICETERM_LOG_PATH="$DIR/$NAME.log" \
  python3 "$HERE/ptyrec.py" "$DIR/$NAME.bytes" \
  "$ROOT/scripts/start.sh" --backend "$BACKEND" --logs "$@"
