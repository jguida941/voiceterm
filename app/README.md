# App Launchers

Platform-specific application launchers for VoiceTerm.

Start here based on what you want:

- macOS launcher: use `macos/VoiceTerm.app`
- Desktop operator workflow: read [operator_console/README.md](operator_console/README.md)
- iPhone/iPad companion: read [ios/README.md](ios/README.md)

## macOS

`macos/VoiceTerm.app` - Double-click app that opens a folder picker and launches VoiceTerm in Terminal.

**Usage:**

1. Double-click `VoiceTerm.app`
2. Select your project folder
3. Terminal opens with VoiceTerm running in that folder

**Building:** The app is a simple AppleScript wrapper. No build step required.

## Windows

`windows/` - Windows launcher (coming soon)

**Planned features:**

- Windows Terminal integration
- PowerShell launcher
- WSL2 support

## Control-Plane Direction

Operator control surfaces stay Rust-first in this repo:

- runtime UI/voice/PTY behavior is the Rust overlay
- operator actions route through `devctl` and policy-gated controller commands
- phone/SSH views consume `controller_state` projections
- optional desktop wrappers may exist, but only as thin operator consoles over the
  existing Rust runtime and repo-owned command surfaces

## VoiceTerm Operator Console

`operator_console/` - optional PyQt6 VoiceTerm Operator Console for the
current review-channel workflow.

Use this when you want a desktop control/read surface for the repo workflow.
Do not start here if you only want the normal VoiceTerm overlay.

Current prototype scope:

- bridge-derived Codex, Claude, and Operator status panes (parsed from `code_audit.md`)
- `review-channel` launch and rollover buttons (launcher wrapper, not live terminal)
- repo-visible operator approve/deny artifacts
- raw `code_audit.md` view, launcher output, and diagnostics pane
- optional persisted dev logs under `dev/reports/review_channel/operator_console/`
- dark operator-console theme for bridge/launcher monitoring sessions

Recommended source-checkout launcher:

```bash
./scripts/operator_console.sh --dev-log
```

The script launches `app/operator_console/run.py` and installs `PyQt6` for the
current Python interpreter when it is missing.

All status indicators derive from periodic parsing of the markdown bridge
(`code_audit.md`). Optional `review_state.json` adds structured approval
packets only — it does not upgrade the console to live terminal telemetry.
When structured review state is absent, the status bar shows
`markdown bridge only; live terminal telemetry unavailable`. The console does
not replace the Rust overlay or embed a full terminal emulator.

## iPhone App

`ios/VoiceTermMobileApp/` - the actual Xcode-backed iPhone/iPad app target.

`ios/VoiceTermMobile/` - the shared Swift package used by that app for bundle
decoding and dashboard UI.

Use this when you want a mobile read/control surface backed by repo-emitted
mobile bundles.

Current scope:

- reads the same emitted `devctl mobile-status` projection bundle preferred by
  the desktop mobile relay path (`dev/reports/mobile/latest/full.json`,
  `compact.json`, and `actions.json`)
- renders a SwiftUI app shell with overview metrics, plan/findings sections,
  multi-agent lane cards, and safe action cards
- exposes typed Ralph/controller action previews from the shared mobile bundle
- keeps simple vs technical reading modes in the UI so it can mirror the
  easier-vs-deeper split already present in the PyQt6 console
- includes a guided simulator demo script for real local verification

Fastest local demo:

```bash
python3 dev/scripts/devctl.py mobile-app --action simulator-demo --format md
```

Real physical-device path:

```bash
python3 dev/scripts/devctl.py mobile-app --action device-install --development-team <TEAM_ID> --format md
```

Verify with:

```bash
cd app/ios/VoiceTermMobile
swift test
```

Build the iOS shell without signing:

```bash
cd app/ios/VoiceTermMobileApp
xcodegen generate
xcodebuild -project VoiceTermMobileApp.xcodeproj -scheme VoiceTermMobileApp -destination generic/platform=iOS CODE_SIGNING_ALLOWED=NO build
```

Overview doc:

```bash
open app/ios/README.md
```
