#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
APP_DIR="$ROOT_DIR/app/ios/VoiceTermMobileApp"
RUN_SCRIPT="$APP_DIR/run_simulator_test.sh"
DEVICE_ID="${1:-}"
APP_ID="com.voiceterm.VoiceTermMobileApp"
LIVE_REVIEW="${VOICETERM_MOBILE_LIVE_REVIEW:-0}"

cat <<'EOF'
VoiceTerm iOS guided simulator demo
===================================

Current runnable app:
  app/ios/VoiceTermMobileApp

Shared package used by that app:
  app/ios/VoiceTermMobile

This demo will build the app, install it in the simulator, sync the latest
repo-backed mobile bundle, and launch the app.
EOF

if [[ "$LIVE_REVIEW" == "1" ]]; then
  cat <<'EOF'

Live review-loop mode is enabled.
The simulator will use the current repo-backed review/control projections,
not just sample-only data.
EOF
fi

if [[ -n "$DEVICE_ID" ]]; then
  "$RUN_SCRIPT" "$DEVICE_ID"
else
  "$RUN_SCRIPT"
fi

SIM_DEVICE="${DEVICE_ID:-booted}"
APP_DATA_DIR="$(xcrun simctl get_app_container "$SIM_DEVICE" "$APP_ID" data)"
LIVE_BUNDLE_DIR="$APP_DATA_DIR/Documents/LiveBundle"

echo
echo "Current live mobile action preview"
echo "=================================="
python3 "$ROOT_DIR/dev/scripts/devctl.py" mobile-status \
  --phone-json dev/reports/autonomy/queue/phone/latest.json \
  --review-status-dir dev/reports/review_channel/latest \
  --view actions \
  --format md || true

cat <<EOF

What to do in the simulator
===========================

1. Wait for VoiceTerm Mobile App to finish launching.
2. On the first screen, tap "Use Live Repo Bundle".
3. Confirm the app shows real repo-backed data instead of only sample data.
4. Open the Terminal section and verify the Codex, Claude, and Operator lane
   views render.

What you should see
===================

- Overview cards from the emitted mobile-status bundle
- Findings and action cards from the same repo-backed bundle
- A read-only Terminal section with split/combined lane views
- Typed Ralph-loop controller previews for report-only, pause, and resume
  when those actions are present in the live bundle

If the live button does not appear or does not switch
=====================================================

- Tap "Reload" once and try "Use Live Repo Bundle" again.
- Confirm the synced bundle exists here:
  $LIVE_BUNDLE_DIR
- The required file is:
  $LIVE_BUNDLE_DIR/full.json

Important boundary
==================

- The phone app now shows real repo-backed Ralph/controller action previews.
- Execution still belongs to repo-owned devctl commands on the host.
- The app is not yet issuing live pause/resume/continue commands by itself.

Docs
====

- app/ios/README.md
- app/ios/VoiceTermMobileApp/README.md
- app/ios/VoiceTermMobile/README.md
EOF

if [[ "$LIVE_REVIEW" == "1" ]]; then
  cat <<'EOF'

Live Ralph/review loop notes
============================

- The app is showing the current repo-backed review/control state from this checkout.
- The Ralph/review loop still executes on the host through repo-owned devctl commands.
- Refresh the live review state with:
  python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md
- Continue with the bounded Ralph/controller actions from the host:
  python3 dev/scripts/devctl.py controller-action --action dispatch-report-only --branch develop --dry-run --format md
  python3 dev/scripts/devctl.py controller-action --action pause-loop --dry-run --format md
  python3 dev/scripts/devctl.py controller-action --action resume-loop --dry-run --format md
- The simulator is a live read surface over those repo-owned commands, not a direct task executor yet.
EOF
fi
