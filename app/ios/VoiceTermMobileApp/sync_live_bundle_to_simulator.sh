#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DEVICE_ID="${1:-booted}"
APP_ID="${VOICETERM_MOBILE_APP_ID:-com.voiceterm.VoiceTermMobileApp}"
TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

cd "$ROOT_DIR"

python3 dev/scripts/devctl.py mobile-status \
  --phone-json dev/reports/autonomy/queue/phone/latest.json \
  --review-status-dir dev/reports/review_channel/latest \
  --emit-projections "$TMP_DIR" \
  --format md >/dev/null

APP_DATA_DIR="$(xcrun simctl get_app_container "$DEVICE_ID" "$APP_ID" data)"
LIVE_BUNDLE_DIR="$APP_DATA_DIR/Documents/LiveBundle"
rm -rf "$LIVE_BUNDLE_DIR"
mkdir -p "$LIVE_BUNDLE_DIR"
cp "$TMP_DIR"/full.json "$LIVE_BUNDLE_DIR"/
for optional_file in compact.json alert.json actions.json latest.md; do
  if [[ -f "$TMP_DIR/$optional_file" ]]; then
    cp "$TMP_DIR/$optional_file" "$LIVE_BUNDLE_DIR"/
  fi
done

echo "Synced live bundle to $LIVE_BUNDLE_DIR"
