#!/bin/bash
#
# VoiceTerm Operator Console launcher
# Run from the repo root: ./scripts/operator_console.sh
#

set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required to launch the VoiceTerm Operator Console." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

exec python3 -m app.operator_console.run --ensure-pyqt6 "$@"
