#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PROJECT="$ROOT_DIR/app/ios/VoiceTermMobileApp/VoiceTermMobileApp.xcodeproj"
SCHEME="VoiceTermMobileApp"
BUILD_CONFIG="Debug"
DERIVED_DATA_PATH="/tmp/voiceterm-mobile-derived"
SIMULATOR_DEVICE_ID="${1:-}"
APP_ID="com.voiceterm.VoiceTermMobileApp"
SYNC_SCRIPT="$ROOT_DIR/app/ios/VoiceTermMobileApp/sync_live_bundle_to_simulator.sh"

usage() {
  cat <<'EOF'
Usage: run_simulator_test.sh [device-udid]
If no UDID is supplied, the script uses the first booted simulator or the first listed available device from `xcrun simctl list devices`.
EOF
}

if [[ "${SIMULATOR_DEVICE_ID}" == "--help" || "${SIMULATOR_DEVICE_ID}" == "-h" ]]; then
  usage
  exit 0
fi

find_device() {
  local booted
  booted="$(xcrun simctl list devices booted | grep -Eo '[0-9A-F-]{36}' | head -n 1)"
  if [[ -n "$booted" ]]; then
    echo "$booted"
    return
  fi
  xcrun simctl list devices available | grep -Eo '[0-9A-F-]{36}' | head -n 1
}

if [[ -z "$SIMULATOR_DEVICE_ID" ]]; then
  SIMULATOR_DEVICE_ID="$(find_device)"
fi

if [[ -z "$SIMULATOR_DEVICE_ID" ]]; then
  echo "No simulator device available; define a UDID or boot a simulator first." >&2
  exit 1
fi

boot_device() {
  if ! xcrun simctl list devices booted | grep -q "$SIMULATOR_DEVICE_ID"; then
    echo "Booting simulator $SIMULATOR_DEVICE_ID"
    xcrun simctl boot "$SIMULATOR_DEVICE_ID"
    xcrun simctl bootstatus "$SIMULATOR_DEVICE_ID" -b
  else
    echo "Simulator $SIMULATOR_DEVICE_ID is already booted"
  fi
}

open_simulator_ui() {
  if ! pgrep -f "Simulator" >/dev/null; then
    open -a Simulator --args -CurrentDeviceUDID "$SIMULATOR_DEVICE_ID"
  fi
}

boot_device
open_simulator_ui

echo "Building $SCHEME for simulator $SIMULATOR_DEVICE_ID"
xcodebuild -project "$PROJECT" \
  -scheme "$SCHEME" \
  -configuration "$BUILD_CONFIG" \
  -destination "id=$SIMULATOR_DEVICE_ID" \
  -derivedDataPath "$DERIVED_DATA_PATH" \
  CODE_SIGNING_ALLOWED=NO \
  build

APP_PATH="$DERIVED_DATA_PATH/Build/Products/$BUILD_CONFIG-iphonesimulator/VoiceTermMobileApp.app"

echo "Terminating any running copy"
xcrun simctl terminate "$SIMULATOR_DEVICE_ID" "$APP_ID" >/dev/null 2>&1 || true
echo "Uninstalling previous install"
xcrun simctl uninstall "$SIMULATOR_DEVICE_ID" "$APP_ID" >/dev/null 2>&1 || true

echo "Installing new build"
xcrun simctl install "$SIMULATOR_DEVICE_ID" "$APP_PATH"

echo "Syncing live repo bundle"
"$SYNC_SCRIPT" "$SIMULATOR_DEVICE_ID"

echo "Launching app"
xcrun simctl launch "$SIMULATOR_DEVICE_ID" "$APP_ID"
