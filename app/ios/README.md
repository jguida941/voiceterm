# VoiceTerm iOS

This directory has one runnable app and one shared package.

## What Is Current

- `VoiceTermMobileApp/` is the actual iPhone/iPad app target.
- `VoiceTermMobile/` is the shared Swift package used by that app.

If you want to run VoiceTerm on iPhone or in the simulator, start from
`VoiceTermMobileApp/`.

## Fastest Simulator Demo

From the repo root:

```bash
python3 dev/scripts/devctl.py mobile-app --action simulator-demo --format md
python3 dev/scripts/devctl.py mobile-app --action simulator-demo --live-review --format md
```

That script:

- boots a simulator if needed
- builds and installs `VoiceTermMobileApp`
- syncs the latest repo-backed mobile bundle into the app sandbox
- launches the app
- prints the exact taps, expected screens, and current Ralph/controller action
  preview from the live bundle

Use `--live-review` when you want the simulator run to refresh the current
review-channel state first and then sync that live repo-backed Ralph/review
bundle into the app. That is the closest current mode to "real loop data in
the simulator" without pretending the app itself is the task executor.

For a plugged-in iPhone or iPad:

```bash
python3 dev/scripts/devctl.py mobile-app --action device-wizard --format md
```

That wizard detects connected physical devices, opens the Xcode project, and
prints the honest signing/install steps for a real device build.

If you already know the Apple Development Team ID to use:

```bash
python3 dev/scripts/devctl.py mobile-app --action device-install --development-team <TEAM_ID> --format md
```

That path attempts a real signed build, device install, and launch through
`xcodebuild` plus `xcrun devicectl`. It is still honest about the real
dependency: if signing is not configured or no device is connected, it fails
with the exact missing prerequisite instead of pretending the install worked.

## Directory Map

- `VoiceTermMobile/`: shared models, bundle decoding, and SwiftUI dashboard
  components
- `VoiceTermMobileApp/`: Xcode app shell, simulator scripts, and app-specific
  import/live-bundle behavior

## Retired Wording

Older docs called the mobile work a "client scaffold". That wording is now
retired because it made the package/app split sound like two competing apps.

Archive record:

- `dev/archive/2026-03-09-ios-mobile-scaffold-language-retired.md`
