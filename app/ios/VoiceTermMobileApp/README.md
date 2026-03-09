# VoiceTerm Mobile App

SwiftUI iPhone/iPad shell over the shared `VoiceTermMobileCore` package.

This app does not invent a second backend. It renders the same
`devctl mobile-status` bundle the desktop Operator Console now prefers:

- `dev/reports/mobile/latest/full.json`
- `dev/reports/mobile/latest/compact.json`
- `dev/reports/mobile/latest/actions.json`

## Current Behavior

- starts in built-in sample mode so the app is usable immediately
- imports a folder that contains the emitted mobile bundle
- remembers the imported folder between launches
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
4. Use `Import Bundle` and choose the folder that contains the latest
   `mobile-status` projections.
