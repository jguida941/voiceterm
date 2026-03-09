# VoiceTerm Mobile App

SwiftUI iPhone/iPad shell over the shared `VoiceTermMobileCore` package.

This app does not invent a second backend. It renders the same
`devctl mobile-status` bundle the desktop Operator Console now prefers:

- `dev/reports/mobile/latest/full.json`
- `dev/reports/mobile/latest/compact.json`
- `dev/reports/mobile/latest/actions.json`

## Current Behavior

- starts in built-in sample mode so the app is usable immediately
- auto-detects a synced `Documents/LiveBundle/` and can switch to it with
  `Use Live Repo Bundle`
- imports either the emitted mobile bundle folder or its `full.json` file
- remembers the imported bundle source between launches
- renders the shared multi-agent dashboard and safe action cards
- stays read-first; device-side execution still belongs to `devctl`

## Generate Project

```bash
cd app/ios/VoiceTermMobileApp
xcodegen generate
```

Open:

```bash
open VoiceTermMobileApp.xcodeproj
```

## Build Without Signing

```bash
cd app/ios/VoiceTermMobileApp
xcodebuild -project VoiceTermMobileApp.xcodeproj \
  -scheme VoiceTermMobileApp \
  -destination generic/platform=iOS \
  CODE_SIGNING_ALLOWED=NO \
  build
```

## Run On Device

1. Open `VoiceTermMobileApp.xcodeproj` in Xcode.
2. Set your Apple development team for `VoiceTermMobileApp`.
3. Build and run on the target iPhone or simulator.
4. Use `Import Bundle` and choose either the folder that contains the latest
   `mobile-status` projections or that folder's `full.json` file.

## Sync Real Repo Data Into Simulator

From the repo root, with the app already installed in the booted simulator:

```bash
app/ios/VoiceTermMobileApp/sync_live_bundle_to_simulator.sh
```

That script emits the current `mobile-status` bundle from the live repo state,
copies it into the app sandbox under `Documents/LiveBundle/`, and makes the
`Use Live Repo Bundle` button available in the app.
